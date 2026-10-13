<div align="center">

**English** · [Español](docs/i18n/README_es.md) · [Português](docs/i18n/README_pt.md) · [Français](docs/i18n/README_fr.md) · [Deutsch](docs/i18n/README_de.md)

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

The interface supports **English, Spanish, Portuguese, French and German**, with dark themes, previews where available and diagnostic logs under **Settings → Logs**.

## Features

The table describes the current source code. Packaged releases may include different features; check their release notes.

| Module | What you can do | Formats and outputs | Selection limit |
| --- | --- | --- | --- |
| Convert | Change format and adjust quality where supported. | JPEG, PNG, WebP, AVIF, HEIC, ICO, BMP, TIFF, GIF outputs. | 100 images |
| Compress | Reduce file size while keeping the original format. | JPEG, PNG, WebP, AVIF, HEIC/HEIF and other supported raster formats. | 100 images |
| Resize / Crop / Canvas | Set dimensions, crop or add canvas space; use size presets. | Common raster images, including JPEG, PNG and WebP. | 100 images |
| Remove background | Remove backgrounds locally with AI. | PNG, WebP or TIFF output with transparency. | 10 images |
| Color palette | Extract colors, copy HEX/RGB/HSL values and export a palette. | One supported image → colors and a PNG palette. | 1 image |
| Watermark | Apply an image logo; adjust position, size, opacity and margin. | Supported base images; transparent PNG recommended for the logo. | 100 images + 1 logo |
| Rename | Preview numbered names, dates and letter case changes. | Changes filenames in their current folder. | 100 files |
| OCR | Extract text with EasyOCR; copy it or export as TXT. | Supported raster images → text. | 10 images |
| EXIF metadata | Inspect, export, edit fields or remove metadata in batches. | JPEG/TIFF editing; TXT/JSON metadata export. | 1 image for editing; 100 for cleanup |
| LQIP / Base64 | Generate low-quality placeholders or encode images for the web. | Base64, data URIs, HTML and CSS; TXT/JSON export. | 1 image |

Format support varies by module, installed codecs and platform. A listed format is not a guarantee that every module can read or write it. See [requirements](#requirements).

## Screenshots

<p align="center">
  <a href="https://github.com/user-attachments/assets/903c897e-eb48-4b6b-b941-2fbfffb234ce"><img src="https://github.com/user-attachments/assets/903c897e-eb48-4b6b-b941-2fbfffb234ce" width="420" alt="Conversion module with selected images and output format controls" /></a>
  <a href="https://github.com/user-attachments/assets/ed7081e4-d106-47db-9744-927be0db9d5d"><img src="https://github.com/user-attachments/assets/ed7081e4-d106-47db-9744-927be0db9d5d" width="420" alt="Background removal module with selected images and output format controls" /></a>
</p>

<details>
<summary>More screenshots: compression, resizing, palette, renaming, EXIF, LQIP and settings</summary>

<p align="center">
  <a href="https://github.com/user-attachments/assets/f8f57bbb-4cdf-4c5f-8d06-a04b2c3dc1b1"><img src="https://github.com/user-attachments/assets/f8f57bbb-4cdf-4c5f-8d06-a04b2c3dc1b1" width="280" alt="Compression module with a quality slider and EXIF removal option" /></a>
  <a href="https://github.com/user-attachments/assets/381c1f71-debd-47a0-837b-fb8f84e41790"><img src="https://github.com/user-attachments/assets/381c1f71-debd-47a0-837b-fb8f84e41790" width="280" alt="Resize module with resize, crop and canvas tabs" /></a>
  <a href="https://github.com/user-attachments/assets/dfe2dd77-f792-4092-a6d7-82b5e96aa104"><img src="https://github.com/user-attachments/assets/dfe2dd77-f792-4092-a6d7-82b5e96aa104" width="280" alt="Extracted color palette with swatches and color values" /></a>
</p>
<p align="center">
  <a href="https://github.com/user-attachments/assets/e3a8f766-84e5-412d-bbaf-acb5936c0380"><img src="https://github.com/user-attachments/assets/e3a8f766-84e5-412d-bbaf-acb5936c0380" width="280" alt="Batch rename module showing original and proposed filenames" /></a>
  <a href="https://github.com/user-attachments/assets/235fce12-9796-4304-9252-f9e016edf483"><img src="https://github.com/user-attachments/assets/235fce12-9796-4304-9252-f9e016edf483" width="280" alt="EXIF editor with author, copyright, software and date fields" /></a>
  <a href="https://github.com/user-attachments/assets/8e8824a4-0bdf-44d8-b82f-7e0c2e1fcfe5"><img src="https://github.com/user-attachments/assets/8e8824a4-0bdf-44d8-b82f-7e0c2e1fcfe5" width="280" alt="LQIP and Base64 module with placeholder size and quality controls" /></a>
</p>
<p align="center">
  <a href="https://github.com/user-attachments/assets/29131d50-2ea2-40c5-9549-d5878d89119a"><img src="https://github.com/user-attachments/assets/29131d50-2ea2-40c5-9549-d5878d89119a" width="280" alt="Yagua settings with interface language and theme selection" /></a>
</p>

</details>

These are existing project screenshots; layouts and controls can differ between versions. Click an image to view it at full size.

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
- **Extract text:** Load up to 10 clear images in OCR, choose recognition languages, then copy the result or export a TXT file. Review the text for recognition errors.

<a id="requirements"></a>

## Requirements and limits

- **Desktop:** Windows or Linux; Linux packages target x86_64. macOS support is experimental.
- **From source:** Python 3.13, Tk and the libraries in [`requirements.txt`](requirements.txt). Prebuilt packages do not require a separate Python installation.
- **Resources:** RAM, disk space and processing time depend on image resolution, batch size and AI models. Keep space for dependencies, downloaded models and outputs; reduce batch size on machines with limited resources. No measured minimum hardware requirements are documented here.
- **Batch limits:** The table lists current UI limits: one image for Palette, LQIP / Base64 or EXIF editing, 10 for OCR/background removal and 100 for the other listed batch operations.
- **Codecs:** HEIC/HEIF uses `pillow-heif`, included in source dependencies. AVIF and other formats depend on Pillow codecs and platform. JPEG has no transparency; use PNG or WebP when alpha is needed. PNG compression can reduce the image to 256 colors, so check the result.
- **AI models:** Downloads can occur on first use or when a newly selected model/language needs one. Offline use requires the models to be present. CPU processing is available; GPU use depends on compatible hardware and libraries.

### Linux system libraries

AppImage may need FUSE 2 (`libfuse2` on compatible distributions). For source runs, Linux CI installs Tk and these libraries on Ubuntu 22.04:

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

Supported inputs differ by module and codec availability. Try a PNG or JPEG copy, review **Settings → Logs**. Export to PNG or WebP if you need transparency.

### Why does compression not reduce every image?

An already optimized image may not become smaller. If compression produces a file at least as large as the original, Yagua copies the original to the output instead. Requested metadata removal is therefore not guaranteed by compression; use the dedicated EXIF cleanup module.

### How do updates work?

Yagua can notify you on startup and lets you check under **Settings → Updates**. The checker looks for newer stable releases with the matching platform prefix (`win-v` or `linux-v`) and excludes prereleases. It opens a download link; it does not automatically install updates. Check Releases manually for test builds and older unprefixed releases.

### How do I report a problem?

Open a [bug report](https://github.com/GuilleBouix/Yagua-Image-Processor/issues/new?template=bug_report.md) with your Yagua version, OS, module, steps to reproduce and relevant logs. Inspect logs in **Settings → Logs** or locate `yagua.log` at:

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

See [`CHANGELOG.md`](CHANGELOG.md) for project history. Some screenshots may lag behind the code. Report bugs, suggest features through [Issues](https://github.com/GuilleBouix/Yagua-Image-Processor/issues), or submit focused pull requests with relevant validation. When changing documented behavior, update all five README languages.

## Support the project

If Yagua helps you, a GitHub star makes it easier for others to find it. You can also help with bug reports, translations or contributions.

**[Sponsor on GitHub](https://github.com/sponsors/GuilleBouix) · [Support via PayPal](https://www.paypal.com/paypalme/guillebouix)**

<p align="center">
  <a href="https://www.paypal.com/paypalme/guillebouix"><img src="https://github.com/user-attachments/assets/2f3f6a1b-990c-4fb8-9fda-7482c1ca20a5" width="220" alt="Support Yagua via PayPal" /></a>
</p>

## License

Yagua is released under the **[MIT License](LICENSE)**. Third-party libraries and models retain their respective licenses.
