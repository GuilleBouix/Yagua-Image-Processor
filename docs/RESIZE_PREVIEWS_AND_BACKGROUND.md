# Resize previews and background removal settings

This guide describes the source on `main` prepared for Yagua 2.0. Older test
packages may not include these controls. It does not announce a release.

## Use

### Resize, Crop and Canvas

- The first image opens automatically. Clicking a row changes the inspected
  image, **without reducing the processing batch**.
- The right panel previews the visible tab and shows original and resulting
  dimensions after applying EXIF orientation.
- Resize follows the existing percentage, pixel, preset and aspect-ratio
  controls. Preserving the ratio fits inside current bounds without upscaling.
- Crop keeps the current centered crop; its preview does not let you drag or
  shift the crop area.
- Canvas centers the image and reduces it if it exceeds the canvas. Width and
  height sliders stay synchronized with the manual inputs and start at
  1080 × 1080 px. The initial range is 1–8192 px; a larger manual value extends
  the slider range. Large saved images remain subject to memory limits.
- Incomplete or invalid values hide the previous result and show a short hint.
  Changing parameters does not write files.
- The checkerboard indicates transparency and is not added to the output file.
  Canvas keeps the existing processing rules for transparency and formats.

Previews use reduced pixels. They help review geometry and composition but do
not show 1:1 detail or final compression. Resize batches remain limited to 100
images.

### Remove Background

The panel shows **Original** after loading and **Result** after processing and
saving successfully. It reads the published output from disk and does not run
inference again. Each row stays associated with its own output; a failed image
shows its original and the error. The batch remains limited to 10 images.

The three settings are always visible:

| Setting | Values | Default | Effect |
| --- | --- | --- | --- |
| Refine edges | Auto / Yes / No | Auto | Auto keeps mask cleanup and enables alpha matting on uniform light backgrounds; Yes requests both for any background; No disables both. |
| Reduce white halo | 0–100% | 85% | Reduces background-color contamination around semi-transparent edges near a detected light background. It is not applied to backgrounds that are not classified as uniform and light. |
| Contract / expand | −5 to +5 px | 0 px | Negative values contract the mask and positive values expand it. The amount uses original-image pixels, not preview pixels. |

Halo reduction works independently of the edge-refinement selector. When
expanding the mask, original pixel colors are restored in newly exposed areas
to avoid black edges from empty transparent pixels. Expansion can reveal
background; contraction can remove fine detail. No setting can restore detail
that the model classified incorrectly.

Output remains transparent and supports PNG, WebP and TIFF. There is no
background-color selector or expandable advanced-settings section. Changing
settings after saving keeps the saved result in the preview and indicates that
the image must be processed again. Moving a slider does not modify the output.

Defaults preserve the previous processing pipeline. No model, dependency,
download or inference provider is added. Refinement can use more CPU, memory
and time; batches still process sequentially.

## Implementation

- `app/modules/resize_geometry.py` shares rounding, dimension calculation,
  cropping and canvas placement between saving and preview. It matches
  `Pillow.thumbnail` rounding, including no upscaling when preserving aspect
  ratio.
- `app/ui/preview.py` contains `LivePreview` and pixel rendering. It loads
  reduced RGBA images from the shared 64 MiB cache and renders at most
  1024 × 1024 px. It does not allocate a full-size canvas just to display a
  large requested canvas.
- Each preview has at most one active worker. Revisions discard stale replies;
  Resize changes are grouped over 150 ms. Decoding, transformations and
  checkerboard rendering run outside Tk. CTk images and widget updates are
  created on the UI thread.
- `StableRender` waits for two identical measurements 16 ms apart. The viewport
  reserves its own size and uses `place` for the image so it cannot affect the
  requested layout size. Optional workspace-height preparation happens before
  rendering to avoid retaining an obsolete initial height.
- Hiding the module suspends renders and cancels timers. A worker that already
  started may finish, but its stale result is discarded. Clearing, reloading or
  closing invalidates older requests. Previews are not preloaded for the batch.
- `FileList.on_select` is optional; other views keep their existing behavior.
  Virtualized rows are reused and only the active image receives a large
  preview. A callback can return `False` to reject selection while processing
  is locked.
- Remove Background associates each input path with its saved output.
  `path_key` treats `/`, `\` and Windows path capitalization as the same path.
  Overwrites invalidate the image cache; copies preserve the original. Atomic
  saving and confirmation dialogs continue to use shared app services.

### Processing contract

`quitar_fondo` and `batch_quitar_fondo` accept the optional keyword-only
parameter `config: RemoveBgConfig | None`. Existing calls and result keys are
preserved. `None` uses the defaults.

`RemoveBgConfig` is immutable. It adds `refine_edges` (`auto`, `on`, `off`),
`halo_strength` (integer 0–100) and `edge_offset` (integer −5–5). Values outside
the contract are rejected before processing. The UI captures the configuration
before save confirmation; the worker does not read Tk variables. A fallback
model keeps the same settings and changes only the model identity.

Pipeline order: background analysis, requested segmentation refinement, edge
adjustment, light-halo reduction and saving. Later refinements use existing
Pillow and NumPy dependencies.

## Validation and reproduction

CI pins dependencies in `requirements.txt`, `requirements-linux-cpu.txt` and
`requirements-dev.txt`. It uses Python 3.13.17 on Windows and Ubuntu 22.04 with
Xvfb on Linux.

On Windows, with the environment activated:

```powershell
python -m pip check
python -m ruff check app tests scripts
python -m pyright --skipunannotated --pythonpath (Get-Command python).Source app
python scripts/ci/check_licenses.py --installed
python -m scripts.ci.preflight --version 2.0.0 --platform windows
python scripts/ci/partitions.py
python scripts/verify.py -q --ignore=tests/ui
python scripts/verify.py -q tests/ui
```

On Linux, install `requirements-linux-cpu.txt` and `requirements-dev.txt`, run
the same quality checks, then:

```bash
python -m pyright --skipunannotated --pythonpath "$(command -v python)" app
python -m scripts.ci.preflight --platform linux
python scripts/ci/partitions.py
xvfb-run -a python scripts/verify.py -q --ignore=tests/ui
xvfb-run -a python scripts/verify.py -q tests/ui
```

`scripts/verify.py` uses temporary preferences and blocks HTTP requests in the
test suite. Linux preflight without `--version` checks local materials without
querying tags; versioned preflight also checks GitHub and requires the
corresponding Actions context.

Specific tests compare geometry and pixels against real outputs for small
images; they cover EXIF, alpha, large canvases with bounded previews, sliders,
invalid inputs, repeated loads, read errors, stale worker replies and hidden
views. They also cover refinement modes, halo, edge adjustment, invalid values,
captured configuration, copies and overwrites.

Visual acceptance should cover a large window and 900 × 600 at 100/75/50% scale,
row selection and all three tabs. At reduced widths the panels stack and may
need scrolling. Try a batch of 100 in Resize and 10 in Remove Background; excess
files should be rejected without changing the existing limits.

Passing the local source suite validates source code. New Windows installers,
portable packages and the AppImage must be validated separately through the
candidate workflow in [CI_RECOVERY.md](CI_RECOVERY.md) before announcing a
public test release.
