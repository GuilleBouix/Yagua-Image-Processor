<div align="center">

[English](../../README.md) · [Español](README_es.md) · [Português](README_pt.md) · [Français](README_fr.md) · **Deutsch** · [Italiano](README_it.md) · [日本語](README_ja.md) · [简体中文](README_zh_cn.md) · [Русский](README_ru.md)

<img src="https://github.com/user-attachments/assets/fc1dacf8-5249-43da-a294-4b20dc423304" width="1000" alt="Yagua-Banner — Bildverarbeitung" />

# Yagua · Image Processor

### Deine Bilder. Dein Computer. Dein Arbeitsablauf.

Kostenlose Open-Source-Desktopwerkzeuge zum Konvertieren, Komprimieren und Verarbeiten von Bildern im Stapel.

**Offizielle Website (Seiten auf Englisch)**

[Startseite](https://yagua.bouixdev.workers.dev/en/) · [Downloads](https://yagua.bouixdev.workers.dev/en/downloads/) · [Dokumentation](https://yagua.bouixdev.workers.dev/en/docs/) · [Häufige Fragen](https://yagua.bouixdev.workers.dev/en/faq/)

<p align="center">
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/releases/latest"><img src="https://img.shields.io/github/v/release/GuilleBouix/Yagua-Image-Processor?style=flat-square&amp;label=stable&amp;color=2563eb" alt="Neueste stabile Version" /></a>
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/releases"><img src="https://img.shields.io/github/downloads/GuilleBouix/Yagua-Image-Processor/total?style=flat-square&amp;label=downloads&amp;color=22c55e" alt="Downloads insgesamt" /></a>
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/GuilleBouix/Yagua-Image-Processor/ci.yml?branch=main&amp;style=flat-square&amp;label=CI" alt="CI-Status" /></a>
  <a href="#requirements"><img src="https://img.shields.io/badge/Python-3.13-3776ab?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.13" /></a>
  <a href="../../LICENSE"><img src="https://img.shields.io/badge/license-MIT-f4c430?style=flat-square" alt="MIT-Lizenz" /></a>
</p>

</div>

## Inhalt

- [Downloads](https://github.com/GuilleBouix/Yagua-Image-Processor/releases)
- [Funktionen](#features)
- [Screenshots](#screenshots)
- [Installation](#installation)
- [Verwendung](#usage)
- [Voraussetzungen](#requirements)
- [FAQ](#faq)
- [Mitwirken](#contributing)

## Warum Yagua?

Yagua bündelt alltägliche Aufgaben der Bildverarbeitung in einer Desktop-App für Webentwickler, Designer, Fotografen und alle, die mit Bildsammlungen arbeiten. Für die Verarbeitung deiner Dateien brauchst du weder ein Abonnement noch einen Browser.

Die Verarbeitung läuft auf deinem Computer. Hintergrundentfernung und OCR benötigen zunächst einen Modelldownload und können danach offline arbeiten, wenn die benötigten Modelle gespeichert sind. Aktualisierungsprüfungen kontaktieren GitHub; Download-, Spenden- und Kartenlinks öffnen sich im Browser.

Die Oberfläche des aktuellen Quellcodes unterstützt **Englisch, Spanisch, Portugiesisch, Französisch, Deutsch, Italienisch, Japanisch, vereinfachtes Chinesisch und Russisch**, mit dunklen Themen und verfügbaren Vorschauen. Veröffentlichte Pakete können weniger Sprachen enthalten; die Verfügbarkeit hängt von der installierten Version ab. Die Oberflächensprache fügt keine OCR-Erkennungssprachen hinzu.

<a id="features"></a>

## Funktionen

Die Tabelle zeigt die Desktopmodule. Verfügbarkeit und Bedienelemente hängen von deiner installierten Version ab; lies ihre Versionshinweise.

| Modul | Möglichkeiten | Formate und Ausgaben | Auswahlgrenze |
| --- | --- | --- | --- |
| Konvertieren | Format ändern und die Qualität anpassen, sofern unterstützt. | Ausgaben als JPEG, PNG, WebP, AVIF, HEIC, ICO, BMP, TIFF und statisches GIF. | 100 Bilder |
| Komprimieren | Dateigröße verringern und das ursprüngliche Format behalten. | JPEG, PNG, WebP, AVIF, HEIC/HEIF und weitere unterstützte Rasterformate. | 100 Bilder |
| Skalieren / Zuschneiden / Leinwand | Abmessungen ändern, zuschneiden oder Fläche hinzufügen; Größenvorlagen verwenden. | Übliche Rasterbilder, darunter JPEG, PNG und WebP. | 100 Bilder |
| Hintergrund entfernen | Hintergründe lokal mit KI entfernen. | PNG-, WebP- oder TIFF-Ausgabe mit Transparenz. | 10 Bilder |
| Farbpalette | Farben extrahieren, HEX/RGB/HSL kopieren und ein PNG pro Bild exportieren. | Unterstützte Bilder → einzelne Paletten; den ganzen Stapel speichern. | 100 Bilder |
| Wasserzeichen | Ein Logo hinzufügen; Position, Größe, Deckkraft und Abstand anpassen. | Unterstützte Ausgangsbilder; transparentes PNG für das Logo empfohlen. | 100 Bilder + 1 Logo |
| Umbenennen | Nummerierung, Datumsangaben und Groß-/Kleinschreibung vorab ansehen. | Ändert Dateinamen im ursprünglichen Ordner. | 100 Dateien |
| OCR | Spanischen und/oder englischen Text mit EasyOCR erkennen; kopieren oder als TXT exportieren. | Unterstützte Rasterbilder → Text. | 10 Bilder |
| EXIF-Metadaten | Anzeigen, exportieren, Felder bearbeiten oder Metadaten im Stapel entfernen. | JPEG/TIFF bearbeiten; Metadaten als TXT/JSON exportieren. | 1 Bild zum Bearbeiten; 100 zum Bereinigen |
| LQIP / Base64 | Platzhalter geringer Qualität erzeugen oder Bilder für das Web kodieren. | Base64, Daten-URIs, HTML und CSS; TXT/JSON-Export. | 1 Bild |

Die Unterstützung hängt vom Modul, den installierten Codecs und der Plattform ab. Ein aufgeführtes Format bedeutet nicht, dass jedes Modul es lesen oder schreiben kann. Siehe [Voraussetzungen](#requirements).

## Screenshots

Yagua-Screenshots mit englischer Oberfläche. Klicke auf ein Vorschaubild, um es in voller Größe zu öffnen. Anordnung und Bedienelemente können je nach Version abweichen.

<table>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/home.webp"><img src="../../assets/screenshots/home.webp" width="450" alt="Startseite mit allen Modulen" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/convert.webp"><img src="../../assets/screenshots/convert.webp" width="450" alt="Konvertierung mit ausgewählten Bildern und Ausgabeformat" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/compress.webp"><img src="../../assets/screenshots/compress.webp" width="450" alt="Komprimierung mit Qualitäts- und Speichereinstellungen" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/resize.webp"><img src="../../assets/screenshots/resize.webp" width="450" alt="Größenänderung mit einer Vorlage für YouTube-Kanalbanner" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/remove-background.webp"><img src="../../assets/screenshots/remove-background.webp" width="450" alt="Hintergrundentfernung mit ausgewähltem Bild" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/palette.webp"><img src="../../assets/screenshots/palette.webp" width="450" alt="Extrahierte Palette mit acht Farben und Farbwerten" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/watermark.webp"><img src="../../assets/screenshots/watermark.webp" width="450" alt="Wasserzeicheneinstellungen und Ergebnisvorschau" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/rename.webp"><img src="../../assets/screenshots/rename.webp" width="450" alt="Stapelumbenennung mit ursprünglichen und vorgeschlagenen Dateinamen" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/ocr.webp"><img src="../../assets/screenshots/ocr.webp" width="450" alt="Englische OCR mit erkanntem Text" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/metadata.webp"><img src="../../assets/screenshots/metadata.webp" width="450" alt="EXIF-Ansicht mit Bildauswahl, Vorschau und Metadatenfeldern" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/lqip-base64.webp"><img src="../../assets/screenshots/lqip-base64.webp" width="450" alt="LQIP-Vergleich mit dem Originalbild und erzeugter Daten-URI" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/settings.webp"><img src="../../assets/screenshots/settings.webp" width="450" alt="Allgemeine Einstellungen für Sprache, Thema, Skalierung und sichtbare Module" /></a></td>
  </tr>
</table>

## Installation

### Version auswählen

Öffne **[GitHub Releases](https://github.com/GuilleBouix/Yagua-Image-Processor/releases)** und wähle dein Betriebssystem. Das Badge **stable** führt zur neuesten stabilen GitHub-Version; neuere Builds mit der Kennzeichnung **Pre-release**, einschließlich `rc`, sind Testversionen. Windows und Linux können unterschiedliche Versionsstände haben.

Die Quellcodeversion steht in [`app/version.py`](../../app/version.py). Das bedeutet nicht, dass ein passendes Installationspaket veröffentlicht wurde. Lies die Hinweise der jeweiligen Veröffentlichung und lade die dort angehängten Dateien herunter.

| Plattform | Paket | Schritte |
| --- | --- | --- |
| Windows | `Yagua_Setup_<version>.exe` | Installer ausführen und Yagua anschließend über das Startmenü oder die Desktopverknüpfung öffnen. |
| Windows portabel | `Yagua_Portable_<version>.zip`, sofern verfügbar | Das gesamte ZIP in einen beschreibbaren Ordner entpacken und darin `Yagua.exe` starten. Die zugehörigen Dateien zusammenlassen. |
| Linux x86_64 | `Yagua-<version>-x86_64.AppImage`, sofern verfügbar | Die heruntergeladene Datei ausführbar machen und wie unten gezeigt starten. |
| macOS | Experimentelle Unterstützung über Quellcode/Build | Ein stabiles macOS-Paket wird nicht zugesichert. Siehe das vorhandene [Build-Skript](../../scripts/build_macos_app.sh). |

Ersetze unter Linux den Beispieldateinamen durch den deiner heruntergeladenen Datei:

~~~bash
chmod +x "Yagua-<version>-x86_64.AppImage"
./"Yagua-<version>-x86_64.AppImage"
~~~

### Aus dem Quellcode starten

Verwende **Python 3.13**, die in der Projekt-CI eingesetzte Version, und Git. Die Installation der Abhängigkeiten kann umfangreich sein, da OCR- und KI-Bibliotheken enthalten sind. Linux benötigt außerdem Tk und die unter [Voraussetzungen](#requirements) genannten Systembibliotheken.

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

Die Befehle verwenden die im Repository festgelegten Abhängigkeitsversionen. Die Windows/Linux-CI bestätigt keine Kompatibilität mit anderen Python-Versionen oder macOS.

<a id="usage"></a>

## Verwendung

1. Öffne Yagua und wähle ein Modul in der Seitenleiste.
2. Lade deine Bilder und stelle die verfügbaren Optionen ein.
3. Prüfe die Vorschau, falls das Modul eine anbietet.
4. Verarbeite die Bilder und wähle bei Aufforderung einen Ausgabeordner; prüfe die Abschlussmeldung auf Fehler.

**LQIP / Base64:** Ein Bild auswählen, Modus und Parameter einstellen, erzeugen, vergleichen und Data URI, HTML, CSS oder reines Base64 kopieren oder exportieren. Ein neues Bild setzt LQIP-Modus, Breite 20 px, Unschärfe 2 und Qualitäten 40/85 zurück; Abbrechen behält den aktuellen Zustand. Beide Modi erzeugen JPEG ohne Transparenz.

**Originaldateien:** Umbenennen ändert die Dateinamen am aktuellen Speicherort. EXIF-Bearbeitung überschreibt das ausgewählte Bild nach Bestätigung. Arbeite bei diesen Vorgängen mit Kopien. Die EXIF-Stapelbereinigung schreibt in den gewählten Ausgabeordner. Andere Exporte verwenden den Speichern- oder Ausgabeordnerablauf des jeweiligen Moduls.

### Praktische Beispiele

- **Webbilder vorbereiten:** Konvertiere bis zu 100 Fotos nach WebP, wähle die Qualität und passe bei Bedarf die Größe an. Erzeuge LQIP-Platzhalter separat als Vorschau während des Ladens deiner Website.
- **Produktfotos vorbereiten:** Lade bis zu 10 Bilder in Hintergrund entfernen und exportiere sie als PNG oder WebP, um Transparenz zu erhalten. Füge bei Bedarf mit Wasserzeichen ein transparentes PNG-Logo hinzu.
- **Text extrahieren:** Lade bis zu 10 scharfe Bilder in OCR, wähle Spanisch, Englisch oder beides und kopiere das Ergebnis oder exportiere eine TXT-Datei. Die Oberflächensprache fügt keine OCR-Erkennungssprachen hinzu. Prüfe den Text auf Erkennungsfehler.

### Vorschau und Einstellungen zur Hintergrundentfernung

- **Skalieren / Zuschneiden / Leinwand:** Klicke auf eine Dateizeile, um ein Bild anzusehen; die Verarbeitung gilt weiterhin für den geladenen Stapel. Die Vorschau folgt dem sichtbaren Tab und zeigt ursprüngliche und endgültige Abmessungen. Breiten-/Höhenregler der Leinwand sind mit manuellen Eingaben synchronisiert. Die verkleinerte Vorschau zeigt die Bildaufteilung, nicht die endgültigen Pixeldetails.

- **Hintergrund entfernen:** zeigt vor der Verarbeitung das Original und danach das gespeicherte Ergebnis. Kantenverfeinerung bietet Auto/Ja/Nein; Weißsaumreduzierung (0–100 %, anfangs 85 %) und Verkleinern/Erweitern des Umrisses (−5 bis +5 Originalpixel, anfangs 0) sind immer sichtbar. Auto erhält das bisherige Verhalten; weiße Säume werden bei erkannten gleichmäßigen hellen Hintergründen reduziert. Die Ausgabe bleibt transparent. Nach Änderungen erneut verarbeiten; keine zusätzlichen Modelldownloads.

<a id="requirements"></a>

## Voraussetzungen und Grenzen

### Hardware

Für die vollständige App einschließlich **OCR und Hintergrundentfernung**:

| Komponente | Vorläufige Mindestanforderung | Empfohlen |
| --- | --- | --- |
| Prozessor | Relativ aktuelle Intel/AMD-x86-64-CPU mit **4 Kernen** | Moderne CPU mit **6–8 Kernen** |
| Arbeitsspeicher des Computers | **8 GB**, mit wenigen anderen geöffneten Anwendungen | **16 GB**; **32 GB** für sehr große Bilder und Multitasking |
| Speicherplatz | **4 GB frei**, zusätzlich zum Platz für Originale und Ergebnisse | **SSD mit mindestens 10 GB freiem Platz**, zusätzlich zu deinen Bildern |
| Grafik | Integrierte Grafik reicht aus; keine dedizierte GPU erforderlich | Integrierte Grafik reicht aus |
| Internet | Für den ersten Modelldownload und die Suche nach Updates | Offline-Nutzung, sobald die benötigten Modelle heruntergeladen sind |

**Dies sind praktische Schätzungen für die vollständige App, keine validierten Hardware-Mindestanforderungen. Tests auf einem Einsteiger-PC stehen noch aus.** Ein Computer mit 4 GB RAM wird für den vollständigen Einsatz von OCR und Hintergrundentfernung nicht empfohlen. Der Ressourcenbedarf hängt von Auflösung, Stapelgröße und Modellen ab; verkleinere Stapel bei begrenzten Ressourcen.

Das getestete Paket verarbeitet Bilder auf der **CPU**; du brauchst weder eine NVIDIA noch eine andere dedizierte Grafikkarte. Priorisiere Prozessor, RAM und SSD. Die Hintergrundentfernung verwendet den CPU-Ausführungsanbieter von ONNX Runtime; siehe die [offizielle ONNX-Runtime-Dokumentation](https://onnxruntime.ai/docs/api/python/api_summary.html).

### Betriebssysteme

| System | Basis und Validierung |
| --- | --- |
| Windows | **Windows 10/11, 64 Bit**; vorzugsweise Windows 11. ONNX Runtime nennt Windows 10 als älteste unterstützte Windows-Version. Die Prüfung des endgültigen Installers und portablen Pakets auf sauberen Windows-10/11-PCs steht noch aus. |
| Linux | **Ubuntu 22.04 x86-64**, die in der CI geprüfte Basis. Andere Distributionen, Versionen und Desktopumgebungen erfordern eine Prüfung des endgültigen AppImage. |
| macOS | Experimentelle Unterstützung; ein validiertes natives Paket wird nicht zugesichert. |

Aktuelle Windows- und Linux-Pakete sind für **x86-64** vorgesehen; es gibt keine validierte native ARM-Version. Die CI verwendet Windows Server und Ubuntu 22.04/Xvfb; diese Prüfungen zertifizieren nicht alle Desktopsysteme. Siehe die [Plattformvoraussetzungen von ONNX Runtime](https://onnxruntime.ai/docs/build/inferencing.html).

<details>
<summary>Gemessener Ressourcenbedarf und erstes Laden des Modells</summary>

Die Paketprüfung dokumentiert diese ungefähren Beobachtungen aus CI-Builds, die am 15. Oktober 2026 getestet wurden:

| Messung | Windows | Linux |
| --- | --- | --- |
| Beobachtete Spitzen-RAM-Nutzung des Prozesses mit mehreren geladenen Modellen | **3,0 GB** | **2,6 GB** |
| App + alle in diesem Test gemessenen Modelle und Caches | **1,10 GB** | **1,53 GB** |
| Erstes Laden des Modells zur Hintergrundentfernung (ISNet) | **53 Sekunden** | **39 Sekunden** |

**Dies sind Beobachtungen, keine garantierten Höchstwerte oder Laufzeiten.** Beim RAM-Test blieben mehrere Modelle geladen; große Fotos können mehr Speicher benötigen. Die Speicherplatzwerte umfassen das gemessene Paket, Modelle und Caches, nicht Originale, Ergebnisse, temporären Platz zum Entpacken oder eine Entwicklungsumgebung für den Quellcode. Ladezeiten hängen vom Computer ab; anschließend wird die Sitzung wiederverwendet. Es sind weder Modelldownloadzeiten noch Verarbeitungszeiten pro Bild.

</details>

### Ausführung und Verarbeitung

- **Quellcode:** Python 3.13, Tk und die Bibliotheken aus [`requirements.txt`](../../requirements.txt). Fertige Pakete benötigen keine separate Python-Installation.
- **Stapel:** Die Funktionstabelle zeigt die aktuellen Oberflächengrenzen: ein Bild für LQIP / Base64 oder EXIF-Bearbeitung, 10 für OCR/Hintergrundentfernung und 100 für die anderen aufgeführten Stapelvorgänge.
- **Codecs:** HEIC/HEIF verwendet `pillow-heif`, das in den Quellcode-Abhängigkeiten enthalten ist. AVIF und andere Formate hängen von Pillow-Codecs und Plattform ab. JPEG unterstützt keine Transparenz; verwende bei Bedarf PNG oder WebP. PNG-Komprimierung kann das Bild auf 256 Farben reduzieren: Prüfe das Ergebnis.
- **KI-Modelle:** Downloads können beim ersten Einsatz oder bei einer neu gewählten Modell-/Sprachkombination erfolgen. Für Offline-Nutzung müssen die Modelle gespeichert sein. Das getestete Paket führt OCR und Hintergrundentfernung auf der CPU aus.

### Systembibliotheken unter Linux

AppImage benötigt **FUSE 2** für die Ausführung per Einhängen (`libfuse2` auf passenden Distributionen). Falls FUSE nicht verfügbar ist, kannst du das AppImage stattdessen entpacken; siehe die [offizielle AppImage-Anleitung](https://docs.appimage.org/user-guide/troubleshooting/fuse.html). Ersetze den Beispieldateinamen durch den der heruntergeladenen Datei:

~~~bash
./"Yagua-<version>-x86_64.AppImage" --appimage-extract-and-run
~~~

Das Entpacken benötigt zusätzlichen temporären Speicherplatz und kann den Start verlangsamen. Für Quellcode-Ausführungen installiert die CI Tk und diese Bibliotheken unter Ubuntu 22.04:

~~~bash
sudo apt-get install python3-tk libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgtk-3-0 libgomp1
~~~

Paketnamen unterscheiden sich je nach Distribution. Stelle sicher, dass Tk für deinen Python-3.13-Interpreter verfügbar ist; das Standard-Tk-Paket der Distribution deckt eine separat installierte Python-Version möglicherweise nicht ab.

<a id="faq"></a>

## Häufige Fragen

### Lädt Yagua meine Bilder hoch?

Die Verarbeitung erfolgt lokal; die Module laden Bilder nicht zu einem Verarbeitungsdienst hoch. Modelldownloads und GitHub-Aktualisierungsprüfungen benötigen eine Verbindung. Externe Links öffnen den Browser; beim Öffnen des EXIF-Kartenlinks werden die ausgewählten GPS-Koordinaten an Google Maps übermittelt.

### Warum dauert der erste KI-Vorgang länger?

OCR und Hintergrundentfernung initialisieren ihre Engines und laden möglicherweise Modelle herunter. Warte, bis dieser Schritt abgeschlossen ist. Spätere Ausführungen können gespeicherte Modelle wiederverwenden; große Bilder und Stapel benötigen weiterhin mehr Ressourcen.

### Warum ist ein Format nicht verfügbar oder wird ein Bild abgelehnt?

Unterstützte Eingaben hängen vom Modul und den verfügbaren Codecs ab. Probiere eine PNG- oder JPEG-Kopie und prüfe `yagua.log`. Exportiere als PNG oder WebP, wenn du Transparenz benötigst.

### Warum verkleinert die Komprimierung nicht jedes Bild?

Ein bereits optimiertes Bild wird möglicherweise nicht kleiner. Ist die EXIF-Entfernung deaktiviert, kopiert Yagua das Original in die Ausgabe, wenn die Komprimierung eine genauso große oder größere Datei erzeugen würde. Ist die EXIF-Entfernung aktiviert, speichert es das verarbeitete Bild auch dann, wenn es größer ist, damit dieser Rückgriff auf das Original dessen EXIF nicht wiederherstellt. Verwende für einen eigenen EXIF-Bereinigungsablauf das Metadatenmodul.

### Wie funktionieren Aktualisierungen?

Yagua kann beim Start informieren und bietet eine Prüfung unter **Einstellungen → Updates**. Die App öffnet einen Downloadlink und installiert Updates nicht automatisch. RC.4/RC.5-Pakete suchen nur nach neueren stabilen Releases mit dem passenden Plattformpräfix (`win-v` oder `linux-v`); Vorabversionen und Entwürfe werden ausgeschlossen, sodass neuere RC-Builds nicht erkannt werden. Lade Testversionen manuell über [GitHub Releases](https://github.com/GuilleBouix/Yagua-Image-Processor/releases) herunter. Diese Pakete können auch nach einem Verbindungsfehler «Keine Updates verfügbar» anzeigen; prüfe im Zweifel Releases direkt, auch ältere Veröffentlichungen ohne Plattformpräfix.

### Wie melde ich ein Problem?

Öffne einen [Fehlerbericht](https://github.com/GuilleBouix/Yagua-Image-Processor/issues/new?template=bug_report.md) mit Yagua-Version, Betriebssystem, Modul, Reproduktionsschritten und relevanten Protokollen. Suche `yagua.log` hier:

- Windows: `%APPDATA%\Yagua\yagua.log`
- Linux: `~/.config/Yagua/yagua.log`
- macOS: `~/Library/Application Support/Yagua/yagua.log`

Protokolle können Dateipfade und Namen enthalten; prüfe sie vor dem Teilen.

<a id="contributing"></a>

## Entwicklung und Mitwirkung

Yagua verwendet **CustomTkinter** für die Oberfläche, **Pillow / pillow-heif** für Bilder, **rembg / ONNX Runtime** für Hintergrundentfernung, **EasyOCR / PyTorch** für OCR und **piexif** für EXIF. Genaue Versionen stehen in [`requirements.txt`](../../requirements.txt).

Installiere nach der Quellcode-Einrichtung die Entwicklungswerkzeuge und führe die CI-Prüfungen aus. Verwende unter Windows direkt die Programme der virtuellen Umgebung:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m ruff check app tests scripts
.\.venv\Scripts\python.exe -m pyright --skipunannotated --pythonpath .\.venv\Scripts\python.exe app
.\.venv\Scripts\python.exe -m pytest -q
~~~

Unter Linux mit aktivierter virtueller Umgebung:

~~~bash
python -m pip install -r requirements-dev.txt
python -m ruff check app tests scripts
python -m pyright --skipunannotated --pythonpath "$(command -v python)" app
python -m pytest -q
~~~

Oberflächentests benötigen eine Anzeige. Installiere unter Linux ohne grafische Umgebung `xvfb` und verwende `xvfb-run -a python -m pytest -q`, wie in der CI.

Siehe [`CHANGELOG.md`](../../CHANGELOG.md) für die Projekthistorie. Manche Screenshots können dem Code hinterherhinken. Melde Fehler, schlage Funktionen über [Issues](https://github.com/GuilleBouix/Yagua-Image-Processor/issues) vor oder sende gezielte PRs mit passenden Prüfergebnissen. Aktualisiere bei Änderungen an dokumentiertem Verhalten alle neun README-Sprachen.

## Projekt unterstützen

Wenn Yagua dir hilft, erleichtert ein GitHub-Stern anderen, es zu entdecken. Du kannst auch durch Fehlerberichte, Übersetzungen oder Beiträge helfen.

**[Yagua schon ausprobiert? Hinterlasse eine Bewertung (auf Englisch)](https://yagua.bouixdev.workers.dev/en/project/#project-rating)**

**[Über GitHub Sponsors unterstützen](https://github.com/sponsors/GuilleBouix) · [Über PayPal unterstützen](https://www.paypal.com/paypalme/guillebouix)**

<p align="center">
  <a href="https://www.paypal.com/paypalme/guillebouix"><img src="https://github.com/user-attachments/assets/2f3f6a1b-990c-4fb8-9fda-7482c1ca20a5" width="220" alt="Yagua über PayPal unterstützen" /></a>
</p>

## Lizenz

Yagua steht unter der **[MIT-Lizenz](../../LICENSE)**. Bibliotheken und Modelle von Drittanbietern behalten ihre jeweiligen Lizenzen.
