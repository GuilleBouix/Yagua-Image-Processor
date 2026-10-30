"""Small generated camera MPOs; no user's photographs are added to the repo."""
import struct

import piexif
from PIL import Image


def camera_mpo(path, *, preview_type=0x010002, orientation=1, same_size=False, oversized_primary=False):
    """Patch the MP entry type in a real Pillow-generated two-JPEG container."""
    image = Image.new('RGB', (160, 120), (220, 25, 30))
    preview = Image.new('RGB', image.size if same_size else (40, 30), (20, 220, 30))
    exif = piexif.dump({'0th': {piexif.ImageIFD.Orientation: orientation,
                              piexif.ImageIFD.Artist: b'Guille'}})
    image.save(path, 'MPO', save_all=True, append_images=[preview], exif=exif, quality=95)
    data = bytearray(path.read_bytes())
    tiff = data.index(b'MPF\0') + 4
    ifd = tiff + struct.unpack_from('<L', data, tiff + 4)[0]
    count = struct.unpack_from('<H', data, ifd)[0]
    for index in range(count):
        entry = ifd + 2 + 12 * index
        tag = struct.unpack_from('<H', data, entry)[0]
        if tag == 0xB002:
            entries = tiff + struct.unpack_from('<L', data, entry + 8)[0]
            struct.pack_into('<L', data, entries, 0xA0030000)
            struct.pack_into('<L', data, entries + 16, 0x40000000 | preview_type)
            if oversized_primary:
                struct.pack_into('<L', data, entries + 4, len(data))
            break
    else:
        raise AssertionError('No MP entries')
    path.write_bytes(data)
    return str(path)
