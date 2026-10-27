<div align="center">

[English](../../README.md) · [Español](README_es.md) · [Português](README_pt.md) · **Français** · [Deutsch](README_de.md) · [Italiano](README_it.md) · [日本語](README_ja.md) · [简体中文](README_zh_cn.md) · [Русский](README_ru.md)

<img src="https://github.com/user-attachments/assets/fc1dacf8-5249-43da-a294-4b20dc423304" width="1000" alt="Bannière Yagua — Traitement d’images" />

# Yagua · Image Processor

### Vos images. Votre ordinateur. Votre façon de travailler.

Des outils de bureau gratuits et open source pour convertir, compresser et traiter des images par lots.

**Site officiel (pages en anglais)**

[Accueil](https://yagua.bouixdev.workers.dev/en/) · [Téléchargements](https://yagua.bouixdev.workers.dev/en/downloads/) · [Documentation](https://yagua.bouixdev.workers.dev/en/docs/) · [Questions fréquentes](https://yagua.bouixdev.workers.dev/en/faq/)

<p align="center">
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/releases/latest"><img src="https://img.shields.io/github/v/release/GuilleBouix/Yagua-Image-Processor?style=flat-square&amp;label=stable&amp;color=2563eb" alt="Dernière version stable" /></a>
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/releases"><img src="https://img.shields.io/github/downloads/GuilleBouix/Yagua-Image-Processor/total?style=flat-square&amp;label=downloads&amp;color=22c55e" alt="Téléchargements totaux" /></a>
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/GuilleBouix/Yagua-Image-Processor/ci.yml?branch=main&amp;style=flat-square&amp;label=CI" alt="État de la CI" /></a>
  <a href="#requirements"><img src="https://img.shields.io/badge/Python-3.13-3776ab?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.13" /></a>
  <a href="../../LICENSE"><img src="https://img.shields.io/badge/license-MIT-f4c430?style=flat-square" alt="Licence MIT" /></a>
</p>

</div>

## Sommaire

- [Téléchargements](https://github.com/GuilleBouix/Yagua-Image-Processor/releases)
- [Fonctionnalités](#features)
- [Captures](#screenshots)
- [Installation](#installation)
- [Utilisation](#usage)
- [Prérequis](#requirements)
- [FAQ](#faq)
- [Contribuer](#contributing)

## Pourquoi Yagua ?

Yagua regroupe les tâches courantes de traitement d’images dans une application de bureau destinée aux développeurs web, designers, photographes et à toute personne travaillant avec des collections d’images. Aucun abonnement ni navigateur n’est nécessaire pour traiter vos fichiers.

Le traitement s’effectue sur votre ordinateur. La suppression d’arrière-plan et l’OCR nécessitent un premier téléchargement de modèles, puis peuvent fonctionner hors ligne si les modèles nécessaires sont en cache. Les vérifications de mises à jour contactent GitHub ; les liens de téléchargement, de don et de carte s’ouvrent dans le navigateur.

L’interface du code actuel propose **l’anglais, l’espagnol, le portugais, le français, l’allemand, l’italien, le japonais, le chinois simplifié et le russe**, avec des thèmes sombres et des aperçus lorsqu’ils sont disponibles. Les paquets publiés peuvent inclure moins de langues ; leur disponibilité dépend de la version installée. La langue de l’interface n’ajoute pas de langues de reconnaissance OCR.

<a id="features"></a>

## Fonctionnalités

Le tableau présente les modules de bureau. Leur disponibilité et leurs commandes dépendent de la version installée ; consultez ses notes de publication.

| Module | Ce que vous pouvez faire | Formats et sorties | Limite de sélection |
| --- | --- | --- | --- |
| Convertir | Changer de format et régler la qualité lorsque le format le permet. | Sorties JPEG, PNG, WebP, AVIF, HEIC, ICO, BMP, TIFF et GIF statique. | 100 images |
| Compresser | Réduire la taille du fichier tout en conservant son format d’origine. | JPEG, PNG, WebP, AVIF, HEIC/HEIF et autres formats matriciels compatibles. | 100 images |
| Redimensionner / Recadrer / Canevas | Modifier les dimensions, recadrer ou ajouter de l’espace ; utiliser des tailles prédéfinies. | Images matricielles courantes, dont JPEG, PNG et WebP. | 100 images |
| Supprimer l’arrière-plan | Retirer les arrière-plans localement avec l’IA. | Sortie PNG, WebP ou TIFF avec transparence. | 10 images |
| Palette de couleurs | Extraire des couleurs, copier les valeurs HEX/RGB/HSL et exporter une palette. | Une image compatible → couleurs et palette PNG. | 1 image |
| Filigrane | Appliquer un logo ; régler position, taille, opacité et marge. | Images de base compatibles ; PNG transparent conseillé pour le logo. | 100 images + 1 logo |
| Renommer | Prévisualiser une numérotation, des dates et des changements de casse. | Modifie les noms dans leur dossier d’origine. | 100 fichiers |
| OCR | Extraire du texte en espagnol et/ou anglais avec EasyOCR ; le copier ou l’exporter en TXT. | Images matricielles compatibles → texte. | 10 images |
| Métadonnées EXIF | Consulter, exporter, modifier des champs ou supprimer les métadonnées par lots. | Modification JPEG/TIFF ; export des métadonnées en TXT/JSON. | 1 image à modifier ; 100 à nettoyer |
| LQIP / Base64 | Générer des aperçus de faible qualité ou encoder des images pour le web. | Base64, URI de données, HTML et CSS ; export TXT/JSON. | 1 image |

La compatibilité dépend du module, des codecs installés et de la plateforme. Un format indiqué ne garantit pas que tous les modules puissent le lire ou l’écrire. Consultez les [prérequis](#requirements).

<a id="screenshots"></a>

## Captures d’écran

Captures de Yagua avec l’interface en anglais. Cliquez sur une miniature pour afficher l’image en taille réelle. La disposition et les commandes peuvent varier selon la version.

<table>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/home.webp"><img src="../../assets/screenshots/home.webp" width="450" alt="Écran d’accueil avec tous les modules" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/convert.webp"><img src="../../assets/screenshots/convert.webp" width="450" alt="Conversion avec images sélectionnées et réglages du format de sortie" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/compress.webp"><img src="../../assets/screenshots/compress.webp" width="450" alt="Compression avec réglages de qualité et EXIF" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/resize.webp"><img src="../../assets/screenshots/resize.webp" width="450" alt="Redimensionnement avec dimensions en pixels et réglages des proportions" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/remove-background.webp"><img src="../../assets/screenshots/remove-background.webp" width="450" alt="Suppression d’arrière-plan avec une image sélectionnée" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/palette.webp"><img src="../../assets/screenshots/palette.webp" width="450" alt="Palette extraite avec dix couleurs et leurs valeurs" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/watermark.webp"><img src="../../assets/screenshots/watermark.webp" width="450" alt="Réglages du filigrane et aperçu du résultat" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/rename.webp"><img src="../../assets/screenshots/rename.webp" width="450" alt="Renommage par lots avec noms d’origine et proposés" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/ocr.webp"><img src="../../assets/screenshots/ocr.webp" width="450" alt="OCR en espagnol avec le texte reconnu" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/metadata.webp"><img src="../../assets/screenshots/metadata.webp" width="450" alt="Visionneuse EXIF avec sélection d’image, aperçu et champs de métadonnées" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/lqip-base64.webp"><img src="../../assets/screenshots/lqip-base64.webp" width="450" alt="Comparaison LQIP avec l’image d’origine et code HTML généré" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/settings.webp"><img src="../../assets/screenshots/settings.webp" width="450" alt="Paramètres généraux de langue, thème, échelle et modules visibles" /></a></td>
  </tr>
</table>

## Installation

### Choisir une version

Ouvrez **[GitHub Releases](https://github.com/GuilleBouix/Yagua-Image-Processor/releases)** et choisissez votre système. Le badge **stable** renvoie à la dernière version stable de GitHub ; les versions plus récentes marquées **Pre-release**, y compris les versions `rc`, sont des versions de test. Windows et Linux peuvent avoir des versions différentes.

La version du code est définie dans [`app/version.py`](../../app/version.py). Cela ne signifie pas qu’un installateur correspondant a été publié. Lisez les notes de chaque publication et téléchargez les fichiers qui lui sont joints.

| Plateforme | Paquet | Étapes |
| --- | --- | --- |
| Windows | `Yagua_Setup_<version>.exe` | Exécutez l’installateur, puis ouvrez Yagua depuis le menu Démarrer ou le raccourci du bureau. |
| Windows portable | `Yagua_Portable_<version>.zip`, si disponible | Extrayez le ZIP entier dans un dossier accessible en écriture et lancez `Yagua.exe`. Conservez les fichiers associés ensemble. |
| Linux x86_64 | `Yagua-<version>-x86_64.AppImage`, si disponible | Rendez le fichier téléchargé exécutable, puis lancez-le comme indiqué ci-dessous. |
| macOS | Prise en charge expérimentale depuis le code/la compilation | Aucun paquet stable pour macOS n’est promis. Consultez le [script de compilation](../../scripts/build_macos_app.sh) existant. |

Sous Linux, remplacez le nom d’exemple par celui du fichier téléchargé :

~~~bash
chmod +x "Yagua-<version>-x86_64.AppImage"
./"Yagua-<version>-x86_64.AppImage"
~~~

### Exécuter depuis le code source

Utilisez **Python 3.13**, la version utilisée par la CI du projet, et Git. Les dépendances peuvent être volumineuses car elles incluent les bibliothèques d’OCR et d’IA. Linux nécessite aussi Tk et les bibliothèques système indiquées dans les [prérequis](#requirements).

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

Ces commandes utilisent les versions de dépendances fixées par le dépôt. Les vérifications de CI Windows/Linux ne confirment pas la compatibilité avec d’autres versions de Python ni avec macOS.

<a id="usage"></a>

## Utilisation

1. Ouvrez Yagua et choisissez un module dans la barre latérale.
2. Chargez vos images et configurez les options disponibles.
3. Vérifiez l’aperçu lorsque le module en propose un.
4. Traitez les images et choisissez un dossier de sortie lorsque cela est demandé ; vérifiez le message final pour repérer les erreurs.

**LQIP / Base64 :** Sélectionnez une image, choisissez le mode et les paramètres, générez, comparez puis copiez ou exportez Data URI, HTML, CSS ou Base64 brut. Charger une autre image réinitialise le mode LQIP, largeur 20 px, flou 2 et qualités 40/85 ; annuler le sélecteur conserve l’état actuel. Les deux modes produisent du JPEG sans transparence.

**Fichiers originaux :** Renommer modifie les noms à leur emplacement actuel. La modification EXIF écrase l’image sélectionnée après confirmation. Travaillez sur des copies pour ces opérations. Le nettoyage EXIF par lots écrit dans le dossier choisi. Les autres exports suivent le processus d’enregistrement ou de dossier de sortie de chaque module.

### Exemples pratiques

- **Préparer des images pour le web :** Convertissez jusqu’à 100 photos en WebP, choisissez la qualité, puis ajustez les dimensions si nécessaire. Générez les aperçus LQIP séparément pour l’affichage pendant le chargement de votre site.
- **Préparer des photos de produits :** Chargez jusqu’à 10 images dans Supprimer l’arrière-plan et exportez en PNG ou WebP pour conserver la transparence. Ajoutez si nécessaire un logo PNG transparent avec Filigrane.
- **Extraire du texte :** Chargez jusqu’à 10 images nettes dans OCR, choisissez l’espagnol, l’anglais ou les deux, puis copiez le résultat ou exportez un TXT. La langue de l’interface n’ajoute pas de langues de reconnaissance OCR. Relisez le texte pour corriger les erreurs de reconnaissance.

<a id="requirements"></a>

## Prérequis et limites

### Matériel

Pour l’application complète, y compris **l’OCR et la suppression d’arrière-plan** :

| Composant | Minimum provisoire | Recommandé |
| --- | --- | --- |
| Processeur | Intel/AMD x86-64 relativement récent, **4 cœurs** | CPU moderne de **6 à 8 cœurs** |
| RAM de l’ordinateur | **8 Go**, avec peu d’autres applications ouvertes | **16 Go** ; **32 Go** pour les très grandes images et le multitâche |
| Stockage | **4 Go libres**, en plus de l’espace pour les originaux et les résultats | **SSD avec 10 Go libres ou plus**, en plus de vos images |
| Graphismes | Circuit graphique intégré suffisant ; GPU dédié non obligatoire | Circuit graphique intégré suffisant |
| Internet | Pour télécharger les modèles au premier usage et rechercher les mises à jour | Utilisation hors ligne une fois les modèles nécessaires téléchargés |

**Ce sont des estimations pratiques pour l’application complète, pas des minima matériels validés. Les essais sur un PC d’entrée de gamme restent à faire.** Un ordinateur avec 4 Go de RAM n’est pas recommandé pour l’usage complet de l’OCR et de la suppression d’arrière-plan. La consommation dépend de la résolution, de la taille du lot et des modèles ; réduisez les lots lorsque les ressources sont limitées.

Le paquet testé effectue le traitement sur le **CPU** ; aucune NVIDIA ni autre carte graphique dédiée n’est nécessaire. Privilégiez processeur, RAM et SSD. La suppression d’arrière-plan utilise le fournisseur d’exécution CPU d’ONNX Runtime ; consultez la [documentation officielle d’ONNX Runtime](https://onnxruntime.ai/docs/api/python/api_summary.html).

### Systèmes d’exploitation

| Système | Base et validation |
| --- | --- |
| Windows | **Windows 10/11, 64 bits** ; Windows 11 de préférence. ONNX Runtime indique Windows 10 comme version minimale de Windows. La validation de l’installateur et du paquet portable finaux sur des PC Windows 10/11 propres reste à faire. |
| Linux | **Ubuntu 22.04 x86-64**, la base vérifiée en CI. Les autres distributions, versions et environnements de bureau nécessitent une validation de l’AppImage final. |
| macOS | Prise en charge expérimentale ; aucun paquet natif validé n’est annoncé. |

Les paquets Windows et Linux actuels ciblent **x86-64** ; aucune version ARM native n’est validée. La CI utilise Windows Server et Ubuntu 22.04/Xvfb ; ces vérifications ne certifient pas tous les systèmes de bureau. Consultez les [prérequis de plateforme d’ONNX Runtime](https://onnxruntime.ai/docs/build/inferencing.html).

<details>
<summary>Consommation mesurée et premier chargement du modèle</summary>

L’audit des paquets rapporte ces observations approximatives pour des compilations de CI testées le 15 octobre 2026 :

| Mesure | Windows | Linux |
| --- | --- | --- |
| Pic de RAM du processus observé avec plusieurs modèles chargés | **3,0 Go** | **2,6 Go** |
| App + tous les modèles et caches mesurés lors de cet essai | **1,10 Go** | **1,53 Go** |
| Premier chargement du modèle de suppression d’arrière-plan (ISNet) | **53 secondes** | **39 secondes** |

**Ce sont des observations, pas des maxima ni des durées garanties.** L’essai de RAM conservait plusieurs modèles chargés ; de grandes photographies peuvent consommer davantage de mémoire. Les chiffres disque couvrent le paquet, les modèles et les caches mesurés, pas les originaux, résultats, fichiers temporaires d’extraction ou un environnement de développement depuis le code. Les temps de chargement dépendent de la machine ; la session est ensuite réutilisée. Ce ne sont ni des temps de téléchargement du modèle ni des temps de traitement par image.

</details>

### Exécution et traitement

- **Code source :** Python 3.13, Tk et les bibliothèques de [`requirements.txt`](../../requirements.txt). Les paquets compilés ne nécessitent pas d’installation séparée de Python.
- **Lots :** Le tableau des fonctionnalités indique les limites actuelles de l’interface : une image pour Palette, LQIP / Base64 ou modification EXIF, 10 pour OCR/suppression d’arrière-plan et 100 pour les autres opérations par lots indiquées.
- **Codecs :** HEIC/HEIF utilise `pillow-heif`, inclus dans les dépendances du code. AVIF et d’autres formats dépendent des codecs Pillow et de la plateforme. JPEG ne gère pas la transparence ; utilisez PNG ou WebP si nécessaire. La compression PNG peut réduire l’image à 256 couleurs : vérifiez le résultat.
- **Modèles d’IA :** Des téléchargements peuvent avoir lieu au premier usage ou lorsqu’un nouveau modèle/une nouvelle langue nécessite un autre modèle. L’usage hors ligne exige des modèles en cache. Le paquet testé exécute l’OCR et la suppression d’arrière-plan sur CPU.

### Bibliothèques système sous Linux

AppImage nécessite **FUSE 2** pour son exécution par montage (`libfuse2` sur les distributions compatibles). Si FUSE n’est pas disponible, l’extraction est une alternative ; consultez les [instructions officielles d’AppImage](https://docs.appimage.org/user-guide/troubleshooting/fuse.html). Remplacez le nom d’exemple par celui du fichier téléchargé :

~~~bash
./"Yagua-<version>-x86_64.AppImage" --appimage-extract-and-run
~~~

L’extraction nécessite de l’espace temporaire supplémentaire et peut ralentir le démarrage. Pour l’exécution depuis le code, la CI installe Tk et ces bibliothèques sur Ubuntu 22.04 :

~~~bash
sudo apt-get install python3-tk libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgtk-3-0 libgomp1
~~~

Les noms des paquets varient selon la distribution. Vérifiez que Tk est disponible pour votre interpréteur Python 3.13 ; le paquet Tk par défaut de la distribution peut ne pas couvrir un Python installé séparément.

<a id="faq"></a>

## Questions fréquentes

### Yagua envoie-t-il mes images ?

Le traitement est local ; les modules n’envoient pas les images à un service de traitement. Les téléchargements de modèles et les vérifications de mises à jour GitHub nécessitent une connexion. Les liens externes ouvrent le navigateur ; le lien de carte EXIF envoie les coordonnées GPS sélectionnées à Google Maps lorsque vous l’ouvrez.

### Pourquoi la première opération d’IA est-elle plus lente ?

OCR et la suppression d’arrière-plan initialisent leurs moteurs et peuvent télécharger des modèles. Attendez la fin de cette étape. Les exécutions suivantes peuvent réutiliser les modèles en cache ; les grandes images et les gros lots demandent toujours davantage de ressources.

### Pourquoi un format est-il indisponible ou une image refusée ?

Les entrées acceptées dépendent du module et des codecs disponibles. Essayez une copie PNG ou JPEG et vérifiez `yagua.log`. Exportez en PNG ou WebP pour conserver la transparence.

### Pourquoi la compression ne réduit-elle pas toutes les images ?

Une image déjà optimisée peut ne pas devenir plus petite. Lorsque la suppression EXIF est désactivée, Yagua copie l’original vers la sortie si la compression produit un fichier aussi volumineux ou plus volumineux. Lorsque la suppression EXIF est activée, il enregistre l’image traitée même si elle est plus grande, pour que ce retour à l’original ne restaure pas ses EXIF. Pour un traitement dédié au nettoyage EXIF, utilisez le module de métadonnées.

### Comment fonctionnent les mises à jour ?

Yagua peut vous avertir au démarrage et permet une vérification dans **Paramètres → Mises à jour**. Il ouvre un lien de téléchargement ; il n’installe pas les mises à jour automatiquement. Les paquets RC.4/RC.5 recherchent uniquement les versions stables plus récentes avec le préfixe de votre plateforme (`win-v` ou `linux-v`) ; ils excluent les préversions et les brouillons et ne détectent donc pas les nouvelles RC. Téléchargez les versions de test manuellement depuis [GitHub Releases](https://github.com/GuilleBouix/Yagua-Image-Processor/releases). Ces paquets peuvent aussi indiquer « Aucune mise à jour disponible » après une erreur de connexion ; en cas de doute, consultez Releases directement, y compris les anciennes publications sans préfixe de plateforme.

### Comment signaler un problème ?

Ouvrez un [rapport de bug](https://github.com/GuilleBouix/Yagua-Image-Processor/issues/new?template=bug_report.md) avec votre version de Yagua, système, module, étapes de reproduction et journaux pertinents. Cherchez `yagua.log` dans :

- Windows: `%APPDATA%\Yagua\yagua.log`
- Linux: `~/.config/Yagua/yagua.log`
- macOS: `~/Library/Application Support/Yagua/yagua.log`

Les journaux peuvent contenir des chemins et noms de fichiers ; relisez-les avant de les partager.

<a id="contributing"></a>

## Développement et contribution

Yagua utilise **CustomTkinter** pour l’interface, **Pillow / pillow-heif** pour les images, **rembg / ONNX Runtime** pour les arrière-plans, **EasyOCR / PyTorch** pour l’OCR et **piexif** pour EXIF. Les versions exactes figurent dans [`requirements.txt`](../../requirements.txt).

Après l’installation depuis le code, installez les outils de développement et lancez les vérifications de CI. Sous Windows, utilisez directement les exécutables de l’environnement virtuel :

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m ruff check app tests scripts
.\.venv\Scripts\python.exe -m pyright --skipunannotated --pythonpath .\.venv\Scripts\python.exe app
.\.venv\Scripts\python.exe -m pytest -q
~~~

Sous Linux, avec l’environnement virtuel activé :

~~~bash
python -m pip install -r requirements-dev.txt
python -m ruff check app tests scripts
python -m pyright --skipunannotated --pythonpath "$(command -v python)" app
python -m pytest -q
~~~

Les tests d’interface nécessitent un affichage. Sous Linux sans interface graphique, installez `xvfb` et utilisez `xvfb-run -a python -m pytest -q`, comme le fait la CI.

Consultez [`CHANGELOG.md`](../../CHANGELOG.md) pour l’historique. Certaines captures peuvent être en retard sur le code. Signalez des bugs, proposez des fonctionnalités dans [Issues](https://github.com/GuilleBouix/Yagua-Image-Processor/issues) ou soumettez des PR ciblées avec une validation pertinente. Lorsqu’un comportement documenté change, mettez à jour les neuf langues du README.

## Soutenir le projet

Si Yagua vous est utile, une étoile GitHub aide d’autres personnes à le découvrir. Vous pouvez aussi contribuer avec des signalements, des traductions ou des améliorations.

**[Vous avez essayé Yagua ? Donnez votre avis (en anglais)](https://yagua.bouixdev.workers.dev/en/project/#project-rating)**

**[Soutenir sur GitHub Sponsors](https://github.com/sponsors/GuilleBouix) · [Soutenir via PayPal](https://www.paypal.com/paypalme/guillebouix)**

<p align="center">
  <a href="https://www.paypal.com/paypalme/guillebouix"><img src="https://github.com/user-attachments/assets/2f3f6a1b-990c-4fb8-9fda-7482c1ca20a5" width="220" alt="Soutenir Yagua via PayPal" /></a>
</p>

## Licence

Yagua est distribué sous **[licence MIT](../../LICENSE)**. Les bibliothèques et modèles tiers conservent leurs licences respectives.
