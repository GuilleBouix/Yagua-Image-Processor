# Image Transform

## Overview
Applies simple batch transforms: rotation, flip, and EXIF correction.

## Supported inputs
- Common formats: `JPG`, `PNG`, `WEBP`, `TIFF`, `HEIC`, `HEIF`, etc.
- Max batch size: 100 images

## Outputs
- Transformed images (same format or module-defined output format, depending on options).

## Workflow
1. Select images.
2. Configure rotation/flip/EXIF options.
3. Choose an output folder.
4. Process.

## Common errors
- “Could not open image”: corrupted file or unsupported format.

## Troubleshooting
- For JPEG (no alpha), output is forced to `RGB` to avoid save errors.
- If rotation looks wrong: toggle EXIF correction depending on your files.

## Examples
- Rotate 90° and apply horizontal flip to 50 images.

## Technical notes
- Uses `with Image.open(...)` to ensure files are closed properly.

## Limitations
- Not an advanced editor; focused on fast batch transforms.

## Performance tips
- Avoid network paths for output folders.
- Split very large batches into smaller runs.

