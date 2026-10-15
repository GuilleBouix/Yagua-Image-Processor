"""Run required tests with disposable settings and external network disabled."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    import pytest
    import requests
    import app.utils.settings as settings
    with TemporaryDirectory(prefix='yagua-verification-') as directory:
        settings.settings_path = lambda: Path(directory) / 'user_settings.json'
        def offline(*args, **kwargs):
            raise requests.ConnectionError('External network forbidden during tests')
        requests.sessions.Session.request = offline
        return pytest.main(sys.argv[1:] or ['-q'])


if __name__ == '__main__':
    raise SystemExit(main())
