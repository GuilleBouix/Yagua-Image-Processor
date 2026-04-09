# Vectorize (SVG)

## Overview
Converts raster images to SVG using `vtracer`.

## Supported inputs
- Formats: `PNG`, `WEBP`, `TIFF`, `HEIC`, `HEIF`
- Max batch size: 50 images
- Size limit: files larger than 1 MB are omitted

## Outputs
- `SVG` (one `.svg` file per image)

## Workflow
1. Select images.
2. Adjust preset/parameters.
3. Pick an output folder.
4. Export.

## Common errors
- “Unsupported format”: you selected a format outside the list (e.g. `JPG`).
- “File too large”: the image is over 1 MB.
- “vtracer is not installed”: missing dependency in the environment.

## Troubleshooting
- If SVG is not generated: check `yagua.log` and verify output folder permissions.
- If HEIC/HEIF fails: confirm `pillow-heif` is installed and HEIF support is registered on startup.

## Examples
- Export a batch of `PNG` images using the “Photo” preset to an `output/` folder.

## Technical notes
- On Windows, paths are normalized to avoid backslashes for `vtracer`.

## Limitations
- `JPG` input is intentionally blocked (focus on transparency-friendly workflows).
- The SVG may not match the raster perfectly (vectorization artifacts are expected).

## Performance tips
- Keep files small (ideally < 1 MB) to speed up processing and avoid omissions.
- For big batches, export to local disks (avoid network drives).

