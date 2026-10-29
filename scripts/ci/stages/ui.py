"""Herramientas de mantenimiento, verificación y empaquetado del proyecto. ui."""

from scripts.ci.stages.common import PYTHON, REPORTS, save, test_dependencies, xvfb
from scripts.ci.partitions import ui_selections
from xml.etree import ElementTree as ET


def merge_reports(paths, destination):
    """Keep the existing complete UI report, refusing failed or empty reports."""
    combined = ET.Element('testsuites')
    for path in paths:
        root = ET.parse(path).getroot()
        suites = [root] if root.tag == 'testsuite' else list(root)
        if not suites or not sum(int(suite.get('tests', 0)) for suite in suites):
            raise ValueError('Missing UI test results')
        for suite in suites:
            if int(suite.get('failures', 0)) or int(suite.get('errors', 0)):
                raise ValueError('Cannot approve failing UI results')
            combined.append(suite)
    ET.ElementTree(combined).write(destination, encoding='utf-8', xml_declaration=True)


def main():
    """Ejecuta la suite de interfaz con Tk disponible en el entorno de CI."""
    test_dependencies()
    REPORTS.mkdir(exist_ok=True)
    for name, selection in zip(('priority', 'remaining'), ui_selections()):
        xvfb(PYTHON, 'scripts/verify.py', '-q', *selection, '--maxfail=1', '--durations=15',
             '-o', 'faulthandler_timeout=60', f'--junitxml=reports/ui-{name}.xml')
    merge_reports([REPORTS / 'ui-priority.xml', REPORTS / 'ui-remaining.xml'], REPORTS / 'ui.xml')
    save('reports/ui.xml', 'reports/ui-priority.xml', 'reports/ui-remaining.xml')


if __name__ == '__main__':
    main()
