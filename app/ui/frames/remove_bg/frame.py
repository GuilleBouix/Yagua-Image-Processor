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

import logging
import threading
from tkinter import filedialog

import customtkinter as ctk

from app.ui import colors, fonts
from app.translations import t
from app.ui.frames.base import BaseFrame
from app.ui.frames.remove_bg.services import (
    batch_quitar_fondo,
    ensure_model,
    estado_rembg,
    modelo_descargado,
    FORMATOS_SALIDA,
    INSTALL_COMMAND,
)

logger = logging.getLogger(__name__)


class RemoveBgFrame(BaseFrame):
    """
    Frame del modulo de eliminacion de fondo.
    Procesa una o varias imagenes y exporta con transparencia.
    """

    def __init__(self, parent):
        """Inicializa el frame."""
        self._formato_salida: ctk.StringVar = ctk.StringVar(value='PNG')
        self._spinner_frame = None
        self._spinner_label = None
        self._spinner_bar = None
        self._lbl_error_dependencia = None
        self._entry_dependencia_cmd = None
        self._btn_copiar_comando = None
        super().__init__(parent, t('remove_bg_title'))

    def _build_content(self):
        """Construye el contenido del modulo."""
        self._crear_spinner()
        self._inicializar_en_background()

    def _crear_spinner(self):
        """Crea un spinner dentro del modulo (no bloqueante)."""
        self._spinner_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        self._spinner_frame.grid(row=1, column=0, padx=28, pady=(8, 6), sticky='ew')
        self._spinner_frame.grid_columnconfigure(0, weight=1)

        self._spinner_label = ctk.CTkLabel(
            self._spinner_frame,
            text=t('loading_model'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            anchor='w'
        )
        self._spinner_label.grid(row=0, column=0, padx=16, pady=(12, 6), sticky='w')

        self._spinner_bar = ctk.CTkProgressBar(
            self._spinner_frame,
            width=220,
            height=10,
            corner_radius=8,
            fg_color=colors.SIDEBAR_SEPARATOR,
            progress_color=colors.ACENTO,
            mode='indeterminate'
        )
        self._spinner_bar.grid(row=1, column=0, padx=16, pady=(0, 12), sticky='w')

    def _inicializar_en_background(self):
        """Inicializa checks pesados sin bloquear la UI."""
        self._show_overlay(t('loading_model'))

        def _worker():
            try:
                disponible, detalle_error = estado_rembg()
            except Exception as exc:
                logger.warning("Error al verificar rembg: %s", exc)
                disponible = False
                detalle_error = str(exc).strip() or type(exc).__name__
            try:
                modelo_ok = modelo_descargado() if disponible else False
            except Exception as exc:
                logger.warning("Error al verificar modelo: %s", exc)
                modelo_ok = False
            self.after(0, lambda: self._build_content_ready(disponible, modelo_ok, detalle_error))

        threading.Thread(target=_worker, daemon=True).start()

    def _build_content_ready(self, disponible: bool, modelo_ok: bool, detalle_error: str | None = None):
        """Construye el contenido una vez finalizados los checks."""
        self._hide_overlay()

        if not disponible:
            self._construir_aviso_dependencia(detalle_error)
            return

        row = 2
        if not modelo_ok:
            self._construir_aviso_primer_uso(row)
            row += 1

        # Boton seleccionar
        self._btn_seleccionar = self._crear_boton_seleccionar(self)
        self._btn_seleccionar.grid(row=row, column=0, padx=28, pady=8, sticky='ew')
        row += 1

        # Lista de archivos
        self._lista_frame = self._crear_lista_archivos(self, height=200)
        self._lista_frame.grid(row=row, column=0, padx=28, pady=8, sticky='ew')
        self._lista_frame.grid_columnconfigure(0, weight=1)
        row += 1

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
        panel.grid(row=row, column=0, padx=28, pady=8, sticky='ew')
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

    def _show_overlay(self, text: str):
        """Muestra spinner dentro del modulo (no bloqueante)."""
        if not self._spinner_frame or not self._spinner_label or not self._spinner_bar:
            return
        self._spinner_label.configure(text=text)
        self._spinner_frame.grid()
        try:
            self._spinner_bar.start()
        except Exception:
            pass

    def _hide_overlay(self):
        """Oculta el spinner interno."""
        if not self._spinner_frame or not self._spinner_bar:
            return
        try:
            self._spinner_bar.stop()
        except Exception:
            pass
        self._spinner_frame.grid_remove()

    def _construir_aviso_dependencia(self, detalle_error: str | None):
        """Muestra panel con el error real y ayuda para instalar dependencias."""
        panel = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel.grid(row=1, column=0, padx=28, pady=8, sticky='ew')
        panel.grid_columnconfigure(0, weight=1)
        resumen, detalle = self._resumir_error_dependencia(detalle_error)

        self._lbl_error_dependencia = ctk.CTkLabel(
            panel,
            text=resumen,
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            anchor='w',
            justify='left',
            wraplength=620
        )
        self._lbl_error_dependencia.grid(row=0, column=0, padx=16, pady=(16, 6), sticky='w')

        if detalle:
            ctk.CTkLabel(
                panel,
                text=detalle,
                font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY,
                anchor='w',
                justify='left',
                wraplength=620
            ).grid(row=1, column=0, padx=16, pady=(0, 6), sticky='w')
            row_reinstall = 2
        else:
            row_reinstall = 1

        ctk.CTkLabel(
            panel,
            text=t('rembg_reinstall_app'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor='w',
            justify='left',
            wraplength=620
        ).grid(row=row_reinstall, column=0, padx=16, pady=(0, 8), sticky='w')

        ctk.CTkLabel(
            panel,
            text=t('rembg_install_from_source'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor='w',
            justify='left',
            wraplength=620
        ).grid(row=row_reinstall + 1, column=0, padx=16, pady=(0, 8), sticky='w')

        fila_comando = ctk.CTkFrame(panel, fg_color='transparent')
        fila_comando.grid(row=row_reinstall + 2, column=0, padx=16, pady=(0, 16), sticky='ew')
        fila_comando.grid_columnconfigure(0, weight=1)

        self._entry_dependencia_cmd = ctk.CTkEntry(
            fila_comando,
            font=ctk.CTkFont(family='Courier New', size=13),
            text_color=colors.ACENTO,
            fg_color=colors.SIDEBAR_BG,
            border_color=colors.SIDEBAR_SEPARATOR,
            justify='left'
        )
        self._entry_dependencia_cmd.grid(row=0, column=0, sticky='ew', padx=(0, 8))
        self._entry_dependencia_cmd.insert(0, INSTALL_COMMAND)

        self._btn_copiar_comando = ctk.CTkButton(
            fila_comando,
            text=t('copy_command'),
            width=120,
            height=32,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            hover_color=colors.SIDEBAR_HOVER,
            command=self._copiar_comando_instalacion
        )
        self._btn_copiar_comando.grid(row=0, column=1, sticky='e')

    def _construir_aviso_primer_uso(self, row: int):
        """Muestra aviso de descarga automatica en el primer uso."""
        aviso = ctk.CTkFrame(
            self,
            corner_radius=8,
            fg_color=colors.SIDEBAR_BG,
            border_width=1,
            border_color=colors.ACENTO_DIMMED
        )
        aviso.grid(row=row, column=0, padx=28, pady=(0, 4), sticky='ew')
        aviso.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            aviso,
            text=t('model_first_download'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            justify='center',
            wraplength=500
        ).grid(row=0, column=0, padx=16, pady=10)

    def _copiar_comando_instalacion(self):
        """Copia el comando sugerido al portapapeles."""
        self.clipboard_clear()
        self.clipboard_append(INSTALL_COMMAND)
        self._lbl_info.configure(text=t('command_copied'))

    def _resumir_error_dependencia(self, detalle_error: str | None) -> tuple[str, str | None]:
        """Convierte errores tecnicos en mensajes breves para la UI."""
        detalle = (detalle_error or '').strip()
        detalle_lower = detalle.lower()

        if 'pymatting' in detalle_lower:
            return (
                t('rembg_unavailable_short'),
                str(t('rembg_missing_dependency')).format(dependency='pymatting'),
            )

        if detalle:
            return t('rembg_unavailable_short'), str(t('rembg_error_detail')).format(error=detalle)

        return t('rembg_unavailable_short'), None

    def _cargar_imagenes(self, rutas):
        """Carga las imagenes seleccionadas."""
        limite = 10
        total = len(rutas)
        if total > limite:
            rutas = rutas[:limite]
            self._limite_msg = str(t('limit_reached')).format(limit=limite, total=total)
        else:
            self._limite_msg = None

        super()._cargar_imagenes(rutas)
        n = len(rutas)
        suffix = t('images_loaded') if n > 1 else t('image_loaded')
        msg = f'{n} {suffix}'
        if self._limite_msg:
            msg += f'  -  {self._limite_msg}'
        self._lbl_info.configure(text=msg)

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
            logger.exception("Error en proceso remove_bg")
            msg = str(exc).strip()
            if not msg or msg.lower() == 'none':
                msg = type(exc).__name__
            self.after(0, lambda: self._handle_error(msg))

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
