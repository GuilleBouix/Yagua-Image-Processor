"""
UI para el modulo de renombrado de archivos en lote.

Relacionado con:
    - app/ui/frames/base.py: Clase base de la que hereda.
    - app/ui/frames/rename/state.py: Estado de la interfaz.
    - app/ui/frames/rename/services.py: Servicios de logica.
    - app/translations/__init__.py: Traducciones de la UI.
"""

from __future__ import annotations

import threading

import customtkinter as ctk

from app.ui import colors, fonts
from app.translations import t
from app.ui.frames.base import BaseFrame
from app.ui.frames.rename.services import generar_nombres_preview, renombrar_archivos
from app.ui.frames.rename.state import RenameState


class RenameFrame(BaseFrame):
    """Frame del modulo de renombrado en lote."""

    def __init__(self, parent):
        """Inicializa el frame."""
        self._state = RenameState()
        super().__init__(parent, t('rename_title'))

    def _build_content(self):
        """Construye el contenido del modulo."""
        # Boton seleccionar
        self._btn_seleccionar = self._crear_boton_seleccionar(self)
        self._btn_seleccionar.grid(row=1, column=0, padx=28, pady=(8, 0), sticky='ew')

        # Panel de opciones
        panel = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel.grid(row=2, column=0, padx=28, pady=8, sticky='ew')
        panel.grid_columnconfigure(1, weight=1)
        self._construir_opciones(panel)

        # Panel de preview
        panel_prev = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel_prev.grid(row=3, column=0, padx=28, pady=(0, 8), sticky='ew')
        panel_prev.grid_columnconfigure(0, weight=1)
        self._construir_preview(panel_prev)

        # Vincular todas las variables al preview
        self._vincular_variables()

    def _construir_opciones(self, p):
        """
        Construye las tres secciones de opciones.

        Args:
            p: Frame padre del panel.
        """
        # ── Prefijo + numeración ──────────────────────────────────────────────
        ctk.CTkCheckBox(
            p,
            text=t('rename_numbering'),
            variable=self._state.numeracion_activa,
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            fg_color=colors.ACENTO,
            hover_color=colors.ACENTO_HOVER,
            border_color=colors.SIDEBAR_SEPARATOR,
            checkmark_color=colors.TEXT_ACTIVE,
        ).grid(row=0, column=0, padx=(16, 8), pady=(14, 8), sticky='w')

        fila_num = ctk.CTkFrame(p, fg_color='transparent')
        fila_num.grid(row=0, column=1, padx=(0, 16), pady=(14, 8), sticky='w')

        ctk.CTkLabel(
            fila_num, text=t('rename_prefix'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).pack(side='left', padx=(0, 6))

        ctk.CTkEntry(
            fila_num,
            textvariable=self._state.prefijo,
            font=fonts.FUENTE_BASE,
            fg_color=colors.FRAMES_BG,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            placeholder_text='foto',
            placeholder_text_color=colors.TEXT_GRAY,
            width=100
        ).pack(side='left', padx=(0, 16))

        ctk.CTkLabel(
            fila_num, text=t('rename_start'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).pack(side='left', padx=(0, 6))

        ctk.CTkEntry(
            fila_num,
            textvariable=self._state.inicio,
            font=fonts.FUENTE_BASE,
            fg_color=colors.FRAMES_BG,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            width=52
        ).pack(side='left')

        # Separador
        ctk.CTkFrame(p, height=1, fg_color=colors.SIDEBAR_SEPARATOR).grid(
            row=1, column=0, columnspan=2, padx=16, pady=2, sticky='ew'
        )

        # ── Agregar fecha ─────────────────────────────────────────────────────
        ctk.CTkCheckBox(
            p,
            text=t('rename_date'),
            variable=self._state.fecha_activa,
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            fg_color=colors.ACENTO,
            hover_color=colors.ACENTO_HOVER,
            border_color=colors.SIDEBAR_SEPARATOR,
            checkmark_color=colors.TEXT_ACTIVE,
        ).grid(row=2, column=0, padx=(16, 8), pady=(8, 8), sticky='w')

        fila_fecha = ctk.CTkFrame(p, fg_color='transparent')
        fila_fecha.grid(row=2, column=1, padx=(0, 16), pady=(8, 8), sticky='w')

        ctk.CTkSegmentedButton(
            fila_fecha,
            values=['prefijo', 'sufijo'],
            variable=self._state.posicion_fecha,
            font=fonts.FUENTE_CHICA,
            selected_color=colors.ACENTO,
            selected_hover_color=colors.ACENTO_HOVER,
            unselected_color=colors.SIDEBAR_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
            command=lambda _: self._actualizar_preview()
        ).pack(side='left', padx=(0, 16))

        ctk.CTkOptionMenu(
            fila_fecha,
            values=['%Y%m%d', '%d%m%Y', '%Y-%m-%d', '%d-%m-%Y'],
            variable=self._state.formato_fecha,
            font=fonts.FUENTE_BASE,
            fg_color=colors.SIDEBAR_BG,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            text_color=colors.TEXT_COLOR,
            dropdown_fg_color=colors.PANEL_BG,
            dropdown_text_color=colors.TEXT_COLOR,
            dropdown_hover_color=colors.SIDEBAR_HOVER,
            command=lambda _: self._actualizar_preview()
        ).pack(side='left')

        # Separador
        ctk.CTkFrame(p, height=1, fg_color=colors.SIDEBAR_SEPARATOR).grid(
            row=3, column=0, columnspan=2, padx=16, pady=2, sticky='ew'
        )

        # ── Capitalización ────────────────────────────────────────────────────
        ctk.CTkLabel(
            p, text=t('rename_case'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).grid(row=4, column=0, padx=(16, 8), pady=(8, 14), sticky='w')

        ctk.CTkSegmentedButton(
            p,
            values=['minusculas', 'mayusculas'],
            variable=self._state.caso,
            font=fonts.FUENTE_CHICA,
            selected_color=colors.ACENTO,
            selected_hover_color=colors.ACENTO_HOVER,
            unselected_color=colors.SIDEBAR_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
            command=self._aplicar_capitalizacion
        ).grid(row=4, column=1, padx=(0, 16), pady=(8, 14), sticky='w')

    def _construir_preview(self, p):
        """
        Construye la tabla de preview con cabeceras y boton renombrar.

        Args:
            p: Frame padre del panel.
        """
        # Header
        header = ctk.CTkFrame(p, fg_color='transparent')
        header.grid(row=0, column=0, padx=16, pady=(12, 6), sticky='ew')
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text=t('rename_preview'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).grid(row=0, column=0, sticky='w')

        self._btn_renombrar = ctk.CTkButton(
            header,
            text=t('rename_btn'),
            height=30, width=110,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._renombrar
        )
        self._btn_renombrar.grid(row=0, column=1, sticky='e')

        # Cabeceras
        cab = ctk.CTkFrame(p, fg_color=colors.SIDEBAR_BG, corner_radius=6)
        cab.grid(row=1, column=0, padx=16, pady=(0, 4), sticky='ew')
        cab.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            cab, text=t('rename_col_original'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, padx=10, pady=5, sticky='w')

        ctk.CTkLabel(
            cab, text=t('rename_col_nuevo'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=1, padx=10, pady=5, sticky='w')

        # Lista scrolleable
        self._lista_preview = ctk.CTkScrollableFrame(
            p,
            fg_color='transparent',
            border_width=0,
            height=140,
            scrollbar_button_color=colors.SIDEBAR_SEPARATOR,
            scrollbar_button_hover_color=colors.ACENTO_DIMMED,
        )
        self._lista_preview.grid(row=2, column=0, padx=16, pady=(0, 12), sticky='ew')
        self._lista_preview.grid_columnconfigure((0, 1), weight=1)

        # Placeholder inicial
        self._renderizar_preview([])

    def _vincular_variables(self):
        """
        Vincula todas las variables de estado al preview en tiempo real.
        Incluye StringVar, BooleanVar y opciones de segmented/option.
        """
        # StringVar — entries y opciones
        for var in (
            self._state.prefijo,
            self._state.inicio,
            self._state.posicion_fecha,
            self._state.formato_fecha,
            self._state.caso,
        ):
            var.trace_add('write', lambda *_: self._actualizar_preview())

        # BooleanVar — checkboxes
        for var in (
            self._state.numeracion_activa,
            self._state.fecha_activa,
        ):
            var.trace_add('write', lambda *_: self._actualizar_preview())

    def _cargar_imagenes(self, rutas):
        """Carga archivos y dispara el preview."""
        self._imagenes = list(rutas)
        self._state.imagenes = self._imagenes
        n = len(rutas)
        suffix = t('files_loaded') if n > 1 else t('file_loaded')
        self._lbl_info.configure(text=f'{n} {suffix}')
        self._actualizar_preview()

    def _actualizar_preview(self, *args):
        """Lanza la generacion del preview en segundo plano."""
        if not self._imagenes:
            return
        threading.Thread(target=self._generar_preview, daemon=True).start()

    def _generar_preview(self):
        """Genera el preview en segundo plano."""
        try:
            opciones = self._state.obtener_opciones()
            preview = generar_nombres_preview(self._imagenes, opciones)
            self.after(0, lambda: self._renderizar_preview(preview))
        except Exception:
            pass

    def _renderizar_preview(self, preview):
        """
        Renderiza la tabla de preview.

        Args:
            preview: Lista de tuplas (nombre_original, nombre_nuevo).
        """
        for widget in self._lista_preview.winfo_children():
            widget.destroy()

        if not preview:
            ctk.CTkLabel(
                self._lista_preview,
                text=t('rename_preview_empty'),
                font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY
            ).grid(row=0, column=0, columnspan=2, pady=16)
            return

        for indice, (original, nuevo) in enumerate(preview):
            cambio = original != nuevo

            ctk.CTkLabel(
                self._lista_preview,
                text=original,
                font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY,
                anchor='w'
            ).grid(row=indice, column=0, padx=(4, 4), pady=2, sticky='w')

            ctk.CTkLabel(
                self._lista_preview,
                text=nuevo,
                font=fonts.FUENTE_CHICA,
                text_color=colors.ACENTO if cambio else colors.TEXT_GRAY,
                anchor='w'
            ).grid(row=indice, column=1, padx=(4, 4), pady=2, sticky='w')

    def _renombrar(self):
        """Inicia el renombrado en segundo plano."""
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_files_first'))
            return
        self._btn_renombrar.configure(state='disabled', text=t('renaming'))
        threading.Thread(target=self._proceso, daemon=True).start()

    def _proceso(self):
        """Ejecuta el renombrado."""
        opciones = self._state.obtener_opciones()
        res = renombrar_archivos(self._imagenes, opciones)
        self.after(0, lambda: self._finalizar(
            res['ok'], res['errores'], res['conflictos']
        ))

    def _finalizar(self, ok, errores, conflictos):
        """Muestra el resultado y limpia la seleccion."""
        self._btn_renombrar.configure(state='normal', text=t('rename_btn'))
        suffix = t('files_loaded') if ok > 1 else t('file_loaded')
        msg = f'{ok} {suffix} {t("renamed")}'
        if conflictos:
            msg += f'  ·  {conflictos} {t("rename_conflicts")}'
        if errores:
            msg += f'  ·  {errores} {t("error_occurred")}'
        self._lbl_info.configure(text=msg)

        # Limpiar despues de renombrar exitoso
        self._imagenes = []
        self._state.imagenes = []
        self._renderizar_preview([])

    def _aplicar_capitalizacion(self, caso):
        """
        Modifica el prefijo segun la capitalizacion elegida
        para forzar actualizacion del preview via trace.

        Args:
            caso: 'sin_cambio', 'minusculas' o 'mayusculas'.
        """
        prefijo_actual = self._state.prefijo.get()
        if not prefijo_actual:
            self._actualizar_preview()
            return

        if caso == 'minusculas':
            self._state.prefijo.set(prefijo_actual.lower())
        elif caso == 'mayusculas':
            self._state.prefijo.set(prefijo_actual.upper())
        else:
            self._actualizar_preview()