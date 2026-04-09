# Remove Background

## Overview
Removes image backgrounds using `rembg` (U^2-Net). After the first model download, it works offline.

## Supported inputs
- Common formats: `JPG`, `PNG`, `WEBP`, `TIFF`, `BMP`, `HEIC`, `HEIF`
- Max batch size: 10 images

## Outputs
- Background-removed images (output format is chosen in the UI, typically `PNG`/`WEBP`).

## Workflow
1. Open the module (may download the model on first run).
2. Select images.
3. Choose output format and folder.
4. Process.

## Common errors
- Model download fails: blocked network/firewall or no internet.
- “Could not open image”: corrupted file or unsupported format.

## Troubleshooting
- If model download fails: try a different network or allow access to the model host.
- If output has no transparency: use `PNG`/`WEBP` output with alpha.

## Examples
- Remove background from 10 `JPG` images and export as `PNG`.

## Technical notes
- `rembg` sessions are created per model and reused for batch processing.

## Limitations
- Quality depends on subject/background contrast.
- First run can be slow due to model download.

## Performance tips
- Use smaller batches on low-RAM machines.
- Avoid network paths for output folders.

