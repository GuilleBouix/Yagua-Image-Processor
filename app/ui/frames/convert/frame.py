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

from app.ui.building import stepwise, steps_for
import logging

import customtkinter as ctk

from app.ui import colors, fonts, styles
from app.translations import t
from app.ui.status import operation_summary
from app.ui.frames.base import BaseFrame
from app.ui.file_list import FileList
from app.ui.frames.convert.services import (
    batch_convertir_safe,
    FORMATOS_DESTINO,
    formato_soporta_calidad,
)
from app.utils.image_utils import heif_supported
from app.ui.frames.convert.state import ConvertState


logger = logging.getLogger(__name__)


class ConvertFrame(BaseFrame):
    """
    Frame del modulo de conversion de formatos.
    
    Permite seleccionar imagenes, elegir formato de destino,
    configurar calidad y convertir las imagenes.
    """
    
    design_system = True
    show_size_notice = True

    def __init__(self, parent, *, defer_build=False):
        """
        Inicializa el frame de conversion.
        
        Args:
            parent: Widget padre.
        """
        logger.info("convert.ui: init")
        self._state = ConvertState()
        super().__init__(parent, t('convert_title'), defer_build=defer_build)

    @stepwise
    def _build_content(self):
        """
        Construye el contenido especifico del modulo.
        
        Incluye boton de seleccion, lista de archivos,
        panel de opciones con selector de formato y
        boton de convertir.
        """
        logger.info("convert.ui: build_content")
        yield
        self.grid_rowconfigure(3, weight=1)
        yield

        self._btn_seleccionar = self._crear_boton_seleccionar(self)
        yield
        self._btn_seleccionar.grid(row=1, column=0, padx=24, pady=(0, 12), sticky='ew')
        yield

        self._panel_opciones = ctk.CTkFrame(
            self,
            **styles.surface('panel'),
        )
        yield
        self._panel_opciones.grid(row=4, column=0, padx=24, pady=(0, 12), sticky='ew')
        yield
        self._panel_opciones.grid_columnconfigure(1, weight=1)
        yield
        (yield from steps_for(self._construir_opciones))
        yield

        # Lista de archivos seleccionados
        ctk.CTkLabel(
            self, text=t('files_loaded').capitalize(), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).grid(row=2, column=0, padx=24, pady=(0, 8), sticky='w')
        yield
        self._lista_frame = self._crear_lista_archivos(self, height=220)
        yield
        self._lista_frame.grid(row=3, column=0, padx=24, pady=(0, 12), sticky='nsew')
        yield
        self._lista_frame.grid_columnconfigure(0, weight=1)
        yield

        # Label de lista vacia
        self._lbl_lista_vacia = self._crear_lista_vacia(self._lista_frame)
        yield
        self._lbl_lista_vacia.pack(pady=12)
        yield

    @stepwise
    def _construir_opciones(self):
        """
        Construye los controles del panel de opciones.
        
        Incluye selector de formato, slider de calidad
        y boton de convertir.
        """
        p = self._panel_opciones
        yield

        # Label de formato destino
        ctk.CTkLabel(
            p, text=t('convert_to'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(16, 8), sticky='w')
        yield

        # Selector segmented de formato
        self._seg_formato = styles.SegmentedButton(
            p,
            values=FORMATOS_DESTINO,
            variable=self._state.fmt_destino,
            font=fonts.FUENTE_CHICA,
            command=self._actualizar_info,
        )
        yield
        self._seg_formato.grid(row=0, column=1, padx=(0, 16), pady=(16, 8), sticky='w')
        yield

        # Label de calidad (se muestra/oculta segun formato)
        self._lbl_calidad_label = ctk.CTkLabel(
            p, text=t('quality'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        )
        yield
        self._lbl_calidad_label.grid(row=1, column=0, padx=(16, 12), pady=8, sticky='w')
        yield

        # Fila con slider y valor de calidad
        fila_cal = ctk.CTkFrame(p, fg_color='transparent')
        yield
        fila_cal.grid(row=1, column=1, padx=(0, 16), pady=8, sticky='ew')
        yield
        fila_cal.grid_columnconfigure(0, weight=1)
        yield

        # Slider de calidad
        self._slider = ctk.CTkSlider(
            fila_cal,
            from_=10, to=100,
            variable=self._state.calidad,
            command=self._actualizar_calidad,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            progress_color=colors.ACENTO,
            fg_color=styles.palette().border,
        )
        yield
        self._slider.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        yield

        # Label del valor de calidad
        self._lbl_calidad = ctk.CTkLabel(
            fila_cal, text=str(self._state.calidad.get()),
            font=fonts.FUENTE_BASE,
            text_color=colors.ACENTO,
            fg_color='transparent',
            width=28
        )
        yield
        self._lbl_calidad.grid(row=0, column=1)
        yield

        yield from self._build_save_selector(p, 2, columnspan=2)

        # Boton de convertir
        self._btn_convertir = self._new_button(
            p,
            role='primary',
            text=t('convert_btn'),
            font=fonts.FUENTE_BASE,
            command=self._convertir
        )
        yield
        self._btn_convertir.grid(
            row=3, column=0, columnspan=2,
            padx=16, pady=(0, 16), sticky='ew'
        )
        yield

        self._actualizar_info()
        yield

    def _on_build_complete(self):
        """Conecta acciones y estado cuando terminó la construcción del módulo."""
        super()._on_build_complete()
        self._virtual_file_list = FileList(
            self._lista_frame, self._filas_lista, self._thumbs, design_system=True
        )
        self._virtual_file_list.sync(self._imagenes)

    def _cargar_imagenes(self, rutas):
        """
        Carga las imagenes seleccionadas.
        
        Args:
            rutas: Lista de rutas de archivos a cargar.
        """
        if self._operation_blocked(global_job=False):
            return
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
        p = styles.palette()
        self._slider.configure(button_color=p.primary if tiene_calidad else p.muted,
                               progress_color=p.primary if tiene_calidad else p.disabled)
        
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
            suffix = t('files_loaded').capitalize() if n > 1 else t('image_loaded')
            msg = f'{n} {suffix} -> {fmt}'
            if self._limite_msg:
                msg += f'  -  {self._limite_msg}'
            self._lbl_info.configure(text=msg)

    def _convertir(self):
        """
        Inicia el proceso de conversion en segundo plano.
        """
        if self._operation_blocked(global_job=True):
            return
        logger.info("convert.ui: click_convertir")
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_images_first_convert'))
            return

        if self._state.fmt_destino.get() == 'HEIC' and not heif_supported():
            self._lbl_info.configure(text=t('heic_requires_plugin'))
            return
        
        paths = tuple(self._imagenes)
        fmt, quality = self._state.fmt_destino.get(), self._state.calidad.get()
        def start(folder, plan):
            """Valida formato y selección antes de iniciar el lote de conversión."""
            self._show_full_overlay(t('processing'))
            self._submit_job(lambda: batch_convertir_safe(paths, fmt_destino=fmt,
                carpeta_salida=folder, calidad=quality, output_policy=plan),
                button=self._btn_convertir, text=t('convert_btn'),
                on_success=self._finish_save, on_error=self._fallo_conversion)
        self._prepare_save(paths, fmt, start)

    def _fallo_conversion(self, error):
        """Muestra el error del lote y restaura los controles del módulo."""
        logger.exception("convert.ui: fallo general", exc_info=error)
        self._btn_convertir.configure(state='normal', text=t('convert_btn'))
        self._hide_full_overlay()
        self._lbl_info.configure(text=f'{t("error_generic")}: {error}')

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
        msg = operation_summary(ok, errores)
        self._lbl_info.configure(text=msg)
