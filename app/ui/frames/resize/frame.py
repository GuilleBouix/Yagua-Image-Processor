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
from tkinter import colorchooser

import customtkinter as ctk

from app.ui import colors, fonts, styles
from app.translations import t
from app.ui.frames.base import BaseFrame
from app.ui.preview import LivePreview
from app.ui.status import operation_summary
from app.ui.image_cache import ImageRequests
from app.utils.saving import path_key
from app.ui.rendering import activate_tab, configure_changed
from app.ui.frames.resize.services import (
    batch_redimensionar,
    batch_recortar,
    batch_canvas,
    canvas_output_format,
    PRESETS_LISTA,
    RATIOS,
    parse_dimensions,
)
from app.ui.frames.resize.state import ResizeState


logger = logging.getLogger(__name__)


class ResizeFrame(BaseFrame):
    """Frame principal del modulo de redimension, recorte y canvas."""

    design_system = True

    def __init__(self, parent, *, defer_build=False):
        """Prepara el estado y la construcción diferida del módulo."""
        logger.info("resize.ui: init")
        self._state = ResizeState()
        self._preview_active_path = ''
        self._crop_source_dimensions: dict[str, int] | None = None
        self._crop_loading_path = ''
        super().__init__(parent, t('resize_title'), defer_build=defer_build)

    def _prepare_additional_steps(self):
        """Agrega pasos de interfaz que deben construirse de forma progresiva."""
        if self._defer_build:
            for mode in (t('pixels'), t('preset'), t('percentage')):
                yield from steps_for(self._actualizar_modo_resize, mode)

    def _on_build_complete(self):
        """Conecta validación y acciones tras construir los controles."""
        self._crop_loader = ImageRequests(self)
        for variable in (self._state.modo_resize, self._state.pct_var, self._state.mantener_ratio,
                         self._state.preset_var, self._state.ratio_var, self._state.color_fondo,
                         self._state.width_var, self._state.height_var,
                         self._state.crop_mode, self._state.crop_width_var, self._state.crop_height_var,
                         self._state.canvas_color,
                         self._state.canvas_width_var, self._state.canvas_height_var):
            variable.trace_add('write', self._update_preview)
        self._state.crop_mode.trace_add('write', self._actualizar_modo_crop)
        self._state.color_fondo.trace_add('write', self._actualizar_fondo_opciones)
        self._state.canvas_color.trace_add('write', self._actualizar_fondo_opciones)
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
        izquierda.grid_rowconfigure(4, weight=1)
        yield
        derecha.grid_rowconfigure(0, weight=1)
        self._preview = LivePreview(derecha, settle=self._settle_preview_layout)
        self._preview.grid(row=0, column=0, padx=16, pady=16, sticky='nsew')
        yield
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

        self._lista_frame = self._crear_lista_archivos(izquierda, height=180)
        yield
        self._lista_frame.grid(row=4, column=0, padx=16, pady=(0, 16), sticky='nsew')
        yield
        self._lbl_lista_vacia = self._crear_lista_vacia(self._lista_frame)
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
                placeholder_text='1920', textvariable=self._state.width_var,
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
                placeholder_text='1080', textvariable=self._state.height_var,
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
        """Construye una vez los controles de proporción y tamaño exacto."""
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
            panel, values=[t('crop_mode_ratio'), t('crop_mode_dimensions')],
            variable=self._state.crop_mode, font=fonts.FUENTE_CHICA,
        ).grid(row=0, column=1, padx=(0, 16), pady=(16, 8), sticky='w')
        yield

        self._crop_ratio_controls = ctk.CTkFrame(panel, fg_color='transparent', corner_radius=0)
        self._crop_ratio_controls.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 8), sticky='nsew')
        yield
        ctk.CTkLabel(self._crop_ratio_controls, text=t('ratio'), font=fonts.FUENTE_BASE,
                     text_color=colors.TEXT_GRAY).grid(row=0, column=0, padx=(0, 12), sticky='w')
        yield
        self._crop_ratio_field = styles.OptionField(
            self._crop_ratio_controls,
            width=140,
            values=list(RATIOS.keys()),
            variable=self._state.ratio_var,
            font=fonts.FUENTE_BASE,
        )
        self._crop_ratio_field.grid(row=0, column=1, sticky='w')
        yield

        self._crop_dimension_controls = ctk.CTkFrame(panel, fg_color='transparent', corner_radius=0)
        self._crop_dimension_controls.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 8), sticky='nsew')
        self._crop_dimension_controls.grid_columnconfigure(1, weight=1)
        self._crop_sliders = {}
        self._crop_entries = []
        yield
        for row, (label, variable) in enumerate((('width', self._state.crop_width_var),
                                                ('height', self._state.crop_height_var))):
            ctk.CTkLabel(self._crop_dimension_controls, text=t(label) + ' (px)',
                         font=fonts.FUENTE_BASE, text_color=colors.TEXT_GRAY).grid(
                row=row, column=0, padx=(0, 12), pady=4, sticky='w')
            yield
            slider = ctk.CTkSlider(
                self._crop_dimension_controls, from_=0, to=1, number_of_steps=1, state='disabled',
                button_color=colors.ACENTO, button_hover_color=colors.ACENTO_HOVER,
                progress_color=colors.ACENTO, fg_color=styles.palette().border,
                command=lambda value, variable=variable: variable.set(str(round(value))),
            )
            yield
            slider.set(1)
            slider.grid(row=row, column=1, padx=(0, 12), pady=4, sticky='ew')
            self._crop_sliders[label] = slider
            variable.trace_add('write', lambda *_, key=label, variable=variable, slider=slider:
                               self._sync_crop_slider(key, variable, slider))
            yield
            entry = styles.Entry(self._crop_dimension_controls, width=80, font=fonts.FUENTE_BASE,
                                 textvariable=variable)
            entry.grid(row=row, column=2, pady=4, sticky='e')
            self._crop_entries.append(entry)
            yield

        self._crop_hints = {}
        for exact, key in ((False, 'crop_centered'), (True, 'crop_exact_hint')):
            hint = ctk.CTkLabel(
                panel, text=t(key), font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY, anchor='w', justify='left', wraplength=260,
            )
            yield
            hint.grid(row=2, column=0, columnspan=2, padx=16, pady=(0, 8), sticky='nsew')
            self._crop_hints[exact] = hint
            yield
        self._actualizar_modo_crop()
        yield

        self._btn_crop = self._new_button(
            panel, role='primary', text=t('crop_tab'),
            font=fonts.FUENTE_BASE,
            command=self._ejecutar_crop
        )
        yield
        self._btn_crop.grid(
            row=3, column=0, columnspan=2, padx=16, pady=(0, 16), sticky='ew'
        )
        yield
        return f

    def _actualizar_modo_crop(self, *_):
        """Eleva paneles ya montados; ambos reservan una geometría común estable."""
        exact = self._state.crop_mode.get() == t('crop_mode_dimensions')
        if getattr(self, '_crop_visible_mode', None) == exact:
            return
        controls = self._crop_dimension_controls if exact else self._crop_ratio_controls
        controls.tkraise()
        self._crop_hints[exact].tkraise()
        self._crop_ratio_field.menu._canvas.configure(takefocus=not exact)
        for entry in self._crop_entries:
            entry._entry.configure(takefocus=exact)
        self._crop_visible_mode = exact

    def _crop_options(self):
        """Captura opciones válidas para preview y guardado sin mezclar modos."""
        if self._state.crop_mode.get() != t('crop_mode_dimensions'):
            return dict(ratio=self._state.ratio_var.get())
        width, height, error = parse_dimensions(self._state.crop_width_var.get(), self._state.crop_height_var.get())
        if error or width is None or height is None or min(width, height) < 1:
            raise ValueError('invalid_dimensions')
        return dict(ancho=width, alto=height)

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

        panel.grid_columnconfigure(2, weight=0)
        yield
        self._canvas_sliders = {}
        yield
        for row, (key, variable) in enumerate((('width', self._state.canvas_width_var),
                                               ('height', self._state.canvas_height_var))):
            ctk.CTkLabel(panel, text=t(key), font=fonts.FUENTE_BASE,
                         text_color=colors.TEXT_GRAY, anchor='w').grid(
                row=row, column=0, padx=(16, 12), pady=(16 if row == 0 else 8, 8), sticky='w')
            yield
            slider = ctk.CTkSlider(panel, from_=1, to=8192, number_of_steps=8191,
                button_color=colors.ACENTO, button_hover_color=colors.ACENTO_HOVER,
                progress_color=colors.ACENTO, fg_color=styles.palette().border,
                command=lambda value, variable=variable: variable.set(str(round(value))))
            yield
            slider.set(int(variable.get()))
            slider.grid(row=row, column=1, padx=(0, 12), pady=(16 if row == 0 else 8, 8), sticky='ew')
            yield
            entry = styles.Entry(panel, width=80, font=fonts.FUENTE_BASE, textvariable=variable)
            yield
            entry.grid(row=row, column=2, padx=(0, 16), pady=(16 if row == 0 else 8, 8), sticky='e')
            yield
            if key == 'width':
                self._canvas_ancho = entry
            else:
                self._canvas_alto = entry
            self._canvas_sliders[key] = slider
            variable.trace_add('write', lambda *_, variable=variable, slider=slider:
                               self._sync_canvas_slider(variable, slider))
            yield

        ctk.CTkLabel(
            panel, text=t('background'), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=2, column=0, padx=(16, 12), pady=8, sticky='w')
        yield

        styles.SegmentedButton(
            panel,
            values=[t('canvas_color'), t('transparent')],
            variable=self._state.color_fondo,
            font=fonts.FUENTE_CHICA,
        ).grid(row=2, column=1, padx=(0, 16), pady=8, sticky='w')
        yield

        color_row = ctk.CTkFrame(panel, fg_color='transparent', corner_radius=0)
        color_row.grid(row=3, column=0, columnspan=3, padx=16, pady=(0, 12), sticky='ew')
        yield
        self._canvas_color_swatch = ctk.CTkFrame(color_row, width=24, height=24,
            corner_radius=0, border_width=1, border_color=styles.palette().border, fg_color='#FFFFFF')
        self._canvas_color_swatch.grid(row=0, column=0, padx=(0, 12))
        yield
        self._canvas_color_button = self._new_button(
            color_row, role='secondary', text='#FFFFFF', height=30, width=120,
            font=fonts.FUENTE_CHICA, command=self._choose_canvas_color,
        )
        self._canvas_color_button.grid(row=0, column=1, sticky='w')
        yield

        self._btn_canvas = self._new_button(
            panel, role='primary', text=t('apply_canvas'),
            font=fonts.FUENTE_BASE,
            command=self._ejecutar_canvas
        )
        yield
        self._btn_canvas.grid(
            row=4, column=0, columnspan=3, padx=16, pady=(0, 16), sticky='ew'
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
        self._update_preview(force=True)
        logger.info("resize.ui: imagenes cargadas (mostradas=%s)", len(self._imagenes))

    def _cambiar_tab(self, tab: str):
        """Cambiar el tab visible en el contenedor.

        Args:
            tab: Nombre del tab a mostrar
        """
        logger.info("resize.ui: cambiar_tab (%s)", tab)
        activate_tab(self._frames, tab)
        self._update_preview()

    def _ejecutar_resize(self):
        """Construye el trabajo de redimensionado con las opciones capturadas."""
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
        """Aplica el recorte configurado sin leer controles desde el worker."""
        if self._operation_blocked(global_job=True):
            return
        try:
            options = self._crop_options()
        except ValueError:
            self._lbl_info.configure(text=t('invalid_dimensions'))
            return
        self._save_resize(batch_recortar, options, self._btn_crop, 'crop_tab')

    def _ejecutar_canvas(self):
        """Prepara la expansión del lienzo con anclaje y color seleccionados."""
        if self._operation_blocked(global_job=True):
            return
        width, height, error = parse_dimensions(self._canvas_ancho.get(), self._canvas_alto.get())
        if error or width is None or height is None or min(width, height) < 1:
            self._lbl_info.configure(text=t('invalid_dimensions'))
            return
        background = self._canvas_background()
        self._save_resize(batch_canvas, dict(ancho=width, alto=height, color_fondo=background), self._btn_canvas,
                          'apply_canvas', format_resolver=canvas_output_format if background is None else None)

    def _save_resize(self, processor, options, button, label, *, format_resolver=None):
        """Publica los resultados mediante el plan de salida seguro."""
        paths = tuple(self._imagenes)
        if not paths:
            self._lbl_info.configure(text=t('load_images_first_resize'))
            return
        def start(folder, plan):
            """Valida opciones y captura los archivos antes de iniciar el trabajo."""
            self._show_full_overlay(t('processing'))
            def work():
                """Aplica al lote las opciones inmutables capturadas por la interfaz."""
                parameters = dict(options)
                return processor(paths, folder, **parameters, output_policy=plan)
            self._submit_job(work, button=button, text=t(label), on_success=self._finish_save)
        if format_resolver is not None:
            self._prepare_save(paths, None, start, format_resolver=format_resolver,
                               format_notice=t('canvas_png_notice'))
        else:
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
        msg = operation_summary(ok, errores, action='processed')
        self._lbl_info.configure(text=msg)

    def _limpiar(self):
        """Limpiar todas las imagenes y reiniciar el estado del frame."""
        if self._operation_blocked(global_job=False):
            return
        super()._limpiar()
        self._crop_loader.cancel()
        self._crop_source_dimensions = None
        self._crop_loading_path = ''
        self._state.crop_width_var.set('')
        self._state.crop_height_var.set('')
        for slider in self._crop_sliders.values():
            slider.configure(from_=0, to=1, number_of_steps=1, state='disabled')
            slider.set(1)
        self._state.imagenes = []
        self._preview_active_path = ''
        self._preview.show(force=True)

    def _actualizar_fondo_opciones(self, *_):
        """Conserva el color elegido y el espacio del control al alternar transparencia."""
        transparent = self._state.color_fondo.get() == t('transparent')
        configure_changed(self._canvas_color_button, text=self._state.canvas_color.get(),
                          state='disabled' if transparent else 'normal')
        configure_changed(self._canvas_color_swatch, fg_color=self._state.canvas_color.get())

    def _canvas_background(self):
        """Captura el fondo como píxeles RGB o transparencia, sin consultar el lote."""
        if self._state.color_fondo.get() == t('transparent'):
            return None
        value = self._state.canvas_color.get().lstrip('#')
        return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))

    def _choose_canvas_color(self):
        """Abre el selector nativo; cancelar conserva el último color confirmado."""
        if self._operation_blocked():
            return
        _, value = colorchooser.askcolor(color=self._state.canvas_color.get(),
            title=t('canvas_choose_color'), parent=self.winfo_toplevel())
        if value:
            self._state.canvas_color.set(value.upper())

    def _select_preview_file(self, path):
        """Cambia la imagen inspeccionada sin modificar las entradas del lote."""
        if self._operation_blocked():
            return False
        self._preview_active_path = path
        self._crop_loader.cancel()
        self._crop_source_dimensions = None
        self._crop_loading_path = path
        for slider in self._crop_sliders.values():
            slider.configure(state='disabled')
        if path:
            self._crop_loader.request(path, (44, 44),
                lambda result, error: self._crop_source_loaded(path, result, error), priority=0)
        self._update_preview()

    def _crop_source_loaded(self, path, result, error):
        """Inicializa sólo la imagen vigente, sin leer archivos desde Tk."""
        if path != self._preview_active_path:
            return
        if result is None or error:
            self._state.crop_width_var.set('')
            self._state.crop_height_var.set('')
        else:
            dimensions = result.oriented_dimensions or result.dimensions
            self._crop_source_dimensions = dict(zip(('width', 'height'), dimensions))
            for key, variable in (('width', self._state.crop_width_var),
                                  ('height', self._state.crop_height_var)):
                maximum = self._crop_source_dimensions[key]
                slider = self._crop_sliders[key]
                slider.configure(from_=1 if maximum > 1 else 0, to=maximum,
                    number_of_steps=max(1, maximum - 1), state='normal' if maximum > 1 else 'disabled')
                variable.set(str(maximum))
        self._crop_loading_path = ''
        self._update_preview()

    def _sync_crop_slider(self, key, variable, slider):
        """Mantiene el límite del original aunque se edite el valor manual."""
        if self._crop_source_dimensions is None:
            return
        try:
            value = int(variable.get())
        except ValueError:
            return
        if value > 0:
            slider.set(min(value, self._crop_source_dimensions[key]))

    def _update_preview(self, *_, force=False):
        """Valida controles y captura la geometría de la pestaña visible."""
        if not hasattr(self, '_preview'):
            return
        path = self._preview_active_path
        if not path:
            self._preview.show()
            return
        from app.modules.resize import RATIOS, preset_a_dimensiones
        try:
            tab = self._tab.get()
            if tab == t('crop_tab'):
                if self._crop_loading_path:
                    self._preview.show(path, error=t('processing'))
                    return
                options = self._crop_options()
                ratio = options.get('ratio')
                spec = (dict(kind='crop', ratio=RATIOS[ratio]) if isinstance(ratio, str) else
                        dict(kind='crop', dimensions=(options['ancho'], options['alto'])))
            elif tab == t('canvas_tab'):
                width = int(self._state.canvas_width_var.get())
                height = int(self._state.canvas_height_var.get())
                if min(width, height) < 1:
                    raise ValueError('invalid_dimensions')
                background = self._canvas_background()
                spec = dict(kind='canvas', size=(width, height), background=background)
            else:
                mode = self._state.modo_resize.get()
                if mode == t('percentage'):
                    options = dict(porcentaje=self._state.pct_var.get())
                elif mode == t('preset'):
                    options = dict(preset=preset_a_dimensiones(self._state.preset_var.get()))
                else:
                    width = int(self._state.width_var.get()) if self._state.width_var.get() else None
                    height = int(self._state.height_var.get()) if self._state.height_var.get() else None
                    if (width is None and height is None) or any(v is not None and v < 1 for v in (width, height)):
                        raise ValueError('invalid_dimensions')
                    options = dict(ancho=width, alto=height, mantener_ratio=self._state.mantener_ratio.get())
                spec = dict(kind='resize', options=options)
        except (ValueError, KeyError):
            self._preview.show(path, error=t('invalid_dimensions'), force=True)
            return
        self._preview.show(path, spec, debounce=150, force=force)

    def _finish_save(self, result, *, strip=False):
        """Actualiza salidas e invalida el render tras posibles sobrescrituras."""
        super()._finish_save(result, strip=strip)
        if self._preview_active_path and any(
                row.get('reemplazado') and row.get('estado') == 'saved'
                and path_key(row['ruta_entrada']) == path_key(self._preview_active_path)
                for row in result.get('resultados', [])):
            self._select_preview_file(self._preview_active_path)
        self._update_preview(force=True)

    def on_view_shown(self):
        """Retoma la preview sólo cuando el módulo está visible."""
        super().on_view_shown()
        if hasattr(self, '_preview'):
            self._preview.set_visible(True)

    def on_view_hidden(self):
        """Suspende renders ocultos sin reconstruir controles ni pestañas."""
        if hasattr(self, '_preview'):
            self._preview.set_visible(False)

    def _sync_canvas_slider(self, variable, slider):
        """Sincroniza valores manuales válidos; conserva entradas incompletas."""
        try:
            value = int(variable.get())
        except ValueError:
            return
        if value < 1:
            return
        upper = max(8192, value)
        if slider.cget('to') != upper:
            slider.configure(to=upper, number_of_steps=upper - 1)
        slider.set(value)
