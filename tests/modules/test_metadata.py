from pathlib import Path

import pytest

import piexif
from PIL import Image

from app.modules.metadata import (
    editar_exif,
    leer_campos_edicion,
    leer_metadatos_safe,
    limpiar_exif,
    preparar_campos_exif,
)


def test_leer_metadatos_safe(fixtures_dir: Path):
    entrada = fixtures_dir / "sample.jpg"
    data, error = leer_metadatos_safe(str(entrada))

    assert error is None
    assert isinstance(data, dict)


def test_limpiar_exif(tmp_path: Path, fixtures_dir: Path):
    entrada = fixtures_dir / "sample.jpg"
    salida = tmp_path / "sample_sin_exif.jpg"

    res = limpiar_exif(str(entrada), str(salida))
    assert Path(res["ruta_salida"]).exists()


def test_editar_exif(tmp_path: Path, fixtures_dir: Path):
    entrada = fixtures_dir / "sample.jpg"
    salida = tmp_path / "sample_edit_exif.jpg"

    ok, warning = editar_exif(
        str(entrada),
        str(salida),
        {"Artist": "Test", "Software": "Yagua"},
    )
    assert ok is True


@pytest.mark.parametrize(
    ('entrada', 'esperada'),
    [
        ('2025:03:04 05:06:07', '2025:03:04 05:06:07'),
        ('2025-03-04 05:06:07', '2025:03:04 05:06:07'),
        ('04-03-2025 05:06:07', '2025:03:04 05:06:07'),
        ('2025-03-04 05:06', '2025:03:04 05:06:00'),
        ('04-03-2025 05:06', '2025:03:04 05:06:00'),
        ('2025:03:04 05:06', '2025:03:04 05:06:00'),
    ],
)
def test_preparar_campos_exif_normaliza_fechas(entrada: str, esperada: str):
    campos, error = preparar_campos_exif({'DateTimeOriginal': entrada})

    assert error is None
    assert campos.values == {'DateTimeOriginal': esperada}


@pytest.mark.parametrize(
    'entrada',
    [
        '2025-02-29 05:06',
        '2025-13-04 05:06',
        '31-04-2025 05:06',
        '2025-03-04 24:00',
        '04/03/2025 05:06',
        '2025-03-04',
    ],
)
def test_preparar_campos_exif_rechaza_fechas_invalidas(entrada: str):
    campos, error = preparar_campos_exif({'DateTimeOriginal': entrada})

    assert campos is None
    assert error == 'invalid_date'


def test_campos_exif_son_opcionales_y_vacios_no_cambian():
    request, error = preparar_campos_exif({'Artist': '', 'Model': '  '})

    assert request is None
    assert error == 'empty'


def test_preparar_campos_exif_parsea_racionales_enumeraciones_y_fecha_sync():
    request, error = preparar_campos_exif(
        {
            'ExposureTime': '1/250',
            'FNumber': '2.8',
            'ISOSpeedRatings': '400',
            'ExposureProgram': '3',
            'DateTimeOriginal': '2025-03-04 05:06',
        },
        sync_dates=True,
    )

    assert error is None
    assert request.values == {
        'ExposureTime': (1, 250),
        'FNumber': (14, 5),
        'ISOSpeedRatings': 400,
        'ExposureProgram': 3,
        'DateTimeOriginal': '2025:03:04 05:06:00',
    }
    assert request.sync_dates is True


@pytest.mark.parametrize(
    ('campos', 'opciones', 'error_esperado'),
    [
        ({'ExposureTime': '0'}, {}, 'invalid_number'),
        ({'FNumber': 'nan'}, {}, 'invalid_number'),
        ({'ISOSpeedRatings': '-1'}, {}, 'invalid_number'),
        ({'ExposureProgram': '99'}, {}, 'invalid_option'),
        ({'GPSLatitude': '-34.6'}, {}, 'gps_pair'),
        ({'GPSLatitude': '90.1', 'GPSLongitude': '0'}, {}, 'invalid_gps'),
        ({'GPSLatitude': '0', 'GPSLongitude': '180.1'}, {}, 'invalid_gps'),
        ({'GPSLatitude': '0', 'GPSLongitude': '0', 'GPSImgDirection': '360'}, {}, 'invalid_gps'),
        ({'GPSLatitude': '0', 'GPSLongitude': '0'}, {'clear_gps': True}, 'gps_conflict'),
        ({}, {'sync_dates': True}, 'sync_requires_date'),
        ({}, {'orientation': 9}, 'invalid_orientation'),
    ],
)
def test_preparar_campos_exif_rechaza_valores_y_opciones_invalidas(
    campos, opciones, error_esperado
):
    _, error = preparar_campos_exif(campos, **opciones)

    assert error == error_esperado


def _imagen_con_exif(path, formato):
    imagen = Image.new('RGB', (3, 2), color='white')
    exif = {
        '0th': {
            piexif.ImageIFD.Make: b'Camara original',
            piexif.ImageIFD.DateTime: b'2019:12:31 23:59:59',
        },
        'Exif': {
            piexif.ExifIFD.DateTimeOriginal: b'2020:01:02 03:04:05',
            piexif.ExifIFD.DateTimeDigitized: b'2020:01:03 04:05:06',
        },
        'GPS': {},
        '1st': {},
    }
    imagen.save(path, formato, exif=piexif.dump(exif))


@pytest.mark.parametrize(('formato', 'extension'), [('JPEG', '.jpg'), ('TIFF', '.tiff')])
def test_editar_exif_guarda_campos_y_conserva_lo_no_editado(tmp_path, formato, extension):
    entrada = tmp_path / f'entrada{extension}'
    salida = tmp_path / f'salida{extension}'
    _imagen_con_exif(entrada, formato)
    request, error = preparar_campos_exif(
        {
            'ImageDescription': 'Foto de prueba',
            'Artist': 'Autora',
            'UserComment': 'Comentario de prueba',
            'FNumber': '2.8',
            'ExposureTime': '1/250',
            'ISOSpeedRatings': '200',
            'GPSLatitude': '-34.6037',
            'GPSLongitude': '-58.3816',
            'GPSAltitude': '25.5',
            'GPSImgDirection': '45',
            'DateTimeOriginal': '2025-03-04 05:06',
        },
        sync_dates=True,
    )

    assert error is None
    assert editar_exif(str(entrada), str(salida), request) == (True, None)
    exif = piexif.load(str(salida))
    assert exif['0th'][piexif.ImageIFD.Make] == b'Camara original'
    assert exif['0th'][piexif.ImageIFD.ImageDescription] == 'Foto de prueba'.encode()
    assert exif['0th'][piexif.ImageIFD.Artist] == 'Autora'.encode()
    assert exif['Exif'][piexif.ExifIFD.FNumber] == (14, 5)
    assert exif['Exif'][piexif.ExifIFD.ExposureTime] == (1, 250)
    assert exif['Exif'][piexif.ExifIFD.ISOSpeedRatings] == 200
    assert exif['Exif'][piexif.ExifIFD.DateTimeOriginal] == b'2025:03:04 05:06:00'
    assert exif['Exif'][piexif.ExifIFD.DateTimeDigitized] == b'2025:03:04 05:06:00'
    assert exif['0th'][piexif.ImageIFD.DateTime] == b'2025:03:04 05:06:00'
    campos = leer_campos_edicion(str(salida))
    assert campos['UserComment'] == 'Comentario de prueba'
    assert campos['GPSLatitude'] == '-34.6037'
    assert campos['GPSLongitude'] == '-58.3816'
    assert campos['GPSAltitude'] == '25.5'
    assert campos['GPSImgDirection'] == '45'


def test_editar_exif_no_sincroniza_fechas_si_no_se_pide(tmp_path):
    entrada = tmp_path / 'entrada.jpg'
    salida = tmp_path / 'salida.jpg'
    _imagen_con_exif(entrada, 'JPEG')
    request, error = preparar_campos_exif({'Artist': 'Nueva autora'})

    assert error is None
    assert editar_exif(str(entrada), str(salida), request) == (True, None)
    exif = piexif.load(str(salida))
    assert exif['0th'][piexif.ImageIFD.DateTime] == b'2019:12:31 23:59:59'
    assert exif['Exif'][piexif.ExifIFD.DateTimeOriginal] == b'2020:01:02 03:04:05'
    assert exif['Exif'][piexif.ExifIFD.DateTimeDigitized] == b'2020:01:03 04:05:06'


@pytest.mark.parametrize(('formato', 'extension'), [('JPEG', '.jpg'), ('TIFF', '.tiff')])
def test_editar_exif_permite_guardar_sobre_el_mismo_archivo(tmp_path, formato, extension):
    ruta = tmp_path / f'original{extension}'
    _imagen_con_exif(ruta, formato)
    request, error = preparar_campos_exif({'Artist': 'Autora nueva'})

    assert error is None
    assert editar_exif(str(ruta), str(ruta), request) == (True, None)
    assert piexif.load(str(ruta))['0th'][piexif.ImageIFD.Artist] == b'Autora nueva'


def test_editar_exif_quita_gps_solo_con_accion_explicita(tmp_path):
    entrada = tmp_path / 'entrada.jpg'
    salida = tmp_path / 'salida.jpg'
    _imagen_con_exif(entrada, 'JPEG')
    exif = piexif.load(str(entrada))
    exif['GPS'] = {
        piexif.GPSIFD.GPSLatitudeRef: b'S',
        piexif.GPSIFD.GPSLatitude: ((34, 1), (0, 1), (0, 1)),
        piexif.GPSIFD.GPSLongitudeRef: b'W',
        piexif.GPSIFD.GPSLongitude: ((58, 1), (0, 1), (0, 1)),
    }
    with Image.open(entrada) as imagen:
        imagen.save(entrada, 'JPEG', exif=piexif.dump(exif))

    request, error = preparar_campos_exif({}, clear_gps=True)

    assert error is None
    assert editar_exif(str(entrada), str(salida), request) == (True, None)
    assert piexif.load(str(salida))['GPS'] == {}


def test_editar_exif_orienta_pixeles_y_normaliza_tag(tmp_path):
    entrada = tmp_path / 'entrada.tiff'
    salida = tmp_path / 'salida.tiff'
    _imagen_con_exif(entrada, 'TIFF')
    exif_original = {
        '0th': {piexif.ImageIFD.Make: b'Camara original'},
        'Exif': {}, 'GPS': {}, '1st': {},
    }
    imagen = Image.new('RGB', (2, 3))
    imagen.putdata([
        (255, 0, 0), (0, 255, 0),
        (0, 0, 255), (255, 255, 0),
        (0, 0, 0), (255, 255, 255),
    ])
    imagen.save(entrada, 'TIFF', exif=piexif.dump(exif_original))
    request, error = preparar_campos_exif({}, orientation=6)

    assert error is None
    assert editar_exif(str(entrada), str(salida), request) == (True, None)
    with Image.open(salida) as resultado:
        assert resultado.size == (3, 2)
        assert list(resultado.get_flattened_data()) == [
            (0, 0, 0), (0, 0, 255), (255, 0, 0),
            (255, 255, 255), (255, 255, 0), (0, 255, 0),
        ]
        assert resultado.getexif().get(piexif.ImageIFD.Orientation) == 1
    assert piexif.load(str(salida))['0th'][piexif.ImageIFD.Make] == b'Camara original'
