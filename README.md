<div align="center">

**English** · [Español](docs/i18n/README_es.md) · [Português](docs/i18n/README_pt.md) · [Français](docs/i18n/README_fr.md) · [Deutsch](docs/i18n/README_de.md) · [Italiano](docs/i18n/README_it.md) · [日本語](docs/i18n/README_ja.md) · [简体中文](docs/i18n/README_zh_cn.md) · [Русский](docs/i18n/README_ru.md)

<img src="https://github.com/user-attachments/assets/fc1dacf8-5249-43da-a294-4b20dc423304" width="1000" alt="Yagua — Image Processor banner" />

# Yagua · Image Processor

### Your images. Your computer. Your workflow.

Free, open-source desktop tools to convert, compress and process images in batches.

<p align="center">
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/releases/latest"><img src="https://img.shields.io/github/v/release/GuilleBouix/Yagua-Image-Processor?style=flat-square&amp;label=stable&amp;color=2563eb" alt="Latest stable release" /></a>
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/releases"><img src="https://img.shields.io/github/downloads/GuilleBouix/Yagua-Image-Processor/total?style=flat-square&amp;label=downloads&amp;color=22c55e" alt="Total downloads" /></a>
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/GuilleBouix/Yagua-Image-Processor/ci.yml?branch=main&amp;style=flat-square&amp;label=CI" alt="CI status" /></a>
  <a href="#requirements"><img src="https://img.shields.io/badge/Python-3.13-3776ab?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.13" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-f4c430?style=flat-square" alt="MIT license" /></a>
</p>

**[Downloads](https://github.com/GuilleBouix/Yagua-Image-Processor/releases) · [Features](#features) · [Installation](#installation)**

[Screenshots](#screenshots) · [Usage](#usage) · [Requirements](#requirements) · [FAQ](#faq) · [Contributing](#contributing)

</div>

## Why Yagua?

Yagua brings everyday image tasks into one desktop app for web developers, designers, photographers and anyone working with image collections. No subscription or browser is needed to process your files.

Image processing runs on your computer. Background removal and OCR need an initial model download, then can work offline with the required models cached. Update checks contact GitHub; opening download, donation or map links uses your browser.

The current source interface supports **English, Spanish, Portuguese, French, German, Italian, Japanese, Simplified Chinese and Russian**, with dark themes and previews where available. Published packages may include fewer languages; availability depends on your installed release. The interface language does not add OCR recognition languages.

## Features

The table lists the desktop modules. Availability and controls depend on your installed release; check its release notes.

| Module | What you can do | Formats and outputs | Selection limit |
| --- | --- | --- | --- |
| Convert | Change format and adjust quality where supported. | JPEG, PNG, WebP, AVIF, HEIC, ICO, BMP, TIFF and static GIF outputs. | 100 images |
| Compress | Reduce file size while keeping the original format. | JPEG, PNG, WebP, AVIF, HEIC/HEIF and other supported raster formats. | 100 images |
| Resize / Crop / Canvas | Set dimensions, crop or add canvas space; use size presets. | Common raster images, including JPEG, PNG and WebP. | 100 images |
| Remove background | Remove backgrounds locally with AI. | PNG, WebP or TIFF output with transparency. | 10 images |
| Color palette | Extract colors, copy HEX/RGB/HSL values and export a palette. | One supported image → colors and a PNG palette. | 1 image |
| Watermark | Apply an image logo; adjust position, size, opacity and margin. | Supported base images; transparent PNG recommended for the logo. | 100 images + 1 logo |
| Rename | Preview numbered names, dates and letter case changes. | Changes filenames in their current folder. | 100 files |
| OCR | Extract Spanish and/or English text with EasyOCR; copy it or export as TXT. | Supported raster images → text. | 10 images |
| EXIF metadata | Inspect, export, edit fields or remove metadata in batches. | JPEG/TIFF editing; TXT/JSON metadata export. | 1 image for editing; 100 for cleanup |
| LQIP / Base64 | Generate low-quality placeholders or encode images for the web. | Base64, data URIs, HTML and CSS; TXT/JSON export. | 1 image |

Format support varies by module, installed codecs and platform. A listed format is not a guarantee that every module can read or write it. See [requirements](#requirements).

## Screenshots

Yagua screenshots with the interface in English. Click any thumbnail to view the full-size image. Layouts and controls can vary between releases.

<table>
  <tr>
    <td align="center" width="33%"><a href="assets/screenshots/home.png"><img src="assets/screenshots/home.png" width="300" alt="Home screen with all modules" /><br /><strong>Home</strong></a></td>
    <td align="center" width="33%"><a href="assets/screenshots/convert.png"><img src="assets/screenshots/convert.png" width="300" alt="Conversion with selected images and output format controls" /><br /><strong>Convert</strong></a></td>
    <td align="center" width="33%"><a href="assets/screenshots/compress.png"><img src="assets/screenshots/compress.png" width="300" alt="Compression with quality and EXIF controls" /><br /><strong>Compress</strong></a></td>
  </tr>
  <tr>
    <td align="center" width="33%"><a href="assets/screenshots/resize.png"><img src="assets/screenshots/resize.png" width="300" alt="Resizing with a size preset and loaded images" /><br /><strong>Resize</strong></a></td>
    <td align="center" width="33%"><a href="assets/screenshots/remove-background.png"><img src="assets/screenshots/remove-background.png" width="300" alt="Background removal with a selected image" /><br /><strong>Remove background</strong></a></td>
    <td align="center" width="33%"><a href="assets/screenshots/palette.png"><img src="assets/screenshots/palette.png" width="300" alt="Extracted palette with eight colors and color values" /><br /><strong>Color palette</strong></a></td>
  </tr>
  <tr>
    <td align="center" width="33%"><a href="assets/screenshots/watermark.png"><img src="assets/screenshots/watermark.png" width="300" alt="Watermark controls and result preview" /><br /><strong>Watermark</strong></a></td>
    <td align="center" width="33%"><a href="assets/screenshots/rename.png"><img src="assets/screenshots/rename.png" width="300" alt="Batch renaming with original and proposed filenames" /><br /><strong>Batch rename</strong></a></td>
    <td align="center" width="33%"><a href="assets/screenshots/ocr.png"><img src="assets/screenshots/ocr.png" width="300" alt="English OCR with recognized text" /><br /><strong>OCR</strong></a></td>
  </tr>
  <tr>
    <td align="center" width="33%"><a href="assets/screenshots/metadata.png"><img src="assets/screenshots/metadata.png" width="300" alt="EXIF editor with metadata fields and an image preview" /><br /><strong>EXIF metadata</strong></a></td>
    <td align="center" width="33%"><a href="assets/screenshots/lqip-base64.png"><img src="assets/screenshots/lqip-base64.png" width="300" alt="LQIP placeholder compared with the original and generated data URI" /><br /><strong>LQIP / Base64</strong></a></td>
    <td align="center" width="33%"><a href="assets/screenshots/settings.png"><img src="assets/screenshots/settings.png" width="300" alt="General settings with language, theme, scale and visible modules" /><br /><strong>Settings</strong></a></td>
  </tr>
</table>

## Installation

### Choose a release

Open **[GitHub Releases](https://github.com/GuilleBouix/Yagua-Image-Processor/releases)** and choose your operating system. The **stable** badge links to GitHub's latest stable release; newer builds marked **Pre-release**, including `rc` builds, are testing versions. Windows and Linux releases can have different versions.

The source version is defined in [`app/version.py`](app/version.py). It does not mean that a matching installer has been published. Read each release's notes and download the assets attached to that release.

| Platform | Package | Steps |
| --- | --- | --- |
| Windows | `Yagua_Setup_<version>.exe` | Run the installer, then open Yagua from the Start menu or desktop shortcut. |
| Windows portable | `Yagua_Portable_<version>.zip`, when provided | Extract the entire ZIP into a writable folder and launch `Yagua.exe` inside it. Keep the accompanying files together. |
| Linux x86_64 | `Yagua-<version>-x86_64.AppImage`, when provided | Make the downloaded file executable, then run it as shown below. |
| macOS | Experimental source/build support | No stable macOS package is promised. See the existing [build script](scripts/build_macos_app.sh). |

For Linux, replace the example filename with the one you downloaded:

~~~bash
chmod +x "Yagua-<version>-x86_64.AppImage"
./"Yagua-<version>-x86_64.AppImage"
~~~

### Run from source

Use **Python 3.13**, the version used by the project's CI, and Git. Dependency installation can be large because it includes OCR and AI libraries. Linux also needs Tk and the system libraries listed under [requirements](#requirements).

**Windows · PowerShell**

~~~powershell
git clone https://github.com/GuilleBouix/Yagua-Image-Processor.git
cd Yagua-Image-Processor
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
~~~

**Linux · Bash**

~~~bash
git clone https://github.com/GuilleBouix/Yagua-Image-Processor.git
cd Yagua-Image-Processor
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
~~~

The commands use the repository's pinned dependencies. Compatibility with other Python versions or macOS is not established by the Windows/Linux CI checks.

## Usage

1. Open Yagua and select a module from the sidebar.
2. Load your images and choose the available processing options.
3. Check the preview where the module provides one.
4. Process the images and choose an output folder when prompted; review the completion message for errors.

**LQIP / Base64:** Select one image, choose the mode and parameters, generate, compare, then copy or export Data URI, HTML, CSS or raw Base64. Loading another image resets LQIP mode, width 20 px, blur 2 and qualities 40/85; canceling the picker preserves the current state. Both modes output JPEG without transparency.

**Original files:** Rename changes filenames in place. EXIF editing overwrites the selected image after confirmation. Work on copies for these operations. Batch EXIF cleanup writes to the chosen output folder. Other export operations use their module's save or output-folder flow.

### Practical workflows

- **Prepare web images:** Convert up to 100 photos to WebP, choose a quality setting, then resize if needed. Generate LQIP placeholders separately for loading previews on your site.
- **Prepare product photos:** Load up to 10 images in Remove background and export as PNG or WebP to keep transparency. Add a transparent PNG logo with Watermark if needed.
- **Extract text:** Load up to 10 clear images in OCR, choose Spanish, English or both, then copy the result or export a TXT file. The interface language does not add OCR recognition languages. Review the text for recognition errors.

<a id="requirements"></a>

## Requirements and limits

### Hardware

For the complete app, including **OCR and background removal**:

| Component | Provisional minimum | Recommended |
| --- | --- | --- |
| Processor | Relatively recent Intel/AMD x86-64 CPU with **4 cores** | Modern CPU with **6–8 cores** |
| System RAM | **8 GB**, with few other applications open | **16 GB**; **32 GB** for very large images and multitasking |
| Storage | **4 GB free**, plus space for originals and outputs | **SSD with 10 GB free or more**, in addition to your images |
| Graphics | Integrated graphics are sufficient; no dedicated GPU required | Integrated graphics are sufficient |
| Internet | For initial model downloads and update checks | Offline use once the required models are downloaded |

**These are practical estimates for the complete app, not validated hardware minimums. Testing on a low-end PC is still pending.** A system with 4 GB of RAM is not recommended for full OCR and background-removal use. Resource usage depends on image resolution, batch size and models; reduce batch size when resources are limited.

The tested package processes images on the **CPU**; you do not need an NVIDIA or other dedicated GPU. Prioritize CPU, RAM and an SSD. Background removal uses ONNX Runtime's CPU execution provider; see the [official ONNX Runtime documentation](https://onnxruntime.ai/docs/api/python/api_summary.html).

### Operating systems

| System | Baseline and validation |
| --- | --- |
| Windows | **Windows 10/11, 64-bit**; Windows 11 preferred. ONNX Runtime lists Windows 10 as its minimum supported Windows version. Final installer and portable-package validation on clean Windows 10/11 PCs is still pending. |
| Linux | **Ubuntu 22.04 x86-64**, the base checked in CI. Other distributions, versions and desktop environments require validation of the final AppImage. |
| macOS | Experimental support; no validated native package is claimed. |

Current Windows and Linux packages target **x86-64**; there is no validated native ARM version. CI uses Windows Server and Ubuntu 22.04/Xvfb; those checks do not certify all desktop systems. See [ONNX Runtime platform requirements](https://onnxruntime.ai/docs/build/inferencing.html).

<details>
<summary>Measured resource usage and first model load</summary>

The package audit records these approximate observations from CI builds tested on October 15, 2026:

| Measurement | Windows | Linux |
| --- | --- | --- |
| Peak process RAM observed with several models loaded | **3.0 GB** | **2.6 GB** |
| App + all models and caches measured in that test | **1.10 GB** | **1.53 GB** |
| First background-removal model load (ISNet) | **53 seconds** | **39 seconds** |

**These are observations, not guaranteed maximums or processing times.** The RAM test kept several models loaded; large photographs can use more memory. The disk figures cover the measured package, models and caches, not originals, outputs, temporary extraction space or a source-development environment. Model-load times depend on the machine; the session is reused afterward. They are not model-download times or per-image processing times.

</details>

### Runtime and processing

- **From source:** Python 3.13, Tk and the libraries in [`requirements.txt`](requirements.txt). Prebuilt packages do not require a separate Python installation.
- **Batch limits:** The feature table lists current UI limits: one image for Palette, LQIP / Base64 or EXIF editing, 10 for OCR/background removal and 100 for the other listed batch operations.
- **Codecs:** HEIC/HEIF uses `pillow-heif`, included in source dependencies. AVIF and other formats depend on Pillow codecs and platform. JPEG has no transparency; use PNG or WebP when alpha is needed. PNG compression can reduce the image to 256 colors, so check the result.
- **AI models:** Downloads can occur on first use or when a newly selected model/language needs one. Offline use requires the models to be present. The tested package runs OCR and background removal on CPU.

### Linux system libraries

AppImage needs **FUSE 2** for its mounted execution mode (`libfuse2` on compatible distributions). If FUSE is unavailable, extraction is an alternative; see the [official AppImage instructions](https://docs.appimage.org/user-guide/troubleshooting/fuse.html). Replace the example filename with the downloaded file:

~~~bash
./"Yagua-<version>-x86_64.AppImage" --appimage-extract-and-run
~~~

Extraction needs additional temporary disk space and can slow startup. For source runs, Linux CI installs Tk and these libraries on Ubuntu 22.04:

~~~bash
sudo apt-get install python3-tk libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgtk-3-0 libgomp1
~~~

Package names vary by distribution. Ensure Tk is available for the Python 3.13 interpreter you use; the distribution's default Tk package may not cover a separately installed Python.

## FAQ

### Does Yagua upload my images?

Processing runs locally; the modules do not upload images to a processing service. Model downloads and GitHub update checks need a network connection. External links open in your browser; the EXIF map link sends the selected GPS coordinates to Google Maps when you open it.

### Why is the first AI operation slower?

OCR and background removal initialize their engines and may download models. Wait for that step to finish. Later runs can reuse cached models; larger images and batches still require more resources.

### Why is a format unavailable or an image rejected?

Supported inputs differ by module and codec availability. Try a PNG or JPEG copy and review `yagua.log`. Export to PNG or WebP if you need transparency.

### Why does compression not reduce every image?

An already optimized image may not become smaller. When EXIF removal is disabled, Yagua copies the original to the output if compression would produce a file at least as large. When EXIF removal is enabled, it saves the processed image even if it is larger, so the original EXIF is not restored by that fallback. For a dedicated EXIF-cleanup workflow, use the metadata module.

### How do updates work?

Yagua can notify you on startup and lets you check under **Settings → Updates**. It opens a download link; it does not automatically install updates. RC.4/RC.5 packages only look for newer stable releases with the matching platform prefix (`win-v` or `linux-v`); they exclude prereleases and drafts, so they do not detect newer RC builds. Download test builds manually from [GitHub Releases](https://github.com/GuilleBouix/Yagua-Image-Processor/releases). Those packages can also report “No updates available” after a connection failure; if in doubt, check Releases directly, including older releases without a platform prefix.

### How do I report a problem?

Open a [bug report](https://github.com/GuilleBouix/Yagua-Image-Processor/issues/new?template=bug_report.md) with your Yagua version, OS, module, steps to reproduce and relevant logs. Locate `yagua.log` at:

- Windows: `%APPDATA%\Yagua\yagua.log`
- Linux: `~/.config/Yagua/yagua.log`
- macOS: `~/Library/Application Support/Yagua/yagua.log`

Logs can contain file paths and names; review them before sharing.

<a id="contributing"></a>

## Development and contributing

Yagua uses **CustomTkinter** for its interface, **Pillow / pillow-heif** for images, **rembg / ONNX Runtime** for background removal, **EasyOCR / PyTorch** for OCR and **piexif** for EXIF. Exact versions are in [`requirements.txt`](requirements.txt).

After source installation, install development tools and run CI checks. On Windows, use the virtual environment's executables directly:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m ruff check app tests scripts
.\.venv\Scripts\python.exe -m pyright --skipunannotated --pythonpath .\.venv\Scripts\python.exe app
.\.venv\Scripts\python.exe -m pytest -q
~~~

On Linux, with the virtual environment activated:

~~~bash
python -m pip install -r requirements-dev.txt
python -m ruff check app tests scripts
python -m pyright --skipunannotated --pythonpath "$(command -v python)" app
python -m pytest -q
~~~

UI tests require a display. In headless Linux environments, install `xvfb` and use `xvfb-run -a python -m pytest -q`, as CI does.

See [`CHANGELOG.md`](CHANGELOG.md) for project history. Some screenshots may lag behind the code. Report bugs, suggest features through [Issues](https://github.com/GuilleBouix/Yagua-Image-Processor/issues), or submit focused pull requests with relevant validation. When changing documented behavior, update all nine README languages.

## Support the project

If Yagua helps you, a GitHub star makes it easier for others to find it. You can also help with bug reports, translations or contributions.

**[Sponsor on GitHub](https://github.com/sponsors/GuilleBouix) · [Support via PayPal](https://www.paypal.com/paypalme/guillebouix)**

<p align="center">
  <a href="https://www.paypal.com/paypalme/guillebouix"><img src="https://github.com/user-attachments/assets/2f3f6a1b-990c-4fb8-9fda-7482c1ca20a5" width="220" alt="Support Yagua via PayPal" /></a>
</p>

## License

Yagua is released under the **[MIT License](LICENSE)**. Third-party libraries and models retain their respective licenses.
