"""Comprueba que las particiones ejecuten los mismos tests que la suite completa."""
import subprocess
import sys

# Exercise recent layout/preview changes first, without running them twice.
UI_PRIORITY = (
    'tests/ui/test_ui_fluency.py',
    'tests/ui/test_live_previews.py',
    'tests/ui/test_preview_stability.py',
    'tests/ui/test_resize_frame.py',
    'tests/ui/test_canvas_color.py',
    'tests/ui/test_palette_frame.py',
    'tests/ui/test_palette_batch.py',
)


def ui_selections():
    """Return disjoint priority and remaining UI selections for the same suite."""
    return UI_PRIORITY, ('tests/ui', *(f'--ignore={path}' for path in UI_PRIORITY))


def collected(*selection):
    """Collect exact pytest node IDs; collection errors stop validation."""
    result = subprocess.run([sys.executable, 'scripts/verify.py', '--collect-only', '-q', *selection],
                            check=True, capture_output=True, text=True)
    return {line for line in result.stdout.splitlines() if line.startswith('tests/') and '::' in line}


def main():
    """Require core/UI and priority/rest to cover the full suite exactly once."""
    full = collected()
    core = collected('--ignore=tests/ui')
    ui = collected('tests/ui')
    if not full or core & ui or core | ui != full:
        raise ValueError(f'Invalid test partitions: full={len(full)}, core={len(core)}, ui={len(ui)}')
    priority, remaining = (collected(*selection) for selection in ui_selections())
    if not priority or priority & remaining or priority | remaining != ui:
        raise ValueError('Invalid priority/rest UI partitions')
    print(f'Collection partition verified: {len(core)} core + {len(ui)} UI = {len(full)} tests')
    print(f'UI partition verified: {len(priority)} priority + {len(remaining)} remaining')


if __name__ == '__main__':
    main()
