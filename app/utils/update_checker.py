"""Consulta versiones de GitHub y valida actualizaciones estables o prerelease."""

from __future__ import annotations

from urllib.parse import urlsplit
import logging
import os
import sys
from dataclasses import dataclass

import requests
from packaging.version import InvalidVersion, Version


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdateInfo:
    """Contiene la versión disponible y el enlace de su publicación."""
    version: str
    release_url: str


class UpdateCheckError(RuntimeError):
    """La comprobación falló; no equivale a no encontrar actualizaciones."""


def get_repo() -> str:
    # Override opcional (útil para forks / staging).
    """Obtiene la identidad del repositorio desde la configuración de la aplicación."""
    return os.environ.get("YAGUA_UPDATE_REPO") or "GuilleBouix/Yagua-Image-Processor"


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
    """Interpreta versiones estables y prereleases devueltas por GitHub."""
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


def check_latest_update(current_version: str) -> UpdateInfo | None:
    """Busca versiones estables publicadas de esta plataforma.

    None significa que la consulta fue correcta y no hay una versión superior.
    Los fallos de conexión, HTTP o respuesta se propagan como UpdateCheckError.
    """
    try:
        cur_v = Version(str(current_version).strip())
    except InvalidVersion as exc:
        raise UpdateCheckError('Invalid installed version') from exc

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
    except (requests.RequestException, ValueError) as exc:
        logger.exception("updates: fallo comprobando releases API (%s)", api_url)
        raise UpdateCheckError('Could not query GitHub releases') from exc
    if not isinstance(payload, list):
        raise UpdateCheckError('Invalid GitHub releases response')

    best_match: tuple[Version, str, str] | None = None
    for release in payload:
        if not isinstance(release, dict) or release.get('draft') or release.get('prerelease'):
            continue

        tag_name = str(release.get('tag_name') or '').strip()
        remote_version = _parse_release_version(tag_name, prefix)
        if (remote_version is None or remote_version.is_prerelease
                or remote_version.is_devrelease or remote_version <= cur_v):
            continue

        raw_url = release.get('html_url')
        release_url = raw_url.strip() if isinstance(raw_url, str) else ''
        try:
            parsed = urlsplit(release_url)
            valid_url = parsed.scheme == 'https' and bool(parsed.netloc) and not parsed.username and not parsed.password
        except ValueError:
            valid_url = False
        if not valid_url:
            release_url = f'https://github.com/{repo}/releases/tag/{tag_name}'

        if best_match is None or remote_version > best_match[0]:
            best_match = (remote_version, tag_name[len(prefix):].strip(), release_url)

    if best_match is None:
        return None
    return UpdateInfo(version=best_match[1], release_url=best_match[2])
