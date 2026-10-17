"""Lectura completa del catálogo EXIF en formatos y rutas multiplataforma."""
import json

import piexif
import pytest
from PIL import Image
from PIL.TiffImagePlugin import IFDRational

from app.modules import metadata


def _crear_imagen(path, formato):
    exif = {
        '0th': {piexif.ImageIFD.Orientation: 1},
        'Exif': {piexif.ExifIFD.ColorSpace: 1},
        'GPS': {}, '1st': {},
    }
    Image.new('RGB', (32, 24), 'white').save(path, formato, exif=piexif.dump(exif))


def _editar(path, campos, **opciones):
    request, error = metadata.preparar_campos_exif(campos, **opciones)
    assert error is None
    assert metadata.editar_exif(str(path), str(path), request) == (True, None)
    result, error = metadata.leer_metadatos_safe(str(path))
    assert error is None
    return result


@pytest.mark.parametrize('formato,extension', [('JPEG', 'jpg'), ('TIFF', 'tiff')])
def test_ver_muestra_los_cinco_campos_del_ejemplo(tmp_path, formato, extension):
    path = tmp_path / f'gáto con espacios.{extension}'
    _crear_imagen(path, formato)
    campos = {
        'ImageDescription': 'Gato', 'Artist': 'Guille', 'Copyright': 'CAT',
        'UserComment': 'Un gato mirando', 'Software': 'Yagua',
    }
    result = _editar(path, campos)
    for nombre, valor in campos.items():
        assert result[metadata.CAMPOS_VISIBLES[nombre][0]] == valor
    assert result['Autor'] == 'Guille'
    assert result['Software'] == 'Yagua'


@pytest.mark.parametrize('formato,extension', [('JPEG', 'jpg'), ('TIFF', 'tiff')])
def test_ver_cubre_editor_secciones_y_exportaciones(tmp_path, formato, extension):
    path = tmp_path / f'completa.{extension}'
    _crear_imagen(path, formato)
    campos = {
        'ImageDescription': 'Cámara, café y 日本語', 'Artist': 'Guille',
        'Copyright': 'CAT', 'UserComment': 'Un gato mirando 👀\nSegunda línea',
        'Software': 'Yagua', 'Make': 'Marca', 'Model': 'Modelo',
        'LensMake': 'Lente marca', 'LensModel': 'Lente modelo',
        'ExposureTime': '1/250', 'FNumber': '2.8', 'ISOSpeedRatings': '400',
        'FocalLength': '35.5', 'FocalLengthIn35mmFilm': '50',
        'ExposureProgram': '0', 'ExposureMode': '0', 'ExposureBiasValue': '0',
        'MeteringMode': '0', 'Flash': '0', 'WhiteBalance': '0', 'LightSource': '0',
        'GPSLatitude': '0', 'GPSLongitude': '0', 'GPSAltitude': '0',
        'GPSImgDirection': '0', 'DateTimeOriginal': '2026-10-16 10:30',
    }
    result = _editar(path, campos, sync_dates=True)
    assert set(campos) == set(metadata.CAMPOS_EDITABLES)
    assert all(metadata.CAMPOS_VISIBLES[nombre][0] in result for nombre in campos)
    assert result['Descripcion de imagen'] == campos['ImageDescription']
    assert result['Comentario'] == campos['UserComment']
    assert result['Velocidad obturacion'] == '1/250s'
    assert result['Apertura'] == 'f/2.8'
    assert result['Focal'] == '35.5mm'
    assert result['ISO'] == '400'
    assert result['Flash'] == '0'
    assert result['Altitud GPS'] == '0 m'
    assert result['Direccion GPS'] == '0°'
    assert result['__gps_decimal__'] == '0.0,0.0'
    assert result['Fecha original'] == result['Fecha digitalizada'] == result['Fecha y hora']
    assert result['Orientacion'] == result['Espacio de color'] == '1'
    for extension in ('txt', 'json'):
        output = tmp_path / ('export.' + extension)
        metadata.exportar_metadatos(result, output, extension)
        text = output.read_text(encoding='utf-8')
        assert '__gps_decimal__' not in text
        if extension == 'json':
            assert json.loads(text) == {key: value for key, value in result.items() if not key.startswith('__')}
        else:
            for key, value in result.items():
                if not key.startswith('__'):
                    assert key in text and value in text


@pytest.mark.parametrize('formato,extension', [('PNG', 'png'), ('WEBP', 'webp')])
def test_visor_conserva_lectura_en_formatos_no_editables(tmp_path, formato, extension):
    path = tmp_path / ('original.' + extension)
    exif = {'0th': {piexif.ImageIFD.ImageDescription: b'Gato'},
            'Exif': {piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump('Café', encoding='unicode')},
            'GPS': {}, '1st': {}}
    Image.new('RGB', (16, 16), 'white').save(path, formato, exif=piexif.dump(exif))
    result = metadata.leer_metadatos(path)
    assert result['Descripcion de imagen'] == 'Gato'
    assert result['Comentario'] == 'Café'


@pytest.mark.parametrize('nombre,valor,esperado', [
    ('ExposureTime', IFDRational(1, 250), '1/250s'),
    ('ExposureTime', (0, 1), '0s'),
    ('FNumber', IFDRational(28, 10), 'f/2.8'),
    ('FocalLength', (71, 2), '35.5mm'),
    ('ImageDescription', b'\x00\x00', ''),
    ('UserComment', piexif.helper.UserComment.dump('Gato 日本語 👀', encoding='unicode'), 'Gato 日本語 👀'),
])
def test_formatear_racionales_unicode_y_cero(nombre, valor, esperado):
    assert metadata._formatear_valor(nombre, valor) == esperado


@pytest.mark.parametrize('formato,extension', [('JPEG', 'jpg'), ('TIFF', 'tiff')])
def test_descripcion_utf8_no_se_muestra_como_latin1(tmp_path, formato, extension):
    path = tmp_path / f'unicode.{extension}'
    _crear_imagen(path, formato)
    result = _editar(path, {'ImageDescription': 'Cámara, café y 日本語'})
    assert result['Descripcion de imagen'] == 'Cámara, café y 日本語'


def test_dimensiones_guardadas_en_ifd_de_captura(tmp_path):
    path = tmp_path / 'dimensiones.jpg'
    exif = {'0th': {}, 'GPS': {}, '1st': {}, 'Exif': {
        piexif.ExifIFD.PixelXDimension: 32,
        piexif.ExifIFD.PixelYDimension: 24,
    }}
    Image.new('RGB', (32, 24), 'white').save(path, 'JPEG', exif=piexif.dump(exif))
    assert metadata.leer_metadatos(path) == {'Ancho': '32', 'Alto': '24'}


def test_lee_ifds_antes_de_cerrar_y_aisla_un_campo_roto(monkeypatch):
    class Source:
        opened = False

        def __enter__(self):
            self.opened = True
            return self

        def __exit__(self, *_):
            self.opened = False

        def getexif(self):
            source = self

            class Exif(dict):
                def get_ifd(self, tag):
                    assert source.opened, 'EXIF accessed after image was closed'
                    if tag == 34665:
                        return {piexif.ExifIFD.FNumber: (1, 0),
                                piexif.ExifIFD.UserComment: b'ASCII\x00\x00\x00Comentario',
                                piexif.ExifIFD.MakerNote: b'binary'}
                    return {1: b'S', 2: ((34, 1), (30, 1), (0, 1)),
                            3: b'W', 4: ((58, 1), (0, 1), (0, 1))}

            return Exif({piexif.ImageIFD.Artist: 'Guille', piexif.ImageIFD.Software: 'Yagua',
                         piexif.ImageIFD.ImageDescription: '', 65500: 'unknown'})

    monkeypatch.setattr(metadata.Image, 'open', lambda _: Source())
    result = metadata.leer_metadatos('virtual.jpg')
    assert result['Autor'] == 'Guille' and result['Comentario'] == 'Comentario'
    assert result['__gps_decimal__'] == '-34.5,-58.0'
    assert result['Latitud GPS'].endswith(' S')
    assert 'Apertura' not in result
    assert 'Descripcion de imagen' not in result
    assert 'MakerNote' not in result and 'unknown' not in result.values()


def test_un_bloque_roto_no_oculta_los_campos_principales(monkeypatch):
    class Exif(dict):
        def get_ifd(self, _):
            raise ValueError('IFD roto')

    class Source:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def getexif(self):
            return Exif({piexif.ImageIFD.Software: 'Yagua'})

    monkeypatch.setattr(metadata.Image, 'open', lambda _: Source())
    assert metadata.leer_metadatos('virtual.jpg') == {'Software': 'Yagua'}


def test_imagen_sin_exif_y_catalogo_compartido(tmp_path):
    path = tmp_path / 'sin-exif.jpg'
    Image.new('RGB', (16, 16), 'white').save(path)
    assert metadata.leer_metadatos(path) == {}
    assert set(metadata.CAMPOS_VISIBLES) == set(metadata._TAGS_VISIBLES)
    assert set(metadata.CAMPOS_EDITABLES) <= set(metadata.CAMPOS_VISIBLES)
    grupos = [nombre for campos in metadata.GRUPOS_CAMPOS_VISIBLES.values() for nombre in campos]
    assert len(grupos) == len(set(grupos))
    assert set(grupos) == set(metadata.CAMPOS_VISIBLES)
