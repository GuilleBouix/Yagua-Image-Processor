"""Aspecto compartido de los avisos flotantes, sin historial ni cola de eventos."""
import tkinter as tk

import customtkinter as ctk

from app.ui import colors, fonts, styles


def toast_host(owner):
    """Encuentra el área central; en vistas aisladas usa su propio contenedor."""
    parent = owner
    while parent is not None:
        content = getattr(parent, 'content', None)
        if content is not None:
            return content
        parent = getattr(parent, 'master', None)
    return owner


class Toast(ctk.CTkFrame):
    """Aviso cuadrado y adaptable con cierre y acción primaria opcional.

    Cada propietario conserva sus reglas de aparición y duración. Los avisos
    simultáneos comparten la esquina superior derecha sin taparse entre sí.
    """
    def __init__(self, parent, text, *, close_command=None, action_text=None, action=None):
        super().__init__(parent, corner_radius=0, fg_color=colors.PANEL_BG,
                         border_width=1, border_color='#357A52')
        self._last_layout = None
        self.grid_columnconfigure(0, weight=1)
        has_action = action is not None and action_text is not None
        self.message = ctk.CTkLabel(self, text=text, font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_COLOR, anchor='w', justify='left', width=1, wraplength=302)
        self.message.grid(row=0, column=0, padx=(16, 8),
                          pady=(16, 12 if has_action else 16), sticky='ew')
        self.close_button = ctk.CTkButton(self, text='×', width=30, height=30,
            fg_color='transparent', border_width=0, corner_radius=0, hover=False,
            text_color=colors.TEXT_COLOR, font=fonts.FUENTE_BASE,
            command=close_command or self.destroy)
        self.close_button._canvas.configure(takefocus=1)
        self.close_button.bind('<Return>', lambda _event: self.close_button.invoke(), add='+')
        self.close_button.bind('<space>', lambda _event: self.close_button.invoke(), add='+')
        self.close_button.grid(row=0, column=1, padx=(0, 16),
                               pady=(16, 12 if has_action else 16), sticky='ne')
        if has_action:
            self.action_button = styles.Button(self, role='primary', text=action_text,
                height=36, width=1, font=fonts.FUENTE_CHICA, command=action)
            self.action_button.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 16), sticky='ew')
        self._host_binding = parent.bind('<Configure>', self._reflow, add='+')
        self.bind('<Configure>', self._reflow, add=True)
        self._reflow()

    def _reflow(self, _event=None):
        """Ajusta ancho, textos y separación sin modificar la geometría de los paneles."""
        if not self.winfo_exists():
            return
        available = max(1, self.master.winfo_width())
        offset = 16.0
        for toast in self.master.winfo_children():
            if not isinstance(toast, Toast):
                continue
            scale = toast._get_widget_scaling()
            width = max(1, min(380, int(available / scale) - 32))
            state = available, scale, offset
            if state != toast._last_layout:
                toast._last_layout = state
                toast.place(relx=1.0, x=-16, y=offset, anchor='ne', relwidth=width * scale / available)
                toast.message.configure(wraplength=max(1, width - 78))
            toast.lift()
            offset += max(toast.winfo_height(), toast.winfo_reqheight()) / scale + 12

    @staticmethod
    def raise_all(parent):
        """Mantiene los avisos sobre la vista al navegar entre herramientas."""
        for child in parent.winfo_children():
            if isinstance(child, Toast):
                child.lift()

    def destroy(self):
        """Desconecta la geometría del padre y libera el lugar para los demás avisos."""
        parent = self.master
        binding = getattr(self, '_host_binding', None)
        if binding:
            parent.unbind('<Configure>', binding)
            self._host_binding = None
        super().destroy()
        try:
            remaining = next((child for child in parent.winfo_children() if isinstance(child, Toast)), None)
            if remaining is not None:
                remaining._reflow()
        except tk.TclError:
            pass  # El contenedor también puede estar cerrándose.
