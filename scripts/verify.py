"""Ejecuta las pruebas con preferencias temporales y sin acceso a la red externa."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    """Ejecuta la suite con preferencias temporales y requisitos de interfaz obligatorios."""
    import pytest
    import requests
    import app.utils.settings as settings
    with TemporaryDirectory(prefix='yagua-verification-') as directory:
        settings.settings_path = lambda: Path(directory) / 'user_settings.json'
        def offline(*args, **kwargs):
            """Bloquea llamadas de red para que la verificación use solo recursos locales."""
            raise requests.ConnectionError('External network forbidden during tests')
        requests.sessions.Session.request = offline
        return pytest.main(sys.argv[1:] or ['-q'])


if __name__ == '__main__':
    raise SystemExit(main())
