# LQIP / Base64

## Overview
Generates LQIP (Low Quality Image Placeholder) and/or Base64 for web usage.

## Supported inputs
- Common raster formats: `JPG`, `PNG`, `WEBP`, `AVIF`, `HEIC`, `HEIF`, etc.
- Max batch size (UI): 100 images

## Outputs
- Strings/Base64 ready to copy/export.

## Workflow
1. Select images.
2. Choose placeholder size/quality.
3. Generate.
4. Copy/export.

## Common errors
- If a specific file fails: it is often corrupted or unsupported.

## Troubleshooting
- Check `yagua.log` to identify the failing file.

## Examples
- Generate LQIP for 20 web images.

## Technical notes
- HTML is escaped and CSS selectors are sanitized to prevent injection in outputs.

## Limitations
- LQIP is a placeholder; it does not replace the full image.

## Performance tips
- Use smaller placeholder sizes for faster generation.

