"""
UI para el modulo de marca de agua (Watermark).
Preview en tiempo real con before/after al ajustar controles.

Relacionado con:
    - app/ui/frames/base.py: Clase base de la que hereda.
    - app/ui/frames/watermark/state.py: Estado de la interfaz.
    - app/ui/frames/watermark/services.py: Servicios de watermark.
    - app/translations/__init__.py: Traducciones de la UI.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from tkinter import filedialog

import cv2
import numpy as np
import customtkinter as ctk
from PIL import Image

from app.ui import colors, fonts
from app.translations import t
from app.ui.frames.base import BaseFrame
from app.ui.frames.watermark.state import WatermarkState
from app.ui.frames.watermark.services import aplicar_watermark_np, batch_aplicar_watermark
from app.modules.compress import formatear_bytes
from app.utils.image_utils import load_cv_image_unchanged


logger = logging.getLogger(__name__)

_PREVIEW_MAX_PX = 260
_DEBOUNCE_MS    = 350

POSICION_LABELS = {
    "Arriba izq.":   "top-left",
    "Arriba der.":   "top-right",
    "Abajo izq.":    "bottom-left",
    "Abajo der.":    "bottom-right",
    "Centro":        "center",
}

PRESET_DEFS = {
    "subtle": {"label_key": "watermark_preset_subtle", "params": {"escala": 15, "opacidad": 30, "posicion": "bottom-right"}},
    "visible": {"label_key": "watermark_preset_visible", "params": {"escala": 25, "opacidad": 60, "posicion": "bottom-right"}},
    "protection": {"label_key": "watermark_preset_protection", "params": {"escala": 40, "opacidad": 85, "posicion": "bottom-right"}},
    "center": {"label_key": "watermark_preset_center", "params": {"escala": 30, "opacidad": 40, "posicion": "center"}},
}

_LEGACY_PRESET_LABEL_TO_ID = {
    "Sutil": "subtle",
    "Visible": "visible",
    "Protección": "protection",
    "ProtecciÃ³n": "protection",
    "Centro": "center",
}

_POS_VALUE_TO_LABEL_KEY = {
    "top-left": "watermark_pos_top_left",
    "top-right": "watermark_pos_top_right",
    "bottom-left": "watermark_pos_bottom_left",
    "bottom-right": "watermark_pos_bottom_right",
    "center": "watermark_pos_center",
}


class WatermarkFrame(BaseFrame):
    """
    Frame del modulo de marca de agua.

    Layout:
        Izquierda : imágenes base + selección watermark + controles
        Derecha   : preview before / after
    """

    def __init__(self, parent):
        logger.info("watermark.ui: init")
        self._state = WatermarkState()

        # Preview
        self._preview_base_bgra = None   # imagen base escalada
        self._preview_wm_bgra   = None   # watermark original (se reescala en preview)
        self._preview_job       = None
        self._preview_activo    = False

        super().__init__(parent, t("watermark_title"))
        try:
            self._btn_limpiar.grid_remove()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  UI                                                                  #
    # ------------------------------------------------------------------ #

    def _build_content(self):
        logger.info("watermark.ui: build_content")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Columna izquierda ---
        panel_izq = ctk.CTkFrame(self, fg_color="transparent")
        panel_izq.grid(row=1, column=0, padx=(20, 8), pady=(0, 12), sticky="nsew")
        panel_izq.grid_columnconfigure(0, weight=1)
        panel_izq.grid_rowconfigure(1, weight=1)

        # Botón imágenes base
        self._btn_seleccionar = self._crear_boton_seleccionar(panel_izq)
        self._btn_seleccionar.grid(row=0, column=0, pady=(0, 6), sticky="ew")

        # Lista archivos
        self._lista_frame = self._crear_lista_archivos(panel_izq, height=110)
        self._lista_frame.grid(row=1, column=0, sticky="nsew")
        self._lista_frame.grid_columnconfigure(0, weight=1)
        self._lbl_lista_vacia = self._crear_lista_vacia(self._lista_frame)
        self._lbl_lista_vacia.pack(pady=12)

        # Botón seleccionar watermark
        self._btn_wm = ctk.CTkButton(
            panel_izq,
            text=t("watermark_select_wm"),
            font=fonts.FUENTE_BASE,
            fg_color=colors.PANEL_BG,
            text_color=colors.TEXT_COLOR,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            hover_color=colors.ACENTO_HOVER,
            command=self._seleccionar_watermark,
        )
        self._btn_wm.grid(row=2, column=0, pady=(6, 0), sticky="ew")

        # Preview del watermark seleccionado (single item)
        self._wm_frame = ctk.CTkFrame(
            panel_izq,
            corner_radius=10,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            height=70
        )
        self._wm_frame.grid(row=3, column=0, pady=(2, 6), sticky="ew")
        self._wm_frame.grid_columnconfigure(1, weight=1)
        self._wm_placeholder = ctk.CTkLabel(
            self._wm_frame,
            text=t("watermark_no_wm"),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor="w"
        )
        self._wm_placeholder.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self._wm_thumb = None

        # Panel controles
        panel_ctrl = ctk.CTkFrame(
            panel_izq,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
        )
        panel_ctrl.grid(row=4, column=0, pady=(4, 0), sticky="ew")
        panel_ctrl.grid_columnconfigure(1, weight=1)
        self._construir_controles(panel_ctrl)

        # --- Columna derecha: preview + limpiar ---
        self._btn_limpiar_preview = ctk.CTkButton(
            self,
            text=t("clean"),
            height=28,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.BTN_CLEAR_BG,
            text_color=colors.BTN_CLEAR_TEXT,
            hover_color=colors.BTN_CLEAR_HOVER,
            command=self._limpiar
        )
        self._btn_limpiar_preview.grid(row=0, column=1, padx=(0, 20), pady=(16, 0), sticky="e")

        panel_preview = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
        )
        panel_preview.grid(row=1, column=1, padx=(8, 20), pady=(0, 12), sticky="nsew")
        panel_preview.grid_columnconfigure(0, weight=1)
        panel_preview.grid_rowconfigure(1, weight=1)
        self._construir_preview(panel_preview)

    def _construir_controles(self, p):
        pad = (16, 16)

        # Preset
        ctk.CTkLabel(
            p, text=t("watermark_preset"),
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY, anchor="w",
        ).grid(row=0, column=0, padx=(16, 8), pady=(12, 2), sticky="w")

        self._combo_preset = ctk.CTkComboBox(
            p,
            values=[],
            font=fonts.FUENTE_BASE,
            fg_color=colors.SIDEBAR_BG,
            border_color=colors.SIDEBAR_SEPARATOR,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            dropdown_fg_color=colors.SIDEBAR_BG,
            dropdown_text_color=colors.TEXT_COLOR,
            dropdown_hover_color=colors.SIDEBAR_HOVER,
            command=self._aplicar_preset,
        )

        preset_ids = list(PRESET_DEFS.keys())
        preset_labels = [t(PRESET_DEFS[p_id]["label_key"]) for p_id in preset_ids]
        self._preset_label_to_id = {label: p_id for label, p_id in zip(preset_labels, preset_ids)}
        self._combo_preset.configure(values=preset_labels)
        self._combo_preset.set(preset_labels[0])
        self._combo_preset.grid(row=0, column=1, padx=(0, 16), pady=(12, 2), sticky="ew")

        sep = ctk.CTkFrame(p, height=1, fg_color=colors.SIDEBAR_SEPARATOR)
        sep.grid(row=1, column=0, columnspan=2, padx=16, pady=(4, 8), sticky="ew")

        # Posición
        ctk.CTkLabel(
            p, text=t("watermark_posicion"),
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY, anchor="w",
        ).grid(row=2, column=0, padx=(16, 8), pady=(0, 4), sticky="w")

        self._combo_pos = ctk.CTkComboBox(
            p,
            values=[],
            font=fonts.FUENTE_BASE,
            fg_color=colors.SIDEBAR_BG,
            border_color=colors.SIDEBAR_SEPARATOR,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            dropdown_fg_color=colors.SIDEBAR_BG,
            dropdown_text_color=colors.TEXT_COLOR,
            dropdown_hover_color=colors.SIDEBAR_HOVER,
            command=self._al_cambiar_posicion,
        )

        pos_values = list(_POS_VALUE_TO_LABEL_KEY.keys())
        pos_labels = [t(_POS_VALUE_TO_LABEL_KEY[v]) for v in pos_values]
        self._pos_label_to_value = {label: v for label, v in zip(pos_labels, pos_values)}
        self._pos_value_to_label = {v: label for label, v in zip(pos_labels, pos_values)}
        self._combo_pos.configure(values=pos_labels)
        # Default que corresponda a bottom-right
        self._combo_pos.set(self._pos_value_to_label.get("bottom-right", pos_labels[0]))
        self._combo_pos.grid(row=2, column=1, padx=(0, 16), pady=(0, 4), sticky="ew")

        # Sliders
        self._lbl_escala_val  = self._crear_slider_fila(
            p, row=3, label=t("watermark_tamano"),
            var=self._state.escala, desde=5, hasta=80, sufijo="%",
        )
        self._lbl_opac_val = self._crear_slider_fila(
            p, row=4, label=t("watermark_opacidad"),
            var=self._state.opacidad, desde=5, hasta=100, sufijo="%",
        )
        self._lbl_margen_val = self._crear_slider_fila(
            p, row=5, label=t("watermark_margen"),
            var=self._state.margen, desde=0, hasta=100, sufijo="px",
        )

        # Hints extremos (solo tamaño)
        self._crear_hint_fila(p, row=6, izq=t("watermark_tamano_pequeño"), der=t("watermark_tamano_grande"))

        # Botón aplicar
        self._btn_aplicar = ctk.CTkButton(
            p,
            text=t("watermark_btn"),
            height=36,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._ejecutar,
        )
        self._btn_aplicar.grid(row=7, column=0, columnspan=2, padx=16, pady=(8, 12), sticky="ew")

    def _crear_slider_fila(self, parent, row, label, var, desde, hasta, sufijo=""):
        parent.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            parent, text=label,
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY,
            anchor="w", width=80,
        ).grid(row=row, column=0, padx=(16, 8), pady=(4, 0), sticky="w")

        fila = ctk.CTkFrame(parent, fg_color="transparent")
        fila.grid(row=row, column=1, padx=(0, 16), pady=(4, 0), sticky="ew")
        fila.grid_columnconfigure(0, weight=1)

        lbl_val = ctk.CTkLabel(
            fila, text=f"{var.get()}{sufijo}",
            font=fonts.FUENTE_CHICA, text_color=colors.ACENTO, width=36,
        )
        lbl_val.grid(row=0, column=1, padx=(6, 0))

        def _on_slide(v, lv=lbl_val):
            lv.configure(text=f"{int(v)}{sufijo}")
            self._disparar_preview()

        ctk.CTkSlider(
            fila,
            from_=desde, to=hasta,
            number_of_steps=hasta - desde,
            variable=var,
            command=_on_slide,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            progress_color=colors.ACENTO,
            fg_color=colors.SIDEBAR_SEPARATOR,
            height=14,
        ).grid(row=0, column=0, sticky="ew")

        return lbl_val

    def _crear_hint_fila(self, parent, row, izq, der):
        fila = ctk.CTkFrame(parent, fg_color="transparent")
        fila.grid(row=row, column=0, columnspan=2, padx=(16, 16), pady=(0, 2), sticky="ew")
        fila.grid_columnconfigure(0, weight=1)
        fila.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(fila, text=izq, font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY, anchor="w").grid(row=0, column=0, padx=(80, 0), sticky="w")
        ctk.CTkLabel(fila, text=der, font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY, anchor="e").grid(row=0, column=1, sticky="e")

    def _construir_preview(self, p):
        ctk.CTkLabel(
            p, text=t("watermark_preview_despues"),
            font=fonts.FUENTE_CHICA, text_color=colors.ACENTO,
        ).grid(row=0, column=0, pady=(10, 4), sticky="w", padx=12)

        placeholder = t("watermark_preview_placeholder")

        self._canvas_preview = ctk.CTkLabel(
            p, text=placeholder,
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY,
            fg_color=colors.FRAMES_BG,
            width=_PREVIEW_MAX_PX, height=_PREVIEW_MAX_PX,
            corner_radius=8, wraplength=_PREVIEW_MAX_PX - 20,
        )
        self._canvas_preview.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="nsew")

        self._lbl_preview_status = ctk.CTkLabel(
            p, text="",
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY,
        )
        self._lbl_preview_status.grid(row=2, column=0, pady=(0, 8))

    # ------------------------------------------------------------------ #
    #  Controles                                                           #
    # ------------------------------------------------------------------ #

    def _aplicar_preset(self, nombre):
        logger.info("watermark.ui: aplicar_preset (%s)", nombre)
        preset_id = None
        if nombre in PRESET_DEFS:
            preset_id = nombre
        else:
            try:
                preset_id = getattr(self, "_preset_label_to_id", {}).get(nombre)
            except Exception:
                preset_id = None
            if not preset_id:
                preset_id = _LEGACY_PRESET_LABEL_TO_ID.get(nombre) or _LEGACY_PRESET_LABEL_TO_ID.get(str(nombre))

        if not preset_id or preset_id not in PRESET_DEFS:
            return

        preset = PRESET_DEFS[preset_id]["params"]
        self._state.escala.set(preset["escala"])
        self._state.opacidad.set(preset["opacidad"])
        self._state.posicion.set(preset["posicion"])

        # Actualizar labels
        for attr, key, suf in [
            ("_lbl_escala_val",  "escala",   "%"),
            ("_lbl_opac_val",    "opacidad", "%"),
        ]:
            if hasattr(self, attr):
                getattr(self, attr).configure(text=f"{preset[key]}{suf}")

        # Sincronizar combo posición
        if hasattr(self, "_combo_pos"):
            try:
                label_pos = getattr(self, "_pos_value_to_label", {}).get(preset["posicion"])
            except Exception:
                label_pos = None
            if not label_pos:
                # Fallback a legacy labels si todavia existen en UI.
                label_pos = next((k for k, v in POSICION_LABELS.items() if v == preset["posicion"]), None)
            if label_pos:
                self._combo_pos.set(label_pos)

        self._disparar_preview()

    def _al_cambiar_posicion(self, valor):
        # Preferimos el map de labels traducidos.
        try:
            pos = getattr(self, "_pos_label_to_value", {}).get(valor)
        except Exception:
            pos = None
        if not pos:
            pos = POSICION_LABELS.get(valor)  # legacy labels (ES)
        self._state.posicion.set(pos or "bottom-right")
        self._disparar_preview()

    def _seleccionar_watermark(self):
        ruta = filedialog.askopenfilename(
            title=t("watermark_select_wm"),
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.bmp *.heic *.heif"), ("PNG", "*.png")],
        )
        if not ruta:
            return
        self._state.ruta_watermark.set(ruta)
        self._mostrar_watermark_item(ruta)
        self._cargar_preview_wm(ruta)

    def _cargar_imagenes(self, rutas):
        logger.info("watermark.ui: cargar_imagenes (total=%s)", len(rutas))
        limite = 100
        total = len(rutas)
        if total > limite:
            rutas = rutas[:limite]
            self._limite_msg = t("limit_reached").format(limit=limite, total=total)
        else:
            self._limite_msg = None

        super()._cargar_imagenes(rutas)
        self._state.imagenes = list(rutas)
        if self._limite_msg:
            self._lbl_info.configure(text=self._limite_msg)
        if rutas:
            self._cargar_preview_base(rutas[0])
        logger.info("watermark.ui: imagenes cargadas (mostradas=%s)", len(rutas))

    # ------------------------------------------------------------------ #
    #  Preview                                                             #
    # ------------------------------------------------------------------ #

    def _cargar_preview_base(self, ruta):
        try:
            img = load_cv_image_unchanged(ruta)
            if img is None:
                return
            if img.ndim == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
            elif img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

            h, w = img.shape[:2]
            escala = min(_PREVIEW_MAX_PX / max(h, w), 1.0)
            nw, nh = max(1, int(w * escala)), max(1, int(h * escala))
            self._preview_base_bgra = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
            self._mostrar_canvas(self._canvas_preview, self._preview_base_bgra)
            self._disparar_preview()
        except Exception as e:
            import logging; logging.getLogger(__name__).warning(f"Error cargando base preview: {e}")

    def _cargar_preview_wm(self, ruta):
        try:
            img = load_cv_image_unchanged(ruta)
            if img is None:
                return
            if img.ndim == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
            elif img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
            self._preview_wm_bgra = img
            self._disparar_preview()
        except Exception as e:
            import logging; logging.getLogger(__name__).warning(f"Error cargando wm preview: {e}")

    def _disparar_preview(self):
        if self._preview_base_bgra is None or self._preview_wm_bgra is None:
            return
        if self._preview_job is not None:
            try:
                self.after_cancel(self._preview_job)
            except Exception:
                pass
        self._preview_job = self.after(_DEBOUNCE_MS, self._lanzar_hilo_preview)

    def _lanzar_hilo_preview(self):
        if self._preview_activo:
            return
        self._preview_activo = True
        self._lbl_preview_status.configure(text=t("watermark_calculando"))
        threading.Thread(target=self._hilo_preview, daemon=True).start()

    def _hilo_preview(self):
        try:
            base = self._preview_base_bgra.copy() # type: ignore
            wm   = self._preview_wm_bgra.copy() # type: ignore

            resultado = aplicar_watermark_np(
                base, wm,
                posicion=self._state.posicion.get(),
                escala=self._state.escala.get() / 100.0,
                opacidad=self._state.opacidad.get() / 100.0,
                margen=max(0, int(self._state.margen.get() * min(base.shape[:2]) / 500)),
            )
            self.after(0, lambda: self._actualizar_preview(resultado))
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(f"Error en hilo preview watermark: {exc}")
            self.after(0, lambda: self._actualizar_preview(None))

    def _actualizar_preview(self, resultado):
        self._preview_activo = False
        self._lbl_preview_status.configure(text="")
        if resultado is None:
            return
        if self._preview_base_bgra is None or self._preview_wm_bgra is None:
            return
        self._mostrar_canvas(self._canvas_preview, resultado)

    def _limpiar(self):
        """Recarga el frame completo para reiniciar el estado."""
        logger.info("watermark.ui: limpiar")
        self.after(0, self._reload_self)

    def _reload_self(self):
        main = self._find_main_window()
        if not main:
            super()._limpiar()
            return
        try:
            if getattr(main, "frames", {}).get("watermark") is self:
                main.frames["watermark"] = None
            self.destroy()
        except Exception:
            pass
        try:
            main.show_module("watermark")
        except Exception:
            pass

    def _find_main_window(self):
        w = self
        while w is not None:
            if hasattr(w, "show_module") and hasattr(w, "frames"):
                return w
            w = getattr(w, "master", None)
        return None

    def _mostrar_watermark_item(self, ruta):
        """Muestra el watermark seleccionado en el panel izquierdo."""
        for w in self._wm_frame.winfo_children():
            w.destroy()

        fila = ctk.CTkFrame(
            self._wm_frame, fg_color=colors.SIDEBAR_BG, corner_radius=8
        )
        fila.grid(row=0, column=0, padx=8, pady=6, sticky="ew")
        fila.grid_columnconfigure(1, weight=1)

        lbl_thumb = ctk.CTkLabel(
            fila, text='', width=44, height=44, fg_color='transparent'
        )
        lbl_thumb.grid(row=0, column=0, padx=(8, 0), pady=6)

        info = ctk.CTkFrame(fila, fg_color='transparent')
        info.grid(row=0, column=1, padx=(10, 8), pady=6, sticky='w')

        p = Path(ruta)
        nombre = p.name if len(p.name) <= 32 else p.name[:29] + '...'
        ctk.CTkLabel(
            info, text=nombre,
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).pack(anchor='w')
        ctk.CTkLabel(
            info,
            text=f'{formatear_bytes(p.stat().st_size)}  -  {p.suffix.upper().lstrip(".")}',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).pack(anchor='w')

        try:
            with Image.open(ruta) as img:
                img = img.copy()
            img.thumbnail((44, 44), Image.Resampling.LANCZOS)
            thumb = ctk.CTkImage(light_image=img, dark_image=img, size=(44, 44))
            lbl_thumb.configure(image=thumb)
            self._wm_thumb = thumb
        except Exception:
            self._wm_thumb = None

    def _mostrar_canvas(self, canvas, img_bgra):
        try:
            if img_bgra.shape[2] == 4:
                img_rgb = cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2RGBA)
                pil_img = Image.fromarray(img_rgb, "RGBA")
            else:
                img_rgb = cv2.cvtColor(img_bgra, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(img_rgb, "RGB")

            h, w = img_bgra.shape[:2]
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(w, h))
            canvas.configure(image=ctk_img, text="")
            canvas._ctk_image = ctk_img
        except Exception as e:
            import logging; logging.getLogger(__name__).warning(f"Error canvas: {e}")

    # ------------------------------------------------------------------ #
    #  Flujo batch                                                         #
    # ------------------------------------------------------------------ #

    def _ejecutar(self):
        logger.info("watermark.ui: click_aplicar")
        if not self._imagenes:
            self._lbl_info.configure(text=t("load_images_first"))
            return

        ruta_wm = self._state.ruta_watermark.get()
        if not ruta_wm:
            self._lbl_info.configure(text=t("watermark_no_wm"))
            return

        carpeta = filedialog.askdirectory(title=t("select_output_folder"))
        if not carpeta:
            logger.info("watermark.ui: proceso_cancelado (sin_carpeta)")
            return

        self._state.carpeta_salida.set(carpeta)
        self._btn_aplicar.configure(state="disabled", text=t("processing"))
        self._show_full_overlay(t("processing"))
        threading.Thread(target=self._proceso, args=(carpeta, ruta_wm), daemon=True).start()

    def _proceso(self, carpeta, ruta_wm):
        res = batch_aplicar_watermark(
            rutas_imagenes=self._imagenes,
            ruta_watermark=ruta_wm,
            carpeta_salida=carpeta,
            posicion=self._state.posicion.get(),
            escala=self._state.escala.get() / 100.0,
            opacidad=self._state.opacidad.get() / 100.0,
            margen=self._state.margen.get(),
        )
        self.after(0, lambda: self._finalizar(res))

    def _finalizar(self, res):
        ok      = res.get("ok", 0)
        errores = res.get("errores", 0)
        logger.info("watermark.ui: finalizar_ok (ok=%s, errores=%s, conflictos=%s)", ok, errores, res.get("conflictos", 0))
        self._hide_full_overlay()
        self._btn_aplicar.configure(state="normal", text=t("watermark_btn"))
        msg = t("watermark_procesadas").format(ok=ok) # type: ignore
        if errores:
            msg += f"  —  {errores} {t('error_occurred')}"
        self._lbl_info.configure(text=msg)
