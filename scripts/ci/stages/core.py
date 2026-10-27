from scripts.ci.stages.common import PYTHON, REPORTS, save, test_dependencies, xvfb


def main():
    test_dependencies()
    REPORTS.mkdir(exist_ok=True)
    xvfb(PYTHON, 'scripts/ci/partitions.py')
    xvfb(PYTHON, 'scripts/verify.py', '-q', '--ignore=tests/ui', '--junitxml=reports/core.xml')
    save('reports/core.xml')


if __name__ == '__main__':
    main()
