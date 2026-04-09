# Convert

## Overview
Converts images between formats (includes HEIC as output if the support plugin is installed).

## Supported inputs
- Common formats: `JPG`, `PNG`, `WEBP`, `BMP`, `TIFF`, `GIF`, `AVIF`, `HEIC`, `HEIF`
- Max batch size (UI): 100 images

## Outputs
- Output formats (UI): `JPEG`, `PNG`, `WEBP`, `AVIF`, `HEIC`, `ICO`, `BMP`, `TIFF`, `GIF`

## Workflow
1. Select images.
2. Choose output format and quality (if applicable).
3. Choose output folder.
4. Convert.

## Common errors
- HEIC not available: missing `pillow-heif` or opener not registered.
- AVIF not available: depends on Pillow AVIF support on your platform.

## Troubleshooting
- Check `yagua.log` when only specific files fail.
- Try converting to `PNG` first if an input file is problematic.

## Examples
- Convert `WEBP` → `JPEG` with quality 90.

## Technical notes
- For `HEIC`, the file is saved as `HEIF` with a `.heic` extension.

## Limitations
- Some formats may vary across OS builds depending on codec support.

## Performance tips
- Avoid cloud folders/slow drives as output destinations.

