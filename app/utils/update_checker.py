from __future__ import annotations

import logging
import os
from dataclasses import dataclass

import requests
from packaging.version import InvalidVersion, Version


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    release_url: str


def get_repo() -> str:
    # Override opcional (útil para forks / staging).
    return os.environ.get("YAGUA_UPDATE_REPO") or "GuilleBouix/Yagua-Image-Editor"


def check_latest_stable(current_version: str) -> UpdateInfo | None:
    """Retorna info de actualización estable si existe, o None.

    Fuente: GitHub Releases latest.json (generado por CI).
    """
    repo = get_repo()
    latest_url = f"https://github.com/{repo}/releases/latest/download/latest.json"
    try:
        r = requests.get(latest_url, timeout=10)
        r.raise_for_status()
        payload = r.json()
        remote_version = str(payload.get("version") or "").strip()
        if not remote_version:
            logger.warning("updates: latest.json sin 'version'")
            return None

        try:
            cur_v = Version(str(current_version).strip())
            rem_v = Version(remote_version)
        except InvalidVersion as exc:
            logger.warning("updates: version invalida (%s)", exc)
            return None

        if rem_v <= cur_v:
            return None

        release_url = f"https://github.com/{repo}/releases/tag/v{remote_version}"
        return UpdateInfo(version=remote_version, release_url=release_url)
    except Exception:
        logger.exception("updates: fallo comprobando latest.json (%s)", latest_url)
        return None

