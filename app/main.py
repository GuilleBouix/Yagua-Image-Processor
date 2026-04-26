"""
Punto de entrada principal de la aplicacion Yagua.
Configura el tema de CustomTkinter e inicia la aplicacion.

Relacionado con:
    - app/app.py: Contiene la clase YaguaApp que se instancia aqui.
    - app/ui/colors.py: Define los temas visuales de la app.
"""

import logging
import sys

import customtkinter as ctk

from app.app import YaguaApp
from app.ui.scale import apply_ui_scale
from app.utils.settings import settings_path


def main():
    """
    Inicializa y ejecuta la aplicacion principal.
    
    Configura CustomTkinter en modo oscuro con tema azul,
    luego crea y ejecuta la ventana principal.
    """
    # Configurar logging a archivo para diagnostico en exe
    log_path = settings_path().with_name('yagua.log')
    logging.basicConfig(
        filename=str(log_path),
        filemode='a',
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )
    logger = logging.getLogger(__name__)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('customtkinter').setLevel(logging.WARNING)

    # Capturar excepciones no manejadas
    def _excepthook(exc_type, exc, tb):
        logging.getLogger(__name__).exception("Excepcion no manejada", exc_info=(exc_type, exc, tb))
        return sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _excepthook

    # Establecer modo oscuro para toda la interfaz
    ctk.set_appearance_mode('dark')
    
    # Establecer tema de color azul para elementos interactivos
    ctk.set_default_color_theme('blue')

    # Aplicar escala global de la UI antes de crear widgets.
    apply_ui_scale()
    
    # Crear instancia de la aplicacion principal
    app = YaguaApp()
    
    # Iniciar el loop principal de la interfaz
    app.mainloop()


if __name__ == '__main__':
    main()
