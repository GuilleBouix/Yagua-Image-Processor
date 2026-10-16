"""Keep translation keys and formatting contracts aligned across all languages."""
import ast
from pathlib import Path
from collections import Counter
from string import Formatter

import pytest

from app.translations import AVAILABLE_LANGUAGES, get_translations
from app import translations
from app.utils import settings
from app.languages import DEFAULT_LANGUAGE, LANGUAGE_MODULES


def _parameters(value):
    return Counter((field, spec, conversion) for _, field, spec, conversion
                   in Formatter().parse(value) if field is not None)


@pytest.mark.parametrize('language', list(AVAILABLE_LANGUAGES))
def test_translation_keys_and_parameters_match(language):
    reference = get_translations('English')
    actual = get_translations(language)
    assert actual.keys() == reference.keys()
    for key, text in reference.items():
        assert isinstance(actual[key], str) and actual[key].strip(), key
        assert _parameters(text) == _parameters(actual[key]), key


@pytest.mark.parametrize('language', list(AVAILABLE_LANGUAGES))
def test_language_roundtrip_preserves_identifiers(monkeypatch, tmp_path, language):
    path = tmp_path / 'settings.json'
    monkeypatch.setattr(translations, 'settings_path', lambda: path)
    monkeypatch.setattr(translations, '_current_lang', None)
    translations.set_language(language)
    assert settings.load_settings(path)['language'] == language
    translations._current_lang = None
    assert translations.get_language() == language


def test_language_registry_keeps_default_and_english_fallback():
    assert DEFAULT_LANGUAGE == 'Español'
    assert list(AVAILABLE_LANGUAGES) == [
        'Español', 'English', 'Portugues', 'Français', 'Deutsch',
        'Italiano', '日本語', '简体中文', 'Русский',
    ]
    assert set(AVAILABLE_LANGUAGES) == set(LANGUAGE_MODULES)
    assert get_translations('unknown') is get_translations('English')


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
