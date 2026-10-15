"""
Ejecutar aplicación
"""

import os
from pathlib import Path

from app.main import main


if __name__ == '__main__':
    if os.environ.get('YAGUA_PACKAGE_SELFTEST'):
        from app.utils.package_selftest import run

        raise SystemExit(run(Path(os.environ['YAGUA_PACKAGE_SELFTEST'])))
    main()
