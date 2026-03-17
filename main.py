"""
Compat entrypoint: delega a app.main para mantener compatibilidad.
"""

from app.main import main


if __name__ == '__main__':
    main()
