"""Check bundled font integrity and glyph coverage without a runtime dependency."""
import hashlib
import json
from pathlib import Path
import struct
from types import SimpleNamespace

import pytest

from app.ui import fonts
from app.translations import get_translations

ROOT = Path(__file__).resolve().parents[1]


def _unicode_glyphs(path):
    data = path.read_bytes()
    def u16(offset):
        return struct.unpack_from('>H', data, offset)[0]
    def u32(offset):
        return struct.unpack_from('>I', data, offset)[0]
    tables = {data[pos:pos + 4]: u32(pos + 8) for pos in range(12, 12 + u16(4) * 16, 16)}
    cmap = tables[b'cmap']
    glyphs = set()
    for pos in range(cmap + 4, cmap + 4 + u16(cmap + 2) * 8, 8):
        platform, encoding = u16(pos), u16(pos + 2)
        if platform != 0 and (platform, encoding) not in {(3, 1), (3, 10)}:
            continue
        base = cmap + u32(pos + 4)
        if u16(base) == 12:
            for group in range(base + 16, base + 16 + u32(base + 12) * 12, 12):
                start, end, glyph = struct.unpack_from('>III', data, group)
                glyphs.update(range(start + (glyph == 0), end + 1))
        elif u16(base) == 4:
            count = u16(base + 6) // 2
            ends = base + 14
            starts = ends + count * 2 + 2
            deltas = starts + count * 2
            offsets = deltas + count * 2
            for index in range(count):
                delta = u16(deltas + index * 2)
                slot = offsets + index * 2
                offset = u16(slot)
                start, end = u16(starts + index * 2), u16(ends + index * 2)
                for code in range(start, min(end, 0xfffe) + 1):
                    glyph = u16(slot + offset + (code - start) * 2) if offset else code
                    if (not offset or glyph) and (glyph + delta) & 0xffff:
                        glyphs.add(code)
    return glyphs


@pytest.mark.parametrize(('language', 'region'), [('日本語', 'jp'), ('简体中文', 'sc'), ('Русский', None)])
def test_bundled_fonts_cover_translations_and_native_language_names(language, region):
    text = ''.join(get_translations(language).values()) + '日本語简体中文РусскийItaliano'
    required = {ord(char) for char in text if not char.isspace()}
    files = ([ROOT / relative for relative in fonts.CJK_FONTS if f'CJK{region}-' in relative]
             if region else [ROOT / fonts.RUTA_FUENTE_INTER])
    native_cjk = {ord(char) for char in '日本語简体中文'}
    for path in files:
        missing = required - _unicode_glyphs(path)
        if region is None:
            missing -= native_cjk  # Covered by the privately registered CJK fallback.
        assert not missing, (path.name, ''.join(chr(code) for code in sorted(missing)))


def test_font_manifest_is_pinned_and_matches_all_bundled_bytes():
    directory = ROOT / 'assets/fonts/noto-cjk'
    attributes = (ROOT / '.gitattributes').read_text(encoding='utf-8')
    assert 'assets/fonts/noto-cjk/LICENSE text eol=lf' in attributes
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['revision'] == '523d033d6cb47f4a80c58a35753646f5c3608a78'
    assert set(manifest['files']) == {Path(path).name for path in fonts.CJK_FONTS} | {'LICENSE'}
    for name, item in manifest['files'].items():
        data = (directory / name).read_bytes()
        assert len(data) == item['bytes']
        assert hashlib.sha256(data).hexdigest() == item['sha256']
    assert manifest['font_bytes'] == sum((directory / Path(path).name).stat().st_size for path in fonts.CJK_FONTS)


@pytest.mark.parametrize('platform', ['win32', 'linux'])
def test_native_registration_is_process_private(monkeypatch, tmp_path, platform):
    path = tmp_path / '日本語.otf'
    calls = []
    def add(*args):
        calls.append(args)
        return 1
    monkeypatch.setattr(fonts.sys, 'platform', platform)
    if platform == 'win32':
        library = SimpleNamespace(AddFontResourceExW=add)
        monkeypatch.setattr(fonts.ctypes, 'WinDLL', lambda *args, **kwargs: library, raising=False)
    else:
        library = SimpleNamespace(FcConfigGetCurrent=lambda: 123, FcConfigAppFontAddFile=add)
        monkeypatch.setattr(fonts.ctypes, 'CDLL', lambda *args: library)
        monkeypatch.setattr(fonts.ctypes.util, 'find_library', lambda _: 'libfontconfig.so.1')
    assert fonts._register_font(path)
    assert calls == ([(str(path), 0x10, None)] if platform == 'win32' else [(123, bytes(path))])


def test_registration_is_idempotent_and_does_not_copy_fonts(monkeypatch, tmp_path):
    path = tmp_path / 'font.otf'
    path.write_bytes(b'font')
    calls = []
    monkeypatch.setattr(fonts, 'resource_path', lambda _: path)
    monkeypatch.setattr(fonts, '_registered', set())
    monkeypatch.setattr(fonts, '_register_font', lambda value: calls.append(value) or True)
    assert all(fonts.registrar_fuentes().values())
    assert all(fonts.registrar_fuentes().values())
    assert calls == [path]
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize('failure', ['missing', 'native-error', 'rejected'])
def test_font_registration_failure_is_logged_without_blocking_startup(monkeypatch, tmp_path, caplog, failure):
    path = tmp_path / 'font.otf'
    if failure != 'missing':
        path.touch()
    monkeypatch.setattr(fonts, 'resource_path', lambda _: path)
    monkeypatch.setattr(fonts, '_registered', set())
    def register(value):
        if failure == 'native-error':
            raise OSError('unavailable')
        return False
    monkeypatch.setattr(fonts, '_register_font', register)
    assert not any(fonts.registrar_fuentes().values())
    assert 'Could not register bundled font' in caplog.text
