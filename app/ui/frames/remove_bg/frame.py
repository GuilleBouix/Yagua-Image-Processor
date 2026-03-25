"""
UI para el modulo de eliminacion de fondo de imagenes.
Quita el fondo y exporta con transparencia en el formato elegido.

Relacionado con:
    - app/ui/frames/base.py: Clase base de la que hereda.
    - app/ui/frames/remove_bg/state.py: Estado de la interfaz.
    - app/ui/frames/remove_bg/services.py: Servicios de logica.
    - app/translations/__init__.py: Traducciones de la UI.
"""

from __future__ import annotations

import threading
from tkinter import filedialog

import customtkinter as ctk

from app.ui import colors, fonts
from app.translations import t
from app.ui.frames.base import BaseFrame
from app.ui.frames.remove_bg.services import (
    batch_quitar_fondo,
    ensure_model,
    rembg_disponible,
    modelo_descargado,
    FORMATOS_SALIDA,
)


class RemoveBgFrame(BaseFrame):
    """
    Frame del modulo de eliminacion de fondo.
    Procesa una o varias imagenes y exporta con transparencia.
    """

    def __init__(self, parent):
        """Inicializa el frame."""
        self._formato_salida: ctk.StringVar = ctk.StringVar(value='PNG')
        self._overlay = None
        self._overlay_label = None
        self._overlay_bar = None
        self._overlay_bind_id = None
        super().__init__(parent, t('remove_bg_title'))

    def _build_content(self):
        """Construye el contenido del modulo."""
        self._inicializar_en_background()

    def _inicializar_en_background(self):
        """Inicializa checks pesados sin bloquear la UI."""
        self._show_overlay(t('loading_model'))

        def _worker():
            try:
                disponible = rembg_disponible()
            except Exception as exc:
                self.logger.warning("Error al verificar rembg: %s", exc)
                disponible = False
            try:
                modelo_ok = modelo_descargado() if disponible else False
            except Exception as exc:
                self.logger.warning("Error al verificar modelo: %s", exc)
                modelo_ok = False
            self.after(0, lambda: self._build_content_ready(disponible, modelo_ok))

        threading.Thread(target=_worker, daemon=True).start()

    def _build_content_ready(self, disponible: bool, modelo_ok: bool):
        """Construye el contenido una vez finalizados los checks."""
        self._hide_overlay()

        if not disponible:
            self._construir_aviso_dependencia()
            return

        if not modelo_ok:
            self._construir_aviso_primer_uso()

        # Boton seleccionar
        self._btn_seleccionar = self._crear_boton_seleccionar(self)
        self._btn_seleccionar.grid(row=1, column=0, padx=28, pady=8, sticky='ew')

        # Lista de archivos
        self._lista_frame = self._crear_lista_archivos(self, height=200)
        self._lista_frame.grid(row=2, column=0, padx=28, pady=8, sticky='ew')
        self._lista_frame.grid_columnconfigure(0, weight=1)

        self._lbl_lista_vacia = self._crear_lista_vacia(self._lista_frame)
        self._lbl_lista_vacia.pack(pady=12)

        # Panel de opciones
        panel = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel.grid(row=3, column=0, padx=28, pady=8, sticky='ew')
        panel.grid_columnconfigure(1, weight=1)

        # Descripcion
        ctk.CTkLabel(
            panel,
            text=t('remove_bg_description'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(14, 8), sticky='w')

        # Selector de formato
        ctk.CTkLabel(
            panel, text=t('output_format'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=1, column=0, padx=(16, 12), pady=(0, 8), sticky='w')

        ctk.CTkSegmentedButton(
            panel,
            values=FORMATOS_SALIDA,
            variable=self._formato_salida,
            font=fonts.FUENTE_CHICA,
            selected_color=colors.SEGMENT_SELECTED,
            selected_hover_color=colors.SEGMENT_SELECTED_HOVER,
            unselected_color=colors.SIDEBAR_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
        ).grid(row=1, column=1, padx=(0, 16), pady=(0, 8), sticky='w')

        # Boton procesar
        self._btn_procesar = ctk.CTkButton(
            panel,
            text=t('remove_bg_btn'),
            height=40,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._procesar
        )
        self._btn_procesar.grid(
            row=2, column=0, columnspan=2,
            padx=16, pady=(0, 16), sticky='ew'
        )

    def _sync_overlay_geometry(self):
        """Ajusta el overlay al tamaño y posición de la ventana."""
        if not self._overlay or not self._overlay.winfo_exists():
            return
        root = self.winfo_toplevel()
        root.update_idletasks()
        w = root.winfo_width()
        h = root.winfo_height()
        x = root.winfo_rootx()
        y = root.winfo_rooty()
        self._overlay.geometry(f'{w}x{h}+{x}+{y}')

    def _show_overlay(self, text: str):
        """Muestra un overlay full-screen con spinner."""
        if self._overlay and self._overlay.winfo_exists():
            if self._overlay_label:
                self._overlay_label.configure(text=text)
            return

        root = self.winfo_toplevel()
        root.update_idletasks()

        self._overlay = ctk.CTkToplevel(root)
        self._overlay.overrideredirect(True)
        self._overlay.attributes('-topmost', True)
        try:
            self._overlay.attributes('-alpha', 0.9)
        except Exception:
            pass

        self._overlay.configure(fg_color=colors.FRAMES_BG)
        self._sync_overlay_geometry()

        base = ctk.CTkFrame(self._overlay, fg_color=colors.FRAMES_BG)
        base.pack(fill='both', expand=True)

        content = ctk.CTkFrame(base, fg_color='transparent')
        content.place(relx=0.5, rely=0.5, anchor='center')

        self._overlay_label = ctk.CTkLabel(
            content,
            text=text,
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR
        )
        self._overlay_label.pack(pady=(0, 10))

        self._overlay_bar = ctk.CTkProgressBar(
            content,
            width=240,
            height=10,
            corner_radius=8,
            fg_color=colors.SIDEBAR_SEPARATOR,
            progress_color=colors.ACENTO,
            mode='indeterminate'
        )
        self._overlay_bar.pack()
        self._overlay_bar.start()

        self._overlay.grab_set()
        self._overlay_bind_id = root.bind(
            '<Configure>', lambda _e: self._sync_overlay_geometry(), add='+'
        )

    def _hide_overlay(self):
        """Oculta y destruye el overlay."""
        if not self._overlay or not self._overlay.winfo_exists():
            return
        try:
            if self._overlay_bar:
                self._overlay_bar.stop()
            self._overlay.grab_release()
        except Exception:
            pass
        root = self.winfo_toplevel()
        if self._overlay_bind_id:
            try:
                root.unbind('<Configure>', self._overlay_bind_id)
            except Exception:
                pass
            self._overlay_bind_id = None
        self._overlay.destroy()
        self._overlay = None
        self._overlay_label = None
        self._overlay_bar = None

    def _construir_aviso_dependencia(self):
        """Muestra panel de instalacion cuando rembg no esta disponible."""
        panel = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel.grid(row=1, column=0, padx=28, pady=8, sticky='ew')
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            panel,
            text=t('rembg_not_installed'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            justify='center'
        ).grid(row=0, column=0, padx=16, pady=(16, 8))

        ctk.CTkLabel(
            panel,
            text='pip install rembg onnxruntime',
            font=ctk.CTkFont(family='Courier New', size=13),
            text_color=colors.ACENTO,
            fg_color=colors.SIDEBAR_BG,
            corner_radius=6,
        ).grid(row=1, column=0, padx=16, pady=(0, 16), ipadx=12, ipady=6)

    def _construir_aviso_primer_uso(self):
        """Muestra aviso de descarga automatica en el primer uso."""
        aviso = ctk.CTkFrame(
            self,
            corner_radius=8,
            fg_color=colors.SIDEBAR_BG,
            border_width=1,
            border_color=colors.ACENTO_DIMMED
        )
        aviso.grid(row=0, column=0, padx=28, pady=(0, 4), sticky='ew')
        aviso.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            aviso,
            text=t('model_first_download'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            justify='center',
            wraplength=500
        ).grid(row=0, column=0, padx=16, pady=10)

    def _cargar_imagenes(self, rutas):
        """Carga las imagenes seleccionadas."""
        super()._cargar_imagenes(rutas)
        n = len(rutas)
        suffix = t('images_loaded') if n > 1 else t('image_loaded')
        self._lbl_info.configure(text=f'{n} {suffix}')

    def _procesar(self):
        """Inicia el proceso en segundo plano."""
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_images_first'))
            return

        carpeta = filedialog.askdirectory(title=t('select_output_folder'))
        if not carpeta:
            return

        self._btn_procesar.configure(state='disabled', text=t('processing'))
        self._show_overlay(t('loading_model'))
        threading.Thread(target=self._proceso, args=(carpeta,), daemon=True).start()

    def _proceso(self, carpeta):
        """Ejecuta la eliminacion de fondo."""
        try:
            if not modelo_descargado():
                self.after(0, lambda: self._show_overlay(t('downloading_model')))
                ensure_model()
                self.after(0, lambda: self._show_overlay(t('loading_model')))
            res = batch_quitar_fondo(
                self._imagenes,
                carpeta,
                formato_salida=self._formato_salida.get()
            )
            self.after(0, lambda: self._finalizar(
                res['ok'],
                res['errores'],
                res.get('conflictos', 0),
            ))
        except Exception as exc:
            self.after(0, lambda: self._handle_error(str(exc)))

    def _handle_error(self, msg: str):
        """Maneja errores y restaura el estado visual."""
        self._hide_overlay()
        self._btn_procesar.configure(state='normal', text=t('remove_bg_btn'))
        self._lbl_info.configure(text=f'{t("error_generic")}: {msg}')

    def _finalizar(self, ok, errores, conflictos=0):
        """Muestra el resultado final."""
        self._hide_overlay()
        self._btn_procesar.configure(state='normal', text=t('remove_bg_btn'))
        suffix = t('images_loaded') if ok > 1 else t('image_loaded')
        msg = f'{ok} {suffix} {t("processed")}'
        if errores:
            msg += f'  -  {errores} {t("error_occurred")}'
        if conflictos:
            msg += f'  -  {conflictos} {t("conflicts_renamed")}'
        self._lbl_info.configure(text=msg)
