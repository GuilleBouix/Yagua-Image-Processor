"""Opt-in visual roles for desktop views. Typography belongs to each caller."""
from dataclasses import dataclass
from typing import Any

import customtkinter as ctk
from PIL import Image

from app.ui import colors


@dataclass(frozen=True)
class Palette:
    """Agrupa colores y tokens visuales compartidos por los módulos."""
    background: str
    panel: str
    inset: str
    border: str
    text: str
    muted: str
    primary: str
    primary_text: str
    primary_hover: str
    hover_border: str
    disabled: str


def contrast(first, second):
    """Calcula la relación de contraste entre dos colores hexadecimales."""
    def luminance(hex_color):
        """Convierte un color sRGB a luminancia relativa para elegir texto legible."""
        values = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
        return sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + .05) / (dark + .05)


def palette():
    """Resuelve los colores al crear el widget y no modifica el tema global de otras vistas."""
    default = colors.get_current_theme() == 'Default'
    primary_text = '#0A0A0B' if default else max(
        (colors.TEXT_ACTIVE, colors.FRAMES_BG, colors.TEXT_COLOR),
        key=lambda candidate: min(contrast(candidate, colors.ACENTO),
                                  contrast(candidate, colors.ACENTO_HOVER)),
    )
    if min(contrast(primary_text, colors.ACENTO), contrast(primary_text, colors.ACENTO_HOVER)) < 4.5:
        primary_text = max(('#000000', '#FFFFFF'), key=lambda candidate: min(
            contrast(candidate, colors.ACENTO), contrast(candidate, colors.ACENTO_HOVER)))
    return Palette(
        colors.FRAMES_BG, colors.PANEL_BG, colors.DROPZONE_BG,
        '#3A3A3C' if default else colors.SIDEBAR_SEPARATOR,
        colors.TEXT_COLOR, colors.TEXT_GRAY, colors.ACENTO,
        primary_text,
        colors.ACENTO_HOVER, '#999999' if default else colors.TEXT_GRAY,
        '#2C2C2E' if default else colors.SIDEBAR_SEPARATOR,
    )


def surface(role) -> dict[str, Any]:
    """Devuelve los colores y bordes del tipo de superficie solicitado."""
    p = palette()
    return dict(corner_radius=0, border_width=1, border_color=p.border,
                fg_color=p.inset if role == 'list' else p.panel)


def scrollbar() -> dict[str, Any]:
    """Devuelve los colores de la barra según el tema vigente."""
    p = palette()
    return dict(scrollbar_fg_color=p.inset,
                scrollbar_button_color='#48484A' if colors.get_current_theme() == 'Default' else colors.ACENTO_DIMMED,
                scrollbar_button_hover_color=p.muted)


class Button(ctk.CTkButton):
    """Primary/secondary roles with reversible disabled, hover and focus states."""
    def __init__(self, parent, *, role='secondary', secondary_bg=None, **kwargs):
        """Configura rol visual, estados de foco y respuesta de teclado del botón."""
        self._design_palette = palette()
        self._design_role = role
        self._design_hover = False
        self._design_focus = False
        p = self._design_palette
        self._design_secondary_bg = secondary_bg or p.background
        kwargs.update(corner_radius=0, border_width=1, border_color=p.border,
                      fg_color=p.primary if role == 'primary' else self._design_secondary_bg,
                      hover_color=p.primary_hover if role == 'primary' else p.panel,
                      text_color=p.primary_text if role == 'primary' else p.text,
                      text_color_disabled=p.muted)
        kwargs.setdefault('height', 40)
        super().__init__(parent, **kwargs)
        self._design_normal_image = self.cget('image')
        self._design_disabled_image = None
        if isinstance(self._design_normal_image, ctk.CTkImage):
            source = self._design_normal_image.cget('light_image').convert('RGBA')
            tinted = Image.new('RGBA', source.size, p.muted)
            tinted.putalpha(source.getchannel('A'))
            self._design_disabled_image = ctk.CTkImage(
                light_image=tinted, dark_image=tinted, size=self._design_normal_image.cget('size'))
        self.bind('<FocusIn>', lambda event=None: self._set_focus(True), add=True)
        self.bind('<FocusOut>', lambda event=None: self._set_focus(False), add=True)
        self.bind('<Return>', lambda event=None: self.invoke(), add=True)
        self.bind('<space>', lambda event=None: self.invoke(), add=True)
        self._canvas.configure(takefocus=1)
        self._paint_state()

    def _set_focus(self, focused):
        """Actualiza el foco accesible y vuelve a pintar el botón."""
        self._design_focus = focused
        self._paint_state()

    def _paint_state(self):
        """Combina rol, foco, hover y estado deshabilitado en los colores del botón."""
        p = self._design_palette
        disabled = self.cget('state') == 'disabled'
        primary = self._design_role == 'primary'
        border = p.primary if primary else p.border
        if disabled:
            border = p.border
        elif self._design_focus:
            border = p.primary_text if primary else p.text
        elif self._design_hover and not primary:
            border = p.hover_border
        super().configure(
            fg_color=p.disabled if disabled else p.primary if primary else self._design_secondary_bg,
            border_color=border,
            border_width=2 if self._design_focus and not disabled else 1,
            hover=not disabled,
        )
        if hasattr(self, '_design_normal_image'):
            image = self._design_disabled_image if disabled else self._design_normal_image
            if self.cget('image') is not image:
                super().configure(image=image)

    def configure(self, require_redraw=False, **kwargs):
        """Sincroniza cambios de estado con la apariencia del botón."""
        state_changed = 'state' in kwargs
        super().configure(require_redraw=require_redraw, **kwargs)
        if state_changed:
            self._design_hover = False
            self._paint_state()

    def _on_enter(self, event=None):
        """Activa el borde de hover al entrar el puntero."""
        self._design_hover = True
        self._paint_state()
        super()._on_enter(event)

    def _on_leave(self, event=None):
        """Retira el borde de hover al salir el puntero."""
        self._design_hover = False
        self._paint_state()
        super()._on_leave(event)


class NavigationButton(Button):
    """Solid navigation states; reserve an outline for keyboard focus only."""
    def _paint_state(self):
        """Conserva el fondo de navegación y reserva el borde para el foco."""
        super()._paint_state()
        if not self._design_focus or self.cget('state') == 'disabled':
            super().configure(border_width=0)

    def set_selected(self, selected, image):
        """Cambia selección, color e icono del acceso de navegación."""
        p = self._design_palette
        self._design_role = 'primary' if selected else 'secondary'
        self._design_normal_image = image
        self.configure(image=image,
                       text_color=p.primary_text if selected else p.text,
                       hover_color=p.primary_hover if selected else p.panel)
        self._paint_state()


class SegmentedButton(ctk.CTkSegmentedButton):
    """CTk segments need separate text colors for selected and unselected items."""
    def __init__(self, parent, **kwargs):
        """Crea segmentos con colores distintos para opciones elegidas y libres."""
        self._design_palette = palette()
        p = self._design_palette
        super().__init__(parent, corner_radius=0, border_width=1, height=30,
                         fg_color=p.border, selected_color=p.primary,
                         selected_hover_color=p.primary_hover,
                         unselected_color=p.inset, unselected_hover_color=p.panel,
                         text_color=p.text, text_color_disabled=p.muted, **kwargs)

    def _create_button(self, index, value):
        """Construye cada opción como un botón con el estilo compartido."""
        button = Button(self, width=0, height=self._current_height,
                      secondary_bg=self._design_palette.inset,
                      text=value, font=self._font, state=self._state,
                      command=lambda: self.set(value, from_button_callback=True),
                      round_width_to_even_numbers=False, round_height_to_even_numbers=False)
        # Agrega espacio horizontal sin aumentar la altura compacta de la fila.
        if button._text_label is not None:
            button._text_label.grid_configure(padx=8)
        return button

    def _select_button_by_value(self, value):
        """Aplica el rol primario al segmento seleccionado."""
        super()._select_button_by_value(value)
        button = self._buttons_dict[value]
        assert isinstance(button, Button)
        button._design_role = 'primary'
        button.configure(text_color=self._design_palette.primary_text)
        button._paint_state()

    def _unselect_button_by_value(self, value):
        """Devuelve al rol secundario el segmento que dejó de estar seleccionado."""
        super()._unselect_button_by_value(value)
        if value in self._buttons_dict:
            button = self._buttons_dict[value]
            assert isinstance(button, Button)
            button._design_role = 'secondary'
            button.configure(text_color=self._design_palette.text)
            button._paint_state()

    def configure(self, require_redraw=False, **kwargs):
        """Propaga estado deshabilitado y selección a los botones internos."""
        super().configure(require_redraw=require_redraw, **kwargs)
        if 'state' in kwargs:
            p = self._design_palette
            for value, button in self._buttons_dict.items():
                selected = value == self.get()
                button.configure(fg_color=p.disabled if kwargs['state'] == 'disabled' else
                                 p.primary if selected else p.inset,
                                 hover=kwargs['state'] != 'disabled')


class Entry(ctk.CTkEntry):
    """Square input with the shared inset surface and stable focus outline."""
    def __init__(self, parent, **kwargs):
        """Configura superficie, texto y eventos de foco del campo de entrada."""
        self._design_palette = palette()
        self._design_hover = self._design_focus = False
        p = self._design_palette
        super().__init__(parent, corner_radius=0, border_width=1,
                         fg_color=p.inset, border_color=p.border,
                         text_color=p.text, placeholder_text_color=p.muted, **kwargs)
        self.bind('<Enter>', lambda event=None: self._set_state('_design_hover', True), add=True)
        self.bind('<Leave>', lambda event=None: self._set_state('_design_hover', False), add=True)
        self.bind('<FocusIn>', lambda event=None: self._set_state('_design_focus', True), add=True)
        self.bind('<FocusOut>', lambda event=None: self._set_state('_design_focus', False), add=True)

    def _set_state(self, name, value):
        """Actualiza una marca de foco o hover y refresca los colores."""
        setattr(self, name, value)
        self._paint_state()

    def _paint_state(self):
        """Dibuja borde y texto según foco, puntero y estado del campo."""
        p = self._design_palette
        disabled = self.cget('state') == 'disabled'
        border = p.border if disabled else p.text if self._design_focus else p.hover_border if self._design_hover else p.border
        super().configure(border_color=border,
                          fg_color=p.disabled if disabled else p.inset,
                          text_color=p.muted if disabled else p.text)

    def configure(self, require_redraw=False, **kwargs):
        """Recalcula la apariencia cuando cambia el estado del campo."""
        super().configure(require_redraw=require_redraw, **kwargs)
        if 'state' in kwargs:
            self._paint_state()


class ComboBox(ctk.CTkComboBox):
    """Conserva la edición de CTk y aplica el estilo cuadrado compartido."""
    def __init__(self, parent, **kwargs):
        """Configura el selector editable y conecta su estado de foco."""
        self._design_palette = palette()
        self._design_hover = self._design_focus = False
        p = self._design_palette
        super().__init__(parent, corner_radius=0, border_width=1,
                         fg_color=p.inset, border_color=p.border,
                         button_color=p.inset, button_hover_color=p.panel,
                         text_color=p.text, text_color_disabled=p.muted,
                         dropdown_fg_color=p.panel, dropdown_text_color=p.text,
                         dropdown_hover_color=p.border, **kwargs)
        self.bind('<FocusIn>', lambda event: self._set_state('_design_focus', True), add=True)
        self.bind('<FocusOut>', lambda event: self._set_state('_design_focus', False), add=True)

    def _draw(self, no_color_updates=False):
        """Dibuja el selector y repasa el borde del área de flecha."""
        super()._draw(no_color_updates)
        self._outline_arrow()

    def _outline_arrow(self):
        # CTk suele pintar el borde de la flecha con el mismo color de relleno.
        """Mantiene visible el contorno del botón desplegable de CTk."""
        self._canvas.itemconfig('border_parts_right',
                                fill=self._apply_appearance_mode(self._border_color),
                                outline=self._apply_appearance_mode(self._border_color))

    def _set_state(self, name, value):
        """Actualiza foco o hover y repinta el selector."""
        setattr(self, name, value)
        self._paint_state()

    def _paint_state(self):
        """Ajusta colores del campo y la flecha según su estado."""
        p = self._design_palette
        disabled = self.cget('state') == 'disabled'
        border = p.border if disabled else p.text if self._design_focus else p.hover_border if self._design_hover else p.border
        super().configure(border_color=border,
                          fg_color=p.disabled if disabled else p.inset,
                          button_color=p.disabled if disabled else p.inset)

    def configure(self, require_redraw=False, **kwargs):
        """Repinta el selector cuando cambia a deshabilitado o normal."""
        super().configure(require_redraw=require_redraw, **kwargs)
        if 'state' in kwargs:
            self._paint_state()

    def _on_enter(self, event=0):
        """Actualiza hover y vuelve a dibujar el borde de la flecha."""
        self._set_state('_design_hover', True)
        super()._on_enter(event)
        self._outline_arrow()

    def _on_leave(self, event=0):
        """Retira hover y vuelve a dibujar el borde de la flecha."""
        self._set_state('_design_hover', False)
        super()._on_leave(event)
        self._outline_arrow()


class CheckBox(ctk.CTkCheckBox):
    """Square checkboxes use the same selection colors as segmented controls."""
    def __init__(self, parent, **kwargs):
        """Aplica colores comunes y permite activar el control con teclado."""
        p = palette()
        super().__init__(parent, corner_radius=0, border_width=1,
                         fg_color=p.primary, hover_color=p.primary_hover,
                         border_color=p.border, checkmark_color=p.primary_text,
                         text_color=p.text, text_color_disabled=p.muted, **kwargs)
        self._canvas.configure(takefocus=1)
        self.bind('<Return>', lambda event: self.toggle(), add=True)
        self.bind('<space>', lambda event: self.toggle(), add=True)
        self.bind('<FocusIn>', lambda event: self.configure(border_color=p.text), add=True)
        self.bind('<FocusOut>', lambda event: self.configure(border_color=p.border), add=True)


class Switch(ctk.CTkSwitch):
    """Mantiene la forma funcional del interruptor y un indicador visible en ambos estados."""
    def __init__(self, parent, **kwargs):
        """Configura colores de ambos estados y accesos de teclado del interruptor."""
        self._design_palette = palette()
        self._design_focus = False
        p = self._design_palette
        super().__init__(parent, border_width=1, fg_color=p.inset,
                         progress_color=p.border, button_color='#FFFFFF',
                         button_hover_color='#FFFFFF', border_color=p.border, **kwargs)
        self._canvas.configure(takefocus=1)
        self.bind('<FocusIn>', lambda event=None: self._set_focus(True), add=True)
        self.bind('<FocusOut>', lambda event=None: self._set_focus(False), add=True)
        self.bind('<Return>', lambda event=None: self.toggle(), add=True)
        self.bind('<space>', lambda event=None: self.toggle(), add=True)

    def _set_focus(self, focused):
        """Marca el foco y redibuja el interruptor."""
        self._design_focus = focused
        self._draw()

    def _draw(self, no_color_updates=False):
        """Dibuja el estado marcado, deshabilitado, hover y foco sin ocultar el indicador."""
        p = self._design_palette
        disabled = self._state == 'disabled'
        self._button_color = '#FFFFFF' if self._check_state and not disabled else p.muted
        self._button_hover_color = self._button_color
        self._progress_color = p.disabled if disabled else p.border
        self._border_color = p.border
        if not disabled:
            if self._design_focus:
                self._border_color = p.text
            elif self._hover_state:
                self._border_color = p.hover_border
        super()._draw(no_color_updates=False)

    def _on_enter(self, event=0):
        """Actualiza hover y repinta el estado del interruptor."""
        super()._on_enter(event)
        self._draw()

    def _on_leave(self, event=0):
        """Retira hover y repinta el estado del interruptor."""
        super()._on_leave(event)
        self._draw()


class _Menu(ctk.CTkOptionMenu):
    """Implementa un menú compatible con tema, estados y teclado."""
    def configure(self, require_redraw=False, **kwargs):
        """Propaga cambios de estado al marco exterior que dibuja su borde."""
        super().configure(require_redraw=require_redraw, **kwargs)
        if 'state' in kwargs:
            assert isinstance(self.master, OptionField)
            self.master._paint_state()


class OptionField(ctk.CTkFrame):
    """Enmarca el menú CTk con un borde fino y una flecha integrada."""
    def __init__(self, parent, **kwargs):
        """Integra un menú desplegable con un borde accesible y controles de teclado."""
        p = palette()
        self._design_palette = p
        self._design_hover = self._design_focus = False
        width = kwargs.pop('width', 220)
        super().__init__(parent, width=width, height=32, corner_radius=0, fg_color=p.border)
        self.grid_columnconfigure(0, weight=1)
        self.menu = _Menu(
            self, corner_radius=0, width=width - 2, height=30,
            fg_color=p.inset, button_color=p.inset, button_hover_color=p.panel,
            text_color=p.text, text_color_disabled=p.muted,
            dropdown_fg_color=p.panel, dropdown_text_color=p.text,
            dropdown_hover_color=p.border, **kwargs,
        )
        self.menu.grid(row=0, column=0, padx=1, pady=1, sticky='ew')
        self.menu._canvas.configure(takefocus=1)
        self.menu.bind('<Enter>', lambda event: self._set_state('_design_hover', True), add=True)
        self.menu.bind('<Leave>', lambda event: self._set_state('_design_hover', False), add=True)
        self.menu.bind('<FocusIn>', lambda event: self._set_state('_design_focus', True), add=True)
        self.menu.bind('<FocusOut>', lambda event: self._set_state('_design_focus', False), add=True)
        self.menu.bind('<Return>', lambda event: self.menu._clicked(), add=True)
        self.menu.bind('<space>', lambda event: self.menu._clicked(), add=True)

    def _set_state(self, name, value):
        """Actualiza el foco o hover y solicita redibujar el marco."""
        setattr(self, name, value)
        self._paint_state()

    def _paint_state(self):
        """Elige el borde del menú según foco, hover y disponibilidad."""
        p = self._design_palette
        disabled = self.menu.cget('state') == 'disabled'
        border = p.border if disabled else p.text if self._design_focus else p.hover_border if self._design_hover else p.border
        self.configure(fg_color=border)
