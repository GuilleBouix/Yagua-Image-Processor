"""
UI para el modulo de eliminacion de fondo de imagenes.
Quita el fondo y exporta con transparencia en el formato elegido.

Relacionado con:
    - app/ui/frames/base.py: Clase base de la que hereda.
    - app/ui/frames/remove_bg/state.py: Estado de la interfaz.
    - app/ui/frames/remove_bg/services.py: Servicios de logica.
    - app/translations/__init__.py: Traducciones de la UI.
"""

from __future__ import annotations

import logging
import sys

import customtkinter as ctk

from app.ui import colors, fonts, styles
from app.ui.scale import scale_wraplength
from app.translations import t
from app.ui.status import operation_summary
from app.ui.preview import LivePreview
from app.utils.saving import path_key
from app.ui.operations import operations
from app.ui.frames.base import BaseFrame
from app.ui.frames.remove_bg.state import RemoveBgState
from app.ui.frames.remove_bg.services import (
    batch_quitar_fondo,
    RemoveBgConfig,
    ensure_model,
    estado_rembg,
    modelo_descargado,
    FORMATOS_SALIDA,
    INSTALL_COMMAND,
)

logger = logging.getLogger(__name__)


class RemoveBgFrame(BaseFrame):
    """
    Frame del modulo de eliminacion de fondo.
    Procesa una o varias imagenes y exporta con transparencia.
    """

    design_system = True

    def __init__(self, parent):
        """Inicializa el frame."""
        self._formato_salida: ctk.StringVar = ctk.StringVar(value='PNG')
        self._state = RemoveBgState()
        self._refine_edges = ctk.StringVar(value=t('remove_bg_auto'))
        self._halo_strength = ctk.IntVar(value=85)
        self._edge_offset = ctk.IntVar(value=0)
        self._preview_active_path = ''
        self._preview_outputs = {}
        self._preview_errors = {}
        self._lbl_error_dependencia = None
        self._entry_dependencia_cmd = None
        self._btn_copiar_comando = None
        self._primer_uso_notice = None
        self._primer_uso_notice_job = None
        super().__init__(parent, t('remove_bg_title'))

    def _build_content(self):
        """Construye el contenido del modulo."""
        # Loader: usamos overlay full-frame (no un componente que empuje el layout).
        # Importante: diferir al siguiente tick para que BaseFrame no lo oculte
        # al finalizar _build().
        self._post_ui(0, self._inicializar_en_background)

    def _on_build_complete(self):
        """Conecta acciones al terminar la construcción del módulo."""
        self._scrollbar.configure(corner_radius=0, width=6, border_spacing=1)

    def _crear_spinner(self):
        """Deprecated: RemoveBG usa overlay full-frame."""
        return

    def _inicializar_en_background(self):
        """Inicializa checks pesados sin bloquear la UI."""
        if operations.is_busy():
            self.after(100, self._inicializar_en_background)
            return
        self._show_overlay(t('loading_model'))

        def _worker():
            """Procesa archivos fuera de Tk y recoge fallos por elemento."""
            try:
                disponible, detalle_error = estado_rembg()
            except Exception as exc:
                logger.warning("Error al verificar rembg: %s", exc)
                disponible = False
                detalle_error = str(exc).strip() or type(exc).__name__
            try:
                modelo_ok = modelo_descargado() if disponible else False
            except Exception as exc:
                logger.warning("Error al verificar modelo: %s", exc)
                modelo_ok = False
            return disponible, modelo_ok, detalle_error

        self._submit_job(_worker, on_success=lambda result: self._build_content_ready(*result),
                         on_error=lambda error: self._build_content_ready(False, False, str(error)))

    def _build_content_ready(self, disponible: bool, modelo_ok: bool, detalle_error: str | None = None):
        """Construye el contenido una vez finalizados los checks."""
        self._hide_overlay()

        if not disponible:
            self._construir_aviso_dependencia(detalle_error)
            return

        izquierda, derecha = self._crear_workspace()
        izquierda.grid_rowconfigure(2, weight=1)
        derecha.grid_rowconfigure(0, weight=1)
        self._preview = LivePreview(derecha, settle=self._settle_preview_layout)
        self._preview.grid(row=0, column=0, padx=16, pady=16, sticky='nsew')

        # Boton seleccionar
        self._btn_seleccionar = self._crear_boton_seleccionar(izquierda)
        self._btn_seleccionar.grid(row=0, column=0, padx=16, pady=(16, 8), sticky='ew')

        self._lista_frame = self._crear_lista_archivos(izquierda, height=160)
        self._lista_frame.grid(row=2, column=0, padx=16, pady=(0, 16), sticky='nsew')
        self._lbl_lista_vacia = self._crear_lista_vacia(self._lista_frame)
        self._lbl_lista_vacia.pack(pady=12)

        # Panel de opciones
        panel = ctk.CTkFrame(
            izquierda,
            **styles.surface('panel'),
        )
        panel.grid(row=1, column=0, padx=16, pady=(0, 16), sticky='new')
        panel.grid_columnconfigure(1, weight=1)

        # Descripcion
        ctk.CTkLabel(
            panel,
            text=t('remove_bg_description'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(16, 8), sticky='w')

        # Selector de formato
        ctk.CTkLabel(
            panel, text=t('output_format'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).grid(row=1, column=0, padx=(16, 12), pady=(0, 8), sticky='w')

        styles.SegmentedButton(
            panel,
            values=FORMATOS_SALIDA,
            variable=self._formato_salida,
            font=fonts.FUENTE_CHICA,
        ).grid(row=1, column=1, padx=(0, 16), pady=(0, 8), sticky='w')

        self._build_processing_controls(panel)

        # Boton procesar
        for _ in self._build_save_selector(panel, 4, columnspan=2):
            pass

        self._btn_procesar = self._new_button(
            panel,
            role='primary',
            text=t('remove_bg_btn'),
            font=fonts.FUENTE_BASE,
            command=self._procesar
        )
        self._btn_procesar.grid(
            row=5, column=0, columnspan=2,
            padx=16, pady=(0, 16), sticky='ew'
        )

        if not modelo_ok:
            self._construir_aviso_primer_uso()

    def _show_overlay(self, text: str):
        """Muestra overlay full-frame (bloquea interaccion)."""
        self._show_full_overlay(text)

    def _hide_overlay(self):
        """Oculta overlay full-frame."""
        self._hide_full_overlay()

    def _construir_aviso_dependencia(self, detalle_error: str | None):
        """Muestra panel con el error real y ayuda para instalar dependencias."""
        panel = ctk.CTkFrame(
            self,
            **styles.surface('panel'),
        )
        panel.grid(row=1, column=0, padx=24, pady=8, sticky='ew')
        panel.grid_columnconfigure(0, weight=1)
        resumen, detalle = self._resumir_error_dependencia(detalle_error)

        self._lbl_error_dependencia = ctk.CTkLabel(
            panel,
            text=resumen,
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            anchor='w',
            justify='left',
            wraplength=scale_wraplength(620)
        )
        self._lbl_error_dependencia.grid(row=0, column=0, padx=16, pady=(16, 8), sticky='w')

        if getattr(sys, 'frozen', False):
            ctk.CTkLabel(
                panel,
                text=t('rembg_packaged_help'),
                font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY,
                anchor='w',
                justify='left',
                wraplength=scale_wraplength(620)
            ).grid(row=1, column=0, padx=16, pady=(0, 16), sticky='w')
            return

        if detalle:
            ctk.CTkLabel(
                panel,
                text=detalle,
                font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY,
                anchor='w',
                justify='left',
                wraplength=scale_wraplength(620)
            ).grid(row=1, column=0, padx=16, pady=(0, 8), sticky='w')
            row_reinstall = 2
        else:
            row_reinstall = 1

        ctk.CTkLabel(
            panel,
            text=t('rembg_reinstall_app'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor='w',
            justify='left',
            wraplength=scale_wraplength(620)
        ).grid(row=row_reinstall, column=0, padx=16, pady=(0, 8), sticky='w')

        ctk.CTkLabel(
            panel,
            text=t('rembg_install_from_source'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor='w',
            justify='left',
            wraplength=scale_wraplength(620)
        ).grid(row=row_reinstall + 1, column=0, padx=16, pady=(0, 8), sticky='w')

        fila_comando = ctk.CTkFrame(panel, fg_color='transparent', corner_radius=0)
        fila_comando.grid(row=row_reinstall + 2, column=0, padx=16, pady=(0, 16), sticky='ew')
        fila_comando.grid_columnconfigure(0, weight=1)

        self._entry_dependencia_cmd = styles.Entry(
            fila_comando,
            font=ctk.CTkFont(family='Courier New', size=13),
            justify='left'
        )
        self._entry_dependencia_cmd.grid(row=0, column=0, sticky='ew', padx=(0, 8))
        self._entry_dependencia_cmd.insert(0, INSTALL_COMMAND)

        self._btn_copiar_comando = self._new_button(
            fila_comando,
            text=t('copy_command'),
            width=120,
            height=30,
            font=fonts.FUENTE_CHICA,
            command=self._copiar_comando_instalacion
        )
        self._btn_copiar_comando.grid(row=0, column=1, sticky='e')

    def _construir_aviso_primer_uso(self):
        """Muestra un aviso temporal en la parte inferior para el primer uso."""
        self._ocultar_aviso_primer_uso()

        aviso = ctk.CTkFrame(
            getattr(self, 'content', self),
            **styles.surface('panel'),
        )
        aviso.place(relx=0.5, rely=1.0, y=-16, anchor='s', relwidth=0.78)
        aviso.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            aviso,
            text=t('model_first_download'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            justify='center',
            wraplength=scale_wraplength(500)
        ).grid(row=0, column=0, padx=16, pady=8)

        self._primer_uso_notice = aviso
        self._primer_uso_notice_job = self.after(5000, self._ocultar_aviso_primer_uso)

    def _ocultar_aviso_primer_uso(self):
        """Oculta y destruye el aviso temporal del primer uso."""
        if self._primer_uso_notice_job is not None:
            try:
                self.after_cancel(self._primer_uso_notice_job)
            except Exception:
                pass
            self._primer_uso_notice_job = None

        if self._primer_uso_notice is not None:
            try:
                if self._primer_uso_notice.winfo_exists():
                    self._primer_uso_notice.destroy()
            except Exception:
                pass
            self._primer_uso_notice = None

    def _copiar_comando_instalacion(self):
        """Copia el comando sugerido al portapapeles."""
        self.clipboard_clear()
        self.clipboard_append(INSTALL_COMMAND)
        self._lbl_info.configure(text=t('command_copied'))

    def _set_overlay_key(self, key: str):
        """Actualiza el texto del overlay a partir de una clave de traduccion."""
        self._show_overlay(t(key))

    def _resumir_error_dependencia(self, detalle_error: str | None) -> tuple[str, str | None]:
        """Convierte errores tecnicos en mensajes breves para la UI."""
        detalle = (detalle_error or '').strip()
        detalle_lower = detalle.lower()

        if 'pymatting' in detalle_lower:
            return (
                t('rembg_unavailable_short'),
                str(t('rembg_missing_dependency')).format(dependency='pymatting'),
            )

        if detalle:
            return t('rembg_unavailable_short'), str(t('rembg_error_detail')).format(error=detalle)

        return t('rembg_unavailable_short'), None

    def _cargar_imagenes(self, rutas):
        """Carga las imagenes seleccionadas."""
        if self._operation_blocked(global_job=False):
            return
        limite = 10
        total = len(rutas)
        if total > limite:
            rutas = rutas[:limite]
            self._limite_msg = str(t('limit_reached')).format(limit=limite, total=total)
        else:
            self._limite_msg = None

        self._preview_outputs.clear()
        self._preview_errors.clear()
        super()._cargar_imagenes(rutas)
        self._refresh_preview()
        n = len(rutas)
        suffix = t('files_loaded').capitalize() if n > 1 else t('image_loaded')
        msg = f'{n} {suffix}'
        if self._limite_msg:
            msg += f'  -  {self._limite_msg}'
        self._lbl_info.configure(text=msg)

    def _procesar(self):
        """Inicia el proceso en segundo plano."""
        if self._operation_blocked(global_job=True):
            return
        if not self._imagenes:
            self._lbl_info.configure(text=t('load_images_first'))
            return

        paths, fmt = tuple(self._imagenes), self._formato_salida.get()
        config = self._processing_config()
        def start(folder, plan):
            """Captura opciones y selección antes de iniciar la operación global."""
            self._preview_outputs.clear()
            self._preview_errors.clear()
            self._refresh_preview()
            self._state.set_model_info(None, False)
            self._show_overlay(t('analyzing_image'))
            def finished(result):
                """Actualiza progreso y controles al completar el lote."""
                if result is not None:
                    self._state.set_model_info(result.get('model_used'), result.get('used_fallback', False))
                    self._finish_save(result)
            self._submit_job(lambda: self._proceso(folder, paths, fmt, output_policy=plan, config=config),
                button=self._btn_procesar, text=t('remove_bg_btn'), on_success=finished)
        self._prepare_save(paths, fmt, start)

    def _proceso(self, carpeta, paths, fmt, *, output_policy=None, config=None):
        """Ejecuta la eliminacion de fondo."""
        try:
            if not modelo_descargado():
                self._post_ui(0, lambda: self._set_overlay_key('downloading_model'))
                ensure_model()

            self._post_ui(0, lambda: self._set_overlay_key('loading_model'))
            self._post_ui(0, lambda: self._set_overlay_key('analyzing_image'))
            res = batch_quitar_fondo(
                paths,
                carpeta,
                formato_salida=fmt,
                **({'output_policy': output_policy} if output_policy is not None else {}),
                **({'config': config} if config is not None else {}),
                status_callback=lambda key: self._post_ui(0, lambda k=key: self._set_overlay_key(k)),
            )
            if output_policy is not None:
                return res
            self._post_ui(0, lambda: self._finalizar(
                res['ok'],
                res['errores'],
                res.get('conflictos', 0),
                res.get('used_fallback', False),
                res.get('model_used'),
            ))
        except Exception as exc:
            logger.exception("Error en proceso remove_bg")
            msg = str(exc).strip()
            if not msg or msg.lower() == 'none':
                msg = type(exc).__name__
            self._post_ui(0, lambda: self._handle_error(msg))
        return locals().get('res')

    def _handle_error(self, msg: str):
        """Maneja errores y restaura el estado visual."""
        self._hide_overlay()
        self._btn_procesar.configure(state='normal', text=t('remove_bg_btn'))
        self._lbl_info.configure(text=f'{t("error_generic")}: {msg}')
        if hasattr(self, '_preview'):
            self._preview_errors[path_key(self._preview_active_path)] = t('error_generic')
            self._refresh_preview()

    def _finalizar(self, ok, errores, conflictos=0, used_fallback=False, model_used=None):
        """Muestra el resultado final."""
        self._hide_overlay()
        self._state.set_model_info(model_used, used_fallback)
        self._btn_procesar.configure(state='normal', text=t('remove_bg_btn'))
        msg = operation_summary(ok, errores, action='processed')
        logger.info('remove_bg.ui: result ok=%s errors=%s fallback=%s model=%s',
                    ok, errores, used_fallback, model_used)
        self._lbl_info.configure(text=msg)

    def _select_preview_file(self, path):
        """Selecciona la entrada inspeccionada sin cambiar el lote de guardado."""
        if self._operation_blocked():
            return False
        self._preview_active_path = path
        self._refresh_preview()

    def _refresh_preview(self):
        """Muestra la salida guardada o el original, asociando rutas normalizadas."""
        path = self._preview_active_path
        key = path_key(path) if path else ''
        output = self._preview_outputs.get(key)
        self._preview.show(output or path, title=t('preview_result' if output else 'preview_original'),
                           note=self._preview_errors.get(key, ''), force=True)

    def _finish_save(self, result, *, strip=False):
        """Asocia cada éxito con su archivo publicado y conserva errores individuales."""
        super()._finish_save(result, strip=strip)
        for row in result.get('resultados', []):
            path = path_key(row['ruta_entrada'])
            self._preview_outputs.pop(path, None)
            self._preview_errors.pop(path, None)
            if row.get('estado') == 'saved' and row.get('ruta_salida'):
                self._preview_outputs[path] = row['ruta_salida']
            elif row.get('estado') == 'error':
                self._preview_errors[path] = t('error_generic') + ': ' + t(row.get('error', 'error_generic'))
        self._refresh_preview()

    def _limpiar(self):
        """Invalida entradas y resultados, conservando los ajustes del usuario."""
        if self._operation_blocked():
            return
        super()._limpiar()
        self._preview_outputs.clear()
        self._preview_errors.clear()
        self._preview_active_path = ''
        if hasattr(self, '_preview'):
            self._preview.show(force=True)

    def on_view_shown(self):
        """Reanuda la preview al mostrar el módulo."""
        super().on_view_shown()
        if hasattr(self, '_preview'):
            self._preview.set_visible(True)

    def on_view_hidden(self):
        """Pausa renders cuando se navega a otra herramienta."""
        if hasattr(self, '_preview'):
            self._preview.set_visible(False)

    def _build_processing_controls(self, panel):
        """Crea una sola vez los tres ajustes visibles; no inicializa modelos."""
        ctk.CTkLabel(panel, text=t('remove_bg_refine'), font=fonts.FUENTE_BASE,
                     text_color=colors.TEXT_GRAY, anchor='w').grid(
            row=2, column=0, padx=(16, 12), pady=(0, 8), sticky='w')
        styles.SegmentedButton(panel,
            values=[t('remove_bg_auto'), t('remove_bg_on'), t('remove_bg_off')],
            variable=self._refine_edges, font=fonts.FUENTE_CHICA,
            command=self._processing_settings_changed).grid(
                row=2, column=1, padx=(0, 16), pady=(0, 8), sticky='w')
        self._edge_controls = ctk.CTkFrame(panel, fg_color='transparent', corner_radius=0)
        self._edge_controls.grid(row=3, column=0, columnspan=2, padx=16, pady=(0, 8), sticky='ew')
        self._edge_controls.grid_columnconfigure(1, weight=1)
        for row, key in ((0, 'remove_bg_halo'), (1, 'remove_bg_contour')):
            ctk.CTkLabel(self._edge_controls, text=t(key), font=fonts.FUENTE_CHICA,
                         text_color=colors.TEXT_GRAY).grid(row=row, column=0, padx=(0, 12), pady=8, sticky='w')
        self._lbl_halo = ctk.CTkLabel(self._edge_controls, text='85%', width=45, font=fonts.FUENTE_CHICA)
        self._lbl_halo.grid(row=0, column=2, padx=(12, 0), pady=8)
        self._lbl_contour = ctk.CTkLabel(self._edge_controls, text='0 px', width=45, font=fonts.FUENTE_CHICA)
        self._lbl_contour.grid(row=1, column=2, padx=(12, 0), pady=8)
        self._slider_halo = ctk.CTkSlider(self._edge_controls, from_=0, to=100, number_of_steps=100,
            variable=self._halo_strength, button_color=colors.ACENTO, button_hover_color=colors.ACENTO_HOVER,
            progress_color=colors.ACENTO, fg_color=styles.palette().border, command=self._halo_changed)
        self._slider_halo.grid(row=0, column=1, sticky='ew', pady=8)
        self._slider_contour = ctk.CTkSlider(self._edge_controls, from_=-5, to=5, number_of_steps=10,
            variable=self._edge_offset, button_color=colors.ACENTO, button_hover_color=colors.ACENTO_HOVER,
            progress_color=colors.ACENTO, fg_color=styles.palette().border, command=self._contour_changed)
        self._slider_contour.grid(row=1, column=1, sticky='ew', pady=8)

    def _halo_changed(self, value):
        """Actualiza la intensidad porcentual para el próximo procesamiento."""
        self._halo_strength.set(round(value))
        self._lbl_halo.configure(text=f'{self._halo_strength.get()}%')
        self._processing_settings_changed()

    def _contour_changed(self, value):
        """Guarda contracción negativa o expansión positiva en píxeles originales."""
        self._edge_offset.set(round(value))
        value = self._edge_offset.get()
        self._lbl_contour.configure(text=f'{value:+d} px' if value else '0 px')
        self._processing_settings_changed()

    def _processing_settings_changed(self, *_):
        """Aclara que mover controles no modifica la salida guardada visible."""
        if self._preview_outputs:
            self._lbl_info.configure(text=t('remove_bg_apply_hint'))

    def _processing_config(self):
        """Captura desde Tk opciones inmutables con identificadores no traducidos."""
        refine = {t('remove_bg_auto'): 'auto', t('remove_bg_on'): 'on', t('remove_bg_off'): 'off'}
        return RemoveBgConfig(refine_edges=refine[self._refine_edges.get()],
                              halo_strength=self._halo_strength.get(), edge_offset=self._edge_offset.get())
