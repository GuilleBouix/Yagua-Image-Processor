from __future__ import annotations

import logging
import os
import sys
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


def get_update_platform() -> str:
    """Retorna la plataforma lógica usada para filtrar releases."""
    override = (os.environ.get("YAGUA_UPDATE_PLATFORM") or "").strip().lower()
    if override in {"windows", "linux"}:
        return override
    return "windows" if sys.platform == "win32" else "linux"


def get_release_tag_prefix(platform: str | None = None) -> str:
    """Retorna el prefijo de tags de release para la plataforma indicada."""
    resolved = platform or get_update_platform()
    return "win-v" if resolved == "windows" else "linux-v"


def _parse_release_version(tag_name: str, prefix: str) -> Version | None:
    if not tag_name.startswith(prefix):
        return None
    raw_version = tag_name[len(prefix):].strip()
    if not raw_version:
        return None
    try:
        return Version(raw_version)
    except InvalidVersion:
        logger.warning("updates: tag con version invalida (%s)", tag_name)
        return None


def check_latest_stable(current_version: str) -> UpdateInfo | None:
    """Retorna info de actualización estable si existe, o None.

    Fuente: GitHub Releases API filtrando por prefijo de plataforma.
    """
    repo = get_repo()
    prefix = get_release_tag_prefix()
    api_url = f"https://api.github.com/repos/{repo}/releases"
    try:
        r = requests.get(
            api_url,
            timeout=10,
            headers={"Accept": "application/vnd.github+json"},
        )
        r.raise_for_status()
        payload = r.json()
        if not isinstance(payload, list):
            logger.warning("updates: respuesta invalida de releases API")
            return None
        try:
            cur_v = Version(str(current_version).strip())
        except InvalidVersion as exc:
            logger.warning("updates: version invalida (%s)", exc)
            return None

        best_match: tuple[Version, str] | None = None
        for release in payload:
            if not isinstance(release, dict):
                continue
            if release.get("draft") or release.get("prerelease"):
                continue

            tag_name = str(release.get("tag_name") or "").strip()
            remote_version = _parse_release_version(tag_name, prefix)
            if remote_version is None or remote_version <= cur_v:
                continue

            release_url = str(release.get("html_url") or "").strip()
            if not release_url:
                release_url = f"https://github.com/{repo}/releases/tag/{tag_name}"

            if best_match is None or remote_version > best_match[0]:
                best_match = (remote_version, release_url)

        if best_match is None:
            return None
        return UpdateInfo(version=str(best_match[0]), release_url=best_match[1])
    except Exception:
        logger.exception("updates: fallo comprobando releases API (%s)", api_url)
        return None
