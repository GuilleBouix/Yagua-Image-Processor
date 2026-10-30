<div align="center">

[English](../../README.md) · [Español](README_es.md) · [Português](README_pt.md) · [Français](README_fr.md) · [Deutsch](README_de.md) · [Italiano](README_it.md) · **日本語** · [简体中文](README_zh_cn.md) · [Русский](README_ru.md)

<img src="https://github.com/user-attachments/assets/fc1dacf8-5249-43da-a294-4b20dc423304" width="1000" alt="Yagua — 画像処理アプリのバナー" />

# Yagua · Image Processor

### あなたの画像。あなたのパソコン。あなたの作業スタイル。

画像の形式変換、圧縮、一括処理に使える、無料のオープンソースデスクトップアプリです。

**公式サイト（ページは英語）**

[ホーム](https://yagua.bouixdev.workers.dev/en/) · [ダウンロード](https://yagua.bouixdev.workers.dev/en/downloads/) · [ドキュメント](https://yagua.bouixdev.workers.dev/en/docs/) · [よくある質問](https://yagua.bouixdev.workers.dev/en/faq/)

<p align="center">
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/releases/latest"><img src="https://img.shields.io/github/v/release/GuilleBouix/Yagua-Image-Processor?style=flat-square&amp;label=stable&amp;color=2563eb" alt="最新の安定版" /></a>
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/releases"><img src="https://img.shields.io/github/downloads/GuilleBouix/Yagua-Image-Processor/total?style=flat-square&amp;label=downloads&amp;color=22c55e" alt="累計ダウンロード数" /></a>
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/GuilleBouix/Yagua-Image-Processor/ci.yml?branch=main&amp;style=flat-square&amp;label=CI" alt="CI の状態" /></a>
  <a href="#requirements"><img src="https://img.shields.io/badge/Python-3.13-3776ab?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.13" /></a>
  <a href="../../LICENSE"><img src="https://img.shields.io/badge/license-MIT-f4c430?style=flat-square" alt="MIT ライセンス" /></a>
</p>

</div>

## 目次

- [ダウンロード](https://github.com/GuilleBouix/Yagua-Image-Processor/releases)
- [機能](#features)
- [スクリーンショット](#screenshots)
- [インストール](#installation)
- [使い方](#usage)
- [動作要件](#requirements)
- [よくある質問](#faq)
- [開発への参加](#contributing)

## Yagua を使う理由

Yagua は、Web 開発者、デザイナー、写真家など、画像を扱う方のために、日常的な画像処理をひとつのデスクトップアプリにまとめています。ファイルの処理にサブスクリプションやブラウザーは必要ありません。

画像処理はお使いのパソコン上で行われます。背景除去と OCR は初回にモデルのダウンロードが必要ですが、必要なモデルがキャッシュされていれば、その後はオフラインでも動作します。更新の確認では GitHub に接続し、ダウンロード、寄付、地図のリンクはブラウザーで開きます。

現在のソースコードのインターフェースは、**英語、スペイン語、ポルトガル語、フランス語、ドイツ語、イタリア語、日本語、簡体字中国語、ロシア語**に対応し、ダークテーマや各機能に応じたプレビューを備えています。配布パッケージに含まれる言語は少ない場合があり、利用できる言語はインストールしたバージョンによって異なります。表示言語を変えても OCR の認識言語は増えません。

<a id="features"></a>

## 機能

以下はデスクトップアプリの各モジュールです。利用できる機能や操作項目はインストールしたバージョンによって異なるため、リリースノートを確認してください。

| モジュール | できること | 形式と出力 | 選択上限 |
| --- | --- | --- | --- |
| 形式変換 | 形式を変更し、対応する形式では品質を調整します。 | JPEG、PNG、WebP、AVIF、HEIC、ICO、BMP、TIFF、静止 GIF を出力。 | 100 枚 |
| 圧縮 | 元の形式を維持しながらファイルサイズを減らします。 | JPEG、PNG、WebP、AVIF、HEIC/HEIF など、対応するラスター形式。 | 100 枚 |
| サイズ変更 / 切り抜き / キャンバス | 割合・ピクセル・プリセットでサイズ変更。比率や正確な寸法で切り抜き、キャンバスの色や透明を選択。 | 対応するラスター画像。透明キャンバスは必要に応じて PNG に変換。 | 100画像 |
| 背景除去 | ローカル AI で背景を除去し、輪郭の調整、白い縁、マスクの大きさを設定。 | 透明な PNG、WebP、TIFF を出力。 | 10画像 |
| カラーパレット | 一括読み込みした画像のパレットを個別に確認し、HEX/RGB/HSL/CSS をコピー。1件または全件保存。 | 対応する静止画像 → 画像ごとに PNG パレット。 | 100画像 |
| 透かし | 画像ロゴを追加し、位置、サイズ、不透明度、余白を調整します。 | 対応する元画像。ロゴには透過 PNG を推奨。 | 100 枚 + ロゴ 1 枚 |
| ファイル名変更 | 連番、日付、大文字・小文字の変更結果をプレビューします。 | ファイルがあるフォルダー内で名前を変更。 | 100 ファイル |
| OCR | EasyOCR でスペイン語および／または英語の文字を抽出し、コピーまたは TXT に出力します。 | 対応するラスター画像 → テキスト。 | 10 枚 |
| EXIF メタデータ | 内容の確認、書き出し、項目の編集、メタデータの一括削除。 | JPEG/TIFF の編集、TXT/JSON へのメタデータ出力。 | 編集は 1 枚、削除は 100 枚 |
| LQIP / Base64 | 低画質のプレースホルダーを生成し、Web 用に画像をエンコードします。 | Base64、data URI、HTML、CSS。TXT/JSON 出力。 | 1 枚 |

対応形式はモジュール、インストール済みのコーデック、プラットフォームによって異なります。ここに記載された形式でも、すべてのモジュールで読み書きできるとは限りません。[動作要件](#requirements)を確認してください。

<a id="screenshots"></a>

## スクリーンショット

英語インターフェースの Yagua のスクリーンショットです。サムネイルをクリックすると原寸の画像を開けます。レイアウトや操作項目はバージョンによって異なる場合があります。

<table>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/home.webp"><img src="../../assets/screenshots/home.webp" width="450" alt="すべてのモジュールを表示したホーム画面" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/convert.webp"><img src="../../assets/screenshots/convert.webp" width="450" alt="選択した画像と出力形式の設定がある形式変換画面" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/compress.webp"><img src="../../assets/screenshots/compress.webp" width="450" alt="品質と保存方法の設定がある圧縮画面" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/resize.webp"><img src="../../assets/screenshots/resize.webp" width="450" alt="YouTube チャンネルアート用のプリセットを選択したサイズ変更画面" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/remove-background.webp"><img src="../../assets/screenshots/remove-background.webp" width="450" alt="画像を選択した背景除去画面" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/palette.webp"><img src="../../assets/screenshots/palette.webp" width="450" alt="抽出した8色と色の値を表示したパレット" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/watermark.webp"><img src="../../assets/screenshots/watermark.webp" width="450" alt="透かしの設定と結果プレビュー" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/rename.webp"><img src="../../assets/screenshots/rename.webp" width="450" alt="元のファイル名と変更候補を表示する一括ファイル名変更" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/ocr.webp"><img src="../../assets/screenshots/ocr.webp" width="450" alt="英語 OCR の認識結果" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/metadata.webp"><img src="../../assets/screenshots/metadata.webp" width="450" alt="画像選択、プレビュー、メタデータ項目がある EXIF 閲覧画面" /></a></td>
  </tr>
  <tr>
    <td align="center" width="50%"><a href="../../assets/screenshots/lqip-base64.webp"><img src="../../assets/screenshots/lqip-base64.webp" width="450" alt="元画像との LQIP 比較と生成されたデータ URI" /></a></td>
    <td align="center" width="50%"><a href="../../assets/screenshots/settings.webp"><img src="../../assets/screenshots/settings.webp" width="450" alt="言語、テーマ、表示倍率、表示モジュールの一般設定" /></a></td>
  </tr>
</table>

<a id="installation"></a>

## インストール

### リリースを選ぶ

**[GitHub Releases](https://github.com/GuilleBouix/Yagua-Image-Processor/releases)** を開き、お使いの OS を選んでください。**stable** バッジは GitHub 上の最新の安定版にリンクしています。`rc` ビルドなど、**Pre-release** と表示された新しいビルドはテスト版です。Windows 版と Linux 版ではバージョンが異なる場合があります。

ソースコードのバージョンは [`app/version.py`](../../app/version.py) に定義されています。同じバージョンのインストーラーが公開されているとは限りません。各リリースの説明を読み、そのリリースに添付されたファイルをダウンロードしてください。

| プラットフォーム | パッケージ | 手順 |
| --- | --- | --- |
| Windows | `Yagua_Setup_<version>.exe` | インストーラーを実行し、スタートメニューまたはデスクトップのショートカットから Yagua を起動します。 |
| Windows ポータブル版 | `Yagua_Portable_<version>.zip`（提供されている場合） | ZIP 全体を書き込み可能なフォルダーに展開し、中の `Yagua.exe` を起動します。同梱ファイルは一緒に保管してください。 |
| Linux x86_64 | `Yagua-<version>-x86_64.AppImage`（提供されている場合） | ダウンロードしたファイルに実行権限を付与し、以下のように起動します。 |
| macOS | ソースからの実行／ビルドは実験的対応 | 安定した macOS パッケージの提供は保証されません。既存の[ビルドスクリプト](../../scripts/build_macos_app.sh)を参照してください。 |

Linux では、以下の例のファイル名をダウンロードしたものに置き換えてください。

~~~bash
chmod +x "Yagua-<version>-x86_64.AppImage"
./"Yagua-<version>-x86_64.AppImage"
~~~

### ソースコードから実行する

プロジェクトの CI で使用している **Python 3.13** と Git を使用してください。OCR と AI のライブラリを含むため、依存関係のインストールは容量が大きくなる場合があります。Linux では Tk と、[動作要件](#requirements)に記載されたシステムライブラリも必要です。

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

これらのコマンドは、リポジトリでバージョンを固定している依存関係を使用します。Windows/Linux の CI の検証から、他の Python バージョンや macOS との互換性が確認されているわけではありません。

<a id="usage"></a>

## 使い方

1. Yagua を起動し、サイドバーからモジュールを選びます。
2. 画像を読み込み、利用できる処理オプションを設定します。
3. プレビューに対応するモジュールでは、その内容を確認します。
4. 画像を処理し、求められた場合は出力フォルダーを選びます。完了メッセージにエラーがないか確認してください。

**LQIP / Base64：** 画像を 1 枚選び、モードとパラメーターを設定して生成・比較し、data URI、HTML、CSS、または Base64 文字列をコピーまたは書き出します。別の画像を読み込むと、LQIP モード、幅 20 px、ぼかし 2、品質 40/85 に戻ります。ファイル選択をキャンセルした場合は現在の状態を維持します。どちらのモードも透過なしの JPEG を出力します。

**元ファイルについて：** ファイル名変更は元の場所で名前を変更します。EXIF の編集は確認後に選択画像を上書きします。これらの操作はコピーで行ってください。EXIF の一括削除では、指定した出力フォルダーに保存します。その他の書き出しは、各モジュールの保存操作や出力フォルダー選択の流れに従います。

### 具体的な使い方

- **Web 用画像の準備：** 最大 100 枚の写真を WebP に変換し、品質を設定して、必要に応じてサイズを変更します。サイトの読み込み時に表示する LQIP プレースホルダーは別途生成します。
- **商品写真の準備：** 背景除去に最大 10 枚を読み込み、透過を保持するため PNG または WebP に書き出します。必要に応じて、透かし機能で透過 PNG のロゴを追加します。
- **文字の抽出：** OCR に鮮明な画像を最大 10 枚読み込み、スペイン語、英語、または両方を選び、結果をコピーするか TXT ファイルに書き出します。表示言語を変えても OCR の認識言語は増えません。認識結果に誤りがないか確認してください。

### 処理オプションとプレビュー

以下は現在開発中のソースコードの操作です。以前に公開されたパッケージには、一部の機能が含まれない場合があります。

#### サイズ変更・切り抜き・キャンバス

三つのタブは最大 **100画像**の処理対象を共有します。ファイルの行をクリックすると、その画像を確認できますが、一括処理の対象は減りません。プレビューは選択中のタブに従い、EXIF の向きを反映した元画像と出力の寸法を表示します。縮小したピクセルで構図を確認するためのもので、最終結果の等倍（1:1）の細部は表しません。設定の変更だけでは保存されません。

- **サイズ変更:** **パーセント** は **1–200%**、初期値は **50%** です。**ピクセル** は幅、高さ、または両方を指定でき、片方だけなら他方を比例計算します。両方を指定して **縦横比を維持** を有効にすると（初期設定）、拡大せずに指定範囲内へ収めます。無効にすると正確な指定寸法になり、画像が変形する場合があります。**プリセット** は SNS、Web、解像度、アイコン用の固定サイズで、縦横比が変わる場合もあります。最初のプリセットは Instagram 1080 × 1080 です。
- **切り抜き:** **縦横比** は **1:1**（初期設定）、**4:3、3:4、16:9、9:16、3:2、2:3、21:9** から選択します。**サイズ** は正の整数の幅と高さを、連動するスライダーと入力欄で指定します。別の画像を選ぶと、向きを反映した元の寸法が入力欄に入り、スライダーの上限も切り替わります。中央から切り抜き、拡大、余白追加、切り抜き領域のドラッグ移動は行いません。指定寸法は処理対象全体に適用されます。小さすぎる画像はスキップして元画像を保持し、残りを処理します。例えば 1000 × 700 を 800 × 600 にすると、左右から各100 px、上下から各50 px を除きます。
- **キャンバス:** 初期寸法は **1080 × 1080 px** です。スライダーは初期状態で **1–8192 px** を扱い、さらに大きい正の整数を手入力すると範囲が広がります。処理できる大きさは使用可能なメモリに依存します。画像は中央に配置し、必要なら比例縮小しますが拡大しません。**色** の初期値は **#FFFFFF** で、HEX ボタンから背景色を選びます。選択をキャンセルしたり **透明** に切り替えたりしても、最後の色は保持されます。

透明キャンバスでは、PNG、WebP、TIFF、AVIF、HEIF は対応するエンコーダーがあれば元の形式を保持し、それ以外は PNG になります。そのため JPEG、BMP、GIF、ICO は PNG に変換されます。確認画面には変換件数が表示され、**元の画像を上書き** でも変換元は保持されます。半透明のピクセルは色付きキャンバスでは背景と合成し、透明キャンバスではアルファを保持します。プレビューの市松模様は保存されません。[詳しいガイド（英語）](../RESIZE_PREVIEWS_AND_BACKGROUND.md)。

#### カラーパレット

**画像を追加** で最大 **100件の重複しない画像**をコレクションに追加でき、重複や除外の件数を表示します。最初の画像は自動で開き、別の行を選ぶと表示中のパレットだけが変わります。**4、6、8、10、12色**（初期値 **6**）を選択します。元の色数が少なければ、結果も指定数より少なくなります。**HEX、RGB、HSL、CSS var** は各形式の色の値をコピーします。完全に透明なピクセルは無視し、半透明のピクセルは背景と合成せず RGB を使用します。完全に透明、読み取り不能、または未対応のアニメーション・複数ページ画像にはエラーを表示します。

**パレットを保存** は開いているパレットを PNG で保存します。**すべて保存** は選択した色数でコレクション全体を処理し、進捗とファイルごとのエラーを表示しながら画像ごとに PNG を出力します。例えば `beach.jpg` は `beach_paleta.png` になり、一括保存時の名前の重複には `beach_paleta_1.png` などの番号が付きます。一括保存では既存ファイルと入力画像を保持し、個別保存でもコレクション内の全入力画像を保護します。ダイアログをキャンセルすると書き込みません。**クリア** はコレクションと結果を空にしますが、保存済みのファイルは削除しません。[一括処理ガイド（スペイン語・英語）](../PALETTE_BATCH.md)。

#### 背景除去

最大 **10画像**を読み込み、透明を扱える **PNG**（初期設定）、**WEBP**、**TIFF** から出力を選択します。行を選ぶと処理前には元画像、処理後には保存済みの結果を表示します。次の三項目は常に表示されます。

- **輪郭を調整: 自動 / はい / いいえ**。初期値は **自動** です。Auto はマスクを整え、均一で明るいと判定した背景で半透明の輪郭を調整します。有効にすると背景によらず両方を要求し、無効にすると両方を停止します。
- **白い縁を軽減: 0–100%**。初期値は **85%** です。背景が均一で明るいと判定された場合に限り、輪郭に残る明るい背景色を減らします。輪郭調整の選択とは独立して機能します。
- **縮小 / 拡張: −5 ～ +5 px**。初期値は **0 px** です。元画像のピクセル単位で、負の値はマスクを縮め、正の値は広げます。縮小で細部が失われたり、拡張で背景が現れたりする場合があります。

設定を変えても、プレビューには最後に保存した結果が残ります。適用するには再処理してください。失敗したファイルには元画像とエラーを表示します。これらの設定は別のモデルを選択せず、追加モデルも必要としませんが、初回の通常のモデルダウンロードは必要です。輪郭調整は CPU、RAM、処理時間を増やす場合があり、失われた細部の復元は保証しません。[詳しいガイド（英語）](../RESIZE_PREVIEWS_AND_BACKGROUND.md)。

#### 保存方法

サイズ変更・切り抜き・キャンバス・背景除去では、初期設定の **コピーを作成** は出力フォルダーを指定します。**元の画像を上書き** は出力形式が同じ場合だけ元ファイルを置き換えます。形式が変わる場合は元画像の横に別ファイルを作成し、元画像を保持します。処理前に確認画面を確認してください。新規ファイルの名前の重複には番号が付き、切り抜きのスキップ件数はエラーとは別に表示されます。パレットは上記の専用 PNG 保存ダイアログを使用します。

<a id="requirements"></a>

## 動作要件と制限

### ハードウェア

**OCR と背景除去を含む全機能**を使う場合：

| 項目 | 暫定的な最小構成 | 推奨構成 |
| --- | --- | --- |
| プロセッサー | 比較的新しい Intel/AMD x86-64 CPU、**4 コア** | 最近の CPU、**6–8 コア** |
| システムメモリ | **8 GB**、他のアプリの起動を控える | **16 GB**。非常に大きな画像や並行作業には **32 GB** |
| ストレージ | **4 GB の空き容量**に加え、元画像と出力用の容量 | **10 GB 以上の空き容量がある SSD**。画像用の容量は別途必要 |
| グラフィックス | 内蔵グラフィックスで十分。専用 GPU は不要 | 内蔵グラフィックスで十分 |
| インターネット | 初回のモデルダウンロードと更新確認に必要 | 必要なモデルをダウンロード済みならオフライン利用可能 |

**これは全機能を使うための実用上の目安であり、検証済みの最小要件ではありません。低スペック PC での検証はまだ行っていません。** OCR と背景除去を含む全機能の利用に、メモリ 4 GB のシステムは推奨しません。使用量は画像の解像度、一括処理の枚数、モデルによって変わります。リソースが限られる場合は、一度に処理する枚数を減らしてください。

検証したパッケージは **CPU** で画像を処理するため、NVIDIA などの専用 GPU は必要ありません。CPU、メモリ、SSD を優先してください。背景除去は ONNX Runtime の CPU 実行プロバイダーを使用します。[ONNX Runtime の公式ドキュメント](https://onnxruntime.ai/docs/api/python/api_summary.html)を参照してください。

### 対応 OS

| システム | 基準となる環境と検証状況 |
| --- | --- |
| Windows | **Windows 10/11、64 ビット**。Windows 11 を推奨します。ONNX Runtime は Windows 10 を Windows の最小対応バージョンとしています。クリーンな Windows 10/11 PC での最終インストーラーおよびポータブル版の検証は未実施です。 |
| Linux | CI で検証している基準環境は **Ubuntu 22.04 x86-64** です。他のディストリビューション、バージョン、デスクトップ環境では、最終 AppImage の検証が必要です。 |
| macOS | 実験的な対応です。検証済みのネイティブパッケージはありません。 |

現在の Windows/Linux パッケージは **x86-64** 向けです。検証済みの ARM ネイティブ版はありません。CI では Windows Server と Ubuntu 22.04/Xvfb を使用していますが、これらの確認はすべてのデスクトップ環境での動作を保証するものではありません。[ONNX Runtime のプラットフォーム要件](https://onnxruntime.ai/docs/build/inferencing.html)を参照してください。

<details>
<summary>リソース使用量とモデル初回読み込みの測定結果</summary>

パッケージの監査では、2026 年 10 月 15 日にテストした CI ビルドで以下のおおよその値が観測されました。

| 測定項目 | Windows | Linux |
| --- | --- | --- |
| 複数のモデルを読み込んだ状態で観測したプロセスメモリのピーク | **3.0 GB** | **2.6 GB** |
| テストで測定したアプリ + 全モデル + キャッシュ | **1.10 GB** | **1.53 GB** |
| 背景除去モデル（ISNet）の初回読み込み | **53 秒** | **39 秒** |

**これらは観測値であり、最大使用量や処理時間を保証するものではありません。** メモリテストでは複数のモデルを読み込んでいました。大きな写真ではさらにメモリを使う場合があります。ディスク容量は測定したパッケージ、モデル、キャッシュの合計で、元画像、出力、一時的な展開領域、ソース開発環境は含みません。モデルの読み込み時間は機器によって異なり、読み込み後はセッションを再利用します。モデルのダウンロード時間や、画像 1 枚あたりの処理時間ではありません。

</details>

### 実行環境と処理

- **ソースからの実行：** Python 3.13、Tk、[`requirements.txt`](../../requirements.txt) のライブラリが必要です。配布済みパッケージを使う場合、Python の別途インストールは不要です。
- **一括処理の上限：** 機能一覧には現在の UI の上限を記載しています。LQIP / Base64、EXIF 編集は 1 枚、OCR と背景除去は 10 枚、その他の記載された一括処理は 100 枚です。
- **コーデック：** HEIC/HEIF はソースの依存関係に含まれる `pillow-heif` を使用します。AVIF などは Pillow のコーデックとプラットフォームに依存します。JPEG は透過に対応していないため、アルファチャンネルが必要なら PNG または WebP を使ってください。PNG の圧縮では 256 色に減色される場合があるため、結果を確認してください。
- **AI モデル：** 初回利用時や、新しく選択したモデル・認識言語に応じてダウンロードが発生する場合があります。オフライン利用には必要なモデルが保存済みである必要があります。検証したパッケージでは OCR と背景除去は CPU で実行されます。

### Linux のシステムライブラリ

AppImage をマウントして実行するには **FUSE 2** が必要です（対応するディストリビューションでは `libfuse2`）。FUSE が使えない場合は展開して実行できます。[AppImage の公式手順](https://docs.appimage.org/user-guide/troubleshooting/fuse.html)を参照してください。例のファイル名はダウンロードしたものに置き換えてください。

~~~bash
./"Yagua-<version>-x86_64.AppImage" --appimage-extract-and-run
~~~

展開には追加の一時ディスク領域が必要で、起動が遅くなる場合があります。ソースからの実行用に、Linux CI では Ubuntu 22.04 に Tk と以下のライブラリをインストールしています。

~~~bash
sudo apt-get install python3-tk libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgtk-3-0 libgomp1
~~~

パッケージ名はディストリビューションによって異なります。使用する Python 3.13 インタープリターで Tk が利用できることを確認してください。ディストリビューション標準の Tk パッケージでは、別途インストールした Python をカバーできない場合があります。

<a id="faq"></a>

## よくある質問

### Yagua は画像をアップロードしますか？

処理はローカルで行われ、各モジュールが画像を処理サービスにアップロードすることはありません。モデルのダウンロードと GitHub の更新確認には接続が必要です。外部リンクはブラウザーで開きます。EXIF の地図リンクを開くと、選択した GPS 座標が Google マップに送信されます。

### 最初の AI 処理が遅いのはなぜですか？

OCR と背景除去はエンジンを初期化し、必要に応じてモデルをダウンロードします。完了するまでお待ちください。その後はキャッシュ済みモデルを再利用できますが、大きな画像や大量の画像の処理には引き続き多くのリソースが必要です。

### 形式が選べない、または画像が読み込めないのはなぜですか？

対応する入力は、モジュールや利用できるコーデックによって異なります。PNG または JPEG のコピーで試し、`yagua.log` を確認してください。透過が必要なら PNG または WebP に書き出してください。

### 圧縮しても小さくならない画像があるのはなぜですか？

最適化済みの画像は、小さくならない場合があります。EXIF 削除が無効な場合、圧縮後のサイズが元以上になると、Yagua は元ファイルを出力先にコピーします。EXIF 削除が有効な場合は、大きくなっても処理済み画像を保存するため、この代替処理によって元の EXIF が戻ることはありません。EXIF の削除を目的とする場合はメタデータモジュールを使ってください。

### 更新はどのように行いますか？

Yagua は起動時の通知に対応し、**設定 → 更新**からも確認できます。ダウンロードリンクを開きますが、自動インストールは行いません。RC.4/RC.5 パッケージは、対応するプラットフォーム接頭辞（`win-v` または `linux-v`）が付いた新しい安定版のみを探します。プレリリースと下書きは除外するため、新しい RC ビルドは検出しません。テスト版は [GitHub Releases](https://github.com/GuilleBouix/Yagua-Image-Processor/releases) から手動でダウンロードしてください。これらのパッケージは接続失敗時にも「更新はありません」と表示する場合があります。不明な場合は、接頭辞のない古いリリースも含め、Releases を直接確認してください。

### 不具合はどこに報告できますか？

Yagua のバージョン、OS、モジュール、再現手順、関連ログを添えて[不具合報告](https://github.com/GuilleBouix/Yagua-Image-Processor/issues/new?template=bug_report.md)を作成してください。`yagua.log` は以下にあります。

- Windows: `%APPDATA%\Yagua\yagua.log`
- Linux: `~/.config/Yagua/yagua.log`
- macOS: `~/Library/Application Support/Yagua/yagua.log`

ログにはファイル名やパスが含まれる場合があります。共有する前に内容を確認してください。

<a id="contributing"></a>

## 開発と貢献

Yagua は、UI に **CustomTkinter**、画像処理に **Pillow / pillow-heif**、背景除去に **rembg / ONNX Runtime**、OCR に **EasyOCR / PyTorch**、EXIF に **piexif** を使用しています。正確なバージョンは [`requirements.txt`](../../requirements.txt) に記載されています。

ソースからインストールした後、開発ツールをインストールし、CI のチェックを実行してください。Windows では仮想環境の実行ファイルを直接使用します。

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m ruff check app tests scripts
.\.venv\Scripts\python.exe -m pyright --skipunannotated --pythonpath .\.venv\Scripts\python.exe app
.\.venv\Scripts\python.exe -m pytest -q
~~~

Linux では仮想環境を有効にして実行します。

~~~bash
python -m pip install -r requirements-dev.txt
python -m ruff check app tests scripts
python -m pyright --skipunannotated --pythonpath "$(command -v python)" app
python -m pytest -q
~~~

UI テストにはディスプレイが必要です。画面のない Linux 環境では `xvfb` をインストールし、CI と同様に `xvfb-run -a python -m pytest -q` を使用してください。

プロジェクトの履歴は [`CHANGELOG.md`](../../CHANGELOG.md) を参照してください。一部のスクリーンショットは現在のコードと異なる場合があります。[Issues](https://github.com/GuilleBouix/Yagua-Image-Processor/issues) で不具合や機能を提案したり、関連する検証を添えて変更内容を絞ったプルリクエストを送ったりできます。文書化された動作を変更した場合は、README の全 9 言語を更新してください。

## プロジェクトを支援する

Yagua が役に立ったら、GitHub でスターを付けることで他の方も見つけやすくなります。不具合報告、翻訳、開発への参加でも支援できます。

**[Yagua を試しましたか？評価をお寄せください（英語）](https://yagua.bouixdev.workers.dev/en/project/#project-rating)**

**[GitHub Sponsors で支援](https://github.com/sponsors/GuilleBouix) · [PayPal で支援](https://www.paypal.com/paypalme/guillebouix)**

<p align="center">
  <a href="https://www.paypal.com/paypalme/guillebouix"><img src="https://github.com/user-attachments/assets/2f3f6a1b-990c-4fb8-9fda-7482c1ca20a5" width="220" alt="PayPal で Yagua を支援" /></a>
</p>

## ライセンス

Yagua は **[MIT ライセンス](../../LICENSE)**で公開されています。サードパーティーのライブラリやモデルには、それぞれのライセンスが適用されます。
