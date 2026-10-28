"""Avisos locales; los documentos se abren solo cuando el usuario lo solicita."""
from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
from tkinter import TclError

import customtkinter as ctk
from PIL import Image, ImageTk

from app.translations import t
from app.ui import colors, fonts, styles
from app.utils.paths import resource_path

logger = logging.getLogger(__name__)


def document_blocks(content):
    """Present the Markdown subset used by our local notices as readable text."""
    def inline(value):
        """Representa enlaces y énfasis del Markdown como texto plano para CTk."""
        value = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', value)
        value = re.sub(r'\*\*(.*?)\*\*', r'\1', value, flags=re.DOTALL)
        return re.sub(r'`([^`]+)`', r'\1', value)

    for block in re.split(r'\n\s*\n', content.strip()):
        lines = block.splitlines()
        if re.match(r'^#{1,6}\s', block):
            yield inline(re.sub(r'^#{1,6}\s+', '', block)), 'heading'
        elif lines[0].lstrip().startswith('|'):
            for line in lines:
                cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
                if all(re.fullmatch(r':?-+:?', cell) for cell in cells):
                    continue
                yield inline(' — '.join(cells)), 'body'
        elif re.match(r'^\s*[-*]\s', block):
            items = []
            for line in lines:
                if re.match(r'^\s*[-*]\s', line):
                    items.append(re.sub(r'^\s*[-*]\s+', '• ', line))
                elif items:
                    items[-1] += ' ' + line.strip()
            yield inline('\n'.join(items)), 'body'
        else:
            yield inline(' '.join(line.strip() for line in lines)), 'body'


class LegalPanel(ctk.CTkFrame):
    """Muestra avisos legales locales y abre los documentos incluidos."""
    def __init__(self, parent, *, set_status):
        """Carga rutas legales locales y construye los avisos compactos."""
        super().__init__(parent, **styles.surface('panel'))
        self._set_status = set_status
        self._window = None
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=t('legal_title'), font=fonts.FUENTE_BASE,
                     anchor='w').grid(row=0, column=0, padx=16, pady=(12, 4), sticky='ew')
        self._labels = []
        for row, key in enumerate(('legal_originals', 'legal_connections'), 1):
            label = ctk.CTkLabel(self, text=t(key), font=fonts.FUENTE_CHICA,
                                 text_color=colors.TEXT_GRAY, anchor='w', justify='left',
                                 width=1, wraplength=500)
            label.grid(row=row, column=0, padx=16, pady=(0, 10), sticky='ew')
            self._labels.append(label)
        styles.Button(self, role='secondary', text=t('legal_open'),
                      font=fonts.FUENTE_CHICA, command=self._open_documents).grid(
                          row=3, column=0, padx=16, pady=(0, 12), sticky='w')
        self.bind('<Configure>', self._fit_text, add=True)

    def _fit_text(self, event):
        """Adapta el texto del aviso al tamaño del panel disponible."""
        width = max(80, int(event.width / self._get_widget_scaling()) - 32)
        for label in self._labels:
            if label.cget('wraplength') != width:
                label.configure(wraplength=width)

    def _open_documents(self):
        """Abre el documento legal seleccionado dentro de la ventana local."""
        if self._window is not None and self._window.winfo_exists():
            self._window.lift()
            return
        window = ctk.CTkToplevel(self)
        self._window = window
        window.title(t('legal_open'))
        window.geometry('760x540')
        window.minsize(360, 300)
        window.transient(self.winfo_toplevel())
        self._set_window_icon(window)
        if sys.platform == 'win32':
            # CustomTkinter vuelve a aplicar su icono después de 200 ms.
            window.after(250, lambda: self._set_window_icon(window))
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(1, weight=1)
        documents = {'Yagua (MIT)': 'LICENSE', t('legal_third_party'): 'THIRD_PARTY_NOTICES.md',
                     t('legal_sources'): 'legal/SOURCE_CODE.md'}
        text = ctk.CTkTextbox(window, font=fonts.FUENTE_CHICA, wrap='word',
                             border_spacing=12)
        text.grid(row=1, column=0, padx=12, pady=12, sticky='nsew')
        text.tag_config('heading', foreground=colors.TEXT_COLOR, spacing1=8, spacing3=6)
        text.tag_config('body', spacing1=2, spacing3=4)

        def show_document(name):
            """Carga el documento local elegido y lo representa en el área de lectura."""
            try:
                content = resource_path(documents[name]).read_text(encoding='utf-8')
            except OSError:
                logger.exception('Cannot read local legal document')
                content = t('legal_error')
            text.configure(state='normal')
            text.delete('1.0', 'end')
            if documents[name].endswith('.md'):
                for block, tag in document_blocks(content):
                    text.insert('end', block + '\n\n', tag)
            else:
                # License originals remain verbatim, including their line breaks.
                text.insert('1.0', content)
            text.yview_moveto(0)
            text.configure(state='disabled')

        field = styles.OptionField(window, values=list(documents), font=fonts.FUENTE_CHICA,
                                   command=show_document)
        field.grid(row=0, column=0, padx=12, pady=(12, 0), sticky='ew')
        styles.Button(window, role='secondary', text=t('legal_folder'),
                      font=fonts.FUENTE_CHICA, command=self._open_folder).grid(
                          row=2, column=0, padx=12, pady=(0, 12), sticky='w')
        show_document('Yagua (MIT)')

    def _set_window_icon(self, window):
        """Aplica el icono de Yagua después de que CTk crea la ventana."""
        if not window.winfo_exists():
            return
        try:
            if sys.platform == 'win32':
                window.iconbitmap(str(resource_path('assets/icon.ico')))
            else:
                with Image.open(resource_path('assets/icon.png')) as image:
                    self._legal_icon = ImageTk.PhotoImage(image.convert('RGBA'), master=window)
                window.iconphoto(False, self._legal_icon)
        except (OSError, TclError):
            logger.warning('Cannot apply Yagua icon to legal window', exc_info=True)

    def _open_folder(self):
        """Abre la carpeta legal local del checkout o del paquete."""
        try:
            path = resource_path('legal').resolve(strict=True)
            if sys.platform == 'win32':
                os.startfile(str(path))
            else:
                subprocess.Popen(['xdg-open', str(path)])
        except OSError:
            logger.exception('Cannot open local legal folder')
            self._set_status(t('legal_error'))
