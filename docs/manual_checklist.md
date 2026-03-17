# Manual QA Checklist

1. Launch app with `python -m app.main`.
2. Verify main window loads, sidebar icons render, and no traceback appears.
3. Click each sidebar module button and confirm the frame swaps without errors.
4. In Settings, change language and confirm the app restarts and reflects the new language.
5. In Compress, load 2+ images and verify list thumbnails appear.
6. In Compress, move quality slider and confirm info text updates with estimated size.
7. In Compress, run export to a folder and confirm output files exist.
8. In Convert, load images, switch format, and confirm info text updates.
9. In Convert, run export and confirm output extensions match the selected format.
10. In Resize, test Percentage, Pixels, and Preset modes with valid inputs and confirm outputs are saved.
11. In Resize, test Canvas with Transparent and non-transparent sources and confirm warning text appears when expected.
12. In Palette, load an image and confirm preview and extracted swatches appear.
13. In Palette, copy a format button and confirm clipboard updates and info message changes.
14. In Palette, export PNG palette and verify file is created.
15. In Metadata, View tab: load image and confirm fields render and GPS links open in browser if present.
16. In Metadata, Edit tab: edit a field and save to a new file, confirm saved file exists.
17. In Metadata, Clean tab: batch load images and confirm cleaned outputs are created.
18. In Rename/Remove BG/Watermark/LQIP/Optimizer modules: verify frame loads without errors and buttons respond (placeholders should not be present).
