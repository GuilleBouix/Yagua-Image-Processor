"""Herramientas de mantenimiento, verificación y empaquetado del proyecto. core."""

from scripts.ci.stages.common import PYTHON, REPORTS, save, test_dependencies, xvfb


def main():
    """Ejecuta las pruebas de lógica que no requieren una ventana Tk."""
    test_dependencies()
    REPORTS.mkdir(exist_ok=True)
    xvfb(PYTHON, 'scripts/ci/partitions.py')
    xvfb(PYTHON, 'scripts/verify.py', '-q', '--ignore=tests/ui', '--junitxml=reports/core.xml')
    save('reports/core.xml')


if __name__ == '__main__':
    main()
