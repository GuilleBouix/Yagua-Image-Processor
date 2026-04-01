"""
UI para el modulo de OCR.
Permite extraer texto de imagenes usando OCR.

Relacionado con:
    - app/ui/frames/base.py: Clase base de la que hereda.
    - app/ui/frames/ocr/state.py: Estado de la interfaz.
    - app/ui/frames/ocr/services.py: Servicios de OCR.
    - app/translations/__init__.py: Traducciones de la UI.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from app.ui import colors, fonts
from app.translations import t
from app.ui.frames.base import BaseFrame
from app.ui.frames.ocr.services import batch_procesar, exportar_texto, ensure_reader
from app.ui.frames.ocr.state import OcrState

logger = logging.getLogger(__name__)

class OcrFrame(BaseFrame):
    """
    Frame del modulo de OCR.
    
    Permite seleccionar imagenes, configurar idiomas,
    procesar OCR y mostrar/exportar el texto extraído.
    """
    
    def __init__(self, parent):
        """
        Inicializa el frame de OCR.
        
        Args:
            parent: Widget padre.
        """
        logger.info("ocr.ui: init")
        self._state = OcrState()
        self._idioma_label = ctk.StringVar(value='')
        self._spinner_frame = None
        self._spinner_label = None
        self._spinner_bar = None
        self._ocr_ready = False
        super().__init__(parent, t('ocr_title'))
        try:
            self._btn_limpiar.grid_configure(column=2, padx=(0, 28), sticky='e')
        except Exception:
            pass

    def _build_content(self):
        """
        Construye el contenido especifico del modulo.

        Layout de dos columnas:
        - Izquierda: seleccion, lista, opciones, acciones
        - Derecha: textarea para texto extra?do
        """
        logger.info("ocr.ui: build_content")
        self._crear_spinner()
        # Configurar dos columnas: izquierda (1) y derecha (2)
        self.grid_columnconfigure(0, weight=1, minsize=400)
        self.grid_columnconfigure(1, weight=1, minsize=400)

        base_row = 2
        # ===== COLUMNA IZQUIERDA =====

        # Boton para seleccionar imagenes
        self._btn_seleccionar = self._crear_boton_seleccionar(self, texto=t('select_images_ocr'))
        self._btn_seleccionar.grid(row=base_row, column=0, padx=(28, 14), pady=(4, 3), sticky='ew')

        # Lista de archivos seleccionados
        self._lista_frame = self._crear_lista_archivos(self, height=120)
        self._lista_frame.grid(row=base_row + 1, column=0, padx=(28, 14), pady=(0, 4), sticky='ew')
        self._lista_frame.grid_columnconfigure(0, weight=1)

        # Label de lista vacia
        self._lbl_lista_vacia = self._crear_lista_vacia(self._lista_frame)
        self._lbl_lista_vacia.pack(pady=8)

        # Panel de opciones de OCR
        self._panel_opciones = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        self._panel_opciones.grid(row=base_row + 2, column=0, padx=(28, 14), pady=(0, 4), sticky='ew')
        self._panel_opciones.grid_columnconfigure(1, weight=1)
        self._construir_opciones()

        # Panel de acciones
        self._panel_acciones = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        self._panel_acciones.grid(row=base_row + 3, column=1, padx=(14, 28), pady=(0, 8), sticky='ew')
        self._panel_acciones.grid_columnconfigure(0, weight=1)
        self._panel_acciones.grid_columnconfigure(1, weight=1)
        self._panel_acciones.grid_columnconfigure(2, weight=1)
        self._construir_acciones()

        # ===== COLUMNA DERECHA =====

        # Textarea para texto extra?do
        self._textarea = ctk.CTkTextbox(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
        )
        self._textarea.grid(row=base_row, column=1, rowspan=3, padx=(14, 28), pady=(6, 6), sticky='ewns')
        self._textarea.insert('0.0', self._state.texto_extraido.get())

        # Configurar weight de fila para que textarea crezca
        self.grid_rowconfigure(base_row, weight=1)
        self.grid_rowconfigure(base_row + 1, weight=1)
        self.grid_rowconfigure(base_row + 2, weight=1)
        self.grid_rowconfigure(base_row + 3, weight=0)

        self._inicializar_en_background()

    def _crear_spinner(self):
        """Crea un spinner dentro del modulo (no bloqueante)."""
        logger.debug("ocr.ui: crear_spinner")
        self._spinner_frame = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        self._spinner_frame.grid(row=1, column=0, columnspan=2, padx=28, pady=(4, 4), sticky='ew')
        self._spinner_frame.grid_columnconfigure(0, weight=1)

        self._spinner_label = ctk.CTkLabel(
            self._spinner_frame,
            text=t('ocr_model_loading'),
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
        self._show_full_overlay(text)

    def _hide_overlay(self):
        """Oculta el spinner interno."""
        if not self._spinner_frame or not self._spinner_bar:
            return
        try:
            self._spinner_bar.stop()
        except Exception:
            pass
        self._spinner_frame.grid_remove()
        self._hide_full_overlay()

    def _inicializar_en_background(self):
        """Inicializa OCR en background sin bloquear la UI."""
        logger.info("ocr.ui: inicializar_en_background")
        self._show_overlay(t('ocr_model_loading'))
        self._btn_procesar.configure(state='disabled')

        def _worker():
            ok = True
            try:
                opcion = self._dropdown_idiomas.get()
                idiomas_str = self._idiomas_map.get(opcion, 'es,en')
                self._state.idiomas.set(idiomas_str)
                idiomas = idiomas_str.split(',')
                ensure_reader(idiomas)
            except Exception as exc:
                logger.exception("Error inicializando OCR: %s", exc)
                ok = False
            self.after(0, lambda: self._finalizar_init(ok))

        threading.Thread(target=_worker, daemon=True).start()

    def _finalizar_init(self, ok: bool):
        if ok:
            self._ocr_ready = True
            self._btn_procesar.configure(state='normal')
        else:
            self._btn_procesar.configure(state='normal')
            self._lbl_info.configure(text=t('error_generic'))
        self._hide_overlay()

    def _construir_opciones(self):
        """
        Construye los controles del panel de opciones.
        
        Incluye dropdown de idiomas y boton de procesar.
        """
        p = self._panel_opciones

        # Label de idiomas
        ctk.CTkLabel(
            p, text=t('ocr_languages'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(10, 6), sticky='w')

        # Mapeo de opciones legibles a valores internos
        self._idiomas_map = {
            'Español/Inglés': 'es,en',
            'Español': 'es',
            'Inglés': 'en',
        }
        
        # Dropdown de idiomas con opciones legibles
        self._dropdown_idiomas = ctk.CTkComboBox(
            p,
            values=list(self._idiomas_map.keys()),
            variable=self._idioma_label,
            font=fonts.FUENTE_BASE,
            fg_color=colors.SIDEBAR_BG,
            border_color=colors.SIDEBAR_SEPARATOR,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            dropdown_fg_color=colors.SIDEBAR_BG,
            dropdown_text_color=colors.TEXT_COLOR,
            dropdown_hover_color=colors.SIDEBAR_HOVER
        )
        # Establecer valor por defecto a la primera opción
        self._dropdown_idiomas.set('Español/Inglés')
        self._state.idiomas.set(self._idiomas_map.get('Español/Inglés', 'es,en'))
        self._dropdown_idiomas.grid(row=0, column=1, padx=(0, 16), pady=(10, 6), sticky='ew')

        # Boton de procesar
        self._btn_procesar = ctk.CTkButton(
            p,
            text=t('process_ocr'),
            height=40,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._procesar
        )
        self._btn_procesar.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 12), sticky='ew')

    def _construir_acciones(self):
        """
        Construye los botones de acciones.
        
        Incluye botones clear, copy, export.
        """
        p = self._panel_acciones

        # Boton limpiar
        self._btn_limpiar_texto = ctk.CTkButton(
            p,
            text=t('clear_text'),
            height=32,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.BTN_CLEAR_BG,
            text_color=colors.BTN_CLEAR_TEXT,
            hover_color=colors.BTN_CLEAR_HOVER,
            command=self._limpiar_texto
        )
        self._btn_limpiar_texto.grid(row=0, column=0, padx=16, pady=6, sticky='ew')

        # Boton copiar
        self._btn_copiar = ctk.CTkButton(
            p,
            text=t('copy_text'),
            height=32,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            hover_color=colors.SIDEBAR_HOVER,
            command=self._copiar_texto
        )
        self._btn_copiar.grid(row=0, column=1, padx=8, pady=6, sticky='ew')

        # Boton exportar
        self._btn_exportar = ctk.CTkButton(
            p,
            text=t('export_text'),
            height=32,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._exportar
        )
        self._btn_exportar.grid(row=0, column=2, padx=(8, 16), pady=6, sticky='ew')

    def _cargar_imagenes(self, rutas):
        """
        Carga las imagenes seleccionadas con limite de 10.
        
        Args:
            rutas: Lista de rutas de archivos a cargar.
        """
        logger.info("ocr.ui: cargar_imagenes (total=%s)", len(rutas))
        limite = 10
        total = len(rutas)
        if total > limite:
            rutas = rutas[:limite]
            self._limite_msg = t('ocr_batch_limit')
        else:
            self._limite_msg = None

        super()._cargar_imagenes(rutas)
        logger.info("ocr.ui: imagenes cargadas (mostradas=%s)", len(rutas))
        self._state.imagenes = list(rutas)
        self._state.texto_extraido.set('')

    def _procesar(self):
        """
        Inicia el proceso de OCR en segundo plano.
        """
        logger.info("ocr.ui: click_procesar")
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_images_first_ocr'))
            return

        self._state.processing.set(True)
        self._btn_procesar.configure(state='disabled', text=t('processing_ocr'))
        self._show_overlay(t('ocr_processing'))

        # Obtener el valor mostrado y convertir al valor interno
        opcion = self._dropdown_idiomas.get()
        idiomas_str = self._idiomas_map.get(opcion, 'es,en')
        idiomas = idiomas_str.split(',')

        threading.Thread(target=self._proceso_ocr, args=(idiomas,), daemon=True).start()

    def _proceso_ocr(self, idiomas):
        """
        Ejecuta el OCR en segundo plano.

        Args:
            idiomas: Lista de idiomas para OCR.
        """
        try:
            logger.info("ocr.ui: proceso_interno_inicio (idiomas=%s)", idiomas)
            res = batch_procesar(self._imagenes, idiomas)
            self.after(0, lambda: self._finalizar_ocr(res))
        except Exception as exc:
            logger.exception("Error en proceso OCR: %s", exc)
            self.after(0, lambda: self._handle_error(str(exc)))

    def _handle_error(self, msg: str):
        """Maneja errores y restaura el estado visual."""
        self._state.processing.set(False)
        self._btn_procesar.configure(state='normal', text=t('process_ocr'))
        self._hide_overlay()
        if not msg or msg.lower() == 'none':
            msg = t('error_generic')
        self._lbl_info.configure(text=f"{t('error_generic')}: {msg}")

    def _finalizar_ocr(self, res):
        """
        Muestra el resultado del OCR.
        
        Args:
            res: Resultado de batch_procesar.
        """
        self._state.processing.set(False)
        self._btn_procesar.configure(state='normal', text=t('process_ocr'))
        self._hide_overlay()

        textos = res['textos']
        texto_completo = ''
        for ruta, texto in textos.items():
            if texto.strip():
                texto_completo += f"=== {Path(ruta).name} ===\n{texto}\n\n"
            else:
                texto_completo += f"=== {Path(ruta).name} ===\n{t('no_text_found')}\n\n"

        self._state.texto_extraido.set(texto_completo.strip())
        self._textarea.delete('0.0', 'end')
        self._textarea.insert('0.0', texto_completo.strip())

        ok = res['ok']
        errores = res['errores']
        msg = f'{ok} {t("images_loaded") if ok > 1 else t("image_loaded")} {t("text_extracted")}'
        if errores:
            msg += f' - {errores} {t("error_occurred")}'
        avif_omitidos = res.get('avif_omitidos', 0)
        if avif_omitidos:
            msg += f' - {t("ocr_avif_requires_plugin")}'
        self._lbl_info.configure(text=msg)
        logger.info("ocr.ui: finalizar_ok (ok=%s, errores=%s, avif_omitidos=%s)", ok, errores, avif_omitidos)

    def _limpiar_texto(self):
        """
        Limpia el texto de la textarea.
        """
        self._state.texto_extraido.set('')
        self._textarea.delete('0.0', 'end')

    def _copiar_texto(self):
        """
        Copia el texto al portapapeles.
        """
        texto = self._textarea.get('0.0', 'end').strip()
        if texto:
            self.clipboard_clear()
            self.clipboard_append(texto)
            self._lbl_info.configure(text=t('text_copied'))

    def _exportar(self):
        """
        Exporta el texto a un archivo .txt.
        """
        texto = self._textarea.get('0.0', 'end').strip()
        if not texto:
            return

        carpeta = filedialog.askdirectory(title=t('select_output_folder'))
        if not carpeta:
            return

        try:
            ruta = exportar_texto(texto, carpeta)
            self._lbl_info.configure(text=f'{t("exported_as")} {Path(ruta).name}')
        except Exception as e:
            logger.exception("Error exportando texto: %s", e)
            self._lbl_info.configure(text=t('error_generic'))
