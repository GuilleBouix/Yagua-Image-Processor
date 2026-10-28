"""Herramientas de mantenimiento, verificación y empaquetado del proyecto. quality."""

from scripts.ci.stages.common import PYTHON, json_report, python, run, save, test_dependencies


def main():
    """Ejecuta lint, tipado y comprobaciones estáticas del código fuente."""
    test_dependencies()
    run('ruff', 'check', 'app', 'tests', 'scripts')
    run('pyright', '--pythonpath', PYTHON, 'app')
    python('scripts/ci/check_licenses.py', '--installed')
    json_report('validation/quality.json', {'status': 'passed'})
    save('reports/validation/quality.json')


if __name__ == '__main__':
    main()
