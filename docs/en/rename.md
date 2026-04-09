# Rename

## Overview
Batch renames files with preview and safe name sanitization.

## Supported inputs
- Image files (as allowed by the module picker)
- Max batch size (UI): 100 files

## Outputs
- Renamed files (same folder or module-defined flow).

## Workflow
1. Select files.
2. Configure prefix/suffix/counter.
3. Preview.
4. Apply.

## Common errors
- Name conflicts: the module avoids overwrites.

## Troubleshooting
- Avoid Windows-invalid characters (`<>:\"/\\|?*`).

## Examples
- `product_001.jpg`, `product_002.jpg`, …

## Technical notes
- Prefixes are sanitized to avoid invalid paths and unsafe characters.

## Limitations
- Renaming only changes filenames, not file contents.

## Performance tips
- For big batches, work on local disks.

