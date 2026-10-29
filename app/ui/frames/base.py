"""
Clase base para frames de la aplicacion.
Contiene metodos y componentes comunes reutilizables.

Proporciona la estructura basica de un modulo: header con titulo
y boton limpiar, area de contenido, y footer para informacion.

Relacionado con:
    - app/ui/main_window.py: Instancia los frames que heredan de esta clase.
    - app/ui/frames/compress/frame.py: Override de metodos especificos.
    - app/ui/frames/convert/frame.py: Override de metodos especificos.
    - app/ui/frames/resize/frame.py: Override de metodos especificos.
    - app/ui/frames/palette/frame.py: Override de metodos especificos.
    - app/ui/frames/metadata/frame.py: Override de metodos especificos.
"""

import logging
import threading
from pathlib import Path
from tkinter import filedialog, Text
from typing import Any

import customtkinter as ctk

from app.ui import colors, fonts
from app.ui.lifetime import UiLifetime
from app.ui.building import finish, steps_for
from app.utils import tintar_icono
from app.modules.compress import formatear_bytes
from app.translations import t
from app.ui.operations import operations


logger = logging.getLogger(__name__)


def _file_size_label(path):
    """Formatea el tamaño de archivo para etiquetas de interfaz."""
    try:
        return formatear_bytes(path.stat().st_size)
    except OSError:
        return t('error_generic')



class BaseFrame(UiLifetime, ctk.CTkScrollableFrame):
    """Construye la estructura compartida de los módulos de la interfaz."""

    design_system = False
    _lista_frame: ctk.CTkFrame | ctk.CTkScrollableFrame
    _lbl_lista_vacia: ctk.CTkLabel

    def __init__(self, parent, title, *, defer_build=False):
        """
        Inicializa el frame base.
        
        Args:
            parent: Widget padre.
            title: Titulo del modulo para mostrar en el header.
        """
        super().__init__(
            parent,
            corner_radius=0,
            fg_color=colors.FRAMES_BG,
            scrollbar_fg_color=colors.FRAMES_BG,
            scrollbar_button_color=colors.SIDEBAR_SEPARATOR,
            scrollbar_button_hover_color=colors.SIDEBAR_HOVER,
        )
        
        # Titulo del modulo
        self._title = title
        
        # Lista de rutas de imagenes cargadas
        self._imagenes = []
        self._save_groups: list[ctk.CTkFrame] = []
        
        # Lista de thumbnails de imagenes
        self._thumbs = []
        
        # Lista de labels de filas de la lista de archivos
        self._filas_lista = []

        # Overlay full-frame reusable
        self._full_overlay_frame = None
        self._full_overlay_card = None
        self._full_overlay_label = None
        self._full_overlay_bar = None
        self._viewport_sync_job = None

        # Asegurar que el contenido ocupe como minimo el viewport visible.
        self.after(0, self._bind_viewport_sync)
        
        # Construir la estructura del frame
        self.build_ready = False
        self._defer_build = defer_build
        self._build_iterator = self._build_steps()
        if not defer_build:
            finish(self._build_iterator)

    def _post_ui(self, delay, callback):
        # Los workers publican aquí; no usan Tk.after. Se conserva delay por compatibilidad con llamadas existentes.
        """Publica una actualización de widget desde una operación asíncrona."""
        if threading.current_thread() is threading.main_thread():
            self.after(delay, callback)
        else:
            operations.post(self, callback)

    def _operation_blocked(self, *, global_job=False):
        """Evita iniciar o editar una vista mientras hay una operación incompatible."""
        busy = operations.is_busy(None if global_job else self)
        if busy and hasattr(self, '_lbl_info'):
            self._lbl_info.configure(text=t('operation_busy'))
        return busy

    def _build_save_selector(self, parent, row, **kwargs):
        """Crea los controles compartidos para elegir el destino de salida."""
        from app.ui.saving import selector_steps
        return selector_steps(self, parent, row, **kwargs)

    def _new_button(self, parent, *, role='secondary', **kwargs):
        """Construye un botón que hereda estilo, idioma y escala de la app."""
        if self.design_system:
            from app.ui.styles import Button
            return Button(parent, role=role, **kwargs)
        return ctk.CTkButton(parent, **kwargs)

    def _prepare_save(self, paths, target_format, proceed, **kwargs):
        """Captura y valida la política de salida seleccionada por el usuario."""
        from app.ui.saving import prepare
        return prepare(self, paths, target_format, proceed, **kwargs)

    def _sync_save_visibility(self):
        """Muestra controles de guardado solo cuando hay resultados compatibles."""
        from app.ui.saving import set_visible
        set_visible(self, bool(self._imagenes))

    def _finish_save(self, result, *, strip=False):
        """Actualiza la interfaz al terminar el guardado del lote."""
        from app.ui.saving import refresh, summary
        refresh(self, result)
        self._lbl_info.grid(sticky='ew')
        self._lbl_info.configure(text=summary(result, strip=strip), width=1,
                                 anchor='w', justify='left', wraplength=max(120, self.winfo_width() - 48))
        if not hasattr(self, '_save_footer_binding'):
            def fit(event):
                """Reduce o reorganiza texto para que no quede cortado."""
                width = max(120, int(event.width / self._get_widget_scaling()) - 48)
                if self._lbl_info.cget('wraplength') != width:
                    self._lbl_info.configure(wraplength=width)
            self._save_footer_binding = self.bind('<Configure>', fit, add=True)

    def _submit_job(self, work, *, button=None, text=None, on_success=None, on_error=None):
        """Freeze controls until the queued result is delivered, including startup errors."""
        if self._operation_blocked(global_job=True):
            self._hide_full_overlay()
            if button is not None:
                button.configure(state='normal', text=text)
            return False
        controls = []
        def freeze(parent):
            """Deshabilita controles mientras el módulo ejecuta un trabajo."""
            for widget in parent.winfo_children():
                if isinstance(widget, (ctk.CTkButton, ctk.CTkEntry, ctk.CTkCheckBox,
                                       ctk.CTkSlider, ctk.CTkOptionMenu, ctk.CTkComboBox, Text, ctk.CTkSwitch)):
                    if widget.cget('state') != 'disabled':
                        controls.append((widget, widget.cget('state')))
                        widget.configure(state='disabled')
                else:
                    freeze(widget)

        def restore():
            """Restaura controles al finalizar o fallar una operación."""
            for widget, state in controls:
                if widget.winfo_exists():
                    widget.configure(state=state)
            if button is not None and button.winfo_exists():
                button.configure(state='normal', text=text)
            self._hide_full_overlay()

        def success(result):
            """Presenta el resultado de una operación completada."""
            restore()
            if on_success is not None:
                on_success(result)
            elif callable(result):
                result()
            self._show_failures(result)


        def failed(error):
            """Muestra el error y restablece la interfaz del módulo."""
            restore()
            handler = on_error or getattr(self, '_handle_error', None)
            if handler is not None:
                handler(error if on_error else str(error))
            else:
                self._lbl_info.configure(text=f"{t('error_generic')}: {t(str(error))}")
        try:
            freeze(self)
            accepted = operations.submit(self, self._title, work, success, failed)
        except Exception as error:
            failed(error)
            return False
        if not accepted:
            restore()
        return accepted

    def _show_failures(self, result):
        """Presenta los fallos individuales devueltos por el procesamiento."""
        if isinstance(result, dict) and result.get('fallos'):
            from tkinter import messagebox
            failures = tuple(result['fallos'])
            details = '\n'.join(f"{item['ruta']}: {t(item['motivo'])}" for item in failures)
            operations.post(self, lambda: messagebox.showwarning(t('error_generic'), details, parent=self))

    def on_view_shown(self):
        """Hook de lifecycle cuando la vista pasa a estar visible."""
        self._schedule_viewport_sync()

    def on_view_hidden(self):
        """Hook de lifecycle cuando la vista deja de estar visible."""
        return

    def _build(self):
        """Construye estructura común y contenido propio del módulo."""
        finish(self._build_steps())

    def _build_steps(self):
        """
        Construye la estructura completa del frame.
        
        Llama a los metodos de construccion en orden:
        header, contenido y footer.
        """
        logger.info("%s: build", self.__class__.__name__)
        if not self._defer_build:
            self._show_full_overlay(t('processing'))
        # Configurar columna para ocupar todo el ancho
        self.grid_columnconfigure(0, weight=1)
        
        # Construir cada seccion
        self._build_header()
        yield
        yield from steps_for(self._build_content)
        yield from self._prepare_additional_steps()
        self._build_footer()
        yield
        self._hide_full_overlay()
        self.build_ready = True
        self._on_build_complete()

    def _on_build_complete(self):
        """Subclass initialization that requires already constructed controls."""
        if self.design_system:
            self._scrollbar.configure(corner_radius=0, width=6, border_spacing=1)

    def _prepare_additional_steps(self):
        """Optional controls that would otherwise be built on the first mode change."""
        yield

    def _bind_viewport_sync(self):
        """Sincroniza la altura minima del frame con el viewport scrollable."""
        if not hasattr(self, "_parent_canvas"):
            return
        try:
            self._parent_canvas.bind("<Configure>", self._schedule_viewport_sync, add="+")
            self.bind("<Configure>", self._schedule_viewport_sync, add="+")
            self._schedule_viewport_sync()
        except Exception:
            logger.exception("%s: no se pudo sincronizar viewport", self.__class__.__name__)

    def _schedule_viewport_sync(self, _event=None):
        """Espera al final del ciclo de geometría antes de medir el viewport."""
        if self._viewport_sync_job is not None or not self.winfo_exists():
            return
        try:
            self._viewport_sync_job = self.after_idle(self._sync_viewport_height)
        except Exception:
            logger.debug("%s: no se pudo programar sync de viewport", self.__class__.__name__, exc_info=True)

    def _sync_viewport_height(self, _event=None):
        """Hace que el frame ocupe al menos todo el alto visible del canvas."""
        self._viewport_sync_job = None
        if not hasattr(self, "_parent_canvas") or not hasattr(self, "_create_window_id"):
            return
        try:
            canvas_height = self._parent_canvas.winfo_height()
            if canvas_height <= 1:
                return
            requested_height = self.winfo_reqheight()
            target_height = max(canvas_height, requested_height)
            if getattr(self, '_viewport_height', None) != target_height:
                self._viewport_height = target_height
                self._parent_canvas.itemconfigure(self._create_window_id, height=target_height)
        except Exception:
            logger.debug("%s: viewport height sync omitido", self.__class__.__name__, exc_info=True)

    def _settle_preview_layout(self):
        """Opt-in preview preparation after the initial workspace has reflowed."""
        previous = getattr(self, '_viewport_height', None)
        self._sync_viewport_height()
        return previous != getattr(self, '_viewport_height', None)

    def _ensure_full_overlay(self):
        """Crea overlay full-frame si no existe."""
        if self._full_overlay_frame:
            return
        overlay_host = getattr(self, "_parent_frame", self)
        from app.ui import styles
        panel_style = styles.surface('panel') if self.design_system else {}
        self._full_overlay_frame = ctk.CTkFrame(
            overlay_host,
            corner_radius=0,
            fg_color=colors.SIDEBAR_BG,
        )
        # Bloquear interaccion
        for ev in ("<Button-1>", "<ButtonRelease-1>", "<Motion>", "<MouseWheel>"):
            self._full_overlay_frame.bind(ev, lambda event=None: "break")

        self._full_overlay_card = ctk.CTkFrame(
            self._full_overlay_frame,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        if panel_style:
            self._full_overlay_card.configure(**panel_style)
        self._full_overlay_label = ctk.CTkLabel(
            self._full_overlay_card,
            text=t('processing'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
        )
        self._full_overlay_bar = ctk.CTkProgressBar(
            self._full_overlay_card,
            width=240,
            height=12,
            corner_radius=0 if self.design_system else 8,
            fg_color=styles.palette().border if self.design_system else colors.SIDEBAR_SEPARATOR,
            progress_color=colors.ACENTO,
            mode='indeterminate'
        )

        self._full_overlay_card.place(relx=0.5, rely=0.5, anchor='center')
        self._full_overlay_label.grid(row=0, column=0, padx=24, pady=(16, 8))
        self._full_overlay_bar.grid(row=1, column=0, padx=24, pady=(0, 16))
        self._full_overlay_frame.place_forget()

    def _show_full_overlay(self, text: str | None = None):
        """Muestra overlay full-frame bloqueando interaccion."""
        self._ensure_full_overlay()
        if self._full_overlay_label and text:
            self._full_overlay_label.configure(text=text)
        self._sync_viewport_height()
        overlay = self._full_overlay_frame
        if overlay is None:
            return
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        try:
            overlay.lift()
        except Exception:
            pass
        if self._full_overlay_bar:
            try:
                self._full_overlay_bar.start()
            except Exception:
                pass

    def _hide_full_overlay(self):
        """Oculta overlay full-frame."""
        if not self._full_overlay_frame:
            return
        if self._full_overlay_bar:
            try:
                self._full_overlay_bar.stop()
            except Exception:
                pass
        self._full_overlay_frame.place_forget()

    def _build_header(self):
        """
        Construye el header con titulo y boton limpiar.
        
        Crea una fila en la parte superior con el titulo
        del modulo y un boton para limpiar la seleccion.
        """
        logger.info("%s: build_header", self.__class__.__name__)
        # Frame transparente para la fila del titulo
        fila_titulo = ctk.CTkFrame(self, fg_color='transparent')
        fila_titulo.grid(row=0, column=0, padx=24, pady=(22, 10), sticky='ew')
        fila_titulo.grid_columnconfigure(0, weight=1)
        fila_titulo.grid_columnconfigure(1, weight=0)
        fila_titulo.grid_columnconfigure(2, weight=0)
        self._title_row = fila_titulo

        # Label del titulo
        ctk.CTkLabel(
            fila_titulo,
            text=self._title,
            font=fonts.FUENTE_TITULO,
            text_color=colors.TEXT_COLOR,
            anchor='w'
        ).grid(row=0, column=0, sticky='w')

        # Boton de limpiar
        self._btn_limpiar = self._new_button(
            fila_titulo,
            text=t('clean'),
            width=80,
            height=30,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.BTN_CLEAR_BG,
            text_color=colors.BTN_CLEAR_TEXT,
            hover_color=colors.BTN_CLEAR_HOVER,
            border_width=0,
            command=self._limpiar
        )
        self._btn_limpiar.grid(row=0, column=1, sticky='e')

    def _build_content(self):
        """
        Construye el contenido especifico del modulo.
        
        Debe ser implementado por las subclases para agregar
        los componentes especificos de cada modulo.
        """
        raise NotImplementedError("Subclasses must implement _build_content")

    def _build_footer(self):
        """
        Construye el footer con label de informacion.
        
        Crea un label donde se mostraran mensajes de estado
        o informacion adicional durante las operaciones.
        """
        logger.info("%s: build_footer", self.__class__.__name__)
        self._lbl_info = ctk.CTkLabel(
            self, text='',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )
        self._lbl_info.grid(row=100, column=0, padx=24, pady=(0, 8), sticky='w')

    def _crear_workspace(self, parent=None, *, row=1, columnspan=1, column_weights=(1, 1), breakpoint=940, padx=24, pady=(0, 12)):
        """Crea dos paneles de trabajo que se apilan al reducir el ancho.

        Los módulos colocan entrada y controles en el panel izquierdo, y la
        lista, preview o salida en el derecho. El umbral se mide sobre el
        ancho disponible del área de contenido, no de la ventana completa.
        column_weights define la proporción entre ambas columnas al estar
        juntas; por defecto conservan el mismo ancho.
        """
        parent = parent or self
        host = ctk.CTkFrame(parent, fg_color='transparent')
        host.grid(row=row, column=0, columnspan=columnspan, padx=padx, pady=pady, sticky='nsew')
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(row, weight=1)
        for column, weight in enumerate(column_weights):
            host.grid_columnconfigure(column, weight=weight, uniform='workspace')
        host.grid_rowconfigure(0, weight=1)

        from app.ui import styles
        panel_style: dict[str, Any] = styles.surface('panel') if self.design_system else dict(
            corner_radius=12, fg_color=colors.PANEL_BG,
            border_width=1, border_color=colors.SIDEBAR_SEPARATOR)
        panels = []
        for column in range(2):
            panel = ctk.CTkFrame(
                host,
                **panel_style,
            )
            panel.grid_columnconfigure(0, weight=1)
            panels.append(panel)

        state: dict[str, bool | None] = {'narrow': None}

        def reflow(event=None):
            """Ajusta la disposición de controles a la escala disponible."""
            width = event.width if event is not None else host.winfo_width()
            narrow = width < breakpoint
            if state['narrow'] == narrow:
                return
            state['narrow'] = narrow
            if narrow:
                host.grid_columnconfigure(1, weight=0, uniform='')
                panels[0].grid(row=0, column=0, padx=0, pady=(0, 12), sticky='nsew')
                panels[1].grid(row=1, column=0, padx=0, pady=0, sticky='nsew')
                host.grid_rowconfigure(0, weight=0)
                host.grid_rowconfigure(1, weight=0)
            else:
                for column, weight in enumerate(column_weights):
                    host.grid_columnconfigure(column, weight=weight, uniform='workspace')
                host.grid_rowconfigure(0, weight=1)
                host.grid_rowconfigure(1, weight=0)
                panels[0].grid(row=0, column=0, padx=(0, 8), pady=0, sticky='nsew')
                panels[1].grid(row=0, column=1, padx=(8, 0), pady=0, sticky='nsew')

        host.bind('<Configure>', reflow, add=True)
        host.after(0, reflow)
        if parent is self:
            self._workspace_host = host
            self._workspace_left, self._workspace_right = panels
        return panels[0], panels[1]

    def _crear_boton_seleccionar(self, parent, texto=None, comando=None):
        """
        Crea un boton estandar para seleccionar archivos.
        
        Args:
            parent: Widget padre del boton.
            texto: Texto del boton (usa traduccion por defecto).
            comando: Funcion a ejecutar al hacer clic.
            
        Returns:
            Boton CTkButton configurado.
        """
        # Usar comando por defecto si no se especifica
        if comando is None:
            comando = self._explorar
        
        # Usar texto por defecto si no se especifica
        if texto is None:
            texto = t('select_images')

        # Crear y retornar el boton
        return self._new_button(
            parent,
            text=texto,
            height=40,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            hover_color=colors.SIDEBAR_HOVER,
            image=tintar_icono('assets/icons/upload.png', colors.ICON_COLOR),
            compound='left',
            command=comando
        )

    def _crear_lista_archivos(self, parent, height=200):
        """
        Crea un frame scrolleable para mostrar lista de archivos.
        
        Args:
            parent: Widget padre del frame.
            height: Altura fija del frame en pixeles.
            
        Returns:
            CTkScrollableFrame configurado.
        """
        # Crear frame scrolleable
        lista = ctk.CTkScrollableFrame(
            parent,
            corner_radius=10,
            fg_color=colors.PANEL_BG,
            height=height
        )
        if self.design_system:
            from app.ui import styles
            lista.configure(**styles.surface('list'), **styles.scrollbar())
            lista._scrollbar.configure(corner_radius=0, width=6, border_spacing=1)
        lista.grid_columnconfigure(0, weight=1)
        return lista

    def _crear_lista_vacia(self, parent):
        """
        Crea un label para mostrar cuando no hay archivos.
        
        Args:
            parent: Widget padre del label.
            
        Returns:
            CTkLabel con mensaje de lista vacia.
        """
        return ctk.CTkLabel(
            parent,
            text=t('no_images'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )

    def _explorar(self, titulo=None, multi=True):
        """
        Abre un dialogo para seleccionar archivos de imagen.
        
        Args:
            titulo: Titulo del dialogo (usa traduccion por defecto).
            multi: Si es True, permite seleccionar multiples archivos.
        """
        if self._operation_blocked():
            return
        logger.info("%s: explorar (multi=%s)", self.__class__.__name__, multi)
        # Usar titulo por defecto si no se especifica
        if titulo is None:
            titulo = t('select_images')
        
        # Seleccion multiple de archivos
        if multi:
            archivos = filedialog.askopenfilenames(
                title=titulo,
                filetypes=[(t('images_loaded'), '*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.avif *.heic *.heif *.ico')]
            )
            # Cargar las imagenes seleccionadas
            if archivos:
                self._cargar_imagenes(list(archivos))
        else:
            # Seleccion de un solo archivo
            archivo = filedialog.askopenfilename(
                title=titulo,
                filetypes=[(t('images_loaded'), '*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.avif *.heic *.heif')]
            )
            if archivo:
                self._cargar_imagenes([archivo])

    def _cargar_imagenes(self, rutas):
        """
        Carga una lista de imagenes y muestra sus filas.
        
        Args:
            rutas: Lista de rutas de archivos a cargar.
        """
        if self._operation_blocked():
            return
        logger.info("%s: cargar_imagenes (total=%s)", self.__class__.__name__, len(rutas))
        # Actualizar lista de imagenes
        self._imagenes = rutas
        self._sync_save_visibility()
        from app.ui.file_list import FileList
        if not hasattr(self, '_virtual_file_list'):
            self._virtual_file_list = FileList(self._lista_frame, self._filas_lista, self._thumbs,
                                               design_system=self.design_system,
                                               on_select=getattr(self, '_select_preview_file', None))
        self._virtual_file_list.statuses.clear()
        self._virtual_file_list.sync(rutas)

    def _agregar_fila_archivo(self, ruta):
        """
        Agrega una fila a la lista con info del archivo.
        
        Args:
            ruta: Ruta del archivo a mostrar.
        """
        p = Path(ruta)
        
        # Crear frame para la fila
        fila = ctk.CTkFrame(
            self._lista_frame, fg_color=colors.SIDEBAR_BG, corner_radius=8
        )
        fila.pack(fill='x', pady=3, padx=2)
        fila.grid_columnconfigure(1, weight=1)

        # Label para el thumbnail
        lbl_thumb = ctk.CTkLabel(
            fila, text='', width=44, height=44, fg_color='transparent'
        )
        lbl_thumb.grid(row=0, column=0, padx=(8, 0), pady=6)

        # Frame para la informacion
        info = ctk.CTkFrame(fila, fg_color='transparent')
        info.grid(row=0, column=1, padx=(10, 8), pady=6, sticky='w')

        # Truncar nombre si es muy largo
        nombre = p.name if len(p.name) <= 32 else p.name[:29] + '...'
        
        # Label del nombre
        ctk.CTkLabel(
            info, text=nombre,
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).pack(anchor='w')
        
        # Label del tamano y extension
        ctk.CTkLabel(
            info,
            text=f'{_file_size_label(p)}  -  {p.suffix.upper().lstrip(".")}',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).pack(anchor='w')

        # Guardar referencia al label del thumbnail
        self._filas_lista.append(lbl_thumb)

    def _limpiar(self):
        """
        Limpia la seleccion de imagenes y reinicia el estado.
        
        Elimina todas las imagenes cargadas y restaura
        el label de lista vacia si existe.
        """
        if self._operation_blocked():
            return
        logger.info("%s: limpiar", self.__class__.__name__)
        # Reiniciar listas
        self._imagenes = []
        self._sync_save_visibility()
        self._thumbs.clear()
        self._filas_lista.clear()
        
        if hasattr(self, '_virtual_file_list'):
            self._virtual_file_list.sync([])
            self._lbl_info.configure(text='')
            return

        # La lista no tiene filas hasta que se cargan los primeros archivos.
        
        # Mostrar label de lista vacia si existe y esta vivo
        if hasattr(self, '_lbl_lista_vacia') and self._lbl_lista_vacia.winfo_exists():
            self._lbl_lista_vacia.pack(pady=12)
        
        # Limpiar label de informacion
        self._lbl_info.configure(text='')
