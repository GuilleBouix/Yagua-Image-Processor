# Metadata (EXIF)

## Overview
View/edit EXIF metadata (including dates) and batch-clean EXIF.

## Supported inputs
- EXIF editing: `JPG/JPEG` and `TIFF` (EXIF-capable formats)
- Batch cleaning (UI): up to 100 images

## Outputs
- The original file overwritten or a saved copy (depending on module flow).
- For batch cleaning: cleaned files written to the output folder.

## Workflow
### Edit
1. Select an image with EXIF.
2. Edit fields (Author, Software, Dates, etc.).
3. Save changes.

### Batch clean
1. Select images.
2. Choose output folder.
3. Run cleaning.

## Common errors
- Invalid date format: use `YYYY:MM:DD HH:MM:SS`.
- Images without EXIF: saved without EXIF (warning).

## Troubleshooting
- If “saved but nothing changed”: reload the file in the module to confirm it was written.

## Examples
- Set `DateTimeOriginal` to `2026:04:09 12:00:00`.

## Technical notes
- Common EXIF date fields:
  - `DateTime`: file date/time (IFD 0)
  - `DateTimeOriginal`: capture timestamp (ExifIFD)
  - `DateTimeDigitized`: digitization timestamp (ExifIFD)

## Limitations
- Not all formats support editable EXIF.

## Performance tips
- For large batches, write outputs to SSD.

