"""
Barra lateral de navegación de la aplicación.
Contiene el menú de módulos disponibles.
"""

from pathlib import Path
from PIL import Image
import customtkinter as ctk
from ui import colors, fonts


def tintar_icono(ruta_icono: str, color_hex: str) -> ctk.CTkImage:
    img = Image.open(ruta_icono).convert('RGBA')
    
    if color_hex:
        r, g, b = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        r_ch, g_ch, b_ch, a_ch = img.split()
        r_ch = r_ch.point(lambda _: r)
        g_ch = g_ch.point(lambda _: g)
        b_ch = b_ch.point(lambda _: b)
        img = Image.merge('RGBA', (r_ch, g_ch, b_ch, a_ch))

    return ctk.CTkImage(light_image=img, dark_image=img, size=(18, 18))

MENU_ITEMS = [
    ('compress', 'Comprimir', 'assets/icons/compress.png'),
    ('convert', 'Convertir', 'assets/icons/convert.png'),
    ('remove_bg', 'Quitar Fondo', 'assets/icons/remove_background.png'),
    ('resize', 'Redimensionar', 'assets/icons/resize.png'),
    ('rename', 'Renombrar Lote', 'assets/icons/rename.png'),
    ('palette', 'Extraer Paleta', 'assets/icons/palette.png'),
    ('watermark', 'Marca de Agua', 'assets/icons/watermark.png'),
    ('metadata', 'Metadatos EXIF', 'assets/icons/metadata.png'),
    ('lqip', 'LQIP / Base64', 'assets/icons/lqip.png'),
    ('optimizer', 'Optimizador', 'assets/icons/optimizer.png'),
]


class Sidebar(ctk.CTkFrame):
    """Barra lateral con botones de navegación."""
    
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

        ruta_icono = Path('assets/icon.png')
        imagen = Image.open(ruta_icono).convert('RGBA')
        
        imagen_ctk = ctk.CTkImage(
            light_image=imagen,
            dark_image=imagen,
            size=(60, 60)
        )
        
        logo = ctk.CTkLabel(self, image=imagen_ctk, text='')
        logo.pack(pady=(20, 10))

        separador = ctk.CTkFrame(
            self,
            height=2,
            fg_color=colors.SIDEBAR_SEPARATOR
        )
        separador.pack(fill='x', padx=20, pady=(10, 20))

        for key, label, icon_path in MENU_ITEMS:
            icon_ctk = tintar_icono(icon_path, colors.ICON_COLOR)
            
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
                command=lambda k=key: self.on_select(k)
            )
            btn.pack(pady=3, padx=10, fill='x')
            
            self.buttons[key] = {'btn': btn, 'icon_path': icon_path}

    def set_active(self, key):
        """Marca el botón activo según el módulo seleccionado."""
        for k, data in self.buttons.items():
            btn = data['btn']
            icon_path = data['icon_path']
            
            if k == key:
                icon_ctk = tintar_icono(icon_path, colors.ICON_COLOR_ACTIVE)
                btn.configure(
                    fg_color=colors.SIDEBAR_ACTIVE,
                    hover_color='#E5E5EA',  
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