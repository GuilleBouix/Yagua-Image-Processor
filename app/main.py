"""
Punto de entrada principal de la aplicación Yagua.
Configura el tema de CustomTkinter e inicia la aplicación.
"""

import customtkinter as ctk

from app.app import YaguaApp


def main():
    """Inicializa y ejecuta la aplicación principal."""
    ctk.set_appearance_mode('dark')
    ctk.set_default_color_theme('blue')
    
    app = YaguaApp()
    app.mainloop()


if __name__ == '__main__':
    main()
