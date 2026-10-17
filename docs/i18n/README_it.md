<div align="center">

[English](../../README.md) · [Español](README_es.md) · [Português](README_pt.md) · [Français](README_fr.md) · [Deutsch](README_de.md) · **Italiano** · [日本語](README_ja.md) · [简体中文](README_zh_cn.md) · [Русский](README_ru.md)

<img src="https://github.com/user-attachments/assets/fc1dacf8-5249-43da-a294-4b20dc423304" width="1000" alt="Banner di Yagua — Elaboratore di immagini" />

# Yagua · Image Processor

### Le tue immagini. Il tuo computer. Il tuo modo di lavorare.

Strumenti desktop gratuiti e open source per convertire, comprimere ed elaborare immagini in batch.

<p align="center">
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/releases/latest"><img src="https://img.shields.io/github/v/release/GuilleBouix/Yagua-Image-Processor?style=flat-square&amp;label=stable&amp;color=2563eb" alt="Ultima versione stabile" /></a>
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/releases"><img src="https://img.shields.io/github/downloads/GuilleBouix/Yagua-Image-Processor/total?style=flat-square&amp;label=downloads&amp;color=22c55e" alt="Download totali" /></a>
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/GuilleBouix/Yagua-Image-Processor/ci.yml?branch=main&amp;style=flat-square&amp;label=CI" alt="Stato della CI" /></a>
  <a href="#requirements"><img src="https://img.shields.io/badge/Python-3.13-3776ab?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.13" /></a>
  <a href="../../LICENSE"><img src="https://img.shields.io/badge/license-MIT-f4c430?style=flat-square" alt="Licenza MIT" /></a>
</p>

**[Download](https://github.com/GuilleBouix/Yagua-Image-Processor/releases) · [Funzionalità](#features) · [Installazione](#installation)**

[Schermate](#screenshots) · [Utilizzo](#usage) · [Requisiti](#requirements) · [Domande frequenti](#faq) · [Contribuire](#contributing)

</div>

## Perché Yagua?

Yagua riunisce le attività quotidiane sulle immagini in un’unica app desktop per sviluppatori web, designer, fotografi e chiunque lavori con raccolte di immagini. Non servono abbonamenti né un browser per elaborare i file.

L’elaborazione avviene sul tuo computer. La rimozione dello sfondo e l’OCR richiedono un download iniziale dei modelli, poi possono funzionare offline con i modelli necessari nella cache. La ricerca di aggiornamenti contatta GitHub; i link per download, donazioni e mappe si aprono nel browser.

Nel codice attuale l’interfaccia supporta **inglese, spagnolo, portoghese, francese, tedesco, italiano, giapponese, cinese semplificato e russo**, con temi scuri e anteprime dove disponibili. I singoli pacchetti possono includere meno lingue: la disponibilità dipende dalla versione installata. La lingua dell’interfaccia non aggiunge lingue di riconoscimento OCR.

<a id="features"></a>

## Funzionalità

La tabella elenca i moduli desktop. La disponibilità e i controlli dipendono dalla versione installata; consulta le relative note di rilascio.

| Modulo | Cosa puoi fare | Formati e output | Limite di selezione |
| --- | --- | --- | --- |
| Convertire | Cambiare formato e regolare la qualità quando il formato lo consente. | Output JPEG, PNG, WebP, AVIF, HEIC, ICO, BMP, TIFF e GIF statici. | 100 immagini |
| Comprimere | Ridurre le dimensioni del file mantenendo il formato originale. | JPEG, PNG, WebP, AVIF, HEIC/HEIF e altri formati raster supportati. | 100 immagini |
| Ridimensionare / Ritagliare / Tela | Impostare le dimensioni, ritagliare o aggiungere spazio alla tela; usare dimensioni predefinite. | Immagini raster comuni, tra cui JPEG, PNG e WebP. | 100 immagini |
| Rimuovere lo sfondo | Rimuovere gli sfondi localmente con l’IA. | Output PNG, WebP o TIFF con trasparenza. | 10 immagini |
| Tavolozza colori | Estrarre colori, copiare valori HEX/RGB/HSL ed esportare una tavolozza. | Un’immagine supportata → colori e una tavolozza PNG. | 1 immagine |
| Filigrana | Applicare un logo; regolare posizione, dimensioni, opacità e margine. | Immagini di base supportate; per il logo è consigliato un PNG trasparente. | 100 immagini + 1 logo |
| Rinominare | Visualizzare in anteprima nomi numerati, date e modifiche a maiuscole/minuscole. | Modifica i nomi dei file nella cartella corrente. | 100 file |
| OCR | Estrarre testo in spagnolo e/o inglese con EasyOCR; copiarlo o esportarlo in TXT. | Immagini raster supportate → testo. | 10 immagini |
| Metadati EXIF | Esaminare, esportare, modificare campi o rimuovere metadati in batch. | Modifica JPEG/TIFF; esportazione dei metadati in TXT/JSON. | 1 immagine per la modifica; 100 per la pulizia |
| LQIP / Base64 | Generare segnaposto a bassa qualità o codificare immagini per il web. | Base64, URI data, HTML e CSS; esportazione TXT/JSON. | 1 immagine |

Il supporto dei formati varia in base al modulo, ai codec installati e alla piattaforma. Un formato elencato non garantisce che tutti i moduli possano leggerlo o scriverlo. Vedi i [requisiti](#requirements).

<a id="screenshots"></a>

## Schermate

Schermate di Yagua con l’interfaccia in inglese. Fai clic su una miniatura per aprire l’immagine a dimensione intera. Disposizione e controlli possono variare tra le versioni.

<table>
  <tr>
    <td align="center" width="33%"><a href="../../assets/screenshots/home.png"><img src="../../assets/screenshots/home.png" width="300" alt="Schermata iniziale con tutti i moduli" /></a></td>
    <td align="center" width="33%"><a href="../../assets/screenshots/convert.png"><img src="../../assets/screenshots/convert.png" width="300" alt="Conversione con immagini selezionate e controlli del formato di output" /></a></td>
    <td align="center" width="33%"><a href="../../assets/screenshots/compress.png"><img src="../../assets/screenshots/compress.png" width="300" alt="Compressione con controlli di qualità ed EXIF" /></a></td>
  </tr>
  <tr>
    <td align="center" width="33%"><a href="../../assets/screenshots/resize.png"><img src="../../assets/screenshots/resize.png" width="300" alt="Ridimensionamento con dimensione predefinita e immagini caricate" /></a></td>
    <td align="center" width="33%"><a href="../../assets/screenshots/remove-background.png"><img src="../../assets/screenshots/remove-background.png" width="300" alt="Rimozione dello sfondo con un’immagine selezionata" /></a></td>
    <td align="center" width="33%"><a href="../../assets/screenshots/palette.png"><img src="../../assets/screenshots/palette.png" width="300" alt="Tavolozza estratta con otto colori e relativi valori" /></a></td>
  </tr>
  <tr>
    <td align="center" width="33%"><a href="../../assets/screenshots/watermark.png"><img src="../../assets/screenshots/watermark.png" width="300" alt="Controlli della filigrana e anteprima del risultato" /></a></td>
    <td align="center" width="33%"><a href="../../assets/screenshots/rename.png"><img src="../../assets/screenshots/rename.png" width="300" alt="Rinomina in batch con nomi originali e proposti" /></a></td>
    <td align="center" width="33%"><a href="../../assets/screenshots/ocr.png"><img src="../../assets/screenshots/ocr.png" width="300" alt="OCR in inglese con il testo riconosciuto" /></a></td>
  </tr>
  <tr>
    <td align="center" width="33%"><a href="../../assets/screenshots/metadata.png"><img src="../../assets/screenshots/metadata.png" width="300" alt="Editor EXIF con campi dei metadati e anteprima dell’immagine" /></a></td>
    <td align="center" width="33%"><a href="../../assets/screenshots/lqip-base64.png"><img src="../../assets/screenshots/lqip-base64.png" width="300" alt="Segnaposto LQIP confrontato con l’originale e URI data generato" /></a></td>
    <td align="center" width="33%"><a href="../../assets/screenshots/settings.png"><img src="../../assets/screenshots/settings.png" width="300" alt="Impostazioni generali di lingua, tema, scala e moduli visibili" /></a></td>
  </tr>
</table>

<a id="installation"></a>

## Installazione

### Scegliere una versione

Apri **[GitHub Releases](https://github.com/GuilleBouix/Yagua-Image-Processor/releases)** e scegli il tuo sistema operativo. Il badge **stable** rimanda all’ultima versione stabile su GitHub; le versioni più recenti contrassegnate **Pre-release**, incluse quelle `rc`, sono versioni di prova. Le versioni per Windows e Linux possono essere diverse.

La versione del codice sorgente è definita in [`app/version.py`](../../app/version.py). Questo non significa che sia stato pubblicato un programma di installazione corrispondente. Leggi le note di ogni rilascio e scarica i file allegati a quella versione.

| Piattaforma | Pacchetto | Procedura |
| --- | --- | --- |
| Windows | `Yagua_Setup_<version>.exe` | Esegui il programma di installazione, poi apri Yagua dal menu Start o dal collegamento sul desktop. |
| Windows portatile | `Yagua_Portable_<version>.zip`, quando disponibile | Estrai tutto lo ZIP in una cartella scrivibile e avvia `Yagua.exe` al suo interno. Mantieni insieme i file inclusi. |
| Linux x86_64 | `Yagua-<version>-x86_64.AppImage`, quando disponibile | Rendi eseguibile il file scaricato, poi avvialo come indicato sotto. |
| macOS | Supporto sperimentale da sorgente/compilazione | Non è garantito un pacchetto stabile per macOS. Vedi lo [script di compilazione](../../scripts/build_macos_app.sh) esistente. |

Su Linux, sostituisci il nome di esempio con quello del file scaricato:

~~~bash
chmod +x "Yagua-<version>-x86_64.AppImage"
./"Yagua-<version>-x86_64.AppImage"
~~~

### Eseguire dal codice sorgente

Usa **Python 3.13**, la versione utilizzata dalla CI del progetto, e Git. L’installazione delle dipendenze può essere voluminosa perché include librerie OCR e IA. Su Linux servono anche Tk e le librerie di sistema indicate nei [requisiti](#requirements).

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

I comandi usano le dipendenze con versioni fissate nel repository. I controlli CI di Windows/Linux non attestano la compatibilità con altre versioni di Python o con macOS.

<a id="usage"></a>

## Utilizzo

1. Apri Yagua e scegli un modulo dalla barra laterale.
2. Carica le immagini e scegli le opzioni di elaborazione disponibili.
3. Controlla l’anteprima, se il modulo la prevede.
4. Elabora le immagini e scegli una cartella di destinazione quando richiesto; verifica eventuali errori nel messaggio finale.

**LQIP / Base64:** Seleziona un’immagine, scegli modalità e parametri, genera, confronta e poi copia o esporta URI data, HTML, CSS o Base64 puro. Caricare un’altra immagine ripristina la modalità LQIP, larghezza 20 px, sfocatura 2 e qualità 40/85; annullare la selezione mantiene lo stato corrente. Entrambe le modalità producono JPEG senza trasparenza.

**File originali:** La rinomina cambia i nomi direttamente nella cartella originale. La modifica EXIF sovrascrive l’immagine selezionata dopo una conferma. Lavora su copie per queste operazioni. La pulizia EXIF in batch salva nella cartella di destinazione scelta. Le altre esportazioni seguono la procedura di salvataggio o selezione della cartella del relativo modulo.

### Esempi pratici

- **Preparare immagini per il web:** Converti fino a 100 foto in WebP, scegli la qualità e ridimensiona se necessario. Genera separatamente i segnaposto LQIP per le anteprime di caricamento del tuo sito.
- **Preparare foto di prodotti:** Carica fino a 10 immagini in Rimuovere lo sfondo ed esportale in PNG o WebP per mantenere la trasparenza. Se necessario, aggiungi un logo PNG trasparente con Filigrana.
- **Estrarre testo:** Carica fino a 10 immagini nitide nell’OCR, scegli spagnolo, inglese o entrambe le lingue, poi copia il risultato o esporta un file TXT. La lingua dell’interfaccia non aggiunge lingue di riconoscimento OCR. Controlla eventuali errori nel testo riconosciuto.

<a id="requirements"></a>

## Requisiti e limiti

### Hardware

Per l’app completa, inclusi **OCR e rimozione dello sfondo**:

| Componente | Minimo provvisorio | Consigliato |
| --- | --- | --- |
| Processore | CPU Intel/AMD x86-64 relativamente recente con **4 core** | CPU moderna con **6–8 core** |
| RAM del sistema | **8 GB**, con poche altre applicazioni aperte | **16 GB**; **32 GB** per immagini molto grandi e multitasking |
| Archiviazione | **4 GB liberi**, oltre allo spazio per originali e risultati | **SSD con almeno 10 GB liberi**, oltre allo spazio per le immagini |
| Grafica | La grafica integrata è sufficiente; non serve una GPU dedicata | La grafica integrata è sufficiente |
| Internet | Per il download iniziale dei modelli e la ricerca di aggiornamenti | Uso offline dopo aver scaricato i modelli necessari |

**Sono stime pratiche per l’app completa, non requisiti minimi hardware convalidati. Mancano ancora prove su un PC di fascia bassa.** Un sistema con 4 GB di RAM non è consigliato per l’uso completo di OCR e rimozione dello sfondo. Il consumo dipende da risoluzione, dimensioni dei batch e modelli; riduci i batch quando le risorse sono limitate.

Il pacchetto testato elabora le immagini sulla **CPU**; non serve una NVIDIA o un’altra GPU dedicata. Dai priorità a CPU, RAM e SSD. La rimozione dello sfondo usa il provider di esecuzione CPU di ONNX Runtime; consulta la [documentazione ufficiale di ONNX Runtime](https://onnxruntime.ai/docs/api/python/api_summary.html).

### Sistemi operativi

| Sistema | Base e convalida |
| --- | --- |
| Windows | **Windows 10/11 a 64 bit**; preferibile Windows 11. ONNX Runtime indica Windows 10 come versione minima di Windows supportata. La convalida finale del programma di installazione e del pacchetto portatile su PC Windows 10/11 puliti è ancora da effettuare. |
| Linux | **Ubuntu 22.04 x86-64**, la base verificata in CI. Altre distribuzioni, versioni e ambienti desktop richiedono la convalida dell’AppImage finale. |
| macOS | Supporto sperimentale; non si dichiara disponibile un pacchetto nativo convalidato. |

I pacchetti attuali per Windows e Linux sono per **x86-64**; non esiste una versione nativa ARM convalidata. La CI usa Windows Server e Ubuntu 22.04/Xvfb; questi controlli non certificano tutti i sistemi desktop. Vedi i [requisiti di piattaforma di ONNX Runtime](https://onnxruntime.ai/docs/build/inferencing.html).

<details>
<summary>Consumo di risorse misurato e primo caricamento del modello</summary>

L’analisi dei pacchetti riporta queste osservazioni approssimative dalle build CI testate il 15 ottobre 2026:

| Misurazione | Windows | Linux |
| --- | --- | --- |
| Picco di RAM del processo osservato con più modelli caricati | **3.0 GB** | **2.6 GB** |
| App + tutti i modelli e le cache misurati nel test | **1.10 GB** | **1.53 GB** |
| Primo caricamento del modello di rimozione dello sfondo (ISNet) | **53 secondi** | **39 secondi** |

**Sono osservazioni, non valori massimi o tempi di elaborazione garantiti.** Nel test RAM erano caricati più modelli; foto grandi possono richiedere più memoria. Le cifre su disco includono il pacchetto, i modelli e le cache misurati, non originali, risultati, spazio temporaneo di estrazione o un ambiente di sviluppo da sorgente. I tempi di caricamento dipendono dal computer; in seguito la sessione viene riutilizzata. Non sono tempi di download dei modelli né tempi di elaborazione per immagine.

</details>

### Ambiente di esecuzione ed elaborazione

- **Da sorgente:** Python 3.13, Tk e le librerie in [`requirements.txt`](../../requirements.txt). I pacchetti precompilati non richiedono un’installazione separata di Python.
- **Limiti dei batch:** La tabella delle funzionalità indica i limiti attuali dell’interfaccia: un’immagine per Tavolozza, LQIP / Base64 o modifica EXIF, 10 per OCR/rimozione dello sfondo e 100 per le altre operazioni in batch elencate.
- **Codec:** HEIC/HEIF usa `pillow-heif`, incluso nelle dipendenze da sorgente. AVIF e altri formati dipendono dai codec di Pillow e dalla piattaforma. JPEG non supporta la trasparenza; usa PNG o WebP quando serve il canale alfa. La compressione PNG può ridurre l’immagine a 256 colori: controlla il risultato.
- **Modelli IA:** Possono essere scaricati al primo utilizzo o quando un nuovo modello o una nuova lingua lo richiedono. Per l’uso offline i modelli devono essere già presenti. Il pacchetto testato esegue OCR e rimozione dello sfondo sulla CPU.

### Librerie di sistema Linux

AppImage richiede **FUSE 2** per l’esecuzione tramite montaggio (`libfuse2` nelle distribuzioni compatibili). Se FUSE non è disponibile, puoi usare l’estrazione; consulta le [istruzioni ufficiali di AppImage](https://docs.appimage.org/user-guide/troubleshooting/fuse.html). Sostituisci il nome di esempio con quello del file scaricato:

~~~bash
./"Yagua-<version>-x86_64.AppImage" --appimage-extract-and-run
~~~

L’estrazione richiede ulteriore spazio temporaneo su disco e può rallentare l’avvio. Per l’esecuzione da sorgente, la CI Linux installa Tk e queste librerie su Ubuntu 22.04:

~~~bash
sudo apt-get install python3-tk libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgtk-3-0 libgomp1
~~~

I nomi dei pacchetti variano in base alla distribuzione. Assicurati che Tk sia disponibile per l’interprete Python 3.13 utilizzato; il pacchetto Tk predefinito della distribuzione potrebbe non coprire un Python installato separatamente.

<a id="faq"></a>

## Domande frequenti

### Yagua carica le mie immagini online?

L’elaborazione è locale; i moduli non caricano le immagini su un servizio di elaborazione. Il download dei modelli e la ricerca di aggiornamenti su GitHub richiedono una connessione. I link esterni si aprono nel browser; aprire il link alla mappa EXIF invia le coordinate GPS selezionate a Google Maps.

### Perché la prima operazione IA è più lenta?

OCR e rimozione dello sfondo inizializzano i propri motori e possono scaricare modelli. Attendi che questa fase finisca. Le esecuzioni successive possono riutilizzare i modelli nella cache; immagini e batch più grandi richiedono comunque più risorse.

### Perché un formato non è disponibile o un’immagine viene rifiutata?

Gli input supportati variano in base al modulo e ai codec disponibili. Prova una copia PNG o JPEG e controlla `yagua.log`. Esporta in PNG o WebP se serve la trasparenza.

### Perché la compressione non riduce tutte le immagini?

Un’immagine già ottimizzata potrebbe non ridursi. Quando la rimozione EXIF è disattivata, Yagua copia l’originale nella destinazione se la compressione produrrebbe un file di dimensioni uguali o maggiori. Quando la rimozione EXIF è attiva, salva l’immagine elaborata anche se è più grande, così questa alternativa non ripristina gli EXIF originali. Per una pulizia EXIF dedicata, usa il modulo dei metadati.

### Come funzionano gli aggiornamenti?

Yagua può avvisarti all’avvio e permette di controllare da **Impostazioni → Aggiornamenti**. Apre un link di download; non installa automaticamente gli aggiornamenti. I pacchetti RC.4/RC.5 cercano solo versioni stabili più recenti con il prefisso della piattaforma corrispondente (`win-v` o `linux-v`); escludono versioni preliminari e bozze, quindi non rilevano nuove build RC. Scarica manualmente le versioni di prova da [GitHub Releases](https://github.com/GuilleBouix/Yagua-Image-Processor/releases). Quei pacchetti possono anche indicare «Nessun aggiornamento disponibile» dopo un errore di connessione; nel dubbio controlla direttamente Releases, incluse le versioni precedenti senza prefisso di piattaforma.

### Come segnalare un problema?

Apri una [segnalazione di bug](https://github.com/GuilleBouix/Yagua-Image-Processor/issues/new?template=bug_report.md) indicando versione di Yagua, sistema operativo, modulo, passaggi per riprodurre il problema e log pertinenti. Trovi `yagua.log` qui:

- Windows: `%APPDATA%\Yagua\yagua.log`
- Linux: `~/.config/Yagua/yagua.log`
- macOS: `~/Library/Application Support/Yagua/yagua.log`

I log possono contenere percorsi e nomi di file: controllali prima di condividerli.

<a id="contributing"></a>

## Sviluppo e contributi

Yagua usa **CustomTkinter** per l’interfaccia, **Pillow / pillow-heif** per le immagini, **rembg / ONNX Runtime** per la rimozione dello sfondo, **EasyOCR / PyTorch** per l’OCR e **piexif** per EXIF. Le versioni esatte sono in [`requirements.txt`](../../requirements.txt).

Dopo l’installazione da sorgente, installa gli strumenti di sviluppo ed esegui i controlli CI. Su Windows, usa direttamente gli eseguibili dell’ambiente virtuale:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m ruff check app tests scripts
.\.venv\Scripts\python.exe -m pyright --skipunannotated --pythonpath .\.venv\Scripts\python.exe app
.\.venv\Scripts\python.exe -m pytest -q
~~~

Su Linux, con l’ambiente virtuale attivato:

~~~bash
python -m pip install -r requirements-dev.txt
python -m ruff check app tests scripts
python -m pyright --skipunannotated --pythonpath "$(command -v python)" app
python -m pytest -q
~~~

I test dell’interfaccia richiedono un display. Negli ambienti Linux senza interfaccia grafica, installa `xvfb` e usa `xvfb-run -a python -m pytest -q`, come fa la CI.

Consulta [`CHANGELOG.md`](../../CHANGELOG.md) per la cronologia del progetto. Alcune schermate possono essere meno aggiornate del codice. Segnala bug, proponi funzionalità tramite [Issues](https://github.com/GuilleBouix/Yagua-Image-Processor/issues) o invia pull request mirate con verifiche pertinenti. Quando cambia un comportamento documentato, aggiorna tutte e nove le lingue del README.

## Sostenere il progetto

Se Yagua ti è utile, una stella su GitHub aiuta altre persone a trovarlo. Puoi contribuire anche con segnalazioni, traduzioni o modifiche al progetto.

**[Sostieni su GitHub Sponsors](https://github.com/sponsors/GuilleBouix) · [Sostieni con PayPal](https://www.paypal.com/paypalme/guillebouix)**

<p align="center">
  <a href="https://www.paypal.com/paypalme/guillebouix"><img src="https://github.com/user-attachments/assets/2f3f6a1b-990c-4fb8-9fda-7482c1ca20a5" width="220" alt="Sostieni Yagua con PayPal" /></a>
</p>

## Licenza

Yagua è distribuito con **[licenza MIT](../../LICENSE)**. Le librerie e i modelli di terze parti mantengono le rispettive licenze.
