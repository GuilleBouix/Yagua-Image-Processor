"""Services UI-agnosticos para Settings."""

import sys
import subprocess

from app.translations import set_language


def set_language_and_restart(lang: str) -> None:
    set_language(lang)
    python = sys.executable
    script = sys.argv[0]
    subprocess.Popen([python, script])
    sys.exit(0)


__all__ = ['set_language_and_restart']
