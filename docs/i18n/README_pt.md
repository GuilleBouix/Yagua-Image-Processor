<div align="center">

[English](../../README.md) · [Español](README_es.md) · **Português** · [Français](README_fr.md) · [Deutsch](README_de.md)

<img src="https://github.com/user-attachments/assets/fc1dacf8-5249-43da-a294-4b20dc423304" width="1000" alt="Banner do Yagua — Processador de imagens" />

# Yagua · Image Processor

### Suas imagens. Seu computador. Seu jeito de trabalhar.

Ferramentas de desktop gratuitas e de código aberto para converter, comprimir e processar imagens em lote.

<p align="center">
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/releases/latest"><img src="https://img.shields.io/github/v/release/GuilleBouix/Yagua-Image-Processor?style=flat-square&amp;label=stable&amp;color=2563eb" alt="Última versão estável" /></a>
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/releases"><img src="https://img.shields.io/github/downloads/GuilleBouix/Yagua-Image-Processor/total?style=flat-square&amp;label=downloads&amp;color=22c55e" alt="Total de downloads" /></a>
  <a href="https://github.com/GuilleBouix/Yagua-Image-Processor/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/GuilleBouix/Yagua-Image-Processor/ci.yml?branch=main&amp;style=flat-square&amp;label=CI" alt="Estado da CI" /></a>
  <a href="#requirements"><img src="https://img.shields.io/badge/Python-3.13-3776ab?style=flat-square&amp;logo=python&amp;logoColor=white" alt="Python 3.13" /></a>
  <a href="../../LICENSE"><img src="https://img.shields.io/badge/license-MIT-f4c430?style=flat-square" alt="Licença MIT" /></a>
</p>

**[Downloads](https://github.com/GuilleBouix/Yagua-Image-Processor/releases) · [Recursos](#features) · [Instalação](#installation)**

[Capturas](#screenshots) · [Uso](#usage) · [Requisitos](#requirements) · [Perguntas frequentes](#faq) · [Contribuir](#contributing)

</div>

## Por que Yagua?

Yagua reúne tarefas comuns de processamento de imagens em um aplicativo de desktop para desenvolvedores web, designers, fotógrafos e qualquer pessoa que trabalhe com coleções de imagens. Você pode processar seus arquivos sem assinatura nem navegador.

O processamento acontece no seu computador. A remoção de fundo e o OCR precisam de um download inicial de modelos; depois podem funcionar offline se os modelos necessários estiverem armazenados. A verificação de atualizações consulta o GitHub; links de download, doação e mapas são abertos no navegador.

A interface está disponível em **inglês, espanhol, português, francês e alemão**, com temas escuros, prévias quando disponíveis e registros de diagnóstico em **Configurações → Logs**.

<a id="features"></a>

## Recursos

A tabela descreve o código atual. As versões empacotadas podem incluir recursos diferentes; confira suas notas de lançamento.

| Módulo | O que você pode fazer | Formatos e saídas | Limite de seleção |
| --- | --- | --- | --- |
| Converter | Alterar o formato e ajustar a qualidade quando permitido. | Saídas JPEG, PNG, WebP, AVIF, HEIC, ICO, BMP, TIFF e GIF. | 100 imagens |
| Comprimir | Reduzir o tamanho do arquivo mantendo seu formato original. | JPEG, PNG, WebP, AVIF, HEIC/HEIF e outros formatos raster compatíveis. | 100 imagens |
| Redimensionar / Recortar / Tela | Alterar dimensões, recortar ou adicionar espaço; usar tamanhos predefinidos. | Imagens raster comuns, como JPEG, PNG e WebP. | 100 imagens |
| Remover fundo | Remover fundos localmente com IA. | Saída PNG, WebP ou TIFF com transparência. | 10 imagens |
| Paleta de cores | Extrair cores, copiar valores HEX/RGB/HSL e exportar uma paleta. | Uma imagem compatível → cores e paleta PNG. | 1 imagem |
| Marca d'água | Aplicar um logo; ajustar posição, tamanho, opacidade e margem. | Imagens base compatíveis; PNG transparente recomendado para o logo. | 100 imagens + 1 logo |
| Renomear | Pré-visualizar numeração, datas e alterações de maiúsculas/minúsculas. | Altera os nomes na pasta original. | 100 arquivos |
| OCR | Extrair texto com EasyOCR; copiar ou exportar como TXT. | Imagens raster compatíveis → texto. | 10 imagens |
| Metadados EXIF | Consultar, exportar, editar campos ou remover metadados em lote. | Edição JPEG/TIFF; exportação de metadados TXT/JSON. | 1 imagem para editar; 100 para limpar |
| LQIP / Base64 | Gerar placeholders de baixa qualidade ou codificar imagens para a web. | Base64, data URI, HTML e CSS; exportação TXT/JSON. | 1 imagem |

A compatibilidade depende do módulo, dos codecs instalados e da plataforma. Um formato listado não garante que todos os módulos possam lê-lo ou gravá-lo. Consulte os [requisitos](#requirements).

<a id="screenshots"></a>

## Capturas de tela

<p align="center">
  <a href="https://github.com/user-attachments/assets/903c897e-eb48-4b6b-b941-2fbfffb234ce"><img src="https://github.com/user-attachments/assets/903c897e-eb48-4b6b-b941-2fbfffb234ce" width="420" alt="Módulo de conversão com imagens selecionadas e controles de formato de saída" /></a>
  <a href="https://github.com/user-attachments/assets/ed7081e4-d106-47db-9744-927be0db9d5d"><img src="https://github.com/user-attachments/assets/ed7081e4-d106-47db-9744-927be0db9d5d" width="420" alt="Módulo de remoção de fundo com imagens selecionadas e controles de saída" /></a>
</p>

<details>
<summary>Mais capturas: compressão, tamanho, paleta, renomeação, EXIF, LQIP e configurações</summary>

<p align="center">
  <a href="https://github.com/user-attachments/assets/f8f57bbb-4cdf-4c5f-8d06-a04b2c3dc1b1"><img src="https://github.com/user-attachments/assets/f8f57bbb-4cdf-4c5f-8d06-a04b2c3dc1b1" width="280" alt="Módulo de compressão com controle de qualidade e opção para remover EXIF" /></a>
  <a href="https://github.com/user-attachments/assets/381c1f71-debd-47a0-837b-fb8f84e41790"><img src="https://github.com/user-attachments/assets/381c1f71-debd-47a0-837b-fb8f84e41790" width="280" alt="Módulo de tamanho com abas para redimensionar, recortar e ajustar a tela" /></a>
  <a href="https://github.com/user-attachments/assets/dfe2dd77-f792-4092-a6d7-82b5e96aa104"><img src="https://github.com/user-attachments/assets/dfe2dd77-f792-4092-a6d7-82b5e96aa104" width="280" alt="Paleta extraída com amostras de cores e seus valores" /></a>
</p>
<p align="center">
  <a href="https://github.com/user-attachments/assets/e3a8f766-84e5-412d-bbaf-acb5936c0380"><img src="https://github.com/user-attachments/assets/e3a8f766-84e5-412d-bbaf-acb5936c0380" width="280" alt="Renomeação em lote com nomes originais e propostos" /></a>
  <a href="https://github.com/user-attachments/assets/235fce12-9796-4304-9252-f9e016edf483"><img src="https://github.com/user-attachments/assets/235fce12-9796-4304-9252-f9e016edf483" width="280" alt="Editor EXIF com campos de autor, copyright, software e data" /></a>
  <a href="https://github.com/user-attachments/assets/8e8824a4-0bdf-44d8-b82f-7e0c2e1fcfe5"><img src="https://github.com/user-attachments/assets/8e8824a4-0bdf-44d8-b82f-7e0c2e1fcfe5" width="280" alt="Módulo LQIP e Base64 com controles de tamanho e qualidade do placeholder" /></a>
</p>
<p align="center">
  <a href="https://github.com/user-attachments/assets/29131d50-2ea2-40c5-9549-d5878d89119a"><img src="https://github.com/user-attachments/assets/29131d50-2ea2-40c5-9549-d5878d89119a" width="280" alt="Configurações do Yagua com seleção de idioma e tema" /></a>
</p>

</details>

Estas são capturas existentes do projeto; a disposição e os controles podem variar entre versões. Clique em uma imagem para vê-la no tamanho original.

<a id="installation"></a>

## Instalação

### Escolha uma versão

Abra **[GitHub Releases](https://github.com/GuilleBouix/Yagua-Image-Processor/releases)** e escolha seu sistema operacional. O badge **stable** leva à última versão estável do GitHub; versões mais novas marcadas **Pre-release**, incluindo `rc`, são versões de teste. Windows e Linux podem ter versões diferentes.

A versão do código é definida em [`app/version.py`](../../app/version.py). Isso não significa que exista um instalador publicado com a mesma versão. Leia as notas de cada lançamento e baixe os arquivos anexados àquela release.

| Plataforma | Pacote | Etapas |
| --- | --- | --- |
| Windows | `Yagua_Setup_<version>.exe` | Execute o instalador e abra o Yagua pelo menu Iniciar ou atalho na área de trabalho. |
| Windows portátil | `Yagua_Portable_<version>.zip`, quando disponível | Extraia o ZIP inteiro em uma pasta com permissão de escrita e execute `Yagua.exe`. Mantenha os arquivos acompanhantes juntos. |
| Linux x86_64 | `Yagua-<version>-x86_64.AppImage`, quando disponível | Dê permissão de execução ao arquivo baixado e execute-o como mostrado abaixo. |
| macOS | Suporte experimental por código/compilação | Não é prometido um pacote estável para macOS. Veja o [script de compilação](../../scripts/build_macos_app.sh) existente. |

No Linux, substitua o nome de exemplo pelo arquivo que você baixou:

~~~bash
chmod +x "Yagua-<version>-x86_64.AppImage"
./"Yagua-<version>-x86_64.AppImage"
~~~

### Executar pelo código-fonte

Use **Python 3.13**, a versão utilizada pela CI, e Git. A instalação das dependências pode ser grande porque inclui bibliotecas de OCR e IA. Linux também precisa de Tk e das bibliotecas do sistema listadas nos [requisitos](#requirements).

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

Os comandos usam as dependências fixadas pelo repositório. As verificações de CI em Windows/Linux não estabelecem compatibilidade com outras versões do Python nem com macOS.

<a id="usage"></a>

## Uso

1. Abra o Yagua e escolha um módulo na barra lateral.
2. Carregue as imagens e configure as opções disponíveis.
3. Confira a prévia quando o módulo oferecer uma.
4. Processe as imagens e escolha uma pasta de saída quando solicitado; confira a mensagem final para identificar erros.

**LQIP / Base64:** Selecione uma imagem, escolha o modo e os parâmetros, gere, compare e copie ou exporte Data URI, HTML, CSS ou Base64 puro. Carregar outra imagem redefine o modo LQIP, largura 20 px, desfoque 2 e qualidades 40/85; cancelar o seletor preserva o estado atual. Ambos os modos geram JPEG sem transparência.

**Arquivos originais:** Renomear altera os nomes na localização atual. Editar EXIF sobrescreve a imagem selecionada após confirmação. Trabalhe com cópias nessas operações. A limpeza EXIF em lote grava na pasta escolhida. As outras exportações usam o fluxo de salvamento ou pasta de saída de cada módulo.

### Exemplos práticos

- **Preparar imagens para a web:** Converta até 100 fotos para WebP, escolha a qualidade e depois ajuste o tamanho se necessário. Gere placeholders LQIP separadamente para mostrar prévias enquanto seu site carrega.
- **Preparar fotos de produtos:** Carregue até 10 imagens em Remover fundo e exporte como PNG ou WebP para manter a transparência. Se necessário, adicione um logo PNG transparente com Marca d'água.
- **Extrair texto:** Carregue até 10 imagens nítidas no OCR, escolha os idiomas de reconhecimento e copie o resultado ou exporte um TXT. Revise o texto para corrigir erros de reconhecimento.

<a id="requirements"></a>

## Requisitos e limites

### Hardware

Para o aplicativo completo, incluindo **OCR e remoção de fundo**:

| Componente | Mínimo provisório | Recomendado |
| --- | --- | --- |
| Processador | Intel/AMD x86-64 relativamente recente, com **4 núcleos** | CPU moderna com **6–8 núcleos** |
| RAM do computador | **8 GB**, com poucos outros aplicativos abertos | **16 GB**; **32 GB** para imagens muito grandes e multitarefa |
| Armazenamento | **4 GB livres**, além do espaço para originais e resultados | **SSD com 10 GB livres ou mais**, além das suas imagens |
| Gráficos | Gráficos integrados são suficientes; GPU dedicada não é obrigatória | Gráficos integrados são suficientes |
| Internet | Para baixar os modelos inicialmente e verificar atualizações | Uso offline com os modelos necessários já baixados |

**São estimativas práticas para o aplicativo completo, não mínimos de hardware validados. Ainda falta testá-los em um computador de entrada.** Não se recomenda um computador com 4 GB de RAM para o uso completo de OCR e remoção de fundo. O consumo depende da resolução, do tamanho do lote e dos modelos; reduza os lotes se os recursos forem limitados.

O pacote testado processa pela **CPU**; você não precisa de uma NVIDIA nem de outra GPU dedicada. Priorize processador, RAM e SSD. A remoção de fundo usa o provedor de execução por CPU do ONNX Runtime; consulte a [documentação oficial do ONNX Runtime](https://onnxruntime.ai/docs/api/python/api_summary.html).

### Sistemas operacionais

| Sistema | Base e validação |
| --- | --- |
| Windows | **Windows 10/11 de 64 bits**; preferencialmente Windows 11. O ONNX Runtime estabelece Windows 10 como versão mínima do Windows. A validação do instalador e do portátil finais em PCs limpos com Windows 10/11 ainda está pendente. |
| Linux | **Ubuntu 22.04 x86-64**, a base verificada pela CI. Outras distribuições, versões e ambientes de desktop precisam de validação do AppImage final. |
| macOS | Suporte experimental; não se afirma que exista um pacote nativo validado. |

Os pacotes atuais de Windows e Linux são **x86-64**; não há versão nativa validada para ARM. A CI usa Windows Server e Ubuntu 22.04/Xvfb; essas verificações não certificam todos os sistemas de desktop. Consulte os [requisitos de plataforma do ONNX Runtime](https://onnxruntime.ai/docs/build/inferencing.html).

<details>
<summary>Consumo medido e primeiro carregamento do modelo</summary>

A [auditoria dos pacotes](../../audit/lean-runtime/README.md) registra estas observações aproximadas em compilações de CI testadas em 15 de outubro de 2026:

| Medição | Windows | Linux |
| --- | --- | --- |
| Pico de RAM do processo observado com vários modelos carregados | **3,0 GB** | **2,6 GB** |
| App + todos os modelos e caches medidos nesse teste | **1,10 GB** | **1,53 GB** |
| Primeiro carregamento do modelo de remoção de fundo (ISNet) | **53 segundos** | **39 segundos** |

**São observações, não máximos nem tempos garantidos.** O teste de RAM manteve vários modelos carregados; fotografias grandes podem consumir mais memória. Os valores de disco cobrem o pacote, modelos e caches medidos, não originais, resultados, espaço temporário de extração nem um ambiente de desenvolvimento pelo código. Os tempos de carregamento dependem do computador; a sessão é reutilizada depois. Não são tempos de download do modelo nem de processamento por imagem.

</details>

### Execução e processamento

- **Código-fonte:** Python 3.13, Tk e as bibliotecas de [`requirements.txt`](../../requirements.txt). Os pacotes compilados não exigem uma instalação separada do Python.
- **Lotes:** A tabela de recursos mostra os limites atuais da interface: uma imagem para Paleta, LQIP / Base64 ou edição EXIF, 10 para OCR/remoção de fundo e 100 para as outras operações em lote listadas.
- **Codecs:** HEIC/HEIF usa `pillow-heif`, incluído nas dependências do código. AVIF e outros formatos dependem dos codecs do Pillow e da plataforma. JPEG não aceita transparência; use PNG ou WebP quando necessário. A compressão PNG pode reduzir a imagem a 256 cores: confira o resultado.
- **Modelos de IA:** Downloads podem acontecer no primeiro uso ou ao selecionar um modelo/idioma que precise de outro modelo. O uso offline exige modelos armazenados. O pacote testado executa OCR e remoção de fundo pela CPU.

### Bibliotecas do sistema no Linux

AppImage precisa de **FUSE 2** para execução por montagem (`libfuse2` em distribuições compatíveis). Se FUSE não estiver disponível, a extração é uma alternativa; consulte as [instruções oficiais do AppImage](https://docs.appimage.org/user-guide/troubleshooting/fuse.html). Substitua o nome de exemplo pelo arquivo baixado:

~~~bash
./"Yagua-<version>-x86_64.AppImage" --appimage-extract-and-run
~~~

A extração precisa de espaço temporário adicional e pode tornar a inicialização mais lenta. Para execução pelo código, a CI instala Tk e estas bibliotecas no Ubuntu 22.04:

~~~bash
sudo apt-get install python3-tk libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgtk-3-0 libgomp1
~~~

Os nomes dos pacotes variam conforme a distribuição. Verifique se Tk está disponível para seu interpretador Python 3.13; o pacote Tk padrão da distribuição pode não atender a um Python instalado separadamente.

<a id="faq"></a>

## Perguntas frequentes

### O Yagua envia minhas imagens?

O processamento é local; os módulos não enviam imagens a um serviço de processamento. Downloads de modelos e verificações de atualização no GitHub precisam de conexão. Links externos abrem o navegador; ao abrir o link de mapa do EXIF, as coordenadas GPS selecionadas são enviadas ao Google Maps.

### Por que a primeira operação com IA demora mais?

OCR e Remover fundo inicializam seus motores e podem baixar modelos. Aguarde essa etapa terminar. As próximas execuções podem reutilizar os modelos armazenados; imagens e lotes grandes continuam exigindo mais recursos.

### Por que um formato está indisponível ou uma imagem é rejeitada?

As entradas aceitas dependem do módulo e dos codecs disponíveis. Tente uma cópia PNG ou JPEG, confira **Configurações → Logs**. Exporte como PNG ou WebP se precisar de transparência.

### Por que a compressão não reduz todas as imagens?

Uma imagem já otimizada pode não diminuir. Se o resultado tiver tamanho igual ou maior que o original, o Yagua copia o original para a saída. Por isso, a compressão também não garante a remoção dos metadados solicitados; use o módulo específico de limpeza EXIF.

### Como funcionam as atualizações?

O Yagua pode avisar ao iniciar e permite verificar em **Configurações → Atualizações**. Procura versões estáveis mais novas com o prefixo da sua plataforma (`win-v` ou `linux-v`) e exclui versões preliminares. Abre um link de download; não instala atualizações automaticamente. Confira Releases manualmente para versões de teste e lançamentos antigos sem prefixo.

### Como relato um problema?

Abra um [relato de erro](https://github.com/GuilleBouix/Yagua-Image-Processor/issues/new?template=bug_report.md) com sua versão do Yagua, sistema operacional, módulo, etapas para reproduzir e logs relevantes. Consulte **Configurações → Logs** ou procure `yagua.log` em:

- Windows: `%APPDATA%\Yagua\yagua.log`
- Linux: `~/.config/Yagua/yagua.log`
- macOS: `~/Library/Application Support/Yagua/yagua.log`

Os logs podem incluir caminhos e nomes de arquivos; revise-os antes de compartilhar.

<a id="contributing"></a>

## Desenvolvimento e contribuição

O Yagua usa **CustomTkinter** para a interface, **Pillow / pillow-heif** para imagens, **rembg / ONNX Runtime** para remover fundos, **EasyOCR / PyTorch** para OCR e **piexif** para EXIF. As versões exatas estão em [`requirements.txt`](../../requirements.txt).

Após instalar pelo código, instale as ferramentas de desenvolvimento e execute as verificações de CI. No Windows, use diretamente os executáveis do ambiente virtual:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m ruff check app tests scripts
.\.venv\Scripts\python.exe -m pyright --skipunannotated --pythonpath .\.venv\Scripts\python.exe app
.\.venv\Scripts\python.exe -m pytest -q
~~~

No Linux, com o ambiente virtual ativado:

~~~bash
python -m pip install -r requirements-dev.txt
python -m ruff check app tests scripts
python -m pyright --skipunannotated --pythonpath "$(command -v python)" app
python -m pytest -q
~~~

Os testes de interface precisam de uma tela. Em Linux sem ambiente gráfico, instale `xvfb` e use `xvfb-run -a python -m pytest -q`, como a CI faz.

Consulte [`CHANGELOG.md`](../../CHANGELOG.md) para o histórico. Algumas capturas podem estar desatualizadas em relação ao código. Relate erros, sugira recursos em [Issues](https://github.com/GuilleBouix/Yagua-Image-Processor/issues) ou envie PRs focados com validação relevante. Ao alterar comportamentos documentados, atualize os cinco idiomas do README.

## Apoie o projeto

Se o Yagua ajuda você, uma estrela no GitHub facilita que outras pessoas o encontrem. Você também pode colaborar com relatos de erros, traduções ou contribuições.

**[Apoiar no GitHub Sponsors](https://github.com/sponsors/GuilleBouix) · [Apoiar pelo PayPal](https://www.paypal.com/paypalme/guillebouix)**

<p align="center">
  <a href="https://www.paypal.com/paypalme/guillebouix"><img src="https://github.com/user-attachments/assets/2f3f6a1b-990c-4fb8-9fda-7482c1ca20a5" width="220" alt="Apoie o Yagua pelo PayPal" /></a>
</p>

## Licença

O Yagua é distribuído sob a **[licença MIT](../../LICENSE)**. Bibliotecas e modelos de terceiros mantêm suas respectivas licenças.
