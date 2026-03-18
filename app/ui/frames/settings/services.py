"""Services UI-agnosticos para Settings."""

import json
import sys
import subprocess
from pathlib import Path

from app.translations import set_language


def _settings_path() -> Path:
    return Path(__file__).resolve().parents[3] / 'user_settings.json'


def _load_settings() -> dict:
    path = _settings_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _save_settings(settings: dict) -> None:
    path = _settings_path()
    path.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding='utf-8')


def restart_app() -> None:
    python = sys.executable
    script = sys.argv[0]
    subprocess.Popen([python, script])
    sys.exit(0)


def set_language_and_restart(lang: str) -> None:
    set_language(lang)
    restart_app()


def set_theme_and_restart(theme: str) -> None:
    settings = _load_settings()
    settings['theme'] = theme
    _save_settings(settings)
    restart_app()


__all__ = ['set_language_and_restart', 'set_theme_and_restart', 'restart_app']
