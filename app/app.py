"""
AplicaciÃ³n principal Yagua.
Contiene la clase principal que inicializa la ventana y componentes.
"""

import logging
import sys
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk

from app.ui import fonts
from app.ui.main_window import MainWindow
from app.translations import t

logger = logging.getLogger(__name__)


class YaguaApp(ctk.CTk):
    """Ventana principal de la aplicaciÃ³n Yagua."""
    
    def __init__(self):
        super().__init__()
        fonts.inicializar_fuentes()
        self.title(t('app_title'))
        self.geometry('1000x500')
        self.update()
        self.state('zoomed')
        self.minsize(900, 600)
        self._setup_icon()
        self.main_window = MainWindow(self)
        self.main_window.pack(fill='both', expand=True)
    
    def _setup_icon(self):
        """Configura el icono de la ventana segÃºn la plataforma."""
        icon_ico = Path('assets/icon.ico')
        icon_png = Path('assets/icon.png')
        
        if sys.platform == 'win32':
            if icon_ico.exists():
                self.iconbitmap(str(icon_ico))
            elif icon_png.exists():
                self._setup_icon_png(icon_png)
            else:
                logger.warning("Icono no encontrado en assets/")
        else:
            if icon_png.exists():
                self._setup_icon_png(icon_png)
            elif icon_ico.exists():
                logger.warning("icon.ico no es compatible con esta plataforma")
            else:
                logger.warning("Icono no encontrado en assets/")
    
    def _setup_icon_png(self, icon_path: Path):
        """Configura el icono desde archivo PNG."""
        try:
            img = Image.open(icon_path).convert('RGBA')
            img_tk = ImageTk.PhotoImage(img)
            self.iconphoto(True, img_tk)  # type: ignore[arg-type]
        except Exception as e:
            logger.warning(f"Error al cargar icono: {e}")
