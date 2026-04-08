"""
UI para el modulo de vectorizacion de imagenes.
Convierte imágenes raster a SVG usando vtracer.

Relacionado con:
    - app/ui/frames/base.py: Clase base de la que hereda.
    - app/ui/frames/vectorizar/state.py: Estado de la interfaz.
    - app/ui/frames/vectorizar/services.py: Servicios de vectorizacion.
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
from app.ui.frames.vectorizar.state import VectorizarState
from app.ui.frames.vectorizar.services import batch_vectorizar


logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
#  Presets: cada uno define los 5 controles de la UI                  #
#  (colormode, nivel_detalle, limpieza, suavidad, tamano)             #
# ------------------------------------------------------------------ #
PRESETS = {
    "Foto": {
        "colormode": "color", "nivel_detalle": 7, "limpieza": 4, "suavidad": 7, "tamano": 4,
    },
    "Ilustración": {
        "colormode": "color", "nivel_detalle": 6, "limpieza": 3, "suavidad": 6, "tamano": 5,
    },
    "Logo": {
        "colormode": "color", "nivel_detalle": 8, "limpieza": 5, "suavidad": 4, "tamano": 7,
    },
    "Line Art": {
        "colormode": "binary", "nivel_detalle": 9, "limpieza": 2, "suavidad": 5, "tamano": 6,
    },
    "Pixel Art": {
        "colormode": "color", "nivel_detalle": 10, "limpieza": 0, "suavidad": 1, "tamano": 8,
    },
    "SVG Liviano": {
        "colormode": "color", "nivel_detalle": 4, "limpieza": 6, "suavidad": 8, "tamano": 9,
    },
    "Máxima Calidad": {
        "colormode": "color", "nivel_detalle": 10, "limpieza": 1, "suavidad": 5, "tamano": 1,
    },
}


def _mapear_params(colormode, nivel_detalle, limpieza, suavidad, tamano):
    """
    Traduce los 5 sliders maestros a los parámetros internos de vtracer.

    nivel_detalle (1-10):
        Alto  → color_precision=8, layer_difference=4, length_threshold=3.0
        Bajo  → color_precision=3, layer_difference=48, length_threshold=9.0

    limpieza (0-10):
        0     → filter_speckle=0
        10    → filter_speckle=64

    suavidad (0-10):
        0     → mode='polygon', corner_threshold=10
        10    → mode='spline', corner_threshold=170

    tamano (1-10, +calidad → +liviano):
        1     → path_precision=8, max_iterations=20
        10    → path_precision=2, max_iterations=2
    """
    t_d = nivel_detalle / 10.0

    color_precision    = max(3, min(8, round(5 + t_d * 3)))
    layer_difference   = max(1, min(64, round(24 - t_d * 20)))
    length_threshold   = round(6.0 - t_d * 4.0, 1)

    filter_speckle     = round(limpieza / 10.0 * 64)

    corner_threshold   = round(20 + (suavidad / 10.0) * 140)
    mode               = "spline" if suavidad >= 5 else "polygon"

    t_s = (tamano - 1) / 9.0
    path_precision     = max(4, min(8, round(8 - t_s * 4)))
    max_iterations     = max(6, min(20, round(20 - t_s * 10)))

    return {
        "colormode":        colormode,
        "filter_speckle":   filter_speckle,
        "color_precision":  color_precision,
        "layer_difference": layer_difference,
        "corner_threshold": corner_threshold,
        "length_threshold": length_threshold,
        "max_iterations":   max_iterations,
        "path_precision":   path_precision,
        "mode":             mode,
        "splice_threshold": 45,
    }


class VectorizarFrame(BaseFrame):
    """
    Frame del modulo de vectorizacion.

    Layout de dos columnas:
        Izquierda: selección de imágenes
        Derecha  : presets + controles + exportar
    """

    def __init__(self, parent):
        logger.info("vectorizar.ui: init")
        self._state = VectorizarState()
        super().__init__(parent, t("vectorizar_title"))
        try:
            self._btn_limpiar.grid_remove()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  UI                                                                  #
    # ------------------------------------------------------------------ #

    def _build_content(self):
        logger.info("vectorizar.ui: build_content")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Columna izquierda: selecci?n de im?genes ---
        panel_izq = ctk.CTkFrame(self, fg_color="transparent")
        panel_izq.grid(row=1, column=0, padx=(20, 8), pady=(0, 12), sticky="nsew")
        panel_izq.grid_columnconfigure(0, weight=1)
        panel_izq.grid_rowconfigure(1, weight=1)

        self._btn_seleccionar = self._crear_boton_seleccionar(panel_izq)
        self._btn_seleccionar.grid(row=0, column=0, pady=(0, 8), sticky="ew")

        self._lista_frame = self._crear_lista_archivos(panel_izq)
        self._lista_frame.grid(row=1, column=0, sticky="nsew")
        self._lista_frame.grid_columnconfigure(0, weight=1)

        self._lbl_lista_vacia = self._crear_lista_vacia(self._lista_frame)
        self._lbl_lista_vacia.pack(pady=12)

        # Botón limpiar (arriba derecha, fuera del contenedor)
        self._btn_limpiar_param = ctk.CTkButton(
            self,
            text=t("clean"),
            height=28,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.BTN_CLEAR_BG,
            text_color=colors.BTN_CLEAR_TEXT,
            hover_color=colors.BTN_CLEAR_HOVER,
            command=self._limpiar,
        )
        self._btn_limpiar_param.grid(row=0, column=1, padx=(0, 20), pady=(16, 0), sticky="e")

        # --- Columna derecha: controles ---
        panel_der = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
        )
        panel_der.grid(row=1, column=1, padx=(8, 20), pady=(0, 12), sticky="nsew")
        panel_der.grid_columnconfigure(0, weight=1)
        self._construir_panel_controles(panel_der)

    def _construir_panel_controles(self, p):
        """Construye presets + sliders + exportar dentro del panel derecho."""
        pad_x = (16, 16)

        # -- Preset --
        ctk.CTkLabel(
            p, text=t("vectorizar_preset"),
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY, anchor="w",
        ).grid(row=0, column=0, padx=pad_x, pady=(14, 2), sticky="w")

        self._combo_preset = ctk.CTkComboBox(
            p,
            values=list(PRESETS.keys()),
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
        self._combo_preset.set(list(PRESETS.keys())[0])
        self._combo_preset.grid(row=1, column=0, padx=pad_x, pady=(0, 6), sticky="ew")
        self._aplicar_preset(self._combo_preset.get(), animar=False)

        # -- Separador visual --
        sep = ctk.CTkFrame(p, height=1, fg_color=colors.SIDEBAR_SEPARATOR)
        sep.grid(row=2, column=0, padx=pad_x, pady=(0, 6), sticky="ew")

        # -- Tipo de vectorización --
        ctk.CTkLabel(
            p, text=t("vectorizar_tipo"),
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY, anchor="w",
        ).grid(row=3, column=0, padx=pad_x, pady=(0, 4), sticky="w")

        self._seg_color = ctk.CTkSegmentedButton(
            p,
            values=[t("vectorizar_color"), t("vectorizar_byn")],
            font=fonts.FUENTE_CHICA,
            selected_color=colors.SEGMENT_SELECTED,
            selected_hover_color=colors.SEGMENT_SELECTED_HOVER,
            unselected_color=colors.SIDEBAR_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
            command=self._al_cambiar_colormode,
        )
        self._seg_color.set(t("vectorizar_color"))
        self._seg_color.grid(row=4, column=0, padx=pad_x, pady=(0, 8), sticky="ew")

        # -- Sliders --
        self._lbl_detalle_val  = self._crear_slider_fila(p, row=5,  label=t("vectorizar_detalle"), var=self._state.nivel_detalle, pad_x=pad_x)
        self._lbl_limpieza_val = self._crear_slider_fila(p, row=7,  label=t("vectorizar_limpieza"), var=self._state.limpieza, pad_x=pad_x)
        self._lbl_suavidad_val = self._crear_slider_fila(p, row=9,  label=t("vectorizar_suavidad"), var=self._state.suavidad, pad_x=pad_x)
        self._lbl_tamano_val   = self._crear_slider_fila(p, row=11, label=t("vectorizar_tamano"), var=self._state.tamano, pad_x=pad_x)

        # Subtítulos de extremos para cada slider
        self._crear_hint_fila(p, row=6,  izq=t("vectorizar_detalle_bajo"),  der=t("vectorizar_detalle_alto"),  pad_x=pad_x)
        self._crear_hint_fila(p, row=8,  izq=t("vectorizar_limpieza_nada"), der=t("vectorizar_limpieza_max"),  pad_x=pad_x)
        self._crear_hint_fila(p, row=10, izq=t("vectorizar_suavidad_ang"),  der=t("vectorizar_suavidad_sua"),  pad_x=pad_x)
        self._crear_hint_fila(p, row=12, izq=t("vectorizar_tamano_cal"),    der=t("vectorizar_tamano_liv"),    pad_x=pad_x)

        # -- Botón exportar --
        self._btn_exportar = ctk.CTkButton(
            p,
            text=t("vectorizar_btn_exportar"),
            height=38,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._ejecutar,
        )
        self._btn_exportar.grid(row=13, column=0, padx=pad_x, pady=(8, 10), sticky="ew")

    def _crear_slider_fila(self, parent, row, label, var, pad_x):
        """Crea una fila con label + slider + valor numérico. Retorna el label de valor."""
        fila = ctk.CTkFrame(parent, fg_color="transparent")
        fila.grid(row=row, column=0, padx=pad_x, pady=(4, 0), sticky="ew")
        fila.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            fila, text=label,
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY,
            anchor="w", width=90,
        ).grid(row=0, column=0, sticky="w")

        lbl_val = ctk.CTkLabel(
            fila, text=str(var.get()),
            font=fonts.FUENTE_CHICA, text_color=colors.ACENTO, width=24,
        )
        lbl_val.grid(row=0, column=2, padx=(6, 0))

        ctk.CTkSlider(
            fila,
            from_=0, to=10,
            number_of_steps=10,
            variable=var,
            command=lambda v, lv=lbl_val: lv.configure(text=str(int(v))),
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            progress_color=colors.ACENTO,
            fg_color=colors.SIDEBAR_SEPARATOR,
            height=14,
        ).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        return lbl_val

    def _crear_hint_fila(self, parent, row, izq, der, pad_x):
        """Fila con dos labels pequeños: extremo izquierdo y derecho del slider."""
        fila = ctk.CTkFrame(parent, fg_color="transparent")
        fila.grid(row=row, column=0, padx=pad_x, pady=(0, 1), sticky="ew")
        fila.grid_columnconfigure(0, weight=1)
        fila.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            fila, text=izq,
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(90, 0))

        ctk.CTkLabel(
            fila, text=der,
            font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY, anchor="e",
        ).grid(row=0, column=1, sticky="e")

    # ------------------------------------------------------------------ #
    #  Lógica de controles                                                 #
    # ------------------------------------------------------------------ #

    def _aplicar_preset(self, nombre, animar=True):
        """Aplica los valores de un preset a todos los controles."""
        logger.info("vectorizar.ui: aplicar_preset (%s)", nombre)
        preset = PRESETS.get(nombre)
        if not preset:
            return

        self._state.colormode.set(preset["colormode"])
        self._state.nivel_detalle.set(preset["nivel_detalle"])
        self._state.limpieza.set(preset["limpieza"])
        self._state.suavidad.set(preset["suavidad"])
        self._state.tamano.set(preset["tamano"])

        # Actualizar labels de valor de sliders si ya existen
        for attr, key in [
            ("_lbl_detalle_val",  "nivel_detalle"),
            ("_lbl_limpieza_val", "limpieza"),
            ("_lbl_suavidad_val", "suavidad"),
            ("_lbl_tamano_val",   "tamano"),
        ]:
            if hasattr(self, attr):
                getattr(self, attr).configure(text=str(preset[key]))

        # Sincronizar segmented button de colormode
        if hasattr(self, "_seg_color"):
            self._seg_color.set(
                t("vectorizar_color") if preset["colormode"] == "color"
                else t("vectorizar_byn")
            )

    def _al_cambiar_colormode(self, valor):
        logger.info("vectorizar.ui: cambiar_colormode (%s)", valor)
        self._state.colormode.set(
            "color" if valor == t("vectorizar_color") else "binary"
        )

    def _cargar_imagenes(self, rutas):
        logger.info("vectorizar.ui: cargar_imagenes (total=%s)", len(rutas))
        omitidos_grandes = 0
        rutas_validas = []
        for r in rutas:
            try:
                if Path(r).stat().st_size > 1_000_000:
                    omitidos_grandes += 1
                    continue
            except Exception:
                # Si no se puede stat-ear, dejamos que el flujo normal lo maneje
                # (o quede fuera si luego falla el thumbnail/lectura).
                pass
            rutas_validas.append(r)

        if omitidos_grandes:
            logger.info("vectorizar.ui: omitidos_por_tamano (>%s bytes=%s)", 1_000_000, omitidos_grandes)

        limite = 50
        total = len(rutas_validas)
        if total > limite:
            rutas_validas = rutas_validas[:limite]
            self._limite_msg = t("limit_reached").format(limit=limite, total=total) # type: ignore
        else:
            self._limite_msg = None

        super()._cargar_imagenes(rutas_validas)
        self._state.imagenes = list(rutas_validas)
        n = len(self._imagenes)
        suffix = t("images_loaded") if n > 1 else t("image_loaded")
        msg = f"{n} {suffix}" if n else ""
        if self._limite_msg:
            msg = f"{msg}  -  {self._limite_msg}" if msg else str(self._limite_msg)
        if omitidos_grandes:
            extra = t("vectorizar_omitidos_por_tamano").format(count=omitidos_grandes)  # type: ignore
            msg = f"{msg}  -  {extra}" if msg else extra
        if msg:
            self._lbl_info.configure(text=msg)
        logger.info("vectorizar.ui: imagenes cargadas (mostradas=%s)", n)
    
    # ------------------------------------------------------------------ #
    # ------------------------------------------------------------------ #

    def _limpiar(self):
        logger.info("vectorizar.ui: limpiar")
        self.after(0, self._reload_self)

    def _reload_self(self):
        main = self._find_main_window()
        if not main:
            super()._limpiar()
            return
        try:
            if getattr(main, "frames", {}).get("vectorizar") is self:
                main.frames["vectorizar"] = None
            self.destroy()
        except Exception:
            pass
        try:
            main.show_module("vectorizar")
        except Exception:
            pass

    def _find_main_window(self):
        w = self
        while w is not None:
            if hasattr(w, "show_module") and hasattr(w, "frames"):
                return w
            w = getattr(w, "master", None)
        return None

    # ------------------------------------------------------------------ #
    #  Flujo: _ejecutar → _proceso → _finalizar                           #
    # ------------------------------------------------------------------ #
    def _ejecutar(self):
        """Inicia el proceso de vectorizacion."""
        logger.info('vectorizar.ui: click_vectorizar')
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_images_first'))
            return

        carpeta = filedialog.askdirectory(title=t('select_output_folder'))
        if not carpeta:
            logger.info('vectorizar.ui: proceso_cancelado (sin_carpeta)')
            return

        self._state.carpeta_salida.set(carpeta)
        self._btn_exportar.configure(state='disabled', text=t('processing'))
        self._lbl_info.configure(
            text=f'{t("processing")} {len(self._imagenes)} imagen{"es" if len(self._imagenes) > 1 else ""}...'
        )

        # Capturar params antes de entrar al thread para evitar
        # accesos a StringVar/IntVar desde hilo secundario
        params = _mapear_params(
            colormode=self._state.colormode.get(),
            nivel_detalle=self._state.nivel_detalle.get(),
            limpieza=self._state.limpieza.get(),
            suavidad=self._state.suavidad.get(),
            tamano=self._state.tamano.get(),
        )

        threading.Thread(
            target=self._proceso,
            args=(carpeta, params),
            daemon=True
        ).start()

    def _proceso(self, carpeta, params):
        """
        Ejecuta la vectorizacion en segundo plano.

        Args:
            carpeta: Carpeta de salida elegida.
            params: Diccionario de parametros ya calculados.
        """
        try:
            resultado = batch_vectorizar(
                rutas_imagenes=self._imagenes,
                carpeta_salida=carpeta,
                **params,
            )
        except Exception as exc:
            logger.exception("vectorizar.ui: error en exportar")
            resultado = {"ok": 0, "errores": len(self._imagenes), "archivos": [], "error": str(exc)}
        self.after(0, lambda: self._finalizar(resultado))

    def _finalizar(self, resultado):
        """
        Muestra el resultado final y reactiva el boton.

        Args:
            resultado: Diccionario con ok, errores, archivos.
        """
        ok      = resultado.get('ok', 0)
        errores = resultado.get('errores', 0)
        logger.info('vectorizar.ui: finalizar (ok=%s, errores=%s)', ok, errores)

        self._btn_exportar.configure(state='normal', text=t('vectorizar_btn_exportar'))
        error_msg = resultado.get('error')
        if error_msg:
            self._lbl_info.configure(text=f'{t("error_generic")}: {error_msg}')
            return
        msg = t('vectorizar_exportadas').format(ok=ok)  # type: ignore
        if errores:
            msg += f'  —  {errores} {t("error_occurred")}'
        self._lbl_info.configure(text=msg)
