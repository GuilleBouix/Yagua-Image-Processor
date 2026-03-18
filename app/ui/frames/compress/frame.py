"""
UI para el modulo de compresion de imagenes.
Permite comprimir imagenes con calidad configurable.

Relacionado con:
    - app/ui/frames/base.py: Clase base de la que hereda.
    - app/ui/frames/compress/state.py: Estado de la interfaz.
    - app/ui/frames/compress/services.py: Servicios de compresion.
    - app/translations/__init__.py: Traducciones de la UI.
"""

from __future__ import annotations

import threading
from tkinter import filedialog

import customtkinter as ctk

from app.ui import colors, fonts
from app.translations import t
from app.ui.frames.base import BaseFrame
from app.ui.frames.compress.services import (
    batch_comprimir,
    estimar_tamano,
    formatear_bytes,
)
from app.ui.frames.compress.state import CompressState


class CompressFrame(BaseFrame):
    """
    Frame del modulo de compresion de imagenes.
    
    Permite seleccionar imagenes, configurar calidad y
    compresion EXIF, y comprimir las imagenes seleccionadas.
    """
    
    def __init__(self, parent):
        """
        Inicializa el frame de compresion.
        
        Args:
            parent: Widget padre.
        """
        self._state = CompressState()
        super().__init__(parent, t('compress_title'))

    def _build_content(self):
        """
        Construye el contenido especifico del modulo.
        
        Incluye boton de seleccion, lista de archivos,
        panel de opciones con calidad y toggle de EXIF,
        y boton de comprimir.
        """
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

        # Panel de opciones de compresion
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
        
        Incluye slider de calidad, toggle de EXIF y
        boton de comprimir.
        """
        p = self._panel_opciones

        # Label de calidad
        ctk.CTkLabel(
            p, text=t('quality'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(16, 8), sticky='w')

        # Fila con slider y valor de calidad
        fila_cal = ctk.CTkFrame(p, fg_color='transparent')
        fila_cal.grid(row=0, column=1, padx=(0, 16), pady=(16, 8), sticky='ew')
        fila_cal.grid_columnconfigure(0, weight=1)

        # Slider de calidad
        self._slider = ctk.CTkSlider(
            fila_cal,
            from_=10, to=100,
            number_of_steps=9,
            variable=self._state.calidad,
            command=self._actualizar_calidad,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            progress_color=colors.ACENTO,
            fg_color=colors.SIDEBAR_SEPARATOR,
        )
        self._slider.grid(row=0, column=0, sticky='ew', padx=(0, 10))

        # Label que muestra el valor actual de calidad
        self._lbl_calidad = ctk.CTkLabel(
            fila_cal, text=str(self._state.calidad.get()),
            font=fonts.FUENTE_BASE,
            text_color=colors.ACENTO,
            fg_color='transparent',
            width=28
        )
        self._lbl_calidad.grid(row=0, column=1)

        # Label de eliminar EXIF
        ctk.CTkLabel(
            p, text=t('remove_exif'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=1, column=0, padx=(16, 12), pady=(8, 16), sticky='w')

        # Toggle de eliminar EXIF
        ctk.CTkSwitch(
            p, text='',
            variable=self._state.quitar_exif,
            onvalue=True, offvalue=False,
            progress_color=colors.ACENTO,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            fg_color=colors.SIDEBAR_SEPARATOR,
        ).grid(row=1, column=1, padx=(0, 16), pady=(8, 16), sticky='w')

        # Boton de comprimir
        self._btn_comprimir = ctk.CTkButton(
            p,
            text=t('compress_btn'),
            height=40,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._comprimir
        )
        self._btn_comprimir.grid(row=2, column=0, columnspan=2, padx=16, pady=(0, 16), sticky='ew')

    def _cargar_imagenes(self, rutas):
        """
        Carga las imagenes seleccionadas y estima el tamano.
        
        Sobrescribe el metodo de BaseFrame para agregar
        estimacion de tamano en segundo plano.
        
        Args:
            rutas: Lista de rutas de archivos a cargar.
        """
        super()._cargar_imagenes(rutas)
        self._state.imagenes = list(rutas)
        threading.Thread(target=self._procesar_carga, args=(rutas,), daemon=True).start()

    def _procesar_carga(self, rutas):
        """
        Calcula el tamano estimado de compresion en segundo plano.
        
        Args:
            rutas: Lista de rutas de archivos.
        """
        estimado = 0
        for ruta in rutas:
            try:
                estimado += estimar_tamano(ruta, self._state.calidad.get())
            except Exception:
                continue
        self.after(0, lambda: self._aplicar_carga(estimado, len(rutas)))

    def _aplicar_carga(self, estimado, n):
        """
        Muestra la informacion de tamano estimado.
        
        Args:
            estimado: Tamano total estimado en bytes.
            n: Cantidad de imagenes.
        """
        if estimado > 0:
            suffix = t('images_loaded') if n > 1 else t('image_loaded')
            self._lbl_info.configure(
                text=f'{n} {suffix} - {t("estimated")} {formatear_bytes(estimado)}'
            )

    def _actualizar_calidad(self, val):
        """
        Actualiza el label de calidad y recalcula el estimado.
        
        Args:
            val: Nuevo valor del slider.
        """
        self._lbl_calidad.configure(text=str(int(val)))
        self._actualizar_estimado()

    def _actualizar_estimado(self, *args):
        """
        Recalcula y muestra el tamano estimado con la calidad actual.
        """
        if not self._imagenes:
            self._lbl_info.configure(text='')
            return
        try:
            estimado = sum(estimar_tamano(r, self._state.calidad.get()) for r in self._imagenes)
            n = len(self._imagenes)
            suffix = t('images_loaded') if n > 1 else t('image_loaded')
            self._lbl_info.configure(
                text=f'{n} {suffix} - {t("estimated")} {formatear_bytes(estimado)}'
            )
        except Exception:
            pass

    def _comprimir(self):
        """
        Inicia el proceso de compresion en segundo plano.
        """
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_images_first'))
            return
        
        carpeta = filedialog.askdirectory(title=t('select_output_folder'))
        if not carpeta:
            return
        
        self._btn_comprimir.configure(state='disabled', text=t('compressing'))
        threading.Thread(target=self._proceso, args=(carpeta,), daemon=True).start()

    def _proceso(self, carpeta):
        """
        Ejecuta la compresion en segundo plano.
        
        Args:
            carpeta: Ruta de la carpeta de salida.
        """
        res = batch_comprimir(
            self._imagenes,
            carpeta,
            calidad=self._state.calidad.get(),
            quitar_exif=self._state.quitar_exif.get(),
        )
        self.after(0, lambda: self._finalizar(
            res['ok'], res['total_original'], res['total_comprimido'], res['reduccion_pct'], res['errores']
        ))

    def _finalizar(self, n, orig, comp, reduccion, errores=0):
        """
        Muestra el resultado final de la compresion.
        
        Args:
            n: Cantidad de imagenes procesadas.
            orig: Tamano total original.
            comp: Tamano total comprimido.
            reduccion: Porcentaje de reduccion.
            errores: Cantidad de errores.
        """
        self._btn_comprimir.configure(state='normal', text=t('compress_btn'))
        suffix = t('images_loaded') if n > 1 else t('image_loaded')
        msg = (
            f'{n} {suffix} - '
            f'{formatear_bytes(orig)} -> {formatear_bytes(comp)} - '
            f'{reduccion}% {t("compressed")}'
        )
        if errores:
            msg += f'  -  {errores} {t("error_occurred")}'
        self._lbl_info.configure(text=msg)
