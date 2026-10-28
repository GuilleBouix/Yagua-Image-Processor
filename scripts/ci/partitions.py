"""Comprueba que las particiones ejecuten los mismos tests que la suite completa."""
import subprocess
import sys


def collected(*selection):
    """Enumera los módulos incluidos en la recopilación de PyInstaller."""
    result = subprocess.run([sys.executable, 'scripts/verify.py', '--collect-only', '-q', *selection],
                            check=True, capture_output=True, text=True)
    return {line for line in result.stdout.splitlines() if line.startswith('tests/') and '::' in line}


def main():
    """Comprueba la partición del paquete entre runtime y dependencias excluidas."""
    full = collected()
    core = collected('--ignore=tests/ui')
    ui = collected('tests/ui')
    if not full or core & ui or core | ui != full:
        raise ValueError(f'Invalid test partitions: full={len(full)}, core={len(core)}, ui={len(ui)}')
    print(f'Collection partition verified: {len(core)} core + {len(ui)} UI = {len(full)} tests')


if __name__ == '__main__':
    main()
