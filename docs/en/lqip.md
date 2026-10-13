# LQIP / Base64

## Overview
Generates LQIP (Low Quality Image Placeholder) and/or Base64 for web usage.

## Supported inputs
- Common raster formats: `JPG`, `PNG`, `WEBP`, `AVIF`, `HEIC`, `HEIF`, etc.
- One image at a time in both LQIP and Base64.

## Outputs
- Strings/Base64 ready to copy/export.

## Workflow
1. Select an image.
2. Choose LQIP or Base64 and adjust its parameters.
3. Generate and compare the original with the result.
4. Choose Data URI, HTML, CSS or raw Base64 and copy/export.

Loading another image discards the result and resets the LQIP mode,
20 px width, blur 2, LQIP quality 40 and Base64 quality 85.
Canceling the picker preserves the current image and settings.

## Common errors
- If a specific file fails: it is often corrupted or unsupported.

## Troubleshooting
- Check `yagua.log` to identify the failing file.

## Examples
- Generate a 20 px placeholder for a web image.

## Technical notes
- HTML is escaped and CSS selectors are sanitized to prevent injection in outputs.

## Limitations
- LQIP is a placeholder; it does not replace the full image.

## Performance tips
- Use smaller placeholder sizes for faster generation.

