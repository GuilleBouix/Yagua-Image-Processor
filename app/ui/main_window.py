"""
Ventana principal de la interfaz de usuario.
Contiene la estructura base con barra lateral y area de contenido.

Relacionado con:
    - app/app.py: Crea e integra esta ventana.
    - app/ui/sidebar.py: Barra lateral de navegacion.
    - app/ui/module_registry.py: Registro de modulos disponibles.
    - app/ui/frames/: Frames de cada modulo.
"""

import logging
import threading
import webbrowser
import customtkinter as ctk

from app.ui.sidebar import Sidebar
from app.ui.module_registry import get_module_spec, iter_enabled_modules, load_frame_class
from app.ui import colors, fonts
from app.utils.update_checker import check_latest_stable
from app.version import __version__
from app.ui.frames.home.frame import HomeFrame


logger = logging.getLogger(__name__)


class MainWindow(ctk.CTkFrame):
    """
    Marco principal que contiene la barra lateral y el area de contenido.
    
    Organiza la interfaz en dos areas principales:
        - Sidebar: Barra lateral con botones de navegacion.
        - Content: Area donde se muestran los frames de cada modulo.
    """
    
    def __init__(self, parent):
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

        # Construir la estructura de la ventana
        self._build()
  
    def _build(self):
        """
        Construye los componentes de la ventana principal.
        
        Crea la sidebar con sus botones y el area de contenido
        donde se mostraran los frames de cada modulo.
        """
        # Crear sidebar y posicionar a la izquierda
        self.sidebar = Sidebar(self, on_select=self.show_module)
        self.sidebar.pack(side='left', fill='y')
        
        # Crear area de contenido y posicionar a la derecha
        self.content = ctk.CTkFrame(self, corner_radius=0)
        self.content.pack(side='left', fill='both', expand=True)
        
        # Inicializar slots para frames lazy-loaded
        first_key = None
        for spec in iter_enabled_modules():
            self.frames[spec.key] = None
            if first_key is None:
                first_key = spec.key

        # Pantalla inicial (no aparece en sidebar)
        self._home = HomeFrame(self.content)
        self._show_view(self._home, key=None)
        # Sidebar sin selección activa hasta que el usuario elija un módulo
        try:
            self.sidebar.set_active(None)
        except Exception:
            pass

        # Check de actualizaciones no bloqueante (solo estable) + banner interno.
        self.after(350, self._check_updates_on_startup)

    def _check_updates_on_startup(self):
        def _worker():
            info = check_latest_stable(__version__)
            if not info:
                return
            self.after(0, lambda: self._show_update_banner(info.version, info.release_url))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_update_banner(self, version: str, url: str):
        # Evitar duplicados en la misma sesión.
        if hasattr(self, "_update_banner") and getattr(self, "_update_banner") is not None:
            try:
                if self._update_banner.winfo_exists():
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
        callback = getattr(view, "on_view_shown", None)
        if callable(callback):
            try:
                callback()
            except Exception:
                logger.exception("navigation: error en on_view_shown para %s", type(view).__name__)

    @staticmethod
    def _notify_view_hidden(view):
        callback = getattr(view, "on_view_hidden", None)
        if callable(callback):
            try:
                callback()
            except Exception:
                logger.exception("navigation: error en on_view_hidden para %s", type(view).__name__)
