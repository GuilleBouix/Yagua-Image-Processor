from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from datetime import datetime

import customtkinter as ctk
import requests
from packaging.version import Version, InvalidVersion

from app.ui import colors, fonts
from app.translations import t
from app.version import __version__

logger = logging.getLogger(__name__)


class UpdatesTab(ctk.CTkFrame):
    """Tab Actualizaciones: check + download + install (Windows/Inno)."""

    def __init__(self, parent):
        super().__init__(parent, fg_color='transparent')
        self.grid_columnconfigure(0, weight=1)
        self._worker_activo = False
        self._build()

    def _build(self):
        panel = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=colors.PANEL_BG,
            border_width=1,
            border_color=colors.SIDEBAR_SEPARATOR
        )
        panel.grid(row=0, column=0, sticky='ew')
        panel.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            panel,
            text=t('updates_title'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            anchor='w'
        ).grid(row=0, column=0, padx=16, pady=(16, 4), sticky='w')

        self._lbl_version = ctk.CTkLabel(
            panel,
            text=f"{t('current_version')}: v{__version__}",
            font=fonts.FUENTE_CHICA,
            text_color=colors.TEXT_GRAY,
            anchor='w'
        )
        self._lbl_version.grid(row=1, column=0, padx=16, pady=(0, 6), sticky='w')

        self._lbl_update_status = ctk.CTkLabel(
            panel,
            text=t('no_updates'),
            font=fonts.FUENTE_BASE,
            text_color=colors.TEXT_COLOR,
            anchor='w'
        )
        self._lbl_update_status.grid(row=2, column=0, padx=16, pady=(0, 12), sticky='w')

        self._btn_check_updates = ctk.CTkButton(
            panel,
            text=t('check_updates'),
            width=160,
            height=34,
            corner_radius=8,
            font=fonts.FUENTE_BASE,
            fg_color=colors.ACENTO,
            text_color=colors.TEXT_ACTIVE,
            hover_color=colors.ACENTO_HOVER,
            command=self._check_updates
        )
        self._btn_check_updates.grid(row=3, column=0, padx=16, pady=(0, 16), sticky='w')

    def _repo_full_name(self) -> str:
        # Default repo (override opcional para forks)
        return os.environ.get("YAGUA_UPDATE_REPO") or "GuilleBouix/Yagua-Image-Editor"

    def _is_installed_build(self) -> bool:
        # Inno Setup deja unins000.exe en el mismo directorio de instalacion.
        if not getattr(sys, "frozen", False):
            return False
        exe = Path(sys.executable).resolve()
        return (exe.parent / "unins000.exe").exists()

    def _set_status(self, text: str):
        if hasattr(self, "_lbl_update_status") and self._lbl_update_status.winfo_exists():
            self._lbl_update_status.configure(text=text)

    def _set_busy(self, busy: bool):
        self._worker_activo = busy
        if hasattr(self, "_btn_check_updates") and self._btn_check_updates.winfo_exists():
            self._btn_check_updates.configure(state="disabled" if busy else "normal")

    def _check_updates(self):
        if self._worker_activo:
            return

        self._set_busy(True)
        self._set_status(t("updates_checking"))

        def _worker():
            repo = self._repo_full_name()
            try:
                if not self._is_installed_build():
                    self.after(0, lambda: self._set_status(t("updates_requires_install")))
                    return

                # Canal estable: releases/latest ignora pre-releases.
                latest_url = f"https://github.com/{repo}/releases/latest/download/latest.json"
                logger.info("updates: fetch latest.json (%s)", latest_url)
                r = requests.get(latest_url, timeout=15)
                r.raise_for_status()
                payload = r.json()

                remote_version = str(payload.get("version") or "").strip()
                if not remote_version:
                    raise RuntimeError("latest.json sin 'version'")

                try:
                    cur_v = Version(str(__version__).strip())
                    rem_v = Version(remote_version)
                except InvalidVersion as exc:
                    raise RuntimeError(f"Version invalida: {exc}") from exc

                if rem_v <= cur_v:
                    self.after(0, lambda: self._set_status(t("no_updates")))
                    return

                self.after(0, lambda: self._set_status(t("updates_available").format(version=remote_version)))  # type: ignore
                self.after(0, lambda: self._set_status(t("updates_downloading")))

                assets = payload.get("assets") or []
                if not isinstance(assets, list):
                    raise RuntimeError("latest.json assets invalido")

                setup_asset = None
                for a in assets:
                    try:
                        name = str(a.get("name") or "")
                    except Exception:
                        continue
                    if name.lower().startswith("yagua_setup_") and name.lower().endswith(".exe"):
                        setup_asset = a
                        break
                if not setup_asset:
                    raise RuntimeError("No se encontro asset setup en latest.json")

                setup_name = str(setup_asset.get("name") or "")
                setup_sha = str(setup_asset.get("sha256") or "").lower().strip()
                if not setup_sha or len(setup_sha) < 32:
                    raise RuntimeError("SHA256 faltante en latest.json")

                dl_url = f"https://github.com/{repo}/releases/download/v{remote_version}/{setup_name}"
                logger.info("updates: download (%s)", dl_url)

                tmp_dir = Path(tempfile.gettempdir()) / "Yagua" / "updates" / remote_version
                tmp_dir.mkdir(parents=True, exist_ok=True)
                setup_path = tmp_dir / setup_name

                with requests.get(dl_url, timeout=30, stream=True) as rr:
                    rr.raise_for_status()
                    with setup_path.open("wb") as f:
                        for chunk in rr.iter_content(chunk_size=1024 * 256):
                            if chunk:
                                f.write(chunk)

                self.after(0, lambda: self._set_status(t("updates_verifying")))
                h = hashlib.sha256()
                with setup_path.open("rb") as f:
                    for chunk in iter(lambda: f.read(1024 * 1024), b""):
                        h.update(chunk)
                local_sha = h.hexdigest().lower()
                if local_sha != setup_sha:
                    try:
                        setup_path.unlink(missing_ok=True)
                    except Exception:
                        pass
                    raise RuntimeError("sha256 mismatch")

                self.after(0, lambda: self._set_status(t("updates_installing")))

                # Script que instala cuando el proceso actual sale y luego relanza.
                pid = os.getpid()
                exe_path = str(Path(sys.executable).resolve())
                ps_path = tmp_dir / "apply_update.ps1"
                log_path = tmp_dir / "update.log"
                # Creamos el log desde Python para confirmar que el launcher realmente se disparó.
                try:
                    log_path.parent.mkdir(parents=True, exist_ok=True)
                    log_path.write_text(
                        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} update: spawn powershell\n",
                        encoding="utf-8",
                    )
                except Exception:
                    pass
                ps_script = f"""param([int]$Pid, [string]$Installer, [string]$ExePath, [string]$LogPath)\n\n$ErrorActionPreference = 'Stop'\n\nfunction Log([string]$Msg) {{\n  $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')\n  \"$ts $Msg\" | Out-File -FilePath $LogPath -Encoding UTF8 -Append\n}}\n\nLog \"update: waiting pid=$Pid\"\nwhile (Get-Process -Id $Pid -ErrorAction SilentlyContinue) {{ Start-Sleep -Milliseconds 250 }}\n\ntry {{\n  Log \"update: starting installer=$Installer\"\n  # Inno Setup suele requerir elevacion para Program Files.\n  $p = Start-Process -FilePath $Installer -ArgumentList '/SP- /VERYSILENT /SUPPRESSMSGBOXES /NORESTART' -Verb RunAs -Wait -PassThru\n  Log \"update: installer exitcode=$($p.ExitCode)\"\n  if ($p.ExitCode -eq 0) {{\n    Log \"update: relaunch $ExePath\"\n    Start-Process -FilePath $ExePath\n  }} else {{\n    Log \"update: install failed\"\n  }}\n}} catch {{\n  Log \"update: exception $($_.Exception.Message)\"\n}}\n"""
                ps_path.write_text(ps_script, encoding="utf-8")

                # Importante: para que aparezca el UAC cuando corresponde, evitamos ejecutar PowerShell en modo "detached/hidden".
                creationflags = 0
                subprocess.Popen(
                    [
                        "powershell",
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(ps_path),
                        "-Pid",
                        str(pid),
                        "-Installer",
                        str(setup_path),
                        "-ExePath",
                        exe_path,
                        "-LogPath",
                        str(log_path),
                    ],
                    cwd=str(tmp_dir),
                    creationflags=creationflags,
                    close_fds=False,
                )

                # Cerrar app (el script se encarga de relanzar).
                self.after(0, self._close_app)

            except Exception as exc:
                logger.exception("updates: error")
                msg = str(exc).lower()
                if "sha256 mismatch" in msg or "mismatch" in msg:
                    self.after(0, lambda: self._set_status(t("updates_hash_mismatch")))
                else:
                    self.after(0, lambda: self._set_status(t("updates_error")))
            finally:
                self.after(0, lambda: self._set_busy(False))

        threading.Thread(target=_worker, daemon=True).start()

    def _close_app(self):
        try:
            root = self.winfo_toplevel()
            root.destroy()
        except Exception:
            os._exit(0)
