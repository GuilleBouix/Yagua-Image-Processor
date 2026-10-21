"""Interfaz grafica para redimensionar, recortar y ajustar canvas.

Permite procesar imagenes de tres formas:
    - Redimension: ajustar tamano por porcentaje, pixeles o preset
    - Recortar: cortar imagenes manteniendo una proporcion
    - Canvas: colocar imagenes sobre un fondo solido o transparente

Relaciones:
    - BaseFrame: app.ui.frames.base.BaseFrame
    - Traducciones: app.translations
    - Colores: app.ui.colors
    - Fuentes: app.ui.fonts
    - Servicios: app.ui.frames.resize.services
    - Estado: app.ui.frames.resize.state
"""

from __future__ import annotations

from app.ui.building import stepwise, steps_for
import logging

import customtkinter as ctk

from app.ui import colors, fonts, styles
from app.translations import t
from app.ui.frames.base import BaseFrame
from app.ui.rendering import activate_tab
from app.ui.frames.resize.services import (
    batch_redimensionar,
    batch_recortar,
    batch_canvas,
    PRESETS_LISTA,
    RATIOS,
    any_supports_transparency,
    canvas_color_for_choice,
    parse_dimensions,
)
from app.ui.frames.resize.state import ResizeState


logger = logging.getLogger(__name__)


class ResizeFrame(BaseFrame):
    """Frame principal del modulo de redimension, recorte y canvas."""

    design_system = True

    def __init__(self, parent, *, defer_build=False):
        logger.info("resize.ui: init")
        self._state = ResizeState()
        super().__init__(parent, t('resize_title'), defer_build=defer_build)

    def _prepare_additional_steps(self):
        if self._defer_build:
            for mode in (t('pixels'), t('preset'), t('percentage')):
                yield from steps_for(self._actualizar_modo_resize, mode)

    def _on_build_complete(self):
        self._scrollbar.configure(corner_radius=0, width=6, border_spacing=1)
        if isinstance(self._lista_frame, ctk.CTkScrollableFrame):
            self._lista_frame._scrollbar.configure(corner_radius=0, width=6, border_spacing=1)

    @stepwise
    def _build_content(self):
        """Construir el contenido principal del frame con tabs."""
        logger.info("resize.ui: build_content")
        yield
        izquierda, derecha = self._crear_workspace()
        yield
        izquierda.grid_rowconfigure(3, weight=1)
        yield
        derecha.grid_rowconfigure(1, weight=1)
        yield

        self._tab = styles.SegmentedButton(
            izquierda,
            values=[t('resize_tab'), t('crop_tab'), t('canvas_tab')],
            font=fonts.FUENTE_BASE,
            command=self._cambiar_tab
        )
        yield
        self._tab.set(t('resize_tab'))
        yield
        self._tab.grid(row=0, column=0, padx=16, pady=(16, 8), sticky='ew')
        yield

        self._btn_seleccionar = self._crear_boton_seleccionar(izquierda)
        yield
        self._btn_seleccionar.grid(row=1, column=0, padx=16, pady=(0, 8), sticky='ew')
        yield

        ctk.CTkLabel(
            derecha, text=t('files_loaded').capitalize(), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).grid(row=0, column=0, padx=16, pady=(16, 8), sticky='w')
        yield
        self._lista_frame = self._crear_lista_archivos(derecha, height=420)
        yield
        self._lista_frame.grid(row=1, column=0, padx=16, pady=(0, 16), sticky='nsew')
        yield
        self._lista_frame.grid_columnconfigure(0, weight=1)
        yield

        self._lbl_lista_vacia = ctk.CTkLabel(
            self._lista_frame,
            text=t('no_images'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )
        yield
        self._lbl_lista_vacia.pack(pady=12)
        yield

        yield from self._build_save_selector(izquierda, 2)

        self._contenedor = ctk.CTkFrame(izquierda, fg_color='transparent', corner_radius=0)
        yield
        self._contenedor.grid(row=3, column=0, padx=16, pady=(0, 16), sticky='nsew')
        yield
        self._contenedor.grid_columnconfigure(0, weight=1)
        yield

        self._frames: dict[str, ctk.CTkFrame] = {
            t('resize_tab'): (yield from steps_for(self._build_tab_resize)),
            t('crop_tab'): (yield from steps_for(self._build_tab_crop)),
            t('canvas_tab'): (yield from steps_for(self._build_tab_canvas)),
        }
        yield
        for f in self._frames.values():
            f.grid(row=0, column=0, sticky='ew')
            yield

        self._cambiar_tab(t('resize_tab'))
        yield

    @stepwise
    def _build_tab_resize(self):
        """Construir el tab de redimension con controles de modo."""
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent', corner_radius=0)
        if self._defer_build:
            f.grid(row=0, column=0, sticky='nsew')
        yield
        f.grid_columnconfigure(0, weight=1)
        yield

        panel = ctk.CTkFrame(
            f, **styles.surface('panel'),
        )
        yield
        panel.grid(row=0, column=0, sticky='ew')
        yield
        panel.grid_columnconfigure(1, weight=1)
        yield

        ctk.CTkLabel(
            panel, text=t('mode'), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(16, 8), sticky='w')
        yield

        styles.SegmentedButton(
            panel,
            values=[t('percentage'), t('pixels'), t('preset')],
            variable=self._state.modo_resize,
            font=fonts.FUENTE_CHICA,
            command=self._actualizar_modo_resize
        ).grid(row=0, column=1, padx=(0, 16), pady=(16, 8), sticky='w')
        yield

        self._frame_controles_resize = ctk.CTkFrame(panel, fg_color='transparent', corner_radius=0)
        yield
        self._frame_controles_resize.grid(
            row=1, column=0, columnspan=2, padx=16, pady=(0, 8), sticky='ew'
        )
        yield
        self._frame_controles_resize.grid_columnconfigure(1, weight=1)
        yield

        self._frame_ratio = ctk.CTkFrame(panel, fg_color='transparent', corner_radius=0)
        yield
        self._frame_ratio.grid(
            row=2, column=0, columnspan=2, padx=16, pady=(0, 8), sticky='ew'
        )
        yield
        styles.CheckBox(
            self._frame_ratio,
            text=t('maintain_aspect'),
            variable=self._state.mantener_ratio,
            font=fonts.FUENTE_BASE,
        ).pack(anchor='w')
        yield

        self._btn_resize = self._new_button(
            panel, role='primary', text=t('resize_tab'),
            font=fonts.FUENTE_BASE,
            command=self._ejecutar_resize
        )
        yield
        self._btn_resize.grid(
            row=3, column=0, columnspan=2, padx=16, pady=(0, 16), sticky='ew'
        )
        yield

        (yield from steps_for(self._actualizar_modo_resize, t('percentage')))
        yield
        return f

    @stepwise
    def _actualizar_modo_resize(self, modo: str):
        """Actualizar controles segun el modo de redimension seleccionado.

        Args:
            modo: Modo actual (porcentaje, pixels o preset)
        """
        logger.info("resize.ui: actualizar_modo_resize (%s)", modo)
        yield
        if not hasattr(self, '_resize_mode_panels'):
            self._resize_mode_panels = {}
            yield
            self._frame_controles_resize.grid_columnconfigure(0, weight=1)
            yield
        for name, panel in self._resize_mode_panels.items():
            if name != modo:
                panel.grid_remove()
                yield

        if modo == t('pixels'):
            self._frame_ratio.grid()
            yield
        else:
            self._frame_ratio.grid_remove()
            yield

        if modo in self._resize_mode_panels:
            self._resize_mode_panels[modo].grid()
            yield
            return
        fc = ctk.CTkFrame(self._frame_controles_resize, fg_color='transparent', corner_radius=0)
        yield
        fc.grid(row=0, column=0, sticky='ew')
        yield
        self._resize_mode_panels[modo] = fc
        yield

        if modo == t('percentage'):
            fc.grid_columnconfigure(0, weight=0)
            yield
            fc.grid_columnconfigure(1, weight=1)
            yield
            fc.grid_columnconfigure(2, weight=0)
            yield

            self._lbl_pct = ctk.CTkLabel(
                fc, text=f'{self._state.pct_var.get()}%', font=fonts.FUENTE_BASE,
                text_color=colors.ACENTO, fg_color='transparent', width=36
            )
            yield

            ctk.CTkSlider(
                fc, from_=1, to=200, variable=self._state.pct_var,
                button_color=colors.ACENTO,
                button_hover_color=colors.ACENTO_HOVER,
                progress_color=colors.ACENTO,
                fg_color=styles.palette().border,
                command=lambda v: self._lbl_pct.configure(text=f'{int(v)}%')
            ).grid(row=0, column=0, columnspan=2, sticky='ew', padx=(0, 8))
            yield

            self._lbl_pct.grid(row=0, column=2)
            yield

        elif modo == t('pixels'):
            fc.grid_columnconfigure(0, weight=0)
            yield
            fc.grid_columnconfigure(1, weight=0)
            yield
            fc.grid_columnconfigure(2, weight=0)
            yield
            fc.grid_columnconfigure(3, weight=0)
            yield

            ctk.CTkLabel(
                fc, text=t('width'), font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY
            ).grid(row=0, column=0, padx=(0, 4), sticky='w')
            yield

            self._entry_ancho = styles.Entry(
                fc, width=90, font=fonts.FUENTE_BASE,
                placeholder_text='1920',
            )
            yield
            self._entry_ancho.grid(row=0, column=1, padx=(0, 16))
            yield

            ctk.CTkLabel(
                fc, text=t('height'), font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY
            ).grid(row=0, column=2, padx=(0, 4), sticky='w')
            yield

            self._entry_alto = styles.Entry(
                fc, width=90, font=fonts.FUENTE_BASE,
                placeholder_text='1080',
            )
            yield
            self._entry_alto.grid(row=0, column=3)
            yield

        elif modo == t('preset'):
            fc.grid_columnconfigure(0, weight=1)
            yield

            styles.OptionField(
                fc,
                width=140,
                values=PRESETS_LISTA,
                variable=self._state.preset_var,
                font=fonts.FUENTE_BASE,
            ).grid(row=0, column=0, sticky='ew')
            yield

    @stepwise
    def _build_tab_crop(self):
        """Construir el tab de recorte con selector de proporcion."""
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent', corner_radius=0)
        if self._defer_build:
            f.grid(row=0, column=0, sticky='nsew')
        yield
        f.grid_columnconfigure(0, weight=1)
        yield

        panel = ctk.CTkFrame(
            f, **styles.surface('panel'),
        )
        yield
        panel.grid(row=0, column=0, sticky='ew')
        yield
        panel.grid_columnconfigure(1, weight=1)
        yield

        ctk.CTkLabel(
            panel, text=t('ratio'), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(16, 8), sticky='w')
        yield

        styles.OptionField(
            panel,
            width=140,
            values=list(RATIOS.keys()),
            variable=self._state.ratio_var,
            font=fonts.FUENTE_BASE,
        ).grid(row=0, column=1, padx=(0, 16), pady=(16, 8), sticky='w')
        yield

        ctk.CTkLabel(
            panel,
            text=t('crop_centered'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 8), sticky='w')
        yield

        self._btn_crop = self._new_button(
            panel, role='primary', text=t('crop_tab'),
            font=fonts.FUENTE_BASE,
            command=self._ejecutar_crop
        )
        yield
        self._btn_crop.grid(
            row=2, column=0, columnspan=2, padx=16, pady=(0, 16), sticky='ew'
        )
        yield
        return f

    @stepwise
    def _build_tab_canvas(self):
        """Construir el tab de canvas con entradas de tamano y color de fondo."""
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent', corner_radius=0)
        if self._defer_build:
            f.grid(row=0, column=0, sticky='nsew')
        yield
        f.grid_columnconfigure(0, weight=1)
        yield

        panel = ctk.CTkFrame(
            f, **styles.surface('panel'),
        )
        yield
        panel.grid(row=0, column=0, sticky='ew')
        yield
        panel.grid_columnconfigure(1, weight=1)
        yield

        ctk.CTkLabel(
            panel, text=t('size'), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(16, 8), sticky='w')
        yield

        fila_dim = ctk.CTkFrame(panel, fg_color='transparent', corner_radius=0)
        yield
        fila_dim.grid(row=0, column=1, padx=(0, 16), pady=(16, 8), sticky='w')
        yield

        self._canvas_ancho = styles.Entry(
            fila_dim, width=80, font=fonts.FUENTE_BASE,
            placeholder_text='1080',
        )
        yield
        self._canvas_ancho.pack(side='left', padx=(0, 8))
        yield

        ctk.CTkLabel(
            fila_dim, text=t('x_symbol'), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY
        ).pack(side='left', padx=(0, 8))
        yield

        self._canvas_alto = styles.Entry(
            fila_dim, width=80, font=fonts.FUENTE_BASE,
            placeholder_text='1080',
        )
        yield
        self._canvas_alto.pack(side='left')
        yield

        ctk.CTkLabel(
            panel, text=t('background'), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=1, column=0, padx=(16, 12), pady=8, sticky='w')
        yield

        styles.SegmentedButton(
            panel,
            values=[t('white'), t('black'), t('transparent')],
            variable=self._state.color_fondo,
            font=fonts.FUENTE_CHICA,
            command=self._actualizar_fondo_opciones
        ).grid(row=1, column=1, padx=(0, 16), pady=8, sticky='w')
        yield

        self._lbl_aviso_fondo = ctk.CTkLabel(
            panel, text='',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        )
        yield
        self._lbl_aviso_fondo.grid(
            row=2, column=0, columnspan=2, padx=16, pady=(0, 4), sticky='w'
        )
        yield

        self._btn_canvas = self._new_button(
            panel, role='primary', text=t('apply_canvas'),
            font=fonts.FUENTE_BASE,
            command=self._ejecutar_canvas
        )
        yield
        self._btn_canvas.grid(
            row=2, column=0, columnspan=2, padx=16, pady=(0, 16), sticky='ew'
        )
        yield
        return f

    def _cargar_imagenes(self, rutas: list[str]):
        """Cargar imagenes seleccionadas y actualizar la interfaz.

        Args:
            rutas: Lista de rutas de archivos seleccionados
        """
        if self._operation_blocked(global_job=False):
            return
        logger.info("resize.ui: cargar_imagenes (total=%s)", len(rutas))
        limite = 100
        total = len(rutas)
        if total > limite:
            rutas = rutas[:limite]
            self._limite_msg = t('limit_reached').format(limit=limite, total=total)
        else:
            self._limite_msg = None

        super()._cargar_imagenes(rutas)
        self._state.imagenes = list(rutas)
        n = len(self._imagenes)
        suffix = t('images_loaded_resize') if n > 1 else t('image_loaded_resize')
        msg = f'{n} {suffix}'
        if self._limite_msg:
            msg += f'  -  {self._limite_msg}'
        self._lbl_info.configure(text=msg)
        logger.info("resize.ui: imagenes cargadas (mostradas=%s)", len(self._imagenes))

    def _cambiar_tab(self, tab: str):
        """Cambiar el tab visible en el contenedor.

        Args:
            tab: Nombre del tab a mostrar
        """
        logger.info("resize.ui: cambiar_tab (%s)", tab)
        activate_tab(self._frames, tab)

    def _ejecutar_resize(self):
        if self._operation_blocked(global_job=True):
            return
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_images_first_resize'))
            return
        mode = self._state.modo_resize.get()
        options = dict(porcentaje=self._state.pct_var.get(), mantener_ratio=False)
        if mode == t('pixels'):
            width, height, error = parse_dimensions(self._entry_ancho.get(), self._entry_alto.get())
            if error:
                self._lbl_info.configure(text=t('invalid_dimensions'))
                return
            options = dict(ancho=width, alto=height, mantener_ratio=self._state.mantener_ratio.get())
        elif mode == t('preset'):
            options = dict(preset_key=self._state.preset_var.get(), mantener_ratio=False)
        self._save_resize(batch_redimensionar, options, self._btn_resize, 'resize_tab')

    def _ejecutar_crop(self):
        if self._operation_blocked(global_job=True):
            return
        self._save_resize(batch_recortar, dict(ratio=self._state.ratio_var.get()), self._btn_crop, 'crop_tab')

    def _ejecutar_canvas(self):
        if self._operation_blocked(global_job=True):
            return
        width, height, error = parse_dimensions(self._canvas_ancho.get(), self._canvas_alto.get())
        if error or not width or not height:
            self._lbl_info.configure(text=t('invalid_dimensions'))
            return
        choice = self._state.canvas_choice_map.get(self._state.color_fondo.get(), 'white')
        self._save_resize(batch_canvas, dict(ancho=width, alto=height), self._btn_canvas,
                          'apply_canvas', canvas_choice=choice)

    def _save_resize(self, processor, options, button, label, *, canvas_choice=None):
        paths = tuple(self._imagenes)
        if not paths:
            self._lbl_info.configure(text=t('load_images_first_resize'))
            return
        def start(folder, plan):
            self._show_full_overlay(t('processing'))
            def work():
                parameters = dict(options)
                if canvas_choice is not None:
                    parameters['color_fondo'], _ = canvas_color_for_choice(
                        canvas_choice, any_supports_transparency(paths))
                return processor(paths, folder, **parameters, output_policy=plan)
            self._submit_job(work, button=button, text=t(label), on_success=self._finish_save)
        self._prepare_save(paths, None, start)

    def _finalizar(self, btn: ctk.CTkButton, texto: str, ok: int, errores: int, conflictos: int = 0):
        """Restaurar estado del boton y mostrar mensaje de resultado.

        Args:
            btn: Boton a restaurar
            texto: Texto original del boton
            ok: Numero de imagenes procesadas correctamente
            errores: Numero de errores ocurridos
        """
        btn.configure(state='normal', text=texto)
        logger.info("resize.ui: finalizar_ok (ok=%s, errores=%s, conflictos=%s)", ok, errores, conflictos)
        self._hide_full_overlay()
        noun = t('image_loaded' if ok == 1 else 'images_loaded')
        msg = f'{ok} {noun} {t("processed" if ok != 1 else "processed_singular")}'
        if errores:
            msg += f'  -  {errores} {t("error_occurred")}'
        if conflictos:
            msg += f'  -  {conflictos} {t("conflicts_renamed")}'
        self._lbl_info.configure(text=msg)

    def _limpiar(self):
        """Limpiar todas las imagenes y reiniciar el estado del frame."""
        if self._operation_blocked(global_job=False):
            return
        super()._limpiar()

    def _actualizar_fondo_opciones(self, valor: str):
        """Mostrar aviso si se elige transparencia con imagenes incompatibles.

        Args:
            valor: Color de fondo seleccionado por el usuario
        """
        choice_key = self._state.canvas_choice_map.get(valor, 'white')
        if choice_key == 'transparent' and self._imagenes:
            soporta_transparencia = any_supports_transparency(self._imagenes)
            _, fallback = canvas_color_for_choice(choice_key, soporta_transparencia)
            if fallback:
                self._lbl_aviso_fondo.configure(text=t('warning_transparency'))
                return
        self._lbl_aviso_fondo.configure(text='')
