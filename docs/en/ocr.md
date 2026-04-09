# OCR (Extract Text)

## Overview
Extracts text from images using EasyOCR (runs locally).

## Supported inputs
- Common formats: `JPG`, `PNG`, `WEBP`, `TIFF`, `BMP`, `HEIC`, `HEIF`
- `AVIF`: only if Pillow has AVIF support in your runtime; otherwise it is omitted with a warning.
- Max batch size: 10 images

## Outputs
- Extracted text (preview + export from the UI)

## Workflow
1. Open the OCR module (engine loads in background).
2. Select images.
3. Pick language(s).
4. Run OCR.
5. Copy or export the text.

## Common errors
- Freeze on open: if it happens, check CPU/RAM and `yagua.log` (EasyOCR initializes models).
- “Could not open image”: corrupted file or unsupported format in Pillow.

## Troubleshooting
- If AVIF does not work: install/enable AVIF support for Pillow on your platform.
- If OCR is slow: CPU is expected; GPU can speed it up significantly.

## Examples
- Extract text from 5 `PNG` images in Spanish/English and export to `.txt`.

## Technical notes
- The EasyOCR `Reader` is cached per language set to avoid costly re-initialization.

## Limitations
- OCR accuracy depends on image quality (small/blurry text reduces precision).

## Performance tips
- Use sharp images and crop to the text area when possible.
- Use smaller batches on low-RAM machines.

