"""Keep translation keys and formatting contracts aligned across all languages."""
import ast
from pathlib import Path
import re

import pytest

from app.translations import AVAILABLE_LANGUAGES, get_translations


@pytest.mark.parametrize('language', list(AVAILABLE_LANGUAGES))
def test_translation_keys_and_parameters_match(language):
    reference = get_translations('English')
    actual = get_translations(language)
    assert actual.keys() == reference.keys()
    for key, text in reference.items():
        assert set(re.findall(r'\{(\w+)\}', text)) == set(re.findall(r'\{(\w+)\}', actual[key])), key


def test_static_translation_keys_exist():
    reference = get_translations('English')
    root = Path(__file__).resolve().parents[1] / 'app'
    missing = []
    for path in root.rglob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == 't' and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                    and node.args[0].value not in reference):
                missing.append((str(path.relative_to(root)), node.lineno, node.args[0].value))
    assert missing == []
