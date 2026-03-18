"""
Barra lateral de navegaciÃ³n de la aplicaciÃ³n.
Contiene el menÃº de mÃ³dulos disponibles.
"""

import logging
import webbrowser
from pathlib import Path
from PIL import Image
import customtkinter as ctk
from app.ui import colors, fonts
from app.utils import tintar_icono
from app.translations import t
from app.ui.module_registry import iter_enabled_modules

logger = logging.getLogger(__name__)

GITHUB_URL = 'https://github.com/GuilleBouix'

LOGO_SIZE = 135

class Sidebar(ctk.CTkFrame):
    """Barra lateral con botones de navegaciÃ³n."""  
    def __init__(self, parent, on_select):
        super().__init__(
            parent,
            width=160,
            corner_radius=0,
            fg_color=colors.SIDEBAR_BG
        )
        
        self.on_select = on_select
        self.buttons = {}
        self._build()

    def _build(self):
        """Construye los elementos de la barra lateral."""

        ruta_icono = Path('assets/icon_2.png')
        try:
            imagen = Image.open(ruta_icono).convert('RGBA')
        except Exception as exc:
            logger.warning("No se pudo cargar el logo: %s", exc)
            imagen = None
        
        if imagen:
            w, h = imagen.size
            if w > h:
                new_size = (LOGO_SIZE, int(h * LOGO_SIZE / w))
            else:
                new_size = (int(w * LOGO_SIZE / h), LOGO_SIZE)
            
            imagen_ctk = ctk.CTkImage(
                light_image=imagen,
                dark_image=imagen,
                size=new_size
            )
            logo = ctk.CTkLabel(self, image=imagen_ctk, text='')
        else:
            logo = ctk.CTkLabel(self, text='')
        logo.pack(pady=(20, 10))

        separador = ctk.CTkFrame(
            self,
            height=2,
            fg_color=colors.SIDEBAR_SEPARATOR
        )
        separador.pack(fill='x', padx=20, pady=(10, 20))

        for spec in iter_enabled_modules():
            icon_ctk = tintar_icono(spec.icon_path, colors.ICON_COLOR)
            label = t(spec.label_key)
            
            btn = ctk.CTkButton(
                self,
                text=f' {label}',
                image=icon_ctk,
                compound='left',
                width=150,
                fg_color='transparent',
                hover_color=colors.SIDEBAR_HOVER,
                text_color=colors.TEXT_COLOR,
                anchor='w',
                font=fonts.FUENTE_BASE,
                command=lambda k=spec.key: self.on_select(k)
            )
            btn.pack(pady=3, padx=10, fill='x')
            
            self.buttons[spec.key] = {'btn': btn, 'icon_path': spec.icon_path}

        # Developed by - enlace al final
        self._frame_footer = ctk.CTkFrame(self, fg_color='transparent')
        self._frame_footer.pack(side='bottom', pady=(0, 10), fill='x', padx=10)
        self._frame_footer.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(
            self._frame_footer,
            text=t('developed_by'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor='e'
        ).grid(row=0, column=0, sticky='e')

        lbl_link = ctk.CTkLabel(
            self._frame_footer,
            text=t('github'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.ACENTO,
            cursor='hand2',
            anchor='w'
        )
        lbl_link.grid(row=0, column=1, sticky='w')
        lbl_link.bind('<Button-1>', lambda _: webbrowser.open(GITHUB_URL))

    def set_active(self, key):
        """Marca el boton activo segun el modulo seleccionado."""
        for k, data in self.buttons.items():
            btn = data['btn']
            icon_path = data['icon_path']
            
            if k == key:
                icon_ctk = tintar_icono(icon_path, colors.ICON_COLOR_ACTIVE)
                btn.configure(
                    fg_color=colors.SIDEBAR_ACTIVE,
                    hover_color=colors.SIDEBAR_ACTIVE_HOVER,
                    text_color=colors.TEXT_ACTIVE,
                    image=icon_ctk
                )
            else:
                icon_ctk = tintar_icono(icon_path, colors.ICON_COLOR)
                
                btn.configure(
                    fg_color='transparent',
                    hover_color=colors.SIDEBAR_HOVER, 
                    text_color=colors.TEXT_COLOR,
                    image=icon_ctk
                )
