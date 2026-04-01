"""
UI para el modulo de conversion de imagenes.
Permite convertir imagenes entre diferentes formatos.

Relacionado con:
    - app/ui/frames/base.py: Clase base de la que hereda.
    - app/ui/frames/convert/state.py: Estado de la interfaz.
    - app/ui/frames/convert/services.py: Servicios de conversion.
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
from app.ui.frames.convert.services import (
    batch_convertir_safe,
    FORMATOS_DESTINO,
    formato_soporta_calidad,
)
from app.modules.image_utils import heif_supported
from app.ui.frames.convert.state import ConvertState


logger = logging.getLogger(__name__)


class ConvertFrame(BaseFrame):
    """
    Frame del modulo de conversion de formatos.
    
    Permite seleccionar imagenes, elegir formato de destino,
    configurar calidad y convertir las imagenes.
    """
    
    def __init__(self, parent):
        """
        Inicializa el frame de conversion.
        
        Args:
            parent: Widget padre.
        """
        logger.info("convert.ui: init")
        self._state = ConvertState()
        super().__init__(parent, t('convert_title'))

    def _build_content(self):
        """
        Construye el contenido especifico del modulo.
        
        Incluye boton de seleccion, lista de archivos,
        panel de opciones con selector de formato y
        boton de convertir.
        """
        logger.info("convert.ui: build_content")
        # Boton para seleccionar imagenes
        self._btn_seleccionar = self._crear_boton_seleccionar(self)
        self._btn_seleccionar.grid(row=1, column=0, padx=28, pady=8, sticky='ew')

        # Lista de archivos seleccionados
        self._lista_frame = self._crear_lista_archivos(self, height=200)
        self._lista_frame.grid(row=2, column=0, padx=28, pady=8, sticky='ew')
        self._lista_frame.grid_columnconfigure(0, weight=1)

        # Label de lista vacia
        self._lbl_lista_vacia = self._crear_lista_vacia(self._lista_frame)
        self._lbl_lista_vacia.pack(pady=12)

        # Panel de opciones de conversion
        self._panel_opciones = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        self._panel_opciones.grid(row=3, column=0, padx=28, pady=8, sticky='ew')
        self._panel_opciones.grid_columnconfigure(1, weight=1)
        self._construir_opciones()

    def _construir_opciones(self):
        """
        Construye los controles del panel de opciones.
        
        Incluye selector de formato, slider de calidad
        y boton de convertir.
        """
        p = self._panel_opciones

        # Label de formato destino
        ctk.CTkLabel(
            p, text=t('convert_to'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(16, 8), sticky='w')

        # Selector segmented de formato
        self._seg_formato = ctk.CTkSegmentedButton(
            p,
            values=FORMATOS_DESTINO,
            variable=self._state.fmt_destino,
            font=fonts.FUENTE_CHICA,
            selected_color=colors.SEGMENT_SELECTED,
            selected_hover_color=colors.SEGMENT_SELECTED_HOVER,
            unselected_color=colors.SIDEBAR_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
            text_color_disabled=colors.TEXT_GRAY,
            command=self._actualizar_info,
        )
        self._seg_formato.grid(row=0, column=1, padx=(0, 16), pady=(16, 8), sticky='w')

        # Label de calidad (se muestra/oculta segun formato)
        self._lbl_calidad_label = ctk.CTkLabel(
            p, text=t('quality'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        )
        self._lbl_calidad_label.grid(row=1, column=0, padx=(16, 12), pady=8, sticky='w')

        # Fila con slider y valor de calidad
        fila_cal = ctk.CTkFrame(p, fg_color='transparent')
        fila_cal.grid(row=1, column=1, padx=(0, 16), pady=8, sticky='ew')
        fila_cal.grid_columnconfigure(0, weight=1)

        # Slider de calidad
        self._slider = ctk.CTkSlider(
            fila_cal,
            from_=10, to=100,
            variable=self._state.calidad,
            command=self._actualizar_calidad,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            progress_color=colors.ACENTO,
            fg_color=colors.SIDEBAR_SEPARATOR,
        )
        self._slider.grid(row=0, column=0, sticky='ew', padx=(0, 10))

        # Label del valor de calidad
        self._lbl_calidad = ctk.CTkLabel(
            fila_cal, text=str(self._state.calidad.get()),
            font=fonts.FUENTE_BASE,
            text_color=colors.ACENTO,
            fg_color='transparent',
            width=28
        )
        self._lbl_calidad.grid(row=0, column=1)

        # Boton de convertir
        self._btn_convertir = ctk.CTkButton(
            p,
            text=t('convert_btn'),
            height=40,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._convertir
        )
        self._btn_convertir.grid(
            row=2, column=0, columnspan=2,
            padx=16, pady=(0, 16), sticky='ew'
        )

        self._actualizar_info()

    def _cargar_imagenes(self, rutas):
        """
        Carga las imagenes seleccionadas.
        
        Args:
            rutas: Lista de rutas de archivos a cargar.
        """
        logger.info("convert.ui: cargar_imagenes (total=%s)", len(rutas))
        limite = 100
        total = len(rutas)
        if total > limite:
            rutas = rutas[:limite]
            self._limite_msg = t('limit_reached').format(limit=limite, total=total)
        else:
            self._limite_msg = None

        super()._cargar_imagenes(rutas)
        self._state.imagenes = list(rutas)
        self._actualizar_info()
        logger.info("convert.ui: imagenes cargadas (mostradas=%s)", len(rutas))

    def _actualizar_calidad(self, val):
        """
        Actualiza el label de calidad.
        
        Args:
            val: Nuevo valor del slider.
        """
        self._lbl_calidad.configure(text=str(int(val)))

    def _actualizar_info(self, *args):
        """
        Actualiza el estado de la UI segun el formato seleccionado.
        
        Muestra/oculta el slider de calidad segun si el
        formato soporta calidad.
        """
        fmt = self._state.fmt_destino.get()
        logger.debug("convert.ui: actualizar_info (fmt=%s)", fmt)
        if fmt == 'HEIC' and not heif_supported():
            self._btn_convertir.configure(state='disabled')
            self._lbl_info.configure(text=t('heic_requires_plugin'))
            return
        self._btn_convertir.configure(state='normal')
        tiene_calidad = formato_soporta_calidad(fmt)
        
        # Habilitar/deshabilitar slider de calidad
        self._slider.configure(state='normal' if tiene_calidad else 'disabled')
        
        # Cambiar color de labels segun disponibilidad
        self._lbl_calidad_label.configure(
            text_color=colors.TEXT_GRAY if tiene_calidad else colors.ACENTO_DIMMED
        )
        self._lbl_calidad.configure(
            text_color=colors.ACENTO if tiene_calidad else colors.ACENTO_DIMMED
        )
        
        # Mostrar cantidad de imagenes
        if self._imagenes:
            n = len(self._imagenes)
            suffix = t('images_loaded') if n > 1 else t('image_loaded')
            msg = f'{n} {suffix} -> {fmt}'
            if self._limite_msg:
                msg += f'  -  {self._limite_msg}'
            self._lbl_info.configure(text=msg)

    def _convertir(self):
        """
        Inicia el proceso de conversion en segundo plano.
        """
        logger.info("convert.ui: click_convertir")
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_images_first_convert'))
            return

        if self._state.fmt_destino.get() == 'HEIC' and not heif_supported():
            self._lbl_info.configure(text=t('heic_requires_plugin'))
            return
        
        carpeta = filedialog.askdirectory(title=t('select_output_folder'))
        if not carpeta:
            logger.info("convert.ui: proceso_cancelado (sin_carpeta)")
            return
        
        self._btn_convertir.configure(state='disabled', text=t('converting'))
        self._show_full_overlay(t('processing'))
        threading.Thread(target=self._proceso, args=(carpeta,), daemon=True).start()

    def _proceso(self, carpeta):
        """
        Ejecuta la conversion en segundo plano.
        
        Args:
            carpeta: Ruta de la carpeta de salida.
        """
        logger.info("convert.ui: proceso_interno_inicio (imagenes=%s, fmt=%s)", len(self._imagenes), self._state.fmt_destino.get())
        res = batch_convertir_safe(
            self._imagenes,
            fmt_destino=self._state.fmt_destino.get(),
            carpeta_salida=carpeta,
            calidad=self._state.calidad.get(),
        )
        self.after(0, lambda: self._finalizar(
            res['ok'],
            res['errores'],
            res['fmt_destino'],
            res.get('conflictos', 0),
        ))

    def _finalizar(self, ok, errores, fmt, conflictos=0):
        """
        Muestra el resultado final de la conversion.
        
        Args:
            ok: Cantidad de imagenes procesadas.
            errores: Cantidad de errores.
            fmt: Formato de destino.
        """
        self._btn_convertir.configure(state='normal', text=t('convert_btn'))
        self._hide_full_overlay()
        logger.info("convert.ui: finalizar_ok (ok=%s, errores=%s, conflictos=%s)", ok, errores, conflictos)
        msg = f'{ok} imagen{"es" if ok != 1 else ""} {t("converted_to" if ok == 1 else "converted_to_plural")} {fmt}'
        if errores:
            msg += f'  -  {errores} {t("error_occurred")}'
        if conflictos:
            msg += f'  -  {conflictos} {t("conflicts_renamed")}'
        self._lbl_info.configure(text=msg)
