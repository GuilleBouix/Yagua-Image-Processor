"""
Punto de entrada principal de la aplicacion Yagua.
Configura el tema de CustomTkinter e inicia la aplicacion.

Relacionado con:
    - app/app.py: Contiene la clase YaguaApp que se instancia aqui.
    - app/ui/colors.py: Define los temas visuales de la app.
"""

import customtkinter as ctk

from app.app import YaguaApp


def main():
    """
    Inicializa y ejecuta la aplicacion principal.
    
    Configura CustomTkinter en modo oscuro con tema azul,
    luego crea y ejecuta la ventana principal.
    """
    # Establecer modo oscuro para toda la interfaz
    ctk.set_appearance_mode('dark')
    
    # Establecer tema de color azul para elementos interactivos
    ctk.set_default_color_theme('blue')
    
    # Crear instancia de la aplicacion principal
    app = YaguaApp()
    
    # Iniciar el loop principal de la interfaz
    app.mainloop()


if __name__ == '__main__':
    main()
