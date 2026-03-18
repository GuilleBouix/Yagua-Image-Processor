"""
UI para el modulo Convertir.
"""

from __future__ import annotations

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
from app.ui.frames.convert.state import ConvertState


class ConvertFrame(BaseFrame):
    def __init__(self, parent):
        self._state = ConvertState()
        super().__init__(parent, t('convert_title'))

    def _build_content(self):
        # Boton seleccionar imagenes
        self._btn_seleccionar = self._crear_boton_seleccionar(self)
        self._btn_seleccionar.grid(row=1, column=0, padx=28, pady=8, sticky='ew')

        # Lista de archivos
        self._lista_frame = self._crear_lista_archivos(self, height=200)
        self._lista_frame.grid(row=2, column=0, padx=28, pady=8, sticky='ew')
        self._lista_frame.grid_columnconfigure(0, weight=1)

        self._lbl_lista_vacia = self._crear_lista_vacia(self._lista_frame)
        self._lbl_lista_vacia.pack(pady=12)

        # Panel opciones
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
        p = self._panel_opciones

        ctk.CTkLabel(
            p, text=t('convert_to'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(16, 8), sticky='w')

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

        self._lbl_calidad_label = ctk.CTkLabel(
            p, text=t('quality'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        )
        self._lbl_calidad_label.grid(row=1, column=0, padx=(16, 12), pady=8, sticky='w')

        fila_cal = ctk.CTkFrame(p, fg_color='transparent')
        fila_cal.grid(row=1, column=1, padx=(0, 16), pady=8, sticky='ew')
        fila_cal.grid_columnconfigure(0, weight=1)

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

        self._lbl_calidad = ctk.CTkLabel(
            fila_cal, text=str(self._state.calidad.get()),
            font=fonts.FUENTE_BASE,
            text_color=colors.ACENTO,
            fg_color='transparent',
            width=28
        )
        self._lbl_calidad.grid(row=0, column=1)

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

    def _cargar_imagenes(self, rutas: list[str]):
        super()._cargar_imagenes(rutas)
        self._state.imagenes = list(rutas)
        self._actualizar_info()

    def _actualizar_calidad(self, val):
        self._lbl_calidad.configure(text=str(int(val)))

    def _actualizar_info(self, *_):
        fmt = self._state.fmt_destino.get()
        tiene_calidad = formato_soporta_calidad(fmt)
        self._slider.configure(state='normal' if tiene_calidad else 'disabled')
        self._lbl_calidad_label.configure(
            text_color=colors.TEXT_GRAY if tiene_calidad else colors.ACENTO_DIMMED
        )
        self._lbl_calidad.configure(
            text_color=colors.ACENTO if tiene_calidad else colors.ACENTO_DIMMED
        )
        if self._imagenes:
            n = len(self._imagenes)
            suffix = t('images_loaded') if n > 1 else t('image_loaded')
            self._lbl_info.configure(text=f'{n} {suffix} -> {fmt}')

    def _convertir(self):
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_images_first_convert'))
            return
        carpeta = filedialog.askdirectory(title=t('select_output_folder'))
        if not carpeta:
            return
        self._btn_convertir.configure(state='disabled', text=t('converting'))
        threading.Thread(target=self._proceso, args=(carpeta,), daemon=True).start()

    def _proceso(self, carpeta: str):
        res = batch_convertir_safe(
            self._imagenes,
            fmt_destino=self._state.fmt_destino.get(),
            carpeta_salida=carpeta,
            calidad=self._state.calidad.get(),
        )
        self.after(0, lambda: self._finalizar(res['ok'], res['errores'], res['fmt_destino']))

    def _finalizar(self, ok, errores, fmt):
        self._btn_convertir.configure(state='normal', text=t('convert_btn'))
        msg = f'{ok} imagen{"es" if ok != 1 else ""} {t("converted_to" if ok == 1 else "converted_to_plural")} {fmt}'
        if errores:
            msg += f'  -  {errores} {t("error_occurred")}'
        self._lbl_info.configure(text=msg)
