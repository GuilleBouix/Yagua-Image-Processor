"""
UI para el modulo LQIP / Base64.
Genera placeholders de baja calidad y strings base64
listos para usar en proyectos web.

Relacionado con:
    - app/ui/frames/base.py: Clase base de la que hereda.
    - app/ui/frames/lqip/state.py: Estado de la interfaz.
    - app/ui/frames/lqip/services.py: Servicios de logica.
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
from app.ui.frames.lqip.services import batch_procesar, exportar_txt, exportar_json
from app.ui.frames.lqip.state import LqipState


logger = logging.getLogger(__name__)


class LqipFrame(BaseFrame):
    """Frame del modulo LQIP / Base64."""

    def __init__(self, parent):
        """Inicializa el frame."""
        logger.info("lqip.ui: init")
        self._state = LqipState()
        super().__init__(parent, t('lqip_title'))

    def _build_content(self):
        logger.info("lqip.ui: build_content")
        # Boton seleccionar
        self._btn_seleccionar = self._crear_boton_seleccionar(self)
        self._btn_seleccionar.grid(row=1, column=0, padx=28, pady=(8, 0), sticky='ew')

        # Lista de archivos — más chica
        self._lista_frame = self._crear_lista_archivos(self, height=90)
        self._lista_frame.grid(row=2, column=0, padx=28, pady=8, sticky='ew')
        self._lista_frame.grid_columnconfigure(0, weight=1)
        self._lbl_lista_vacia = self._crear_lista_vacia(self._lista_frame)
        self._lbl_lista_vacia.pack(pady=8)

        # Panel de opciones
        panel = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel.grid(row=3, column=0, padx=28, pady=(0, 6), sticky='ew')
        panel.grid_columnconfigure(0, weight=1)
        self._construir_opciones(panel)

    def _construir_opciones(self, p):
        # Fila 1: modo + descripcion
        fila_modo = ctk.CTkFrame(p, fg_color='transparent')
        fila_modo.grid(row=0, column=0, padx=16, pady=(12, 0), sticky='ew')
        fila_modo.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            fila_modo, text=t('lqip_mode'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).grid(row=0, column=0, padx=(0, 12), sticky='w')

        # Mapa de valores traduzidos a internos
        self._modo_a_interno = {
            t('lqip_mode_lqip'): 'lqip',
            t('lqip_mode_b64'): 'base64',
        }
        
        self._seg_modo = ctk.CTkSegmentedButton(
            fila_modo,
            values=[t('lqip_mode_lqip'), t('lqip_mode_b64')],
            variable=self._state.modo,
            font=fonts.FUENTE_CHICA,
            selected_color=colors.SEGMENT_SELECTED,
            selected_hover_color=colors.SEGMENT_SELECTED_HOVER,
            unselected_color=colors.SIDEBAR_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
            command=self._cambiar_modo
        )
        self._seg_modo.grid(row=0, column=1, sticky='w')

        self._lbl_descripcion = ctk.CTkLabel(
            fila_modo,
            text=t('lqip_mode_lqip_desc'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor='w', wraplength=300
        )
        self._lbl_descripcion.grid(row=0, column=2, padx=(16, 0), sticky='w')

        # Separador
        ctk.CTkFrame(p, height=1, fg_color=colors.SIDEBAR_SEPARATOR).grid(
            row=1, column=0, padx=16, pady=(8, 4), sticky='ew'
        )

        # Opciones especificas del modo
        self._frame_opciones_modo = ctk.CTkFrame(p, fg_color='transparent')
        self._frame_opciones_modo.grid(row=2, column=0, padx=16, pady=(6, 0), sticky='ew')
        self._frame_opciones_modo.grid_columnconfigure((0, 1, 2), weight=1)
        self._construir_opciones_lqip()

        # Separador
        ctk.CTkFrame(p, height=1, fg_color=colors.SIDEBAR_SEPARATOR).grid(
            row=3, column=0, padx=16, pady=(8, 4), sticky='ew'
        )

        # Exportar
        fila_export = ctk.CTkFrame(p, fg_color='transparent')
        fila_export.grid(row=4, column=0, padx=16, pady=(4, 12), sticky='ew')
        fila_export.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            fila_export, text=t('lqip_export_field'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, sticky='w', pady=(0, 4))

        ctk.CTkLabel(
            fila_export, text=t('lqip_actions'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=1, columnspan=3, sticky='w', pady=(0, 4), padx=(12, 0))

        self._campo_export = ctk.StringVar(value='DATA_URI')
        ctk.CTkOptionMenu(
            fila_export,
            values=[t('DATA_URI'), t('HTML_TAG'), t('CSS_BG')],
            variable=self._campo_export,
            font=fonts.FUENTE_BASE,
            fg_color=colors.SIDEBAR_BG,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            text_color=colors.TEXT_COLOR,
            dropdown_fg_color=colors.PANEL_BG,
            dropdown_text_color=colors.TEXT_COLOR,
            dropdown_hover_color=colors.SIDEBAR_HOVER,
            width=120
        ).grid(row=1, column=0, sticky='w', padx=(0, 12))

        self._btn_procesar = ctk.CTkButton(
            fila_export,
            text=t('lqip_btn_process'),
            height=34, corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._procesar
        )
        self._btn_procesar.grid(row=1, column=1, sticky='ew', padx=(0, 4))

        ctk.CTkButton(
            fila_export,
            text=t('lqip_btn_copy'),
            height=34, corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            hover_color=colors.SIDEBAR_HOVER,
            command=self._copiar
        ).grid(row=1, column=2, sticky='ew', padx=4)

        ctk.CTkButton(
            fila_export,
            text=t('lqip_btn_save'),
            height=34, corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            hover_color=colors.SIDEBAR_HOVER,
            command=self._guardar
        ).grid(row=1, column=3, sticky='ew', padx=(4, 0))

    def _construir_opciones_lqip(self):
        """Construye los controles especificos del modo LQIP."""
        f = self._frame_opciones_modo

        # Limpiar sin destroy — desconectar variables primero
        for w in f.winfo_children():
            w.grid_forget()

        ctk.CTkLabel(
            f, text=t('lqip_width'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, sticky='w', pady=(0, 4))

        ctk.CTkEntry(
            f,
            textvariable=self._state.ancho_lqip,
            font=fonts.FUENTE_BASE,
            fg_color=colors.FRAMES_BG,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            placeholder_text='20',
            placeholder_text_color=colors.TEXT_GRAY,
        ).grid(row=1, column=0, sticky='ew', padx=(0, 12))

        ctk.CTkLabel(
            f, text=t('lqip_blur'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=1, sticky='w', pady=(0, 4))

        ctk.CTkEntry(
            f,
            textvariable=self._state.blur,
            font=fonts.FUENTE_BASE,
            fg_color=colors.FRAMES_BG,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            placeholder_text='2',
            placeholder_text_color=colors.TEXT_GRAY,
        ).grid(row=1, column=1, sticky='ew', padx=(0, 12))

        ctk.CTkLabel(
            f, text=t('lqip_quality'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=2, sticky='w', pady=(0, 4))

        fila_cal = ctk.CTkFrame(f, fg_color='transparent')
        fila_cal.grid(row=1, column=2, sticky='ew')
        fila_cal.grid_columnconfigure(0, weight=1)

        self._lbl_cal_lqip = ctk.CTkLabel(
            fila_cal, text=str(self._state.calidad_lqip.get()),
            font=fonts.FUENTE_BASE,
            text_color=colors.ACENTO,
            fg_color='transparent', width=28
        )
        ctk.CTkSlider(
            fila_cal,
            from_=10, to=80,
            variable=self._state.calidad_lqip,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            progress_color=colors.ACENTO,
            fg_color=colors.SIDEBAR_SEPARATOR,
            command=lambda v: self._lbl_cal_lqip.configure(text=str(int(v)))
        ).grid(row=0, column=0, sticky='ew', padx=(0, 6))
        self._lbl_cal_lqip.grid(row=0, column=1)


    def _construir_opciones_b64(self):
        """Construye los controles especificos del modo base64 completo."""
        f = self._frame_opciones_modo

        for w in f.winfo_children():
            w.grid_forget()

        f.grid_columnconfigure(0, weight=1)
        f.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            f, text=t('lqip_quality'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 4))

        fila_cal = ctk.CTkFrame(f, fg_color='transparent')
        fila_cal.grid(row=1, column=0, columnspan=2, sticky='ew')
        fila_cal.grid_columnconfigure(0, weight=1)

        self._lbl_cal_b64 = ctk.CTkLabel(
            fila_cal, text=str(self._state.calidad_b64.get()),
            font=fonts.FUENTE_BASE,
            text_color=colors.ACENTO,
            fg_color='transparent', width=28
        )
        ctk.CTkSlider(
            fila_cal,
            from_=10, to=100,
            variable=self._state.calidad_b64,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            progress_color=colors.ACENTO,
            fg_color=colors.SIDEBAR_SEPARATOR,
            command=lambda v: self._lbl_cal_b64.configure(text=str(int(v)))
        ).grid(row=0, column=0, sticky='ew', padx=(0, 6))
        self._lbl_cal_b64.grid(row=0, column=1)

    def _cambiar_modo(self, modo):
        """Cambia controles y descripcion segun el modo."""
        logger.info("lqip.ui: cambiar_modo (%s)", modo)
        # Convertir valor traduzido a interno
        modo_interno = self._modo_a_interno.get(modo, 'lqip')
        self._state.modo.set(modo_interno)
        
        modo_lqip = t('lqip_mode_lqip')
        
        if modo == modo_lqip:
            self._lbl_descripcion.configure(text=t('lqip_mode_lqip_desc'))
            self._construir_opciones_lqip()
        else:
            self._lbl_descripcion.configure(text=t('lqip_mode_b64_desc'))
            self._construir_opciones_b64()

    def _cargar_imagenes(self, rutas):
        """Carga archivos y limpia resultados anteriores."""
        logger.info("lqip.ui: cargar_imagenes (total=%s)", len(rutas))
        limite = 100
        total = len(rutas)
        if total > limite:
            rutas = rutas[:limite]
            self._limite_msg = t('limit_reached').format(limit=limite, total=total)
        else:
            self._limite_msg = None

        super()._cargar_imagenes(rutas)
        self._state.imagenes = list(rutas)
        self._state.resultados = []
        n = len(rutas)
        suffix = t('images_loaded') if n > 1 else t('image_loaded')
        msg = f'{n} {suffix}'
        if self._limite_msg:
            msg += f'  -  {self._limite_msg}'
        self._lbl_info.configure(text=msg)
        logger.info("lqip.ui: imagenes cargadas (mostradas=%s)", len(rutas))

    def _procesar(self):
        """Inicia el procesamiento en segundo plano."""
        logger.info("lqip.ui: click_procesar")
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_images_first'))
            return

        self._btn_procesar.configure(state='disabled', text=t('processing'))
        self._show_full_overlay(t('processing'))
        opciones = self._state.obtener_opciones()
        threading.Thread(
            target=self._proceso, args=(opciones,), daemon=True
        ).start()

    def _proceso(self, opciones):
        """Ejecuta el procesamiento."""
        logger.info("lqip.ui: proceso_interno_inicio (imagenes=%s, modo=%s)", len(self._imagenes), opciones.get('modo'))
        res = batch_procesar(
            self._imagenes,
            modo=opciones['modo'],
            ancho=opciones['ancho'],
            blur=opciones['blur'],
            calidad_lqip=opciones['calidad_lqip'],
            calidad_b64=opciones['calidad_b64'],
        )
        self._state.resultados = res['resultados']
        self.after(0, lambda: self._finalizar(res['ok'], res['errores']))

    def _finalizar(self, ok, errores):
        """Muestra el resultado del procesamiento."""
        self._btn_procesar.configure(state='normal', text=t('lqip_btn_process'))
        logger.info("lqip.ui: finalizar_ok (ok=%s, errores=%s)", ok, errores)
        self._hide_full_overlay()
        suffix = t('images_loaded') if ok > 1 else t('image_loaded')
        msg = f'{ok} {suffix} {t("processed")}  -  {t("lqip_ready_to_export")}'
        if errores:
            msg += f'  -  {errores} {t("error_occurred")}'
        self._lbl_info.configure(text=msg)

    def _copiar(self):
        """Copia el campo seleccionado al portapapeles."""
        logger.info("lqip.ui: copiar_resultado")
        if not self._state.resultados:
            self._lbl_info.configure(text=t('lqip_process_first'))
            return

        campo = self._campo_export.get()
        contenido = '\n\n'.join(
            r.get(campo, '') for r in self._state.resultados
        )
        self.clipboard_clear()
        self.clipboard_append(contenido)
        self._lbl_info.configure(text=t('lqip_copied'))
        self.after(2000, lambda: self._lbl_info.configure(
            text=f'{len(self._state.resultados)} {t("processed")}'
        ))

    def _guardar(self):
        """Guarda los resultados en archivo .txt o .json."""
        logger.info("lqip.ui: guardar_resultado")
        if not self._state.resultados:
            self._lbl_info.configure(text=t('lqip_process_first'))
            return

        ruta = filedialog.asksaveasfilename(
            title=t('lqip_save_title'),
            defaultextension='.txt',
            filetypes=[
                (t('file_txt'), '*.txt'),
                (t('file_json'), '*.json'),
            ],
            initialfile='lqip_output'
        )
        if not ruta:
            return

        if ruta.endswith('.json'):
            exportar_json(self._state.resultados, ruta)
        else:
            exportar_txt(
                self._state.resultados,
                ruta,
                campo=self._campo_export.get()
            )

        from pathlib import Path
        self._lbl_info.configure(
            text=f'{t("lqip_saved_as")} {Path(ruta).name}'
        )
