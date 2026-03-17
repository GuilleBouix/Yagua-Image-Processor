"""
UI para el modulo Redimensionar / Recortar / Canvas.
"""

from __future__ import annotations

import threading
from tkinter import filedialog

import customtkinter as ctk

from app.ui import colors, fonts
from app.translations import t
from app.ui.frames.base import BaseFrame
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


class ResizeFrame(BaseFrame):
    def __init__(self, parent):
        self._state = ResizeState()
        super().__init__(parent, t('resize_title'))

    def _build_content(self):
        # Tabs
        self._tab = ctk.CTkSegmentedButton(
            self,
            values=[t('resize_tab'), t('crop_tab'), t('canvas_tab')],
            font=fonts.FUENTE_BASE,
            selected_color="#949494",
            selected_hover_color="#949494",
            unselected_color=colors.PANEL_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
            command=self._cambiar_tab
        )
        self._tab.set(t('resize_tab'))
        self._tab.grid(row=1, column=0, padx=28, pady=(0, 8), sticky='ew')

        # Boton seleccionar imagenes
        self._btn_seleccionar = self._crear_boton_seleccionar(self)
        self._btn_seleccionar.grid(row=2, column=0, padx=28, pady=(0, 8), sticky='ew')

        # Lista de archivos
        self._lista_frame = self._crear_lista_archivos(self, height=120)
        self._lista_frame.grid(row=3, column=0, padx=28, pady=(0, 8), sticky='ew')
        self._lista_frame.grid_columnconfigure(0, weight=1)

        self._lbl_lista_vacia = ctk.CTkLabel(
            self._lista_frame,
            text=t('no_images'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )
        self._lbl_lista_vacia.pack(pady=12)

        # Contenedor de tabs
        self._contenedor = ctk.CTkFrame(self, fg_color='transparent')
        self._contenedor.grid(row=4, column=0, padx=28, sticky='ew')
        self._contenedor.grid_columnconfigure(0, weight=1)

        self._frames: dict[str, ctk.CTkFrame] = {
            t('resize_tab'): self._build_tab_resize(),
            t('crop_tab'): self._build_tab_crop(),
            t('canvas_tab'): self._build_tab_canvas(),
        }
        for f in self._frames.values():
            f.grid(row=0, column=0, sticky='ew')

        self._cambiar_tab(t('resize_tab'))

    def _build_tab_resize(self) -> ctk.CTkFrame:
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent')
        f.grid_columnconfigure(0, weight=1)

        panel = ctk.CTkFrame(
            f, corner_radius=12, fg_color=colors.PANEL_BG,
            border_width=1, border_color=colors.SIDEBAR_SEPARATOR
        )
        panel.grid(row=0, column=0, sticky='ew')
        panel.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            panel, text=t('mode'), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(16, 8), sticky='w')

        ctk.CTkSegmentedButton(
            panel,
            values=[t('percentage'), t('pixels'), t('preset')],
            variable=self._state.modo_resize,
            font=fonts.FUENTE_CHICA,
            selected_color="#949494",
            selected_hover_color="#949494",
            unselected_color=colors.SIDEBAR_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
            command=self._actualizar_modo_resize
        ).grid(row=0, column=1, padx=(0, 16), pady=(16, 8), sticky='w')

        self._frame_controles_resize = ctk.CTkFrame(panel, fg_color='transparent')
        self._frame_controles_resize.grid(
            row=1, column=0, columnspan=2, padx=16, pady=(0, 8), sticky='ew'
        )
        self._frame_controles_resize.grid_columnconfigure(1, weight=1)

        self._frame_ratio = ctk.CTkFrame(panel, fg_color='transparent')
        self._frame_ratio.grid(
            row=2, column=0, columnspan=2, padx=16, pady=(0, 8), sticky='ew'
        )
        ctk.CTkCheckBox(
            self._frame_ratio,
            text=t('maintain_aspect'),
            variable=self._state.mantener_ratio,
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY,
            fg_color=colors.ACENTO,
            hover_color=colors.ACENTO_HOVER,
            border_color=colors.SIDEBAR_SEPARATOR,
            checkmark_color=colors.TEXT_ACTIVE,
        ).pack(anchor='w')

        self._btn_resize = ctk.CTkButton(
            panel, text=t('resize_tab'), height=40, corner_radius=8,
            font=fonts.FUENTE_BASE, fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE, hover_color=colors.ACENTO_HOVER,
            command=self._ejecutar_resize
        )
        self._btn_resize.grid(
            row=3, column=0, columnspan=2, padx=16, pady=(0, 16), sticky='ew'
        )

        self._actualizar_modo_resize(t('percentage'))
        return f

    def _actualizar_modo_resize(self, modo: str):
        for w in self._frame_controles_resize.winfo_children():
            w.destroy()

        fc = self._frame_controles_resize

        if modo == t('pixels'):
            self._frame_ratio.grid()
        else:
            self._frame_ratio.grid_remove()

        if modo == t('percentage'):
            fc.grid_columnconfigure(0, weight=0)
            fc.grid_columnconfigure(1, weight=1)
            fc.grid_columnconfigure(2, weight=0)

            self._lbl_pct = ctk.CTkLabel(
                fc, text='50%', font=fonts.FUENTE_BASE,
                text_color=colors.ACENTO, fg_color='transparent', width=36
            )

            ctk.CTkSlider(
                fc, from_=1, to=200, variable=self._state.pct_var,
                button_color=colors.ACENTO,
                button_hover_color=colors.ACENTO_HOVER,
                progress_color=colors.ACENTO,
                fg_color=colors.SIDEBAR_SEPARATOR,
                command=lambda v: self._lbl_pct.configure(text=f'{int(v)}%')
            ).grid(row=0, column=0, columnspan=2, sticky='ew', padx=(0, 8))

            self._lbl_pct.grid(row=0, column=2)

        elif modo == t('pixels'):
            fc.grid_columnconfigure(0, weight=0)
            fc.grid_columnconfigure(1, weight=0)
            fc.grid_columnconfigure(2, weight=0)
            fc.grid_columnconfigure(3, weight=0)

            ctk.CTkLabel(
                fc, text=t('width'), font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY
            ).grid(row=0, column=0, padx=(0, 4), sticky='w')

            self._entry_ancho = ctk.CTkEntry(
                fc, width=90, font=fonts.FUENTE_BASE,
                fg_color=colors.FRAMES_BG,
                border_color=colors.SIDEBAR_SEPARATOR,
                text_color=colors.TEXT_COLOR,
                placeholder_text='1920',
                placeholder_text_color=colors.TEXT_GRAY
            )
            self._entry_ancho.grid(row=0, column=1, padx=(0, 16))

            ctk.CTkLabel(
                fc, text=t('height'), font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY
            ).grid(row=0, column=2, padx=(0, 4), sticky='w')

            self._entry_alto = ctk.CTkEntry(
                fc, width=90, font=fonts.FUENTE_BASE,
                fg_color=colors.FRAMES_BG,
                border_color=colors.SIDEBAR_SEPARATOR,
                text_color=colors.TEXT_COLOR,
                placeholder_text='1080',
                placeholder_text_color=colors.TEXT_GRAY
            )
            self._entry_alto.grid(row=0, column=3)

        elif modo == t('preset'):
            fc.grid_columnconfigure(0, weight=1)

            ctk.CTkOptionMenu(
                fc,
                values=PRESETS_LISTA,
                variable=self._state.preset_var,
                font=fonts.FUENTE_BASE,
                fg_color=colors.SIDEBAR_BG,
                button_color=colors.ACENTO,
                button_hover_color=colors.ACENTO_HOVER,
                text_color=colors.TEXT_COLOR,
                dropdown_fg_color=colors.PANEL_BG,
                dropdown_text_color=colors.TEXT_COLOR,
                dropdown_hover_color=colors.SIDEBAR_HOVER,
            ).grid(row=0, column=0, sticky='ew')

    def _build_tab_crop(self) -> ctk.CTkFrame:
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent')
        f.grid_columnconfigure(0, weight=1)

        panel = ctk.CTkFrame(
            f, corner_radius=12, fg_color=colors.PANEL_BG,
            border_width=1, border_color=colors.SIDEBAR_SEPARATOR
        )
        panel.grid(row=0, column=0, sticky='ew')
        panel.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            panel, text='Ratio', font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(16, 8), sticky='w')

        ctk.CTkOptionMenu(
            panel,
            values=list(RATIOS.keys()),
            variable=self._state.ratio_var,
            font=fonts.FUENTE_BASE,
            fg_color=colors.SIDEBAR_BG,
            button_color=colors.ACENTO,
            button_hover_color=colors.ACENTO_HOVER,
            text_color=colors.TEXT_COLOR,
            dropdown_fg_color=colors.PANEL_BG,
            dropdown_text_color=colors.TEXT_COLOR,
            dropdown_hover_color=colors.SIDEBAR_HOVER,
        ).grid(row=0, column=1, padx=(0, 16), pady=(16, 8), sticky='w')

        ctk.CTkLabel(
            panel,
            text=t('crop_centered'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 8), sticky='w')

        self._btn_crop = ctk.CTkButton(
            panel, text=t('crop_tab'), height=40, corner_radius=8,
            font=fonts.FUENTE_BASE, fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE, hover_color=colors.ACENTO_HOVER,
            command=self._ejecutar_crop
        )
        self._btn_crop.grid(
            row=2, column=0, columnspan=2, padx=16, pady=(0, 16), sticky='ew'
        )
        return f

    def _build_tab_canvas(self) -> ctk.CTkFrame:
        f = ctk.CTkFrame(self._contenedor, fg_color='transparent')
        f.grid_columnconfigure(0, weight=1)

        panel = ctk.CTkFrame(
            f, corner_radius=12, fg_color=colors.PANEL_BG,
            border_width=1, border_color=colors.SIDEBAR_SEPARATOR
        )
        panel.grid(row=0, column=0, sticky='ew')
        panel.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            panel, text=t('size'), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, padx=(16, 12), pady=(16, 8), sticky='w')

        fila_dim = ctk.CTkFrame(panel, fg_color='transparent')
        fila_dim.grid(row=0, column=1, padx=(0, 16), pady=(16, 8), sticky='w')

        self._canvas_ancho = ctk.CTkEntry(
            fila_dim, width=80, font=fonts.FUENTE_BASE,
            fg_color=colors.FRAMES_BG,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            placeholder_text='1080',
            placeholder_text_color=colors.TEXT_GRAY
        )
        self._canvas_ancho.pack(side='left', padx=(0, 8))

        ctk.CTkLabel(
            fila_dim, text='x', font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY
        ).pack(side='left', padx=(0, 8))

        self._canvas_alto = ctk.CTkEntry(
            fila_dim, width=80, font=fonts.FUENTE_BASE,
            fg_color=colors.FRAMES_BG,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            placeholder_text='1080',
            placeholder_text_color=colors.TEXT_GRAY
        )
        self._canvas_alto.pack(side='left')

        ctk.CTkLabel(
            panel, text=t('background'), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=1, column=0, padx=(16, 12), pady=8, sticky='w')

        ctk.CTkSegmentedButton(
            panel,
            values=[t('white'), t('black'), t('transparent')],
            variable=self._state.color_fondo,
            font=fonts.FUENTE_CHICA,
            selected_color="#949494",
            selected_hover_color="#949494",
            unselected_color=colors.SIDEBAR_BG,
            unselected_hover_color=colors.SIDEBAR_HOVER,
            text_color=colors.TEXT_COLOR,
            command=self._actualizar_fondo_opciones
        ).grid(row=1, column=1, padx=(0, 16), pady=8, sticky='w')

        self._lbl_aviso_fondo = ctk.CTkLabel(
            panel, text='',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        )
        self._lbl_aviso_fondo.grid(
            row=2, column=0, columnspan=2, padx=16, pady=(0, 4), sticky='w'
        )

        self._btn_canvas = ctk.CTkButton(
            panel, text=t('apply_canvas'), height=40, corner_radius=8,
            font=fonts.FUENTE_BASE, fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE, hover_color=colors.ACENTO_HOVER,
            command=self._ejecutar_canvas
        )
        self._btn_canvas.grid(
            row=2, column=0, columnspan=2, padx=16, pady=(0, 16), sticky='ew'
        )
        return f

    def _cargar_imagenes(self, rutas: list[str]):
        super()._cargar_imagenes(rutas)
        self._state.imagenes = list(rutas)
        n = len(self._imagenes)
        suffix = t('images_loaded_resize') if n > 1 else t('image_loaded_resize')
        self._lbl_info.configure(text=f'{n} {suffix}')

    def _cambiar_tab(self, tab: str):
        for nombre, frame in self._frames.items():
            if nombre == tab:
                frame.grid()
                frame.tkraise()
            else:
                frame.grid_remove()

    def _ejecutar_resize(self):
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_images_first_resize'))
            return
        carpeta = filedialog.askdirectory(title=t('select_output_folder'))
        if not carpeta:
            return

        modo = self._state.modo_resize.get()
        ancho_px = None
        alto_px = None
        if modo == t('pixels'):
            ancho_px, alto_px, err = parse_dimensions(
                self._entry_ancho.get(),
                self._entry_alto.get()
            )
            if err:
                self._lbl_info.configure(text=t('invalid_dimensions'))
                return
        self._btn_resize.configure(state='disabled', text=t('processing'))

        def _proc():
            if modo == t('percentage'):
                res = batch_redimensionar(
                    self._imagenes, carpeta,
                    porcentaje=self._state.pct_var.get(),
                    mantener_ratio=False
                )
            elif modo == t('pixels'):
                res = batch_redimensionar(
                    self._imagenes, carpeta,
                    ancho=ancho_px, alto=alto_px,
                    mantener_ratio=self._state.mantener_ratio.get()
                )
            else:
                res = batch_redimensionar(
                    self._imagenes, carpeta,
                    preset_key=self._state.preset_var.get(),
                    mantener_ratio=False
                )
            ok = res['ok']
            errores = res['errores']
            self.after(0, lambda: self._finalizar(
                self._btn_resize, t('resize_tab'), ok, errores
            ))

        threading.Thread(target=_proc, daemon=True).start()

    def _ejecutar_crop(self):
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_images_first_resize'))
            return
        carpeta = filedialog.askdirectory(title=t('select_output_folder'))
        if not carpeta:
            return

        self._btn_crop.configure(state='disabled', text=t('processing'))
        ratio = self._state.ratio_var.get()

        def _proc():
            res = batch_recortar(
                self._imagenes, carpeta,
                ratio=ratio
            )
            ok = res['ok']
            errores = res['errores']
            self.after(0, lambda: self._finalizar(
                self._btn_crop, t('crop_tab'), ok, errores
            ))

        threading.Thread(target=_proc, daemon=True).start()

    def _ejecutar_canvas(self):
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_images_first_resize'))
            return
        ancho, alto, err = parse_dimensions(self._canvas_ancho.get(), self._canvas_alto.get())
        if err or not ancho or not alto:
            self._lbl_info.configure(text=t('invalid_dimensions'))
            return
        carpeta = filedialog.askdirectory(title=t('select_output_folder'))
        if not carpeta:
            return

        fondo_elegido = self._state.color_fondo.get()
        self._btn_canvas.configure(state='disabled', text=t('processing'))

        def _proc():
            choice_key = self._state.canvas_choice_map.get(fondo_elegido, 'white')
            soporta_transparencia = any_supports_transparency(self._imagenes)
            color, _ = canvas_color_for_choice(choice_key, soporta_transparencia)

            res = batch_canvas(
                self._imagenes, carpeta,
                ancho=ancho, alto=alto,
                color_fondo=color
            )
            ok = res['ok']
            errores = res['errores']
            self.after(0, lambda: self._finalizar(
                self._btn_canvas, t('apply_canvas'), ok, errores
            ))

        threading.Thread(target=_proc, daemon=True).start()

    def _finalizar(self, btn: ctk.CTkButton, texto: str, ok: int, errores: int):
        btn.configure(state='normal', text=texto)
        msg = f'{ok} imagen{"es" if ok != 1 else ""} {t("processed" if ok != 1 else "processed_singular")}'
        if errores:
            msg += f'  -  {errores} {t("error_occurred")}'
        self._lbl_info.configure(text=msg)

    def _limpiar(self):
        self._imagenes = []
        self._thumbs.clear()
        self._filas_lista.clear()
        for w in self._lista_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._lista_frame,
            text=t('no_images'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).pack(pady=12)
        self._lbl_info.configure(text='')

    def _actualizar_fondo_opciones(self, valor: str):
        """Muestra aviso si se elige Transparente con imagenes que no lo soportan."""
        choice_key = self._state.canvas_choice_map.get(valor, 'white')
        if choice_key == 'transparent' and self._imagenes:
            soporta_transparencia = any_supports_transparency(self._imagenes)
            _, fallback = canvas_color_for_choice(choice_key, soporta_transparencia)
            if fallback:
                self._lbl_aviso_fondo.configure(text=t('warning_transparency'))
                return
        self._lbl_aviso_fondo.configure(text='')
