# Resize

## Overview
Batch-resizes images while preserving aspect ratio (depending on options).

## Supported inputs
- Common formats: `JPG`, `PNG`, `WEBP`, `TIFF`, `HEIC`, `HEIF`, etc.
- Max batch size (UI): 100 images

## Outputs
- Resized images in the output folder.

## Workflow
1. Select images.
2. Configure size (width/height) and options.
3. Choose output folder.
4. Process.

## Common errors
- If a file cannot be opened: it may be corrupted or unsupported.

## Troubleshooting
- To preserve transparency, use alpha-capable formats (`PNG/WEBP/TIFF/HEIF`).

## Examples
- Resize to 1200px width while keeping aspect ratio.

## Technical notes
- Alpha is preserved when the output format supports it.

## Limitations
- Final quality depends on resampling.

## Performance tips
- Avoid max-size batches on low-RAM machines.

