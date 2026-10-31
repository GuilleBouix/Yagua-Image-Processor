"""Lossless EXIF updates for static PNG/WebP containers.

Image payloads are copied verbatim. Only explicit pixel transformations use an
encoder; these helpers validate framing before writing an atomic stage file.
"""
from __future__ import annotations

from pathlib import Path
import struct
import zlib

import piexif
from PIL.PngImagePlugin import PngInfo

SUPPORTED_FORMATS = frozenset(('JPEG', 'TIFF', 'PNG', 'WEBP'))
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


def png_chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    """Validate lengths, CRCs and critical PNG framing without decoding pixels."""
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError('invalid_metadata_container')
    chunks, offset = [], 8
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError('invalid_metadata_container')
        size = struct.unpack_from('>I', data, offset)[0]
        end = offset + size + 12
        if size > 0x7fffffff or end > len(data):
            raise ValueError('invalid_metadata_container')
        kind, payload = data[offset + 4:offset + 8], data[offset + 8:end - 4]
        if (not all(65 <= value <= 90 or 97 <= value <= 122 for value in kind)
                or kind[2] & 32 or (not kind[0] & 32 and kind not in (b'IHDR', b'PLTE', b'IDAT', b'IEND'))):
            raise ValueError('invalid_metadata_container')
        if zlib.crc32(kind + payload) & 0xffffffff != struct.unpack_from('>I', data, end - 4)[0]:
            raise ValueError('invalid_metadata_container')
        chunks.append((kind, payload))
        offset = end
        if kind == b'IEND':
            break
    kinds = [kind for kind, _ in chunks]
    if (offset != len(data) or not chunks or kinds[0] != b'IHDR' or len(chunks[0][1]) != 13
            or kinds[-1] != b'IEND' or chunks[-1][1] or b'IDAT' not in kinds
            or kinds.count(b'IHDR') != 1 or kinds.count(b'eXIf') > 1):
        raise ValueError('invalid_metadata_container')
    indices = [i for i, kind in enumerate(kinds) if kind == b'IDAT']
    if indices != list(range(indices[0], indices[-1] + 1)):
        raise ValueError('invalid_metadata_container')
    return chunks


def webp_chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    """Validate RIFF framing including padding and the single-image payload."""
    if (len(data) < 12 or data[:4] != b'RIFF' or data[8:12] != b'WEBP'
            or struct.unpack_from('<I', data, 4)[0] + 8 != len(data)):
        raise ValueError('invalid_metadata_container')
    chunks, offset = [], 12
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError('invalid_metadata_container')
        kind = data[offset:offset + 4]
        size = struct.unpack_from('<I', data, offset + 4)[0]
        end = offset + 8 + size
        padded = end + size % 2
        if padded > len(data) or (size % 2 and data[end] != 0):
            raise ValueError('invalid_metadata_container')
        chunks.append((kind, data[offset + 8:end]))
        offset = padded
    kinds = [kind for kind, _ in chunks]
    if any(kind in kinds for kind in (b'ANIM', b'ANMF')):
        raise ValueError('unsupported_frames')
    if (sum(kind in (b'VP8 ', b'VP8L') for kind in kinds) != 1
            or kinds.count(b'EXIF') > 1 or kinds.count(b'VP8X') > 1
            or (b'VP8X' in kinds and (kinds[0] != b'VP8X' or len(chunks[0][1]) != 10))):
        raise ValueError('invalid_metadata_container')
    if any(kinds.count(kind) > 1 for kind in (b'ALPH', b'ICCP', b'XMP ')):
        raise ValueError('invalid_metadata_container')
    extended = next((payload for kind, payload in chunks if kind == b'VP8X'), None)
    features = ((b'ICCP', 0x20), (b'EXIF', 0x08), (b'XMP ', 0x04))
    if extended is None:
        if any(kind in kinds for kind, _ in features) or b'ALPH' in kinds:
            raise ValueError('invalid_metadata_container')
    elif (extended[0] & 0xc3 or extended[1:4] != b'\x00\x00\x00'
          or any(bool(extended[0] & flag) != (kind in kinds) for kind, flag in features)):
        raise ValueError('invalid_metadata_container')
    if b'ALPH' in kinds and (b'VP8L' in kinds or kinds.index(b'ALPH') > kinds.index(b'VP8 ')):
        raise ValueError('invalid_metadata_container')
    return chunks


def read_exif(path, fmt: str) -> dict:
    """Read EXIF bytes from a container, allowing images without an EXIF block."""
    if fmt not in ('PNG', 'WEBP'):
        return piexif.load(str(path))
    chunks = (png_chunks if fmt == 'PNG' else webp_chunks)(Path(path).read_bytes())
    tag = b'eXIf' if fmt == 'PNG' else b'EXIF'
    data = next((payload for kind, payload in chunks if kind == tag), None)
    if data is None:
        return {'0th': {}, 'Exif': {}, 'GPS': {}, 'Interop': {}, '1st': {}, 'thumbnail': None}
    if not data.startswith(b'Exif\x00\x00'):
        data = b'Exif\x00\x00' + data
    return piexif.load(data)


def rewrite(path, destination, fmt: str, *, exif: bytes | None = None, clean=False):
    """Replace EXIF or remove descriptive metadata while retaining image bytes."""
    data = Path(path).read_bytes()
    if fmt == 'PNG':
        chunks = png_chunks(data)
        if any(kind == b'acTL' for kind, _ in chunks):
            raise ValueError('unsupported_frames')
        removed = {b'eXIf', b'tEXt', b'zTXt', b'iTXt', b'tIME'} if clean else {b'eXIf'}
        chunks = [(kind, payload) for kind, payload in chunks if kind not in removed]
        if exif is not None:
            payload = exif[6:] if exif.startswith(b'Exif\x00\x00') else exif
            chunks.insert(1, (b'eXIf', payload))
        output = bytearray(PNG_SIGNATURE)
        for kind, payload in chunks:
            output += struct.pack('>I', len(payload)) + kind + payload
            output += struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff)
    else:
        chunks = webp_chunks(data)
        # piexif already creates/updates VP8X when inserting the EXIF chunk.
        if not clean and exif is not None:
            import io
            buffer = io.BytesIO()
            piexif.insert(exif, data, buffer)
            output = buffer.getvalue()
        else:
            chunks = [(kind, payload) for kind, payload in chunks if kind not in (b'EXIF', b'XMP ')]
            output = bytearray(b'RIFF\x00\x00\x00\x00WEBP')
            for kind, payload in chunks:
                if kind == b'VP8X':
                    payload = bytes((payload[0] & ~0x0c,)) + payload[1:]
                output += kind + struct.pack('<I', len(payload)) + payload + b'\x00' * (len(payload) % 2)
            struct.pack_into('<I', output, 4, len(output) - 8)
    (png_chunks if fmt == 'PNG' else webp_chunks)(bytes(output))
    Path(destination).write_bytes(output)


def _transform_png16(source, destination, *, exif, clean, orientation):
    """Use the existing OpenCV decoder for color depths Pillow reduces to 8 bits."""
    import cv2
    import numpy as np
    from PIL import Image

    chunks = png_chunks(Path(source).read_bytes())
    pixels = cv2.imdecode(np.frombuffer(Path(source).read_bytes(), dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if pixels is None or pixels.dtype != np.uint16:
        raise ValueError('invalid_metadata_container')
    with Image.open(source) as original:
        original_orientation = original.getexif().get(274, 1)
    for value in (original_orientation, orientation):
        if value == 2:
            pixels = np.flip(pixels, 1)
        elif value == 3:
            pixels = np.rot90(pixels, 2)
        elif value == 4:
            pixels = np.flip(pixels, 0)
        elif value == 5:
            pixels = pixels.swapaxes(0, 1)
        elif value == 6:
            pixels = np.rot90(pixels, 3)
        elif value == 7:
            pixels = np.flip(pixels.swapaxes(0, 1), (0, 1))
        elif value == 8:
            pixels = np.rot90(pixels, 1)
    ok, encoded = cv2.imencode('.png', np.ascontiguousarray(pixels))
    if not ok:
        raise OSError('error_saving')
    encoded_chunks = png_chunks(encoded.tobytes())
    removed = {b'eXIf', b'tEXt', b'zTXt', b'iTXt', b'tIME'} if clean else {b'eXIf'}
    metadata = []
    for kind, payload in chunks:
        if kind in removed or kind in (b'IHDR', b'IDAT', b'IEND', b'PLTE', b'tRNS'):
            continue
        # Only known rendering data and safe-to-copy ancillary chunks survive
        # a pixel transform. OpenCV expands grayscale+alpha to RGBA at 16 bits.
        if not kind[3] & 32 and kind not in (
                b'iCCP', b'gAMA', b'cHRM', b'sRGB', b'cICP', b'mDCV', b'cLLI', b'bKGD', b'sBIT', b'tIME'):
            continue
        if chunks[0][1][9] == 4:
            if kind == b'bKGD':
                payload *= 3
            elif kind == b'sBIT':
                payload = payload[:1] * 3 + payload[1:]
        metadata.append((kind, payload))
    if exif is not None:
        metadata.append((b'eXIf', exif[6:] if exif.startswith(b'Exif\x00\x00') else exif))
    result = bytearray(PNG_SIGNATURE)
    for kind, payload in encoded_chunks[:1] + metadata + encoded_chunks[1:]:
        result += struct.pack('>I', len(payload)) + kind + payload
        result += struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff)
    png_chunks(bytes(result))
    Path(destination).write_bytes(result)


def save_transformed(image, source, destination, fmt: str, *, exif=None, clean=False, orientation=None):
    """Encode an explicit orientation transform without additional pixel loss."""
    options = {}
    if fmt == 'PNG':
        header = png_chunks(Path(source).read_bytes())[0][1]
        if header[8] == 16 and header[9] in (2, 4, 6):
            _transform_png16(source, destination, exif=exif, clean=clean, orientation=orientation)
            return
    if image.info.get('icc_profile'):
        options['icc_profile'] = image.info['icc_profile']
    if fmt == 'PNG':
        info = PngInfo()
        for kind, payload in png_chunks(Path(source).read_bytes()):
            if kind in (b'gAMA', b'cHRM', b'sRGB', b'cICP', b'mDCV', b'cLLI', b'pHYs', b'sBIT', b'bKGD') or (
                    not clean and kind in (b'tEXt', b'zTXt', b'iTXt', b'tIME')):
                info.add(kind, payload)
        options['pnginfo'] = info
        if 'transparency' in image.info:
            options['transparency'] = image.info['transparency']
    else:
        options.update(lossless=True, exact=True)
        if not clean and image.info.get('xmp'):
            options['xmp'] = image.info['xmp']
    if exif is not None:
        options['exif'] = exif
    # PNG otherwise reuses image.info['exif'] even when no exif kwarg is passed.
    pixels = image.copy()
    pixels.info.clear()
    pixels.save(destination, fmt, **options)
