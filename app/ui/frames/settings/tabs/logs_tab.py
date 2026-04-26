from __future__ import annotations

from datetime import datetime
import customtkinter as ctk

from app.ui import colors, fonts
from app.ui.scale import scale_wraplength
from app.translations import t
from app.utils.settings import settings_path


class LogsTab(ctk.CTkFrame):
    """Tab Logs: tabla con scroll de yagua.log."""

    def __init__(self, parent):
        super().__init__(parent, fg_color='transparent')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1, minsize=400)
        self._build()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.grid(row=0, column=0, sticky='ew')
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text=t('logs_title'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            anchor='w'
        ).grid(row=0, column=0, sticky='w')

        self._btn_refresh_logs = ctk.CTkButton(
            header,
            text=t('refresh'),
            width=120,
            height=30,
            corner_radius=8,
            font=fonts.FUENTE_CHICA,
            fg_color=colors.BTN_CLEAR_BG,
            text_color=colors.BTN_CLEAR_TEXT,
            hover_color=colors.BTN_CLEAR_HOVER,
            command=self._cargar_logs
        )
        self._btn_refresh_logs.grid(row=0, column=1, sticky='e')

        tabla = ctk.CTkScrollableFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR,
            height=400
        )
        tabla.grid(row=1, column=0, pady=(10, 0), sticky='nsew')
        tabla.grid_columnconfigure(3, weight=1)
        self._logs_table = tabla

        self._render_logs_header()
        self._cargar_logs()

    def _render_logs_header(self):
        for w in self._logs_table.winfo_children():
            w.destroy()
        headers = [t('log_date'), t('log_level'), t('log_module'), t('log_message')]
        for col, text in enumerate(headers):
            ctk.CTkLabel(
                self._logs_table,
                text=text,
                font=fonts.FUENTE_CHICA,
                text_color=colors.TEXT_GRAY,
                anchor='w'
            ).grid(row=0, column=col, padx=10, pady=(8, 6), sticky='w')

    def _cargar_logs(self):
        self._render_logs_header()
        log_path = settings_path().with_name('yagua.log')
        if not log_path.exists():
            self._render_empty()
            return

        try:
            lines = log_path.read_text(encoding='utf-8', errors='ignore').splitlines()[-500:]
        except Exception:
            self._render_empty()
            return

        row = 1
        for line in reversed(lines):
            parsed = self._parse_log_line(line)
            if not parsed:
                continue
            fecha, nivel, modulo, mensaje = parsed
            ctk.CTkLabel(self._logs_table, text=fecha, font=fonts.FUENTE_CHICA, text_color=colors.TEXT_GRAY, anchor='w').grid(row=row, column=0, padx=10, pady=2, sticky='w')
            ctk.CTkLabel(self._logs_table, text=nivel, font=fonts.FUENTE_CHICA, text_color=colors.TEXT_COLOR, anchor='w').grid(row=row, column=1, padx=10, pady=2, sticky='w')
            ctk.CTkLabel(self._logs_table, text=modulo, font=fonts.FUENTE_CHICA, text_color=colors.TEXT_COLOR, anchor='w').grid(row=row, column=2, padx=10, pady=2, sticky='w')
            ctk.CTkLabel(self._logs_table, text=mensaje, font=fonts.FUENTE_CHICA, text_color=colors.TEXT_COLOR, anchor='w', wraplength=scale_wraplength(540)).grid(row=row, column=3, padx=10, pady=2, sticky='w')
            row += 1

        if row == 1:
            self._render_empty()

    def _render_empty(self):
        ctk.CTkLabel(
            self._logs_table,
            text=t('logs_empty'),
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY
        ).grid(row=1, column=0, padx=10, pady=10, sticky='w')

    def _parse_log_line(self, line: str):
        try:
            fecha, rest = line.split(' [', 1)
            nivel, rest = rest.split('] ', 1)
            modulo, mensaje = rest.split(': ', 1)
            datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S,%f")
            return fecha, nivel, modulo, mensaje
        except Exception:
            return None
