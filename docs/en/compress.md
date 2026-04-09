# Compress

## Overview
Reduces image file size with a quality control.

## Supported inputs
- Common formats: `JPG`, `PNG`, `WEBP`, `AVIF`, `HEIC`, `HEIF`, `TIFF`
- Max batch size (UI): 100 images

## Outputs
- Compressed images (module output format).

## Workflow
1. Select images.
2. Adjust quality.
3. Choose output folder.
4. Compress.

## Common errors
- Very low quality: can heavily degrade output (visible artifacts).

## Troubleshooting
- If only some files fail, check `yagua.log` to identify the failing file.

## Examples
- Compress 100 `JPG` files at 80% quality.

## Technical notes
- For formats supporting `quality` (AVIF/HEIF/WEBP/JPEG), the quality parameter is applied.

## Limitations
- Some formats depend on runtime support (AVIF/HEIF).

## Performance tips
- For big batches, export to local disks.

