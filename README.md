# WhatsApp Constructor - Indexação Forense

Ferramenta desenvolvida em Python para processamento, indexação e auditoria de extrações lógicas do WhatsApp. O sistema processa exportações nativas (`.txt` e mídias), reconstrói a cadeia de leitura em uma interface HTML interativa, calcula assinaturas digitais (SHA-256) e realiza transcrição de mídias offline utilizando Inteligência Artificial.

## 📥 Download (Executável)
Para usar o software sem precisar instalar o Python ou configurar códigos, faça o download da versão executável mais recente clicando no link abaixo:

👉 **[BAIXAR WHATSAPP CONSTRUCTOR (Versão Mais Recente)](https://github.com/GabrielSi2022/WhatsApp-Constructor/releases/download/V1.0/whatsconstructor.exe)**

---

## 💻 Visão Técnica
O software atua como um parser e construtor forense. Ele não realiza a extração física do dispositivo, mas sim o tratamento do dado bruto exportado, garantindo a imutabilidade da prova através de espelhamento criptográfico e gerando relatórios formatados para uso em investigações e processos judiciais.

## 🛠️ Stack Tecnológico e Dependências
*   **Linguagem:** Python 3.x
*   **Interface Gráfica:** `tkinter` (nativo) com suporte a temas estilizados (ttk).
*   **Transcrição de IA (Offline):** `openai-whisper` (requer `ffmpeg` embutido).
*   **Geração de PDF:** `fpdf2` (com filtro de encodagem `windows-1252` para sanitização de caracteres complexos/emojis).
*   **Criptografia/Integridade:** Biblioteca nativa `hashlib` (SHA-256).
*   **Build/Empacotamento:** `PyInstaller` para geração de executável standalone (`.exe`) em ambiente Windows.

## ⚙️ Arquitetura e Módulos Principais

| Módulo | Descrição Técnica |
| :--- | :--- |
| **Regex Parser** | Núcleo de leitura do arquivo `.txt`. Utiliza Expressões Regulares (Regex) para identificar timestamps (suporta anos com 2 ou 4 dígitos), remetentes e anexos, normalizando padrões do Android e iOS. |
| **Hash Engine** | Calcula o Hash SHA-256 de todos os artefatos manipulados (TXT original, mídias copiadas, HTML gerado e PDFs) para garantir a preservação da Cadeia de Custódia. |
| **Transcritor Whisper** | Módulo que intercepta áudios e vídeos (extensões `.opus`, `.mp4`, etc.) e utiliza o modelo Whisper offline (FP16/CPU) para converter fala em texto diretamente no laudo. |
| **Construtor HTML** | Injeta os dados parseados em um template HTML/CSS/JS estático e autossuficiente (não requer servidor). Suporta alternância de temas de impressão (`@media print`) para economia de tinta. |
| **Construtor PDF** | Gera o Relatório de Análise e a Relação de Integrantes. Possui tratamento de encodagem para evitar crashes da biblioteca `fpdf2` ao processar Emojis presentes nos nomes de contatos. |

## 📦 Instruções de Build (Compilação)
Para gerar o executável standalone (`.exe`) para Windows a partir do código fonte, garantindo que todas as dependências ocultas do Whisper, a pasta de logomarcas institucionais e o FFmpeg sejam embutidos, utilize o comando abaixo:

```cmd
pyinstaller --noconfirm --onefile --windowed --icon="icone.ico" --add-binary "ffmpeg.exe;." --add-data "logos;logos" --add-data "icone.ico;." --collect-data whisper whatsconstructor.py
```

### Requisitos para o Build:
*   O arquivo `ffmpeg.exe` deve estar no diretório raiz do projeto.
*   A pasta `logos/` deve existir no diretório raiz contendo as imagens institucionais prévias.
*   O arquivo `icone.ico` deve estar no diretório raiz.

## ⚖️ Nota de Uso
Este software foi projetado para auxiliar autoridades e peritos na visualização e documentação de evidências digitais extraídas de forma lícita e com autorização prévia.