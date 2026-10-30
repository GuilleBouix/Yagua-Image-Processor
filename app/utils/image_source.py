"""Recognize camera JPEG/MPO previews without flattening real image collections."""
from pathlib import Path

from PIL import Image


def mpo_preview_count(image: Image.Image) -> int:
    """Accept only a leading primary JPEG followed by explicitly tagged small previews.

    Undefined, stereo, panorama and malformed MP entries remain unsupported. Reading
    the frame headers verifies that a claimed preview is smaller than the primary;
    the caller's selected frame and EXIF are restored before returning.
    """
    if image.format != 'MPO':
        return 0
    frame = image.tell()
    try:
        entries = getattr(image, 'mpinfo', {}).get(0xB002, [])
        count = getattr(image, 'n_frames', 1)
        if count < 2 or len(entries) != count:
            return 0
        if entries[0]['Attribute']['MPType'] != 'Baseline MP Primary Image':
            return 0
        previews = {'Large Thumbnail (VGA Equivalent)', 'Large Thumbnail (Full HD Equivalent)'}
        if any(entry['Attribute']['MPType'] not in previews for entry in entries[1:]):
            return 0
        if any(entry['Attribute']['ImageDataFormat'] != 'JPEG' or entry['Size'] <= 0 for entry in entries):
            return 0
        image.seek(0)
        width, height = image.size
        for index in range(1, count):
            image.seek(index)
            if image.width > width or image.height > height or image.width * image.height >= width * height:
                return 0
        return count - 1
    except (KeyError, TypeError, ValueError, OSError, IndexError):
        return 0
    finally:
        image.seek(frame)


def primary_jpeg_bytes(path: str | Path) -> bytes:
    """Extract a validated primary JPEG and remove its obsolete MPF index losslessly.

    Metadata-only edits use these bytes instead of copying MPO offsets and secondary
    JPEGs into an output whose layout no longer matches that index. ICC/EXIF markers
    and compressed pixel data are preserved; no JPEG encoding is performed here.
    """
    with Image.open(path) as image:
        if not mpo_preview_count(image):
            raise ValueError('unsupported_frames')
        entries = getattr(image, 'mpinfo')[0xB002]
        length = entries[0]['Size']
    with open(path, 'rb') as stream:
        data = stream.read(length)
    if len(data) != length or not data.startswith(b'\xff\xd8') or not data.endswith(b'\xff\xd9'):
        raise ValueError('unsupported_frames')
    chunks, position, removed = [data[:2]], 2, False
    while position < len(data):
        start = position
        if data[position] != 0xFF:
            raise ValueError('unsupported_frames')
        while position < len(data) and data[position] == 0xFF:
            position += 1
        if position >= len(data):
            raise ValueError('unsupported_frames')
        marker = data[position]
        position += 1
        if marker == 0xDA:  # SOS: the remaining bytes include the compressed image.
            if not removed:
                raise ValueError('unsupported_frames')
            return b''.join(chunks) + data[start:]
        if position + 2 > len(data):
            raise ValueError('unsupported_frames')
        size = int.from_bytes(data[position:position + 2], 'big')
        end = position + size
        if size < 2 or end > len(data):
            raise ValueError('unsupported_frames')
        if marker == 0xE2 and data[position + 2:position + 6] == b'MPF\0':
            # MP offsets are relative to the TIFF header after the MPF signature.
            # A corrupt primary size must not copy secondary JPEG bytes as a tail.
            if length > min(position + 6 + entry['DataOffset'] for entry in entries[1:]):
                raise ValueError('unsupported_frames')
            removed = True
        else:
            chunks.append(data[start:end])
        position = end
    raise ValueError('unsupported_frames')
