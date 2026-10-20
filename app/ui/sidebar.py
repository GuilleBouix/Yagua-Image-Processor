"""
Barra lateral de navegacion de la aplicacion.
Contiene el menu de modulos disponibles.

Relacionado con:
    - app/ui/main_window.py: Contiene e integra esta sidebar.
    - app/ui/module_registry.py: Provee la lista de modulos habilitados.
    - app/ui/colors.py: Colores del tema actual.
    - app/ui/fonts.py: Fuentes de texto.
    - app/utils/__init__.py: Tintar iconos con colores del tema.
    - app/translations/__init__.py: Traducciones de labels.
"""

from app.ui.building import finish, stepwise, steps_for
import logging
import webbrowser
from PIL import Image
import customtkinter as ctk

from app.ui import colors, fonts
from app.utils import tintar_icono
from app.utils.paths import resource_path
from app.translations import t
from app.ui.module_registry import iter_enabled_modules

# URL de donacion (PayPal)
DONATION_URL = 'https://paypal.me/guillebouix?locale.x=es_XC&country.x=AR'


logger = logging.getLogger(__name__)

# URL del repositorio de GitHub
GITHUB_URL = 'https://github.com/GuilleBouix'

# Tamano maximo del logo en la parte superior
LOGO_SIZE = 135


class Sidebar(ctk.CTkFrame):
    """
    Barra lateral con botones de navegacion.
    
    Muestra el logo de la app, una lista de modulos disponibles
    y un enlace al repositorio de GitHub.
    """
    
    def __init__(self, parent, on_select, *, defer_build=False):
        """
        Inicializa la barra lateral.
        
        Args:
            parent: Widget padre.
            on_select: Callback llamado cuando se selecciona un modulo.
        """
        super().__init__(
            parent,
            width=220,
            corner_radius=0,
            fg_color=colors.SIDEBAR_BG
        )
        
        # Guardar callback para navegacion entre modulos
        self.on_select = on_select
        self._active_key = None
        self.on_home = None
        
        # Diccionario para guardar referencias a los botones
        self.buttons = {}
        
        # Construir la estructura de la sidebar
        self._build_iterator = steps_for(self._build)
        if not defer_build:
            finish(self._build_iterator)

    @stepwise
    def _build(self):
        """
        Construye los elementos de la barra lateral.
        
        Incluye logo, separador, botones de navegacion
        y footer con enlace a GitHub.
        """
        # Cargar imagen del logo
        ruta_icono = resource_path('assets/icon.png')
        yield
        try:
            imagen = Image.open(ruta_icono).convert('RGBA')
            yield
        except Exception as exc:
            # Usar imagen vacia si no se puede cargar el logo
            logger.warning("No se pudo cargar el logo: %s", exc)
            yield
            imagen = None
            yield
        
        # Calcular tamano proporcional del logo
        if imagen:
            w, h = imagen.size
            yield
            if w > h:
                new_size = (LOGO_SIZE, int(h * LOGO_SIZE / w))
                yield
            else:
                new_size = (int(w * LOGO_SIZE / h), LOGO_SIZE)
                yield
            
            # Crear imagen para CTk
            imagen_ctk = ctk.CTkImage(
                light_image=imagen,
                dark_image=imagen,
                size=new_size
            )
            yield
            logo = ctk.CTkLabel(self, image=imagen_ctk, text='')
            yield
        else:
            logo = ctk.CTkLabel(self, text='')
            yield
        self.logo = logo
        yield
        logo.pack(pady=(20, 10))
        yield
        logo.configure(cursor='hand2')
        yield
        logo.bind('<Button-1>', lambda _event: self.on_home() if callable(self.on_home) else None)
        yield

        # Crear linea separadora
        separador = ctk.CTkFrame(
            self,
            height=2,
            fg_color=colors.SIDEBAR_SEPARATOR
        )
        yield
        separador.pack(fill='x', padx=20, pady=(10, 20))
        yield

        specs = list(iter_enabled_modules())
        yield
        if len(specs) > 1:
            # Contenedor scrollable solo si hay mas de un modulo
            self._modules_container = ctk.CTkScrollableFrame(
                self,
                fg_color='transparent',
                corner_radius=0,
                scrollbar_fg_color=colors.SIDEBAR_BG,
                scrollbar_button_color=colors.SIDEBAR_SEPARATOR,
                scrollbar_button_hover_color=colors.SIDEBAR_HOVER
            )
            yield
        else:
            self._modules_container = ctk.CTkFrame(self, fg_color='transparent', corner_radius=0)
            yield
        self._modules_container.pack(fill='both', expand=True, padx=0, pady=(0, 10))
        yield

        # Crear botones para cada modulo habilitado
        for spec in specs:
            # Tintar icono con el color del tema
            icon_ctk = tintar_icono(spec.icon_path, colors.ICON_COLOR)
            yield
            
            # Obtener label traducible
            label = t(spec.label_key)
            yield
            
            # Crear boton del modulo
            btn = ctk.CTkButton(
                self._modules_container,
                text=f' {label}',
                image=icon_ctk,
                compound='left',
                width=200,
                fg_color='transparent',
                hover_color=colors.SIDEBAR_HOVER,
                text_color=colors.TEXT_COLOR,
                anchor='w',
                font=fonts.FUENTE_BASE,
                command=lambda k=spec.key: self.on_select(k)
            )
            yield
            btn.pack(pady=3, padx=10, fill='x')
            yield
            
            # Guardar referencia al boton para actualizar estado
            self.buttons[spec.key] = {'btn': btn, 'icon_path': spec.icon_path}
            yield

        # Crear footer con enlace a GitHub
        self._frame_footer = ctk.CTkFrame(self, fg_color='transparent')
        yield
        self._frame_footer.pack(side='bottom', pady=(0, 10), fill='x', padx=10)
        yield
        self._frame_footer.grid_columnconfigure((0, 1), weight=1)
        yield

        # Label "Developed by"
        ctk.CTkLabel(
            self._frame_footer,
            text=t('developed_by'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor='e'
        ).grid(row=0, column=0, sticky='e')
        yield

        # Label clickeable de GitHub
        lbl_link = ctk.CTkLabel(
            self._frame_footer,
            text=t('github'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.ACENTO,
            cursor='hand2',
            anchor='w'
        )
        yield
        lbl_link.grid(row=0, column=1, sticky='w')
        yield
        
        # Abrir GitHub al hacer clic
        lbl_link.bind('<Button-1>', lambda _: webbrowser.open(GITHUB_URL))
        yield

        # Boton de donacion
        icon_donar = tintar_icono('assets/icons/heart.png', '#FFFFFF')
        yield
        btn_donar = ctk.CTkButton(
            self._frame_footer,
            text=t('donate'),
            image=icon_donar,
            compound='left',
            width=120,
            height=28,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.SIDEBAR_BG,
            text_color=colors.TEXT_COLOR,
            hover_color=colors.SIDEBAR_HOVER,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            command=lambda: webbrowser.open(DONATION_URL)
        )
        yield
        btn_donar.grid(row=1, column=0, columnspan=2, pady=(8, 0), sticky='ew')
        yield

    def set_active(self, key):
        """
        Marca el boton activo segun el modulo seleccionado.
        
        Cambia el color del boton y su icono para indicar
        cual es el modulo actualmente visible.
        
        Args:
            key: Identificador del modulo activo.
        """
        if self._active_key == key:
            return
        previous, self._active_key = self._active_key, key
        # Unchanged buttons already have their inactive style. Recreating all
        # eleven PhotoImages here causes a visible X11 pause at startup.
        for module_key in (previous, key):
            data = self.buttons.get(module_key)
            if data is None:
                continue
            btn = data['btn']
            icon_path = data['icon_path']
            
            if module_key == key:
                # Estilo para boton activo
                icon_ctk = tintar_icono(icon_path, colors.ICON_COLOR_ACTIVE)
                btn.configure(
                    fg_color=colors.SIDEBAR_ACTIVE,
                    hover_color=colors.SIDEBAR_ACTIVE_HOVER,
                    text_color=colors.TEXT_ACTIVE,
                    image=icon_ctk
                )
            else:
                # Estilo para botones inactivos
                icon_ctk = tintar_icono(icon_path, colors.ICON_COLOR)
                btn.configure(
                    fg_color='transparent',
                    hover_color=colors.SIDEBAR_HOVER, 
                    text_color=colors.TEXT_COLOR,
                    image=icon_ctk
                )
