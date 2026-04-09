# Watermark

## Overview
Applies a watermark to a batch of images. The real-time preview is based on the first selected image.

## Supported inputs
- Base images: common formats (`JPG`, `PNG`, `WEBP`, `TIFF`, `HEIC`, `HEIF`, etc.)
- Watermark image: `PNG` recommended (supports transparency), `WEBP`, etc.
- Max batch size: 100 images

## Outputs
- Exported images with the watermark applied (module output format).

## Workflow
1. Select base images (up to 100).
2. Select 1 watermark image.
3. Adjust preset/position/size/opacity/margin.
4. Apply and choose an output folder.

## Common errors
- “Weird background” around watermark: often the watermark has no real alpha (export as transparent PNG).
- Black preview: confirm both base and watermark images loaded; check `yagua.log`.

## Troubleshooting
- Use a transparent `PNG` watermark whenever possible.
- For accented/unicode paths on Windows: the loader supports Unicode, but verify permissions/paths.

## Examples
- Apply a semi-transparent logo at “bottom-right” with 20px margin.

## Technical notes
- Preview runs on a downscaled image for responsiveness.

## Limitations
- Preview is not pixel-perfect for very large images (it’s an approximation).

## Performance tips
- Keep watermark images reasonably sized.
- Avoid slow external drives for big batches.

