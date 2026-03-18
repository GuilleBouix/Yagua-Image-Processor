"""
UI Frames - Modulos de interfaz de usuario.
Contiene todos los frames de cada modulo de la aplicacion.

Relacionado con:
    - app/ui/main_window.py: Instancia estos frames segun el modulo seleccionado.
    - app/ui/frames/base.py: Clase base de la que heredan los frames.
    - app/ui/frames/compress/: Modulo de compresion de imagenes.
    - app/ui/frames/convert/: Modulo de conversion de formatos.
    - app/ui/frames/metadata/: Modulo de metadatos EXIF.
    - app/ui/frames/palette/: Modulo de paleta de colores.
    - app/ui/frames/resize/: Modulo de redimensionado.
    - app/ui/frames/settings/: Modulo de configuracion.
    - app/ui/frames/placeholder_frame.py: Placeholder generico.
    - app/ui/frames/rename_frame.py: Placeholder de renombrar.
    - app/ui/frames/remove_bg_frame.py: Placeholder de quitar fondo.
    - app/ui/frames/lqip_frame.py: Placeholder de LQIP.
"""

from app.ui.frames.compress import CompressFrame
from app.ui.frames.convert import ConvertFrame
from app.ui.frames.metadata import MetadataFrame
from app.ui.frames.palette import PaletteFrame
from app.ui.frames.placeholder_frame import PlaceholderFrame
from app.ui.frames.resize import ResizeFrame
from app.ui.frames.settings import SettingsFrame
