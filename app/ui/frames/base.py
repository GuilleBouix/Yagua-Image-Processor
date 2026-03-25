"""
Clase base para frames de la aplicacion.
Contiene metodos y componentes comunes reutilizables.

Proporciona la estructura basica de un modulo: header con titulo
y boton limpiar, area de contenido, y footer para informacion.

Relacionado con:
    - app/ui/main_window.py: Instancia los frames que heredan de esta clase.
    - app/ui/frames/compress/frame.py: Override de metodos especificos.
    - app/ui/frames/convert/frame.py: Override de metodos especificos.
    - app/ui/frames/resize/frame.py: Override de metodos especificos.
    - app/ui/frames/palette/frame.py: Override de metodos especificos.
    - app/ui/frames/metadata/frame.py: Override de metodos especificos.
"""

import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image

from app.ui import colors, fonts
from app.utils import tintar_icono
from app.modules.compress import formatear_bytes
from app.translations import t


class BaseFrame(ctk.CTkFrame):
    """
    Clase base para todos los frames de modulos.
    
    Proporciona componentes comunes como header, lista de archivos
    y footer de informacion. Las subclases deben implementar
    _build_content() para agregar su contenido especifico.
    """
    
    def __init__(self, parent, title):
        """
        Inicializa el frame base.
        
        Args:
            parent: Widget padre.
            title: Titulo del modulo para mostrar en el header.
        """
        super().__init__(parent, corner_radius=0, fg_color=colors.FRAMES_BG)
        
        # Titulo del modulo
        self._title = title
        
        # Lista de rutas de imagenes cargadas
        self._imagenes = []
        
        # Lista de thumbnails de imagenes
        self._thumbs = []
        
        # Lista de labels de filas de la lista de archivos
        self._filas_lista = []
        
        # Construir la estructura del frame
        self._build()

    def _build(self):
        """
        Construye la estructura completa del frame.
        
        Llama a los metodos de construccion en orden:
        header, contenido y footer.
        """
        # Configurar columna para ocupar todo el ancho
        self.grid_columnconfigure(0, weight=1)
        
        # Construir cada seccion
        self._build_header()
        self._build_content()
        self._build_footer()

    def _build_header(self):
        """
        Construye el header con titulo y boton limpiar.
        
        Crea una fila en la parte superior con el titulo
        del modulo y un boton para limpiar la seleccion.
        """
        # Frame transparente para la fila del titulo
        fila_titulo = ctk.CTkFrame(self, fg_color='transparent')
        fila_titulo.grid(row=0, column=0, padx=28, pady=(26, 8), sticky='ew')
        fila_titulo.grid_columnconfigure(0, weight=1)

        # Label del titulo
        ctk.CTkLabel(
            fila_titulo,
            text=self._title,
            font=fonts.FUENTE_TITULO,
            text_color=colors.TEXT_COLOR,
            anchor='w'
        ).grid(row=0, column=0, sticky='w')

        # Boton de limpiar
        self._btn_limpiar = ctk.CTkButton(
            fila_titulo,
            text=t('clean'),
            width=80,
            height=30,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.BTN_CLEAR_BG,
            text_color=colors.BTN_CLEAR_TEXT,
            hover_color=colors.BTN_CLEAR_HOVER,
            border_width=0,
            command=self._limpiar
        )
        self._btn_limpiar.grid(row=0, column=1, sticky='e')

    def _build_content(self):
        """
        Construye el contenido especifico del modulo.
        
        Debe ser implementado por las subclases para agregar
        los componentes especificos de cada modulo.
        """
        raise NotImplementedError("Subclasses must implement _build_content")

    def _build_footer(self):
        """
        Construye el footer con label de informacion.
        
        Crea un label donde se mostraran mensajes de estado
        o informacion adicional durante las operaciones.
        """
        self._lbl_info = ctk.CTkLabel(
            self, text='',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )
        self._lbl_info.grid(row=100, column=0, pady=(0, 4))

    def _crear_boton_seleccionar(self, parent, texto=None, comando=None):
        """
        Crea un boton estandar para seleccionar archivos.
        
        Args:
            parent: Widget padre del boton.
            texto: Texto del boton (usa traduccion por defecto).
            comando: Funcion a ejecutar al hacer clic.
            
        Returns:
            Boton CTkButton configurado.
        """
        # Usar comando por defecto si no se especifica
        if comando is None:
            comando = self._explorar
        
        # Usar texto por defecto si no se especifica
        if texto is None:
            texto = t('select_images')

        # Crear y retornar el boton
        return ctk.CTkButton(
            parent,
            text=texto,
            height=40,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            text_color=colors.TEXT_COLOR,
            hover_color=colors.SIDEBAR_HOVER,
            image=tintar_icono('assets/icons/upload.png', colors.ICON_COLOR),
            compound='left',
            command=comando
        )

    def _crear_lista_archivos(self, parent, height=200):
        """
        Crea un frame scrolleable para mostrar lista de archivos.
        
        Args:
            parent: Widget padre del frame.
            height: Altura fija del frame en pixeles.
            
        Returns:
            CTkScrollableFrame configurado.
        """
        # Crear frame scrolleable
        lista = ctk.CTkScrollableFrame(
            parent,
            corner_radius=10,
            fg_color=colors.PANEL_BG,
            height=height
        )
        lista.grid_columnconfigure(0, weight=1)
        return lista

    def _crear_lista_vacia(self, parent):
        """
        Crea un label para mostrar cuando no hay archivos.
        
        Args:
            parent: Widget padre del label.
            
        Returns:
            CTkLabel con mensaje de lista vacia.
        """
        return ctk.CTkLabel(
            parent,
            text=t('no_images'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        )

    def _explorar(self, titulo=None, multi=True):
        """
        Abre un dialogo para seleccionar archivos de imagen.
        
        Args:
            titulo: Titulo del dialogo (usa traduccion por defecto).
            multi: Si es True, permite seleccionar multiples archivos.
        """
        # Usar titulo por defecto si no se especifica
        if titulo is None:
            titulo = t('select_images')
        
        # Seleccion multiple de archivos
        if multi:
            archivos = filedialog.askopenfilenames(
                title=titulo,
                filetypes=[('Imagenes', '*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.avif *.ico')]
            )
            # Cargar las imagenes seleccionadas
            if archivos:
                self._cargar_imagenes(list(archivos))
        else:
            # Seleccion de un solo archivo
            archivo = filedialog.askopenfilename(
                title=titulo,
                filetypes=[('Imagenes', '*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.avif')]
            )
            if archivo:
                self._cargar_imagenes([archivo])

    def _cargar_imagenes(self, rutas):
        """
        Carga una lista de imagenes y muestra sus filas.
        
        Args:
            rutas: Lista de rutas de archivos a cargar.
        """
        # Actualizar lista de imagenes
        self._imagenes = rutas
        self._thumbs.clear()
        self._filas_lista.clear()

        # Limpiar la lista de archivos
        for w in self._lista_frame.winfo_children():
            w.destroy()

        # Agregar fila para cada imagen
        for ruta in rutas:
            self._agregar_fila_archivo(ruta)

        # Cargar thumbnails en segundo plano
        threading.Thread(
            target=self._cargar_thumbs_en_background,
            args=(rutas,),
            daemon=True
        ).start()

    def _agregar_fila_archivo(self, ruta):
        """
        Agrega una fila a la lista con info del archivo.
        
        Args:
            ruta: Ruta del archivo a mostrar.
        """
        p = Path(ruta)
        
        # Crear frame para la fila
        fila = ctk.CTkFrame(
            self._lista_frame, fg_color=colors.SIDEBAR_BG, corner_radius=8
        )
        fila.pack(fill='x', pady=3, padx=2)
        fila.grid_columnconfigure(1, weight=1)

        # Label para el thumbnail
        lbl_thumb = ctk.CTkLabel(
            fila, text='', width=44, height=44, fg_color='transparent'
        )
        lbl_thumb.grid(row=0, column=0, padx=(8, 0), pady=6)

        # Frame para la informacion
        info = ctk.CTkFrame(fila, fg_color='transparent')
        info.grid(row=0, column=1, padx=(10, 8), pady=6, sticky='w')

        # Truncar nombre si es muy largo
        nombre = p.name if len(p.name) <= 32 else p.name[:29] + '...'
        
        # Label del nombre
        ctk.CTkLabel(
            info, text=nombre,
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR, anchor='w'
        ).pack(anchor='w')
        
        # Label del tamano y extension
        ctk.CTkLabel(
            info,
            text=f'{formatear_bytes(p.stat().st_size)}  -  {p.suffix.upper().lstrip(".")}',
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY, anchor='w'
        ).pack(anchor='w')

        # Guardar referencia al label del thumbnail
        self._filas_lista.append(lbl_thumb)

    def _cargar_thumbs_en_background(self, rutas):
        """
        Carga thumbnails en segundo plano para no bloquear la UI.
        
        Args:
            rutas: Lista de rutas de archivos para generar thumbnails.
        """
        thumbs = []
        
        # Generar thumbnail para cada archivo
        for ruta in rutas:
            try:
                # Abrir y copiar imagen
                with Image.open(ruta) as img:
                    img = img.copy()
                
                # Redimensionar manteniendo aspecto
                img.thumbnail((44, 44), Image.Resampling.LANCZOS)
                
                # Crear CTkImage
                thumb = ctk.CTkImage(light_image=img, dark_image=img, size=(44, 44))
            except Exception:
                thumb = None
            thumbs.append(thumb)
        
        # Aplicar thumbnails en el hilo principal
        self.after(0, lambda: self._aplicar_thumbs(thumbs))

    def _aplicar_thumbs(self, thumbs):
        """
        Aplica los thumbnails cargados a los labels correspondientes.
        
        Args:
            thumbs: Lista de CTkImage generados.
        """
        # Filtrar thumbnails validos
        self._thumbs = [t for t in thumbs if t]
        
        # Asignar cada thumbnail a su label
        for i, thumb in enumerate(thumbs):
            if thumb and i < len(self._filas_lista):
                self._filas_lista[i].configure(image=thumb)

    def _limpiar(self):
        """
        Limpia la seleccion de imagenes y reinicia el estado.
        
        Elimina todas las imagenes cargadas y restaura
        el label de lista vacia si existe.
        """
        # Reiniciar listas
        self._imagenes = []
        self._thumbs.clear()
        self._filas_lista.clear()
        
        # Destruir todas las filas
        for w in self._lista_frame.winfo_children():
            w.destroy()
        
        # Mostrar label de lista vacia si existe
        if hasattr(self, '_lbl_lista_vacia'):
            self._lbl_lista_vacia.pack(pady=12)
        
        # Limpiar label de informacion
        self._lbl_info.configure(text='')
