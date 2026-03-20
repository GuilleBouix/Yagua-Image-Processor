"""
Traducciones al Espanol.
Diccionario de textos para la interfaz en idioma espanol.

Relacionado con:
    - app/translations/__init__.py: Sistema de traducciones.
    - app/translations/en.py: Traducciones en ingles (referencia).
    - app/translations/pt.py: Traducciones en portugues.

Este archivo contiene todas las claves de traduccion usadas
en la aplicacion organizadas por seccion:
    - App: Titulo general de la aplicacion.
    - Sidebar: Labels de navegacion.
    - Comprimir: Modulo de compresion.
    - Convert: Modulo de conversion.
    - Palette: Modulo de paleta de colores.
    - Metadata: Modulo de metadatos EXIF.
    - Resize: Modulo de redimensionado.
    - Settings: Modulo de configuracion.
"""

TRANSLATIONS = {
    # App
    'app_title': 'Yagua - Procesador de Imagenes',
    
    # Sidebar
    'compress': 'Comprimir',
    'convert': 'Convertir',
    'remove_bg': 'Quitar Fondo',
    'resize': 'Redimensionar',
    'rename': 'Renombrar Lote',
    'palette': 'Extraer Paleta',
    'watermark': 'Marca de Agua',
    'metadata': 'Metadatos EXIF',
    'lqip': 'LQIP / Base64',
    'optimizer': 'Optimizador',
    'settings': 'Ajustes',
    'developed_by': 'Developed by ',
    'github': '@bouix.dev',
    
    # Comprimir
    'compress_title': 'Comprimir',
    'select_images': 'Seleccionar imagenes',
    'no_images': 'Sin imagenes cargadas',
    'quality': 'Calidad',
    'remove_exif': 'Quitar EXIF',
    'compress_btn': 'Comprimir',
    'clean': 'Limpiar',
    'compressing': 'Comprimiendo...',
    'load_images_first': 'Carga al menos una imagen.',
    'select_output_folder': 'Elegi carpeta de salida',
    'estimated': 'estimado',
    'images_loaded': 'imagenes',
    'image_loaded': 'imagen',
    'compressed': 'mas pequeno',
    'error_occurred': 'con error',
    'size_reduction': 'reduccion',
    
    # Convertir
    'convert_title': 'Convertir',
    'convert_to': 'Convertir a',
    'convert_btn': 'Convertir',
    'converting': 'Convirtiendo...',
    'converted_to': 'convertida a',
    'converted_to_plural': 'convertidas a',
    'load_images_first_convert': 'Carga al menos una imagen.',
    
    # Quitar Fondo
    'remove_bg_title':        'Quitar Fondo',
    'background_type':        'Fondo resultante',
    'bg_transparent':         'Transparente',
    'bg_white':               'Blanco',
    'bg_black':               'Negro',
    'bg_custom':              'Custom',
    'custom_color':           'Color',
    'pick_color':             'Elegir',
    'transparency_png_only':  'Transparente exporta como PNG.',
    'remove_bg_btn':          'Quitar fondo',
    'processing':             'Procesando...',
    'processed':              'procesadas',
    'rembg_not_installed':    'rembg no está instalado.\nEjecutá este comando en tu terminal:',
    'model_first_download':   'Modelo u2netp descargado automáticamente al procesar.',
    'output_format':         'Formato de salida',
    'remove_bg_description': 'Elimina el fondo y exporta con transparencia.',

    # Palette
    'palette_title': 'Paleta de colores',
    'colors_to_extract': 'Colores a extraer',
    'load_image_for_palette': 'Carga una imagen para ver la paleta',
    'save_palette': 'Guardar paleta como imagen',
    'save_palette_btn': 'Guardar Paleta de Colores',
    'no_image_selected': 'Sin imagen seleccionada',
    'select_image_for_palette': 'Selecciona una Imagen',
    'colors_extracted': 'colores extraidos',
    'click_format_to_copy': 'haz clic en un formato para copiar',
    'copied': 'Copiado:',
    'save_palette_first': 'Carga una imagen primero',
    'saved_as': 'Guardada como',
    'saving': 'Guardando...',
    'error_generic': 'Error',
    
    # Renombrar
    'rename_title':        'Renombrar Lote',
    'rename_numbering':    'Prefijo + numeración  (foto_001, foto_002...)',
    'rename_prefix':       'Prefijo',
    'rename_start':        'Inicio',
    'rename_replace':      'Reemplazar texto',
    'rename_search':       'Buscar',
    'rename_search_ph':    'texto a buscar',
    'rename_replace_with': 'Reemplazar por',
    'rename_replace_ph':   'texto nuevo',
    'rename_date':         'Agregar fecha',
    'rename_date_position':'Posición',
    'rename_prefix_pos':   'Prefijo',
    'rename_suffix_pos':   'Sufijo',
    'rename_date_format':  'Formato',
    'rename_case':         'Capitalización',
    'rename_case_none':    'Normal',
    'rename_case_lower':   'minúsc.',
    'rename_case_upper':   'MAYÚSC.',
    'rename_clean':        'Quitar espacios y caracteres especiales',
    'rename_preview':      'Preview',
    'rename_btn':          'Renombrar',
    'rename_col_original': 'Nombre original',
    'rename_col_nuevo':    'Nombre nuevo',
    'rename_preview_empty':'Cargá archivos para ver el preview',
    'files_loaded':        'archivos cargados',
    'file_loaded':         'archivo cargado',
    'load_files_first':    'Primero cargá archivos.',
    'renaming':            'Renombrando...',
    'renamed':             'renombrados',
    'rename_conflicts':    'conflictos omitidos',
    

    # Metadata
    'metadata_title': 'Metadatos EXIF',
    'view': 'Ver',
    'edit': 'Editar',
    'clean_batch': 'Limpiar lote',
    'select_image_view': 'Selecciona una imagen para ver sus metadatos',
    'select_image_edit': 'Selecciona una imagen para editar sus metadatos',
    'select_images_clean': 'Selecciona imagenes para limpiar EXIF',
    'no_metadata': 'Sin metadatos - carga una imagen',
    'no_metadata_image': 'Esta imagen no tiene metadatos EXIF',
    'view_on_maps': 'Ver en Maps',
    'export_txt': 'Exportar en .txt',
    'export_json': 'Exportar en .json',
    'export_metadata': 'Exportar metadatos',
    'reading_metadata': 'Leyendo metadatos...',
    'fields_found': 'campos encontrados',
    'export_metadata_first': 'Carga una imagen primero',
    'exported_as': 'Exportado como',
    'artist': 'Autor',
    'copyright': 'Copyright',
    'software': 'Software',
    'datetime': 'Fecha y hora',
    'enter_field': 'Ingresa {}...',
    'save_changes': 'Guardar cambios',
    'saving_changes': 'Guardando...',
    'saved_as_file': 'Guardado:',
    'error_saving': 'Error al guardar',
    'enter_at_least_one': 'Ingresa al menos un campo para editar.',
    'editing': 'Editando:',
    'select_output_save': 'Guardar imagen editada',
    'images_ready_clean': 'imagenes listas para limpiar',
    'clean_exif': 'Limpiar EXIF',
    'cleaning': 'Limpiando...',
    'cleaned': 'imagenes limpiadas',
    'load_images_first_clean': 'Primero carga imagenes.',
    'select_output_folder_clean': 'Carpeta de salida',
    'without_exif': 'sinexif',
    
    # Resize
    'resize_title': 'Redimensionar',
    'resize_tab': 'Redimensionar',
    'crop_tab': 'Recortar',
    'canvas_tab': 'Canvas',
    'mode': 'Modo',
    'percentage': 'Porcentaje',
    'pixels': 'Pixeles',
    'preset': 'Preset',
    'maintain_aspect': 'Mantener relacion de aspecto',
    'width': 'Ancho',
    'height': 'Alto',
    'size': 'Tamaño',
    'background': 'Fondo',
    'white': 'Blanco',
    'black': 'Negro',
    'transparent': 'Transparente',
    'apply_canvas': 'Aplicar Canvas',
    'processing': 'Procesando...',
    'images_loaded_resize': 'imagenes cargadas',
    'image_loaded_resize': 'imagen cargada',
    'processed': 'procesadas',
    'processed_singular': 'procesada',
    'load_images_first_resize': 'Carga una imagen primero',
    'invalid_dimensions': 'Ingresa ancho y alto validos.',
    'warning_transparency': 'Advertencia: JPG/BMP no soportan transparencia - se usara el color negro.',
    'crop_centered': 'Recorte centrado - la imagen se recorta desde el centro.',
    'redim': 'redim',
    'crop': 'crop',
    'canvas': 'canvas',

    # Settings
    'settings_title': 'Ajustes',
    'language': 'Idioma',
    'select_language': 'Seleccionar idioma',
    'appearance': 'Apariencia',
    'theme': 'Tema',
    'ui_theme': 'Tema de la interfaz',
    'dark': 'Oscuro',
    'light': 'Claro',
    'system': 'Sistema',
    'restart_required': 'Reiniciando aplicacion para aplicar el idioma...',
}
