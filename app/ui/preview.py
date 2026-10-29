"""Previews acotadas y reutilizables para Redimensionar y Quitar Fondo.

Los workers sólo manejan píxeles; el hilo Tk crea los recursos gráficos.
Relacionado con image_cache, rendering.StableRender y resize_geometry.
Los contratos y límites están en docs/PREVIEWS_AND_BACKGROUND.md.
"""
from pathlib import Path
from threading import Thread

import customtkinter as ctk
from PIL import Image, ImageDraw

from app.modules.resize_geometry import fit_size, resize_size, centered_crop, canvas_geometry
from app.modules.resize import compose_canvas
from app.translations import t
from app.ui import fonts, styles
from app.ui.image_cache import image_cache
from app.ui.lifetime import UiLifetime
from app.ui.operations import operations
from app.ui.rendering import StableRender, configure_changed


def render_pixels(source, bounds, spec, checker_colors):
    """Compone geometría y damero a tamaño de viewport, sin lienzos completos.

    spec describe original, resize, crop o canvas con parámetros capturados
    en Tk. Devuelve píxeles reducidos, dimensiones originales y finales.
    Debe ejecutarse fuera de Tk; el remuestreo reducido no simula la codificación.
    """
    original = source.oriented_dimensions or source.dimensions
    image = source.image
    kind = spec.get('kind', 'original')
    output = original
    box = None
    if kind == 'resize':
        output = resize_size(original, **spec['options'])
    elif kind == 'crop':
        logical_box = centered_crop(original, spec.get('ratio'), dimensions=spec.get('dimensions'))
        output = logical_box[2] - logical_box[0], logical_box[3] - logical_box[1]
        coordinates = tuple(round(value * image.size[i % 2] / original[i % 2])
                            for i, value in enumerate(logical_box))
        box = (coordinates[0], coordinates[1], max(coordinates[0] + 1, coordinates[2]),
               max(coordinates[1] + 1, coordinates[3]))
    elif kind == 'canvas':
        output = spec['size']
    if min(output) < 1:
        raise ValueError('invalid_dimensions')
    display = fit_size(output, bounds)
    if kind == 'canvas':
        fitted, offset = canvas_geometry(original, output)
        scale = display[0] / output[0], display[1] / output[1]
        placed_size = tuple(max(1, min(display[i], round(fitted[i] * scale[i]))) for i in (0, 1))
        position = round(offset[0] * scale[0]), round(offset[1] * scale[1])
        background = spec['background']
        placed = image.resize(placed_size, Image.Resampling.LANCZOS)
        rendered = compose_canvas(placed, display, position, background)
    else:
        cropped = image.crop(box) if box is not None else image
        rendered = cropped.resize(display, Image.Resampling.LANCZOS)
    checker = Image.new('RGB', display, checker_colors[0])
    draw = ImageDraw.Draw(checker)
    for y in range(0, display[1], 12):
        for x in range(0, display[0], 12):
            if (x // 12 + y // 12) % 2:
                draw.rectangle((x, y, x + 11, y + 11), fill=checker_colors[1])
    checker.paste(rendered, (0, 0), rendered.getchannel('A'))
    return checker, original, output


class LivePreview(UiLifetime, ctk.CTkFrame):
    """Conserva el viewport y acepta sólo el render de la revisión vigente."""

    def __init__(self, parent, *, settle=None):
        palette = styles.palette()
        super().__init__(parent, fg_color='transparent', corner_radius=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.path = ''
        self.spec = {}
        self.revision = 0
        self.photo = None
        self.output_dimensions = None
        self.applied_path = ''
        self._working = False
        self._settle = settle
        self._last_key = None
        self._error = ''
        self.note = ''
        self._debounce = None
        self._checker_colors = (palette.inset, palette.border)
        self.name = ctk.CTkLabel(self, text='', width=1, anchor='w', font=fonts.FUENTE_BASE)
        self.name.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        self.viewport = ctk.CTkFrame(self, height=280, width=1, corner_radius=0, fg_color=palette.inset)
        self.viewport.grid(row=1, column=0, sticky='nsew')
        self.viewport.grid_propagate(False)
        self.image = ctk.CTkLabel(self.viewport, text=t('preview_empty'), width=1, height=1,
                                 font=fonts.FUENTE_CHICA, text_color=palette.muted, justify='center')
        self.image.place(relwidth=1, relheight=1)
        self.info = ctk.CTkLabel(self, text='', width=1, anchor='w', font=fonts.FUENTE_CHICA,
                                text_color=palette.muted)
        self.info.grid(row=2, column=0, sticky='ew', pady=(8, 0))
        self.renderer = StableRender(self, self.viewport, self._render)
        self.viewport.bind('<Configure>', self._wrap, add=True)

    def _wrap(self, event):
        """Ajusta textos al ancho disponible sin cambiar el tamaño del viewport."""
        width = max(1, int(event.width / self._get_widget_scaling()) - 24)
        for label in (self.name, self.image, self.info):
            configure_changed(label, wraplength=width)

    def _clear_pixels(self, message):
        """Libera recursos Tk para no mostrar una imagen anterior como vigente."""
        self.image.configure(image=None, text=message)
        self.image._label.configure(image='')
        self.photo = None
        self.output_dimensions = None
        self.applied_path = ''

    def show(self, path='', spec=None, *, title='', error='', note='', debounce=0, force=False):
        """Captura selección/configuración e invalida entregas anteriores desde Tk.

        force fuerza relectura tras recargas o guardados; debounce agrupa entradas.
        error impide renderizar un resultado inválido, note acompaña datos válidos.
        """
        spec = spec or {}
        if not force and self.path == path and self.spec == spec and self._error == error:
            self.renderer.request()
            return
        self.path, self.spec = str(path), spec
        self._error = error
        self.note = note
        self.revision += 1
        self._last_key = None
        if self._debounce:
            self.after_cancel(self._debounce)
            self._debounce = None
        self.name.configure(text=(f'{title} · ' if title and path else '') + (Path(path).name if path else ''))
        self.info.configure(text='')
        self._clear_pixels(error or t('processing' if path else 'preview_empty'))
        if not path or error:
            self.renderer.cancel()
            return
        if debounce:
            self._debounce = self.after(debounce, self._request)
        else:
            self.renderer.request()

    def _request(self):
        """Solicita render después de completar el debounce de los controles."""
        self._debounce = None
        self.renderer.request()

    def set_visible(self, visible):
        """Suspende timers y descarta resultados de workers al ocultar la vista."""
        if not visible:
            self.revision += 1
            if self._debounce:
                self.after_cancel(self._debounce)
                self._debounce = None
        self.renderer.set_visible(visible)

    def _render(self, measurements):
        """Captura medidas estables y lanza como máximo un worker de píxeles."""
        if self._settle is not None and self._settle():
            self.renderer.request()
            return
        if self._working or not self.path or self._debounce or self._error:
            return
        width, height, scale = measurements
        bounds = (max(1, min(1024, int(width / scale) - 24)),
                  max(1, min(1024, int(height / scale) - 24)))
        key = (self.revision, self.path, bounds, scale)
        if self._last_key == key:
            return
        self._working = True
        path, spec, checker = self.path, self.spec, self._checker_colors

        def work():
            try:
                source = image_cache.load(path, (1024, 1024), mode='RGBA')
                result, error = render_pixels(source, bounds, spec, checker), None
            except Exception as exc:
                result, error = None, exc
            operations.post(self, lambda: self._loaded(key, result, error))
        Thread(target=work, daemon=True, name='yagua-preview').start()

    def _loaded(self, key, result, error):
        """Publica en Tk sólo si coinciden archivo, revisión, medidas y escala."""
        self._working = False
        scale = self.viewport._get_widget_scaling()
        bounds = (max(1, min(1024, int(self.viewport.winfo_width() / scale) - 24)),
                  max(1, min(1024, int(self.viewport.winfo_height() / scale) - 24)))
        if key[0] != self.revision or key[2:] != (bounds, scale) or not self.renderer.enabled:
            self.renderer.request()
            return
        self._last_key = key
        if error or result is None:
            message = str(error)
            self._clear_pixels(t(message if message in ('crop_too_large', 'invalid_dimensions') else 'preview_error'))
            return
        pixels, original, output = result
        self.photo = ctk.CTkImage(light_image=pixels, dark_image=pixels, size=pixels.size)
        self.image.configure(image=self.photo, text='')
        self.output_dimensions, self.applied_path = output, key[1]
        self.info.configure(text=t('preview_dimensions').format(width=original[0], height=original[1],
                           out_width=output[0], out_height=output[1]) + (' · ' + self.note if self.note else ''))
        self.renderer.request()
