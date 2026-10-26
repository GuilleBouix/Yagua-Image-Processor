"""Opt-in visual roles for desktop views. Typography belongs to each caller."""
from dataclasses import dataclass
from typing import Any

import customtkinter as ctk
from PIL import Image

from app.ui import colors


@dataclass(frozen=True)
class Palette:
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
    def luminance(hex_color):
        values = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
        return sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + .05) / (dark + .05)


def palette():
    """Resolve at construction time; never change another view's theme globals."""
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
    p = palette()
    return dict(corner_radius=0, border_width=1, border_color=p.border,
                fg_color=p.inset if role == 'list' else p.panel)


def scrollbar() -> dict[str, Any]:
    p = palette()
    return dict(scrollbar_fg_color=p.inset,
                scrollbar_button_color='#48484A' if colors.get_current_theme() == 'Default' else colors.ACENTO_DIMMED,
                scrollbar_button_hover_color=p.muted)


class Button(ctk.CTkButton):
    """Primary/secondary roles with reversible disabled, hover and focus states."""
    def __init__(self, parent, *, role='secondary', secondary_bg=None, **kwargs):
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
        self._design_focus = focused
        self._paint_state()

    def _paint_state(self):
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
        state_changed = 'state' in kwargs
        super().configure(require_redraw=require_redraw, **kwargs)
        if state_changed:
            self._design_hover = False
            self._paint_state()

    def _on_enter(self, event=None):
        self._design_hover = True
        self._paint_state()
        super()._on_enter(event)

    def _on_leave(self, event=None):
        self._design_hover = False
        self._paint_state()
        super()._on_leave(event)


class NavigationButton(Button):
    """Solid navigation states; reserve an outline for keyboard focus only."""
    def _paint_state(self):
        super()._paint_state()
        if not self._design_focus or self.cget('state') == 'disabled':
            super().configure(border_width=0)

    def set_selected(self, selected, image):
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
        self._design_palette = palette()
        p = self._design_palette
        super().__init__(parent, corner_radius=0, border_width=1, height=30,
                         fg_color=p.border, selected_color=p.primary,
                         selected_hover_color=p.primary_hover,
                         unselected_color=p.inset, unselected_hover_color=p.panel,
                         text_color=p.text, text_color_disabled=p.muted, **kwargs)

    def _create_button(self, index, value):
        button = Button(self, width=0, height=self._current_height,
                      secondary_bg=self._design_palette.inset,
                      text=value, font=self._font, state=self._state,
                      command=lambda: self.set(value, from_button_callback=True),
                      round_width_to_even_numbers=False, round_height_to_even_numbers=False)
        # Horizontal breathing room without increasing the compact row's height.
        if button._text_label is not None:
            button._text_label.grid_configure(padx=8)
        return button

    def _select_button_by_value(self, value):
        super()._select_button_by_value(value)
        button = self._buttons_dict[value]
        assert isinstance(button, Button)
        button._design_role = 'primary'
        button.configure(text_color=self._design_palette.primary_text)
        button._paint_state()

    def _unselect_button_by_value(self, value):
        super()._unselect_button_by_value(value)
        if value in self._buttons_dict:
            button = self._buttons_dict[value]
            assert isinstance(button, Button)
            button._design_role = 'secondary'
            button.configure(text_color=self._design_palette.text)
            button._paint_state()

    def configure(self, require_redraw=False, **kwargs):
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
        setattr(self, name, value)
        self._paint_state()

    def _paint_state(self):
        p = self._design_palette
        disabled = self.cget('state') == 'disabled'
        border = p.border if disabled else p.text if self._design_focus else p.hover_border if self._design_hover else p.border
        super().configure(border_color=border,
                          fg_color=p.disabled if disabled else p.inset,
                          text_color=p.muted if disabled else p.text)

    def configure(self, require_redraw=False, **kwargs):
        super().configure(require_redraw=require_redraw, **kwargs)
        if 'state' in kwargs:
            self._paint_state()


class ComboBox(ctk.CTkComboBox):
    """Preserve CTk's editable selector with the shared square input styling."""
    def __init__(self, parent, **kwargs):
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
        super()._draw(no_color_updates)
        self._outline_arrow()

    def _outline_arrow(self):
        # CTk normally paints the arrow section's border with its fill color.
        self._canvas.itemconfig('border_parts_right',
                                fill=self._apply_appearance_mode(self._border_color),
                                outline=self._apply_appearance_mode(self._border_color))

    def _set_state(self, name, value):
        setattr(self, name, value)
        self._paint_state()

    def _paint_state(self):
        p = self._design_palette
        disabled = self.cget('state') == 'disabled'
        border = p.border if disabled else p.text if self._design_focus else p.hover_border if self._design_hover else p.border
        super().configure(border_color=border,
                          fg_color=p.disabled if disabled else p.inset,
                          button_color=p.disabled if disabled else p.inset)

    def configure(self, require_redraw=False, **kwargs):
        super().configure(require_redraw=require_redraw, **kwargs)
        if 'state' in kwargs:
            self._paint_state()

    def _on_enter(self, event=0):
        self._set_state('_design_hover', True)
        super()._on_enter(event)
        self._outline_arrow()

    def _on_leave(self, event=0):
        self._set_state('_design_hover', False)
        super()._on_leave(event)
        self._outline_arrow()


class CheckBox(ctk.CTkCheckBox):
    """Square checkboxes use the same selection colors as segmented controls."""
    def __init__(self, parent, **kwargs):
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
    """Keep the functional switch shape, with a visible thumb in both states."""
    def __init__(self, parent, **kwargs):
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
        self._design_focus = focused
        self._draw()

    def _draw(self, no_color_updates=False):
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
        super()._on_enter(event)
        self._draw()

    def _on_leave(self, event=0):
        super()._on_leave(event)
        self._draw()


class _Menu(ctk.CTkOptionMenu):
    def configure(self, require_redraw=False, **kwargs):
        super().configure(require_redraw=require_redraw, **kwargs)
        if 'state' in kwargs:
            assert isinstance(self.master, OptionField)
            self.master._paint_state()


class OptionField(ctk.CTkFrame):
    """A one-pixel outline around a CTk menu, with an integrated dark arrow."""
    def __init__(self, parent, **kwargs):
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
        setattr(self, name, value)
        self._paint_state()

    def _paint_state(self):
        p = self._design_palette
        disabled = self.menu.cget('state') == 'disabled'
        border = p.border if disabled else p.text if self._design_focus else p.hover_border if self._design_hover else p.border
        self.configure(fg_color=border)
