from scripts.ci.stages.common import PYTHON, REPORTS, save, test_dependencies, xvfb


def main():
    test_dependencies()
    REPORTS.mkdir(exist_ok=True)
    xvfb(PYTHON, 'scripts/verify.py', '-q', 'tests/ui', '--junitxml=reports/ui.xml')
    save('reports/ui.xml')


if __name__ == '__main__':
    main()
