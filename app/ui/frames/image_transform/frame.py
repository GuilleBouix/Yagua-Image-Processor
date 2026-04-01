"""
UI para el modulo de transformaciones geometricas.
Permite rotar, voltear y corregir orientacion de imagenes en lote.

Relacionado con:
    - app/ui/frames/base.py: Clase base de la que hereda.
    - app/ui/frames/image_transform/state.py: Estado de la interfaz.
    - app/ui/frames/image_transform/services.py: Servicios de logica.
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
from app.ui.frames.image_transform.services import batch_transformar
from app.ui.frames.image_transform.state import ImageTransformState


logger = logging.getLogger(__name__)


class ImageTransformFrame(BaseFrame):
    """
    Frame del modulo de transformaciones geometricas.
    Soporta rotacion rapida, libre, volteo y correccion EXIF en lote.
    """

    def __init__(self, parent):
        """Inicializa el frame."""
        logger.info("image_transform.ui: init")
        self._state = ImageTransformState()
        super().__init__(parent, t('image_transform_title'))

    def _build_content(self):
        """Construye el contenido del modulo."""
        logger.info("image_transform.ui: build_content")
        # Boton seleccionar
        self._btn_seleccionar = self._crear_boton_seleccionar(self)
        self._btn_seleccionar.grid(row=1, column=0, padx=28, pady=(4, 0), sticky='ew')

        # Lista de archivos
        self._lista_frame = self._crear_lista_archivos(self, height=100)
        self._lista_frame.grid(row=2, column=0, padx=28, pady=6, sticky='ew')
        self._lista_frame.grid_columnconfigure(0, weight=1)
        self._crear_lista_vacia(self._lista_frame).pack(pady=8)

        # Panel principal
        panel = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel.grid(row=3, column=0, padx=28, pady=(0, 6), sticky='ew')
        panel.grid_columnconfigure(0, weight=1)
        self._construir_panel(panel)

    def _construir_panel(self, p):
        """
        Construye las cuatro secciones del panel.

        Args:
            p: Frame padre del panel.
        """
        # ── Seccion 1: Rotacion rapida ────────────────────────────────────────
        ctk.CTkLabel(
            p, text=t('transform_quick_rotation'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).grid(row=0, column=0, padx=16, pady=(10, 4), sticky='w')

        fila_rot = ctk.CTkFrame(p, fg_color='transparent')
        fila_rot.grid(row=1, column=0, padx=16, pady=(0, 8), sticky='ew')
        fila_rot.grid_columnconfigure((0, 1, 2), weight=1)

        self._btn_90_izq = self._crear_boton_accion_rapida(
            fila_rot, t('transform_90_left'), lambda: self._seleccionar_rotacion('90_izq')
        )
        self._btn_90_izq.grid(row=0, column=0, padx=(0, 6), sticky='ew')

        self._btn_180 = self._crear_boton_accion_rapida(
            fila_rot, t('transform_180'), lambda: self._seleccionar_rotacion('180')
        )
        self._btn_180.grid(row=0, column=1, padx=6, sticky='ew')

        self._btn_90_der = self._crear_boton_accion_rapida(
            fila_rot, t('transform_90_right'), lambda: self._seleccionar_rotacion('90_der')
        )
        self._btn_90_der.grid(row=0, column=2, padx=(6, 0), sticky='ew')

        # Mapa para actualizar estilos facilmente
        self._botones_rotacion = {
            '90_izq': self._btn_90_izq,
            '180':    self._btn_180,
            '90_der': self._btn_90_der,
        }

        # Separador
        ctk.CTkFrame(p, height=1, fg_color=colors.SIDEBAR_SEPARATOR).grid(
            row=2, column=0, padx=16, pady=3, sticky='ew'
        )

        # ── Seccion 2: Volteo ─────────────────────────────────────────────────
        ctk.CTkLabel(
            p, text=t('transform_flip'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).grid(row=3, column=0, padx=16, pady=(8, 4), sticky='w')

        fila_flip = ctk.CTkFrame(p, fg_color='transparent')
        fila_flip.grid(row=4, column=0, padx=16, pady=(0, 8), sticky='ew')
        fila_flip.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkCheckBox(
            fila_flip,
            text=t('transform_flip_h'),
            variable=self._state.flip_horizontal,
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            fg_color=colors.ACENTO,
            hover_color=colors.ACENTO_HOVER,
            border_color=colors.SIDEBAR_SEPARATOR,
            checkmark_color=colors.TEXT_ACTIVE,
        ).grid(row=0, column=0, sticky='w', padx=(0, 12))

        ctk.CTkCheckBox(
            fila_flip,
            text=t('transform_flip_v'),
            variable=self._state.flip_vertical,
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            fg_color=colors.ACENTO,
            hover_color=colors.ACENTO_HOVER,
            border_color=colors.SIDEBAR_SEPARATOR,
            checkmark_color=colors.TEXT_ACTIVE,
        ).grid(row=0, column=1, sticky='w')

        # Separador
        ctk.CTkFrame(p, height=1, fg_color=colors.SIDEBAR_SEPARATOR).grid(
            row=5, column=0, padx=16, pady=3, sticky='ew'
        )

        # ── Seccion 3: Rotacion libre ─────────────────────────────────────────
        ctk.CTkLabel(
            p, text=t('transform_free_rotation'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).grid(row=6, column=0, padx=16, pady=(8, 4), sticky='w')

        fila_libre = ctk.CTkFrame(p, fg_color='transparent')
        fila_libre.grid(row=7, column=0, padx=16, pady=(0, 8), sticky='ew')
        fila_libre.grid_columnconfigure(0, weight=1)

        self._lbl_angulo = ctk.CTkLabel(
            fila_libre, text='0°',
            font=fonts.FUENTE_BASE,
            text_color=colors.ACENTO,
            fg_color='transparent', width=36
        )

        ctk.CTkSlider(
            fila_libre,
            from_=-180, to=180,
            number_of_steps=360,
            variable=self._state.angulo_libre,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            progress_color=colors.ACENTO,
            fg_color=colors.SIDEBAR_SEPARATOR,
            command=self._actualizar_angulo
        ).grid(row=0, column=0, sticky='ew', padx=(0, 8))

        self._lbl_angulo.grid(row=0, column=1)

        ctk.CTkButton(
            fila_libre,
            text=t('transform_reset'),
            width=60, height=28,
            corner_radius=6,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.SIDEBAR_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_GRAY,
            hover_color=colors.SIDEBAR_HOVER,
            command=self._resetear_angulo
        ).grid(row=0, column=2, padx=(8, 0))

        # Separador
        ctk.CTkFrame(p, height=1, fg_color=colors.SIDEBAR_SEPARATOR).grid(
            row=8, column=0, padx=16, pady=3, sticky='ew'
        )

        # ── Seccion 4: Correccion EXIF + Boton aplicar ────────────────────────
        fila_bottom = ctk.CTkFrame(p, fg_color='transparent')
        fila_bottom.grid(row=9, column=0, padx=16, pady=(8, 10), sticky='ew')
        fila_bottom.grid_columnconfigure(0, weight=1)

        ctk.CTkCheckBox(
            fila_bottom,
            text=t('transform_exif'),
            variable=self._state.corregir_exif,
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            fg_color=colors.ACENTO,
            hover_color=colors.ACENTO_HOVER,
            border_color=colors.SIDEBAR_SEPARATOR,
            checkmark_color=colors.TEXT_ACTIVE,
        ).grid(row=0, column=0, sticky='w')

        self._btn_aplicar = ctk.CTkButton(
            fila_bottom,
            text=t('transform_btn_apply'),
            height=36, corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._ejecutar
        )
        self._btn_aplicar.grid(row=0, column=1, sticky='e')

    def _cargar_imagenes(self, rutas):
        """Carga imagenes con limite de 100."""
        logger.info("image_transform.ui: cargar_imagenes (total=%s)", len(rutas))
        limite = 100
        total = len(rutas)
        if total > limite:
            rutas = rutas[:limite]
            self._limite_msg = t('limit_reached').format(limit=limite, total=total)
        else:
            self._limite_msg = None

        super()._cargar_imagenes(rutas)
        self._state.imagenes = list(rutas)
        n = len(rutas)
        suffix = t('images_loaded') if n > 1 else t('image_loaded')
        msg = f'{n} {suffix}'
        if self._limite_msg:
            msg += f'  -  {self._limite_msg}'
        self._lbl_info.configure(text=msg)
        logger.info("image_transform.ui: imagenes cargadas (mostradas=%s)", len(rutas))

    def _crear_boton_accion_rapida(self, parent, texto, comando):
        """
        Crea un boton de accion rapida con estilo inactivo por defecto.

        Args:
            parent: Widget padre.
            texto: Texto del boton.
            comando: Funcion al hacer click.

        Returns:
            CTkButton configurado.
        """
        return ctk.CTkButton(
            parent,
            text=texto,
            height=40,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.SIDEBAR_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            hover_color=colors.SIDEBAR_HOVER,
            command=comando
        )

    def _seleccionar_rotacion(self, valor):
        """
        Selecciona o deselecciona una rotacion rapida.
        Si se hace click en la activa, la deselecciona.

        Args:
            valor: Clave de la rotacion ('90_izq', '90_der', '180').
        """
        actual = self._state.rotacion_rapida.get()
        logger.debug("image_transform.ui: seleccionar_rotacion (valor=%s, actual=%s)", valor, actual)

        if actual == valor:
            # Deseleccionar si se hace click en la activa
            self._state.resetear_rotacion_rapida()
        else:
            self._state.rotacion_rapida.set(valor)

        self._actualizar_estilos_rotacion()

    def _actualizar_estilos_rotacion(self):
        """Actualiza el estilo visual de los botones de rotacion rapida."""
        activa = self._state.rotacion_rapida.get()

        for clave, boton in self._botones_rotacion.items():
            if clave == activa:
                boton.configure(
                    fg_color=colors.ACENTO,
                    text_color=colors.TEXT_ACTIVE,
                    border_color=colors.ACENTO
                )
            else:
                boton.configure(
                    fg_color=colors.SIDEBAR_BG,
                    text_color=colors.TEXT_COLOR,
                    border_color=colors.SIDEBAR_SEPARATOR
                )

    def _actualizar_angulo(self, valor):
        """
        Actualiza el label del angulo al mover el slider.

        Args:
            valor: Nuevo valor del slider.
        """
        self._lbl_angulo.configure(text=f'{int(valor)}°')

    def _resetear_angulo(self):
        """Resetea el slider de angulo a 0."""
        logger.debug("image_transform.ui: resetear_angulo")
        self._state.resetear_angulo()
        self._lbl_angulo.configure(text='0°')

    def _cargar_imagenes(self, rutas):
        """Carga archivos en el estado."""
        logger.info("image_transform.ui: cargar_imagenes (total=%s)", len(rutas))
        super()._cargar_imagenes(rutas)
        self._state.imagenes = list(rutas)
        n = len(rutas)
        suffix = t('images_loaded') if n > 1 else t('image_loaded')
        self._lbl_info.configure(text=f'{n} {suffix}')
        logger.info("image_transform.ui: imagenes cargadas (mostradas=%s)", len(rutas))

    def _ejecutar(self):
        """Inicia el procesamiento en segundo plano."""
        logger.info("image_transform.ui: click_aplicar")
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_images_first'))
            return

        if not self._state.hay_transformaciones():
            self._lbl_info.configure(text=t('transform_select_one'))
            return

        carpeta = filedialog.askdirectory(title=t('select_output_folder'))
        if not carpeta:
            logger.info("image_transform.ui: proceso_cancelado (sin_carpeta)")
            return

        self._btn_aplicar.configure(state='disabled', text=t('processing'))
        self._show_full_overlay(t('processing'))
        opciones = self._state.obtener_opciones()

        threading.Thread(
            target=self._proceso,
            args=(carpeta, opciones),
            daemon=True
        ).start()

    def _proceso(self, carpeta, opciones):
        """
        Ejecuta las transformaciones en segundo plano.

        Args:
            carpeta: Carpeta de salida.
            opciones: Diccionario de transformaciones.
        """
        logger.info("image_transform.ui: proceso_interno_inicio (imagenes=%s)", len(self._imagenes))
        res = batch_transformar(self._imagenes, carpeta, opciones)
        self.after(0, lambda: self._finalizar(res['ok'], res['errores']))

    def _finalizar(self, ok, errores):
        """
        Muestra el resultado final.

        Args:
            ok: Imagenes procesadas correctamente.
            errores: Cantidad de errores.
        """
        self._btn_aplicar.configure(state='normal', text=t('transform_btn_apply'))
        logger.info("image_transform.ui: finalizar_ok (ok=%s, errores=%s)", ok, errores)
        self._hide_full_overlay()
        suffix = t('images_loaded') if ok > 1 else t('image_loaded')
        msg = f'{ok} {suffix} {t("processed")}'
        if errores:
            msg += f'  ·  {errores} {t("error_occurred")}'
        self._lbl_info.configure(text=msg)
