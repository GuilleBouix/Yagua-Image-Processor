"""
Ventana principal de la interfaz de usuario.
Contiene la estructura base con barra lateral y area de contenido.

Relacionado con:
    - app/app.py: Crea e integra esta ventana.
    - app/ui/sidebar.py: Barra lateral de navegacion.
    - app/ui/module_registry.py: Registro de modulos disponibles.
    - app/ui/frames/: Frames de cada modulo.
"""

from app.ui.building import finish, stepwise, steps_for
import logging
import threading
import webbrowser
import customtkinter as ctk

from app.ui.sidebar import Sidebar
from app.ui.module_registry import get_module_spec, iter_enabled_modules, load_frame_class
from app.ui import colors, fonts
from app.ui.lifetime import UiLifetime
from app.utils.update_checker import check_latest_update
from app.version import __version__
from app.ui.frames.home.frame import HomeFrame
from app.translations import t
from app.ui.operations import operations


logger = logging.getLogger(__name__)


class MainWindow(UiLifetime, ctk.CTkFrame):
    """
    Marco principal que contiene la barra lateral y el area de contenido.
    
    Organiza la interfaz en dos areas principales:
        - Sidebar: Barra lateral con botones de navegacion.
        - Content: Area donde se muestran los frames de cada modulo.
    """
    
    def __init__(self, parent, *, defer_build=False, auto_updates=True):
        """
        Inicializa la ventana principal.
        
        Args:
            parent: Widget padre (normalmente la instancia de YaguaApp).
        """
        super().__init__(parent, corner_radius=0)

        # Diccionario para almacenar las instancias de frames (lazy-loaded)
        self.frames = {}
        self._active_view_key = None
        self._active_view = None
        self._defer_build = defer_build
        self._auto_updates = auto_updates
        self._updates_started = False
        self.build_ready = False
        self._preloader = None
        self._poll_operations()

        # Construir la estructura de la ventana
        self._build_iterator = self._build_steps()
        if not defer_build:
            finish(self._build_iterator)

    def _build_steps(self):
        """Construye la ventana por bloques para mantener el loop de eventos fluido."""
        yield from steps_for(self._build)
        self.build_ready = True
  
    @stepwise
    def _build(self):
        """
        Construye los componentes de la ventana principal.
        
        Crea la sidebar con sus botones y el area de contenido
        donde se mostraran los frames de cada modulo.
        """
        # Crear sidebar y posicionar a la izquierda
        if self._defer_build:
            self.sidebar = Sidebar(self, on_select=self.show_module, defer_build=True)
            self.sidebar.pack(side='left', fill='y')
            yield from self.sidebar._build_iterator
        else:
            self.sidebar = Sidebar(self, on_select=self.show_module)
        yield
        setattr(self.sidebar, "on_home", self.show_home)
        yield
        self.sidebar.pack(side='left', fill='y')
        yield
        
        # Crear area de contenido y posicionar a la derecha
        self.content = ctk.CTkFrame(self, corner_radius=0)
        yield
        self.content.pack(side='left', fill='both', expand=True)
        yield
        
        # Inicializar slots para frames lazy-loaded
        first_key = None
        yield
        for spec in iter_enabled_modules():
            self.frames[spec.key] = None
            yield
            if first_key is None:
                first_key = spec.key
                yield

        # Pantalla inicial (no aparece en sidebar)
        if self._defer_build:
            self._home = HomeFrame(self.content, defer_build=True)
            self._get_view_host(self._home).place(x=0, y=0, relwidth=1, relheight=1)
            yield from self._home._build_iterator
        else:
            self._home = HomeFrame(self.content)
        yield
        set_home_navigation = getattr(self._home, "set_on_select", None)
        yield
        if callable(set_home_navigation):
            set_home_navigation(self.show_module)
            yield
        self._show_view(self._home, key=None)
        yield
        # Sidebar sin selección activa hasta que el usuario elija un módulo
        try:
            self.sidebar.set_active(None)
            yield
        except Exception:
            pass

        # Check de versiones estables publicadas, sin bloquear la interfaz.
        if self._auto_updates:
            self.start_updates()
        yield

    def start_updates(self):
        """Inicia polling de operaciones y actualizaciones con callbacks de Tk."""
        if not self._updates_started:
            self._updates_started = True
            self.after(350, self._check_updates_on_startup)

    def _poll_operations(self):
        """Recoge resultados y avisos de workers desde el hilo principal."""
        if not self.winfo_exists():
            return
        try:
            operations.drain(lambda owner: bool(owner.winfo_exists()))
        except Exception:
            logger.exception('Operation polling failed')
        self.after(30, self._poll_operations)

    def _check_updates_on_startup(self):
        """Consulta GitHub sin bloquear la navegación inicial."""
        def _worker():
            """Ejecuta una consulta externa fuera del hilo de interfaz."""
            try:
                info = check_latest_update(__version__)
            except Exception:
                logger.exception('updates: fallo en la comprobación al iniciar')
                return
            if not info:
                return
            operations.post(self, lambda: self._show_update_banner(info.version, info.release_url))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_update_banner(self, version: str, url: str):
        # Evitar duplicados en la misma sesión.
        """Presenta la versión disponible sin bloquear el arranque."""
        banner = getattr(self, "_update_banner", None)
        if banner is not None:
            try:
                if banner.winfo_exists():
                    return
            except Exception:
                pass

        banner = ctk.CTkFrame(
            self.content,
            corner_radius=0,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
        )
        # Banner inferior (no invasivo). Usamos y negativo para dejar un margen interno.
        banner.place(relx=0.5, rely=1.0, y=-12, anchor="s", relwidth=0.94)
        banner.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(
            banner,
            text=t("updates_available").format(version=version),  # type: ignore
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_COLOR,
            anchor="w",
        )
        lbl.grid(row=0, column=0, padx=14, pady=10, sticky="ew")

        btn = ctk.CTkButton(
            banner,
            text=t("updates_download_btn").format(version=version),  # type: ignore
            height=28,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=lambda: webbrowser.open(url),
        )
        btn.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="e")

        btn_x = ctk.CTkButton(
            banner,
            text="×",
            width=28,
            height=28,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            hover_color=colors.SIDEBAR_HOVER,
            command=lambda: self._hide_update_banner(),
        )
        btn_x.grid(row=0, column=2, padx=(0, 12), pady=10, sticky="e")

        self._update_banner = banner

    def _hide_update_banner(self):
        """Retira el aviso y libera los widgets que contiene."""
        try:
            if hasattr(self, "_update_banner") and self._update_banner is not None and self._update_banner.winfo_exists():
                self._update_banner.destroy()
        except Exception:
            logger.exception("updates: no se pudo ocultar banner")
        self._update_banner = None
    
    def show_module(self, key):
        """
        Muestra el modulo seleccionado en el area de contenido.
        
        Si el frame del modulo no existe aun, lo crea bajo demanda
        (lazy loading) para mejorar el rendimiento de inicio.
        
        Args:
            key: Identificador del modulo a mostrar.
        """
        # Verificar que la key exista en los frames
        if key not in self.frames:
            return

        self._navigation_revision = getattr(self, '_navigation_revision', 0) + 1
        revision = self._navigation_revision
        spec = get_module_spec(key)
        if self._preloader is not None and self.frames[key] is None and spec and spec.preload_ui:
            self._show_module_loading(key, t('startup_module').format(module=t(spec.label_key)))
            def ready(frame):
                """Actualiza el aviso de versión si la consulta terminó con datos válidos."""
                if self._navigation_revision == revision:
                    self._show_view(frame, key=key)
                    self.sidebar.set_active(key)
            def failed(_error):
                """Registra un fallo de consulta sin detener el arranque de la aplicación."""
                if self._navigation_revision == revision:
                    self._loading_label.configure(text=t('startup_module_error'))
            self._preloader.ensure(key, ready, failed)
            return

        if self._preloader is not None and not self._preloader.running:
            self._preloader.pause()

        previous_key = self._active_view_key
        logger.info("navigation: show_module from=%s to=%s", previous_key, key)

        # Crear frame si no existe (lazy loading)
        if self.frames[key] is None:
            spec = get_module_spec(key)
            if not spec:
                return
            
            # Cargar la clase del frame dinamicamente
            cls = load_frame_class(spec)

            # Crear instancia del frame en el area de contenido
            frame = cls(self.content)
            self.frames[key] = frame
            logger.info("navigation: lazy_loaded key=%s frame=%s", key, frame.__class__.__name__)

        # Mostrar unicamente la vista activa
        self._show_view(self.frames[key], key=key)

        # Actualizar boton activo en la sidebar
        self.sidebar.set_active(key)

    def show_home(self):
        """Vuelve a Inicio al activar el logo del panel lateral."""
        self._navigation_revision = getattr(self, '_navigation_revision', 0) + 1
        if self._preloader is not None and not self._preloader.running:
            self._preloader.pause()
        self._show_view(self._home, key=None)
        self.sidebar.set_active(None)

    def _show_module_loading(self, key, text):
        """Muestra progreso mientras se prepara el módulo solicitado."""
        if not hasattr(self, '_loading_view'):
            self._loading_view = ctk.CTkFrame(self.content, fg_color=colors.FRAMES_BG, corner_radius=0)
            self._loading_label = ctk.CTkLabel(self._loading_view, text='',
                text_color=colors.TEXT_GRAY, font=fonts.FUENTE_BASE, wraplength=360, justify='center')
            self._loading_label.place(relx=.5, rely=.5, anchor='center')
        self._loading_label.configure(text=text)
        self._show_view(self._loading_view, key=key)
        self.sidebar.set_active(key)

    def show_preload_errors(self, labels):
        """Expone errores de precarga sin impedir abrir otros módulos."""
        self._home.show_preload_errors(labels)

    def _show_view(self, view, key):
        """Oculta la vista activa y muestra la nueva de forma explicita."""
        if self._active_view is view and self._active_view_key == key:
            logger.info("navigation: view already active key=%s", key)
            return

        previous_view = self._active_view
        previous_key = self._active_view_key

        if previous_view is not None:
            self._hide_view(previous_view, previous_key)

        host = self._get_view_host(view)
        host.place(x=0, y=0, relwidth=1, relheight=1)
        try:
            host.lift()
        except Exception:
            logger.debug("navigation: no se pudo elevar vista key=%s", key, exc_info=True)

        self._active_view = view
        self._active_view_key = key
        self._notify_view_shown(view)
        logger.info("navigation: activated key=%s host=%s", key, type(host).__name__)

    def _hide_view(self, view, key):
        """Oculta una vista existente sin destruirla."""
        host = self._get_view_host(view)
        self._notify_view_hidden(view)
        try:
            host.place_forget()
            logger.info("navigation: hidden key=%s host=%s", key, type(host).__name__)
        except Exception:
            logger.exception("navigation: no se pudo ocultar key=%s", key)
        finally:
            if self._active_view is view:
                self._active_view = None
                self._active_view_key = None

    @staticmethod
    def _get_view_host(view):
        """Retorna el widget visual que se placea para una vista."""
        return getattr(view, "_parent_frame", view)

    @staticmethod
    def _notify_view_shown(view):
        """Notifica al frame visible que puede reanudar previews y timers."""
        callback = getattr(view, "on_view_shown", None)
        if callable(callback):
            try:
                callback()
            except Exception:
                logger.exception("navigation: error en on_view_shown para %s", type(view).__name__)

    @staticmethod
    def _notify_view_hidden(view):
        """Informa al módulo que dejó de estar visible para pausar previews."""
        callback = getattr(view, "on_view_hidden", None)
        if callable(callback):
            try:
                callback()
            except Exception:
                logger.exception("navigation: error en on_view_hidden para %s", type(view).__name__)
