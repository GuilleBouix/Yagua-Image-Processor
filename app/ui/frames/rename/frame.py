"""
UI para el modulo de renombrado de archivos en lote.

Relacionado con:
    - app/ui/frames/base.py: Clase base de la que hereda.
    - app/ui/frames/rename/state.py: Estado de la interfaz.
    - app/ui/frames/rename/services.py: Servicios de logica.
    - app/translations/__init__.py: Traducciones de la UI.
"""

from __future__ import annotations

from app.ui.building import stepwise, steps_for
import logging
import threading
from app.ui.rendering import VirtualRows, PooledRow, configure_changed

import customtkinter as ctk

from app.ui import colors, fonts, styles
from app.translations import t
from app.ui.status import operation_summary
from app.ui.frames.base import BaseFrame
from app.ui.frames.rename.services import generar_nombres_preview, renombrar_archivos
from app.ui.frames.rename.state import RenameState

FORMATOS_FECHA = {
    'AAAAMMDD':  '%Y%m%d',
    'DDMMAAAA':  '%d%m%Y',
    'AAAA-MM-DD': '%Y-%m-%d',
    'DD-MM-AAAA': '%d-%m-%Y',
}

class RenameFrame(BaseFrame):
    """Frame del modulo de renombrado en lote."""

    design_system = True
    logger = logging.getLogger(__name__)
    def __init__(self, parent, *, defer_build=False):
        """Inicializa el frame."""
        self.logger.info("rename.ui: init")
        self._state = RenameState()
        self._formato_fecha_label = ctk.StringVar(value='AAAAMMDD')
        self._posicion_fecha_label = ctk.StringVar(value=t('rename_prefix_pos'))
        self._caso_label = ctk.StringVar(value=t('rename_case_lower'))
        super().__init__(parent, t('rename_title'), defer_build=defer_build)

    @stepwise
    def _build_content(self):
        """Construye el contenido del modulo."""
        self.logger.info("rename.ui: build_content")
        yield
        izquierda, derecha = self._crear_workspace()
        yield
        izquierda.grid_rowconfigure(4, weight=1)
        yield
        derecha.grid_rowconfigure(2, weight=1)
        yield
        # Boton seleccionar
        self._btn_seleccionar = self._crear_boton_seleccionar(izquierda)
        yield
        self._btn_seleccionar.grid(row=0, column=0, padx=16, pady=(16, 8), sticky='ew')
        yield

        # Panel de opciones
        panel = ctk.CTkFrame(
            izquierda,
            **styles.surface('panel'),
        )
        yield
        panel.grid(row=1, column=0, padx=16, pady=(0, 16), sticky='new')
        yield
        panel.grid_columnconfigure(1, weight=1)
        yield
        (yield from steps_for(self._construir_opciones, panel))
        yield

        self._btn_renombrar = self._new_button(
            izquierda,
            role='primary',
            text=t('rename_btn'),
            height=40,
            font=fonts.FUENTE_BASE,
            command=self._renombrar,
        )
        yield
        self._btn_renombrar.grid(row=2, column=0, padx=16, pady=(0, 16), sticky='ew')
        yield

        ctk.CTkLabel(
            izquierda, text=t('files_loaded').capitalize(), font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).grid(row=3, column=0, padx=16, pady=(0, 8), sticky='w')
        yield
        self._lista_frame = self._crear_lista_archivos(izquierda, height=180)
        yield
        self._lista_frame.grid(row=4, column=0, padx=16, pady=(0, 16), sticky='nsew')
        yield
        self._lista_frame.grid_columnconfigure(0, weight=1)
        yield
        self._lbl_lista_vacia = self._crear_lista_vacia(self._lista_frame)
        yield
        self._lbl_lista_vacia.pack(pady=8)
        yield

        # Preview directamente en el panel derecho del workspace.
        (yield from steps_for(self._construir_preview, derecha))
        yield

        # Vincular todas las variables al preview
        self._vincular_variables()
        yield
        self._sync_display_vars()
        yield

    @stepwise
    def _construir_opciones(self, p):
        """
        Construye las tres secciones de opciones.

        Args:
            p: Frame padre del panel.
        """
        # Seccion: Prefijo + numeracion
        styles.CheckBox(
            p,
            text=t('rename_numbering'),
            variable=self._state.numeracion_activa,
            font=fonts.FUENTE_BASE,
        ).grid(row=0, column=0, padx=(16, 8), pady=(16, 8), sticky='w')
        yield

        fila_num = ctk.CTkFrame(p, fg_color='transparent')
        yield
        fila_num.grid(row=0, column=1, padx=(0, 16), pady=(16, 8), sticky='w')
        yield

        ctk.CTkLabel(
            fila_num, text=t('rename_prefix'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).pack(side='left', padx=(0, 6))
        yield

        styles.Entry(
            fila_num,
            textvariable=self._state.prefijo,
            font=fonts.FUENTE_BASE,
            placeholder_text=t('rename_placeholder'),
            width=140
        ).pack(side='left', padx=(0, 16))
        yield

        ctk.CTkLabel(
            fila_num, text=t('rename_start'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).pack(side='left', padx=(0, 6))
        yield

        styles.Entry(
            fila_num,
            textvariable=self._state.inicio,
            font=fonts.FUENTE_BASE,
            width=52
        ).pack(side='left')
        yield

        # Seccion: Agregar fecha
        styles.CheckBox(
            p,
            text=t('rename_date'),
            variable=self._state.fecha_activa,
            font=fonts.FUENTE_BASE,
        ).grid(row=1, column=0, padx=(16, 8), pady=8, sticky='w')
        yield

        fila_fecha = ctk.CTkFrame(p, fg_color='transparent')
        yield
        fila_fecha.grid(row=1, column=1, padx=(0, 16), pady=8, sticky='w')
        yield

        styles.SegmentedButton(
            fila_fecha,
            values=[t('rename_prefix_pos'), t('rename_suffix_pos')],
            variable=self._posicion_fecha_label,
            font=fonts.FUENTE_CHICA,
            command=self._on_posicion_fecha_change
        ).pack(side='left', padx=(0, 16))
        yield

        styles.OptionField(
            fila_fecha,
            width=140,
            values=list(FORMATOS_FECHA.keys()),
            variable=self._formato_fecha_label,
            font=fonts.FUENTE_BASE,
            command=self._on_formato_fecha_change
        ).pack(side='left')
        yield

        # Seccion: Capitalizacion
        ctk.CTkLabel(
            p, text=t('rename_case'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).grid(row=2, column=0, padx=(16, 8), pady=(8, 16), sticky='w')
        yield

        styles.SegmentedButton(
            p,
            values=[t('rename_case_lower'), t('rename_case_upper')],
            variable=self._caso_label,
            font=fonts.FUENTE_CHICA,
            command=self._aplicar_capitalizacion
        ).grid(row=2, column=1, padx=(0, 16), pady=(8, 16), sticky='w')
        yield

    @stepwise
    def _construir_preview(self, p):
        """
        Construye la tabla de preview con cabeceras.

        Args:
            p: Frame padre del panel.
        """
        # Header
        header = ctk.CTkFrame(p, fg_color='transparent')
        yield
        header.grid(row=0, column=0, padx=16, pady=(10, 4), sticky='ew')
        yield
        header.grid_columnconfigure(0, weight=1)
        yield

        ctk.CTkLabel(
            header, text=t('rename_preview'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).grid(row=0, column=0, sticky='w')
        yield

        # Cabeceras
        cab = ctk.CTkFrame(p, **styles.surface('list'))
        yield
        cab.grid(row=1, column=0, padx=16, pady=(0, 4), sticky='ew')
        yield
        cab.grid_columnconfigure((0, 1), weight=1)
        yield

        ctk.CTkLabel(
            cab, text=t('rename_col_original'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=0, padx=10, pady=5, sticky='w')
        yield

        ctk.CTkLabel(
            cab, text=t('rename_col_nuevo'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=0, column=1, padx=10, pady=5, sticky='w')
        yield

        # Lista scrolleable
        self._lista_preview = ctk.CTkScrollableFrame(
            p,
            height=120,
            **styles.surface('list'),
            **styles.scrollbar(),
        )
        yield
        self._lista_preview.grid(row=2, column=0, padx=16, pady=(0, 10), sticky='nsew')
        yield
        self._lista_preview.grid_columnconfigure((0, 1), weight=1)
        yield

        # Placeholder inicial
        self._renderizar_preview([])
        yield

    def _on_build_complete(self):
        """Conecta los controles al terminar la construcción de la vista."""
        super()._on_build_complete()
        for frame in (self, self._lista_frame, self._lista_preview):
            if isinstance(frame, ctk.CTkScrollableFrame):
                frame._scrollbar.configure(corner_radius=0, width=6, border_spacing=1)

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
            self._posicion_fecha_label,
            self._formato_fecha_label,
            self._caso_label,
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
        if self._operation_blocked(global_job=False):
            return
        self.logger.info("rename.ui: cargar_imagenes (total=%s)", len(rutas))
        limite = 100
        total = len(rutas)
        if total > limite:
            rutas = rutas[:limite]
            self._limite_msg = t('limit_reached').format(limit=limite, total=total)
        else:
            self._limite_msg = None

        super()._cargar_imagenes(rutas)
        self._state.imagenes = list(self._imagenes)
        n = len(rutas)
        suffix = t('files_loaded') if n > 1 else t('file_loaded')
        msg = f'{n} {suffix}'
        if self._limite_msg:
            msg += f'  -  {self._limite_msg}'
        self._lbl_info.configure(text=msg)
        self._actualizar_preview()
        self.logger.info("rename.ui: imagenes cargadas (mostradas=%s)", len(rutas))

    def _actualizar_preview(self, *args):
        """Lanza la generacion del preview en segundo plano."""
        if not self._imagenes:
            return
        paths, options = tuple(self._imagenes), self._state.obtener_opciones()
        signature = (paths, repr(sorted(options.items())))
        if getattr(self, '_preview_signature', None) == signature:
            return
        self._preview_signature = signature
        self._rename_revision = getattr(self, '_rename_revision', 0) + 1
        revision = self._rename_revision
        previous = getattr(self, '_preview_job', None)
        if previous is not None:
            self.after_cancel(previous)
        self._preview_job = self.after(60, lambda: self._start_preview(paths, options, revision))

    def _start_preview(self, paths, options, revision):
        """Inicia la previsualización con los valores actuales del formulario."""
        self._preview_job = None
        threading.Thread(target=self._generar_preview, args=(paths, options, revision), daemon=True).start()

    def _limpiar(self):
        """Restablece selección y reglas de renombrado."""
        if self._operation_blocked():
            return
        self._rename_revision = getattr(self, '_rename_revision', 0) + 1
        previous = getattr(self, '_preview_job', None)
        if previous is not None:
            self.after_cancel(previous)
        self._preview_job = None
        self._preview_signature = None
        self._state.imagenes = []
        super()._limpiar()
        self._renderizar_preview([])

    def _generar_preview(self, paths, opciones, revision):
        """Genera el preview en segundo plano."""
        try:
            preview = generar_nombres_preview(paths, opciones)
            self._post_ui(0, lambda: self._renderizar_preview(preview) if revision == self._rename_revision and tuple(self._imagenes) == paths else None)
        except Exception as exc:
            self.logger.warning("Error al generar preview: %s", exc)

    def _renderizar_preview(self, preview):
        """
        Renderiza la tabla de preview.

        Args:
            preview: Lista de tuplas (nombre_original, nombre_nuevo).
        """
        if not hasattr(self, '_preview_rows'):
            for widget in self._lista_preview.winfo_children():
                if isinstance(widget, ctk.CTkLabel):
                    widget.grid_remove()
            def create(parent):
                """Construye una fila editable de reglas o previsualización."""
                row = PooledRow(parent, corner_radius=0, fg_color='transparent')
                row.grid_columnconfigure((0, 1), weight=1, uniform='rename-preview')
                row.original_label = ctk.CTkLabel(row, text='', width=1, font=fonts.FUENTE_CHICA,
                    text_color=colors.TEXT_GRAY, anchor='w')
                row.original_label.grid(row=0, column=0, sticky='ew', padx=4)
                row.new_label = ctk.CTkLabel(row, text='', width=1, font=fonts.FUENTE_CHICA, anchor='w')
                row.new_label.grid(row=0, column=1, sticky='ew', padx=4)
                return row
            def render(row, index):
                """Refresca nombres propuestos sin modificar todavía los archivos."""
                original, nuevo = self._preview_data[index]
                configure_changed(row.original_label, text=original)
                configure_changed(row.new_label, text=nuevo, text_color=colors.ACENTO if original != nuevo else colors.TEXT_GRAY)
            self._preview_rows = VirtualRows(self._lista_preview, create, render, row_height=34)
            self._preview_empty = ctk.CTkLabel(self._lista_preview, text=t('rename_preview_empty'),
                font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY)
        self._preview_data = preview
        self._preview_rows.sync(range(len(preview)))
        if preview:
            self._preview_empty.pack_forget()
        else:
            self._preview_empty.pack(pady=16)

    def _renombrar(self):
        """Inicia el renombrado en segundo plano."""
        if self._operation_blocked(global_job=True):
            return
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_files_first'))
            return
        self._btn_renombrar.configure(state='disabled', text=t('renaming'))
        self._show_full_overlay(t('processing'))
        paths, options = tuple(self._imagenes), self._state.obtener_opciones()
        self._submit_job(lambda: self._proceso(paths, options),
                         button=self._btn_renombrar, text=t('rename_btn'))

    def _proceso(self, paths, opciones):
        """Ejecuta el renombrado."""
        res = renombrar_archivos(paths, opciones)
        self._post_ui(0, lambda: self._finalizar(
            res['ok'], res['errores'], res['conflictos']
        ))
        return res

    def _finalizar(self, ok, errores, conflictos):
        """Muestra el resultado y limpia la seleccion."""
        self._btn_renombrar.configure(state='normal', text=t('rename_btn'))
        self.logger.info("rename.ui: finalizar_ok (ok=%s, errores=%s, conflictos=%s)", ok, errores, conflictos)
        self._hide_full_overlay()
        msg = operation_summary(ok, errores, action='renamed', skipped=conflictos)
        # Limpiar despues de renombrar exitoso
        self._imagenes = []
        self._state.imagenes = []
        super()._limpiar()
        self._renderizar_preview([])
        self._lbl_info.configure(text=msg)

    def _aplicar_capitalizacion(self, caso):
        """
        Modifica el prefijo segun la capitalizacion elegida
        para forzar actualizacion del preview via trace.

        Args:
            caso: Valor traduzido del optionmenu ('minúsc.', 'MAYÚSC.', etc.)
        """
        self.logger.info("rename.ui: aplicar_capitalizacion (%s)", caso)
        prefijo_actual = self._state.prefijo.get()
        
        # Comparar contra valores traduzidos para determinar accion
        es_minusculas = caso == t('rename_case_lower')
        es_mayusculas = caso == t('rename_case_upper')
        
        if not prefijo_actual:
            if es_minusculas:
                self._state.caso.set('minusculas')
            elif es_mayusculas:
                self._state.caso.set('mayusculas')
            self._actualizar_preview()
            return

        if es_minusculas:
            self._state.caso.set('minusculas')
            self._state.prefijo.set(prefijo_actual.lower())
        elif es_mayusculas:
            self._state.caso.set('mayusculas')
            self._state.prefijo.set(prefijo_actual.upper())
        else:
            self._actualizar_preview()

    def _on_posicion_fecha_change(self, valor):
        """Actualizar posicion de fecha en el estado."""
        # Comparar contra valores traduzidos
        if valor == t('rename_suffix_pos'):
            self._state.posicion_fecha.set('sufijo')
        elif valor == t('rename_prefix_pos'):
            self._state.posicion_fecha.set('prefijo')
        self._actualizar_preview()

    def _on_formato_fecha_change(self, valor):
        """Actualizar formato de fecha en el estado."""
        self._state.formato_fecha.set(FORMATOS_FECHA.get(valor, '%Y%m%d'))
        self._actualizar_preview()

    def _sync_display_vars(self):
        """Sincroniza labels visibles con el estado interno."""
        if self._state.posicion_fecha.get() == 'sufijo':
            self._posicion_fecha_label.set(t('rename_suffix_pos'))
        else:
            self._posicion_fecha_label.set(t('rename_prefix_pos'))

        for label, fmt in FORMATOS_FECHA.items():
            if fmt == self._state.formato_fecha.get():
                self._formato_fecha_label.set(label)
                break

        if self._state.caso.get() == 'mayusculas':
            self._caso_label.set(t('rename_case_upper'))
        else:
            self._caso_label.set(t('rename_case_lower'))
