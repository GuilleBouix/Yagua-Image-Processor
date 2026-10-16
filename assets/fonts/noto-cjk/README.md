# Bundled CJK fonts

- Upstream: https://github.com/notofonts/noto-cjk
- Release: **Sans2.004**, revision **523d033d6cb47f4a80c58a35753646f5c3608a78**.
- Original static OTF files: Noto Sans CJK JP and SC, Regular and Bold.
- Sources: `Sans/OTF/Japanese/` and `Sans/OTF/SimplifiedChinese/` at that revision.
- License: SIL Open Font License 1.1, reproduced in [LICENSE](LICENSE).
- Original font files are unmodified; copyright notices remain embedded in them.

[manifest.json](manifest.json) records each original file's byte count and SHA256.
The four fonts add **66,939,968 bytes (66.94 MB / 63.84 MiB)** before compression,
plus this documentation, the license and manifest. This is the resource increase,
not a measurement of a rebuilt installer or AppImage.

The application registers them privately with Windows GDI or Linux Fontconfig.
They are loaded from application resources, without internet, administrator
rights or installation in a system/user font directory.

Linux needs Tk built with Xft/Fontconfig support, as provided by the distribution's
`python3-tk`. A Tk build limited to X11 core fonts cannot use these OTF resources.
The package verification rejects missing font families instead of accepting a
fallback with unreadable characters.

Japanese uses **Noto Sans CJK JP**; Simplified Chinese uses **Noto Sans CJK SC**.
Both families are registered so the language selector can show their native names
while another interface language is active. OCR models/languages are independent.
