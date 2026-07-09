import os
import re
import sys
import shutil
import hashlib
import threading
import warnings
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

# Ignora os avisos de atualização da biblioteca FP16
warnings.filterwarnings("ignore")

# Importa a biblioteca de PDF
try:
    from fpdf import FPDF
except ImportError:
    messagebox.showerror("Erro de Dependência", "A biblioteca 'fpdf2' não está instalada. Rode: pip install fpdf2")
    sys.exit()

def configurar_caminho_ffmpeg():
    if getattr(sys, 'frozen', False):
        caminho_base = sys._MEIPASS
    else:
        caminho_base = os.path.dirname(os.path.abspath(__file__))
    os.environ["PATH"] += os.pathsep + caminho_base

configurar_caminho_ffmpeg()

try:
    import whisper
    WHISPER_DISPONIVEL = True
except ImportError:
    WHISPER_DISPONIVEL = False

# --- INTERCEPTADOR DA BARRA DE DOWNLOAD ---
class InterceptadorDownload:
    def __init__(self, callback):
        self.original_stderr = sys.stderr
        self.callback = callback
        self.pattern = re.compile(r'(\d{1,3})%')

    def write(self, message):
        if self.original_stderr is not None:
            self.original_stderr.write(message)
        match = self.pattern.search(message)
        if match:
            try:
                pct = int(match.group(1))
                if pct <= 100:
                    self.callback(pct, 100, f"A transferir modelo de IA: {pct}% concluído...")
            except:
                pass

    def flush(self):
        if self.original_stderr is not None:
            self.original_stderr.flush()

# --- CLASSE DO GERADOR DE PDF PERICIAL ---
class RelatorioForensePDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 14)
        self.cell(0, 10, 'RELATÓRIO TÉCNICO DE INDEXAÇÃO E INTEGRIDADE DE DADOS', 0, 1, 'C')
        self.set_font('helvetica', 'I', 10)
        self.cell(0, 5, 'Análise Preliminar de Extração Lógica - WhatsApp', 0, 1, 'C')
        self.line(10, 28, 200, 28)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

# --- FUNÇÕES NÚCLEO ---
def calcular_hash_sha256(caminho_arquivo):
    sha256_hash = hashlib.sha256()
    try:
        with open(caminho_arquivo, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        return f"Erro ao calcular hash: {e}"

def limpar_nome_arquivo(nome):
    nome_limpo = re.sub(r'[\u200e\u200f\u202a\u202b\u202c\u200b\u202d\u202e]', '', nome)
    return nome_limpo.strip()

def encontrar_arquivo(nome_procurado, pasta_raiz):
    nome_limpo = limpar_nome_arquivo(nome_procurado)
    for root, dirs, files in os.walk(pasta_raiz):
        if nome_limpo in files:
            return os.path.join(root, nome_limpo), nome_limpo

    nome_base = os.path.splitext(nome_limpo)[0].rstrip('._')
    for root, dirs, files in os.walk(pasta_raiz):
        for arquivo in files:
            if arquivo.startswith(nome_base):
                return os.path.join(root, arquivo), arquivo
                
    return None, nome_limpo

def gerar_pdf_pericial(caminho_saida, incluir_certidao, dados_certidao, registro_hashes, data_hora_atual, modelo_ia, nome_html):
    pdf = RelatorioForensePDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, '1. METODOLOGIA E ESCOPO DO PROCEDIMENTO', 0, 1)
    
    pdf.set_font('helvetica', '', 10)
    metodologia_texto = (
        "O presente relatório documenta a indexação e o cálculo de integridade de dados provenientes de uma extração "
        "lógica de conversas do aplicativo WhatsApp. Ressalta-se que a extração primária dos dados foi realizada "
        "através da funcionalidade nativa 'Exportar Conversa' do próprio aplicativo alvo, gerando um arquivo de "
        "texto (.txt) acompanhado de seus respectivos arquivos de mídia.\n\n"
        "Este software não realiza extração física ou invasiva do dispositivo móvel. Sua função limita-se a "
        "processar o material previamente exportado, reconstruir a cadeia de leitura de forma legível (HTML) "
        "e calcular as assinaturas digitais (Hash SHA-256) para fins de preservação da cadeia de custódia e "
        "imutabilidade das provas. Transcrições de áudio, quando aplicáveis, são processadas offline."
    )
    pdf.multi_cell(0, 5, metodologia_texto)
    pdf.ln(5)

    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, '2. INFORMAÇÕES DO PROCESSAMENTO', 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.cell(0, 6, f"Data e Hora do Procedimento: {data_hora_atual}", 0, 1)
    pdf.cell(0, 6, f"Modelo de IA Utilizado (Transcrição): {modelo_ia if modelo_ia else 'Nenhum / Não solicitado'}", 0, 1)
    pdf.cell(0, 6, f"Ficheiro de Leitura Gerado: {nome_html}", 0, 1)
    pdf.ln(5)

    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, '3. REGISTRO DE INTEGRIDADE (HASH SHA-256)', 0, 1)
    pdf.set_font('courier', '', 8)
    
    for registro in registro_hashes:
        pdf.multi_cell(0, 4, registro)
    
    if incluir_certidao:
        pdf.ln(15)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, '4. CERTIDÃO DE INDEXAÇÃO', 0, 1)
        pdf.set_font('helvetica', '', 10)
        
        certidao_texto = (
            f"CERTIFICA-SE, para os devidos fins e sob as penas da lei, que a extração primária dos dados "
            f"foi realizada mediante autorização prévia, expressa e voluntária do(a) proprietário(a) do dispositivo. "
            f"Certifica-se ainda que foi procedida a indexação e o processamento dos dados listados no item 3 deste "
            f"documento, de forma a garantir a sua integridade e espelhamento fiel em relação aos arquivos "
            f"exportados da origem.\n\n"
            f"Nada mais havendo a constar, lavra-se o presente relatório que segue devidamente assinado."
        )
        pdf.multi_cell(0, 5, certidao_texto)
        
        pdf.ln(25)
        
        pdf.line(55, pdf.get_y(), 155, pdf.get_y())
        pdf.ln(2)
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(0, 5, f"{dados_certidao['nome'].upper()}", 0, 1, 'C')
        pdf.set_font('helvetica', '', 10)
        pdf.cell(0, 5, f"{dados_certidao['cargo']} - MASP/Matrícula: {dados_certidao['masp']}", 0, 1, 'C')

    pdf.output(caminho_saida)

def processar_exportacao(pasta_entrada, pasta_saida, usar_transcricao, nome_modelo, incluir_certidao, dados_certidao, nome_relatorio, nome_titular_informado, callback_progresso):
    arquivo_txt = None
    for root, dirs, files in os.walk(pasta_entrada):
        for arquivo in files:
            if arquivo.endswith(".txt"):
                arquivo_txt = os.path.join(root, arquivo)
                break
        if arquivo_txt:
            break
            
    if not arquivo_txt:
        raise FileNotFoundError("Nenhum ficheiro .txt encontrado na pasta de origem.")

    if callback_progresso: callback_progresso(0, 100, "A mapear ficheiros reais na pasta...")

    extensoes_alvo = ('.opus', '.mp3', '.wav', '.ogg', '.m4a', '.mp4', '.mov', '.avi', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.doc', '.docx')
    arquivos_reais = [f for r, d, files in os.walk(pasta_entrada) for f in files if f.lower().endswith(extensoes_alvo)]

    mensagens = []
    arquivos_midia_referenciados = []

    regex_android = r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2}) - (.*?): (.*)"
    regex_ios = r"\[(\d{2}/\d{2}/\d{4}[ ,]+\d{2}:\d{2}:\d{2})\] (.*?): (.*)"

    with open(arquivo_txt, 'r', encoding='utf-8') as f:
        for linha in f:
            match = re.match(regex_android, linha)
            if not match:
                match = re.match(regex_ios, linha)
                
            if match:
                timestamp, remetente, conteudo = match.groups()
                conteudo_limpo = re.sub(r'[\u200e\u200f\u202a-\u202e]', '', conteudo).strip()
                
                nome_arquivo = None
                tipo = "texto"

                for arq_real in arquivos_reais:
                    if arq_real in conteudo_limpo:
                        nome_arquivo = arq_real
                        tipo = "midia"
                        break
                
                if not nome_arquivo:
                    marcadores = ["(arquivo anexado)", "(ficheiro anexado)", "<mídia omitida>", "<media omitted>", "anexado", "omitid", "Anexo:"]
                    if any(m in conteudo_limpo.lower() for m in marcadores):
                        match_arq = re.search(r'([a-zA-Z0-9_\-\s\.]+\.\w{3,4})', conteudo_limpo)
                        if match_arq:
                            nome_arquivo = match_arq.group(1).strip()
                            tipo = "midia"

                if nome_arquivo and nome_arquivo not in arquivos_midia_referenciados:
                    arquivos_midia_referenciados.append(nome_arquivo)

                mensagens.append({
                    "timestamp": timestamp,
                    "remetente": remetente,
                    "conteudo": conteudo_limpo,
                    "tipo": tipo,
                    "nome_arquivo": nome_arquivo
                })

    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)

    registro_hashes = []
    data_hora_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    mapa_nomes_reais = {}

    audios_para_transcrever = [m for m in arquivos_midia_referenciados if m.lower().endswith(('.opus', '.mp3', '.ogg', '.wav', '.m4a'))]
    total_midias = len(arquivos_midia_referenciados)
    total_passos = total_midias + (len(audios_para_transcrever) if usar_transcricao else 0)
    passos_concluidos = 0

    for nome_midia in arquivos_midia_referenciados:
        caminho_origem, nome_real = encontrar_arquivo(nome_midia, pasta_entrada)
        
        if caminho_origem:
            caminho_destino = os.path.join(pasta_saida, nome_real)
            shutil.copy2(caminho_origem, caminho_destino)
            hash_arquivo = calcular_hash_sha256(caminho_destino)
            registro_hashes.append(f"{nome_real}\nSHA256: {hash_arquivo}\n")
            mapa_nomes_reais[nome_midia] = nome_real
        else:
            registro_hashes.append(f"{nome_midia}\nSTATUS: ARQUIVO NÃO ENCONTRADO NA ORIGEM\n")
            mapa_nomes_reais[nome_midia] = nome_midia

        passos_concluidos += 1
        if callback_progresso: 
            callback_progresso(passos_concluidos, total_passos, f"A copiar e a gerar Hash: {passos_concluidos}/{total_midias}")

    if usar_transcricao and WHISPER_DISPONIVEL:
        redirecionador = InterceptadorDownload(callback_progresso)
        sys.stderr = redirecionador
        
        try:
            if getattr(sys, 'frozen', False):
                pasta_base_app = os.path.dirname(sys.executable)
            else:
                pasta_base_app = os.path.dirname(os.path.abspath(__file__))
            
            pasta_modelos = os.path.join(pasta_base_app, "modelos_ia")
            os.makedirs(pasta_modelos, exist_ok=True)
            modelo_ia = whisper.load_model(nome_modelo, download_root=pasta_modelos)
            
        except Exception as e:
            sys.stderr = redirecionador.original_stderr 
            raise Exception(f"Erro ao carregar IA (Verifique se o FFmpeg está instalado): {e}")
            
        sys.stderr = redirecionador.original_stderr 

        transcricoes_feitas = 0
        for msg in mensagens:
            if msg["tipo"] == "midia" and msg["nome_arquivo"]:
                nome_real = mapa_nomes_reais.get(msg["nome_arquivo"], "")
                if nome_real.lower().endswith(('.opus', '.mp3', '.ogg', '.wav', '.m4a')):
                    caminho_destino = os.path.join(pasta_saida, nome_real)
                    
                    if os.path.exists(caminho_destino):
                        transcricoes_feitas += 1
                        if callback_progresso: 
                            callback_progresso(passos_concluidos, total_passos, f"A transcrever áudio {transcricoes_feitas}/{len(audios_para_transcrever)}...")
                        
                        try:
                            resultado = modelo_ia.transcribe(caminho_destino, language="pt", fp16=False)
                            msg["transcricao"] = resultado["text"].strip()
                        except Exception as e:
                            msg["transcricao"] = f"[Erro na transcrição: {str(e)}]"
                        
                        passos_concluidos += 1

    if callback_progresso: callback_progresso(total_passos, total_passos, "A gerar relatórios finais...")

    nome_arquivo_html = f"{nome_relatorio}_Leitor_Forense.html"
    nome_arquivo_pdf = f"{nome_relatorio}_Relatorio_Pericial.pdf"

    caminho_html = os.path.join(pasta_saida, nome_arquivo_html)
    gerar_html(mensagens, caminho_html, mapa_nomes_reais, nome_relatorio, nome_titular_informado)
    
    hash_html = calcular_hash_sha256(caminho_html)
    registro_hashes.append(f"\n[ARQUIVO RECONSTRUÍDO - HTML] {nome_arquivo_html}\nSHA256: {hash_html}\n")

    caminho_pdf = os.path.join(pasta_saida, nome_arquivo_pdf)
    gerar_pdf_pericial(
        caminho_pdf, 
        incluir_certidao,
        dados_certidao, 
        registro_hashes, 
        data_hora_atual, 
        nome_modelo if usar_transcricao else None,
        nome_arquivo_html
    )

def gerar_html(lista_mensagens, caminho_saida, mapa_nomes, titulo_relatorio, nome_titular_informado):
    # Determina quem é o dono do aparelho para formatar de verde na direita
    titular_oficial = ""
    if lista_mensagens:
        titular_oficial = lista_mensagens[0]['remetente'] # Fallback
        
    if nome_titular_informado:
        for msg in lista_mensagens:
            if nome_titular_informado.lower() in msg['remetente'].lower():
                titular_oficial = msg['remetente']
                break

    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>{titulo_relatorio}</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #e5ddd5; padding: 20px; }}
            .chat-container {{ max-width: 800px; margin: 0 auto; }}
            
            .search-bar-container {{ position: sticky; top: 0; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; gap: 10px; align-items: center; z-index: 1000; margin-bottom: 20px; }}
            .search-box {{ flex-grow: 1; padding: 10px; border: 2px solid #128C7E; border-radius: 5px; font-size: 15px; }}
            .btn-nav {{ padding: 10px 15px; background-color: #128C7E; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }}
            .search-count {{ font-weight: bold; color: #555; min-width: 60px; text-align: center; }}

            .msg-wrapper {{ display: flex; margin-bottom: 15px; width: 100%; }}
            
            /* Titular fica na direita (Verde) / Outro na esquerda (Branco) */
            .titular {{ justify-content: flex-end; }}
            .outro {{ justify-content: flex-start; }}
            
            .mensagem {{ padding: 10px; border-radius: 8px; max-width: 70%; position: relative; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }}
            .titular .mensagem {{ background-color: #dcf8c6; }}
            .outro .mensagem {{ background-color: white; }}
            
            .remetente {{ font-weight: bold; font-size: 0.8em; color: #075e54; margin-bottom: 3px; }}
            .texto {{ color: #303030; line-height: 1.4; }}
            .timestamp {{ font-size: 0.7em; color: #777; text-align: right; margin-top: 5px; display: block; }}
            .caixa-transcricao {{ margin-top: 8px; padding: 8px; background-color: #e8f5e9; border-left: 4px solid #25d366; border-radius: 4px; font-size: 0.9em; font-style: italic; }}
            
            .msg-highlight {{ border: 2px solid #ff9800 !important; background-color: #fff3e0 !important; }}
            .msg-active {{ box-shadow: 0 0 15px 5px rgba(255, 152, 0, 0.6) !important; }}
        </style>
    </head>
    <body>
        <div class="chat-container">
            <h2 style="text-align: center; color: #333;">{titulo_relatorio} - Leitor Forense</h2>
            
            <div class="search-bar-container">
                <input type="text" id="searchInput" class="search-box" placeholder="🔍 Localizar na conversa ou transcrições...">
                <span id="searchCount" class="search-count">0/0</span>
                <button id="btnPrev" class="btn-nav" disabled onclick="navegarBusca(-1)">⬆️</button>
                <button id="btnNext" class="btn-nav" disabled onclick="navegarBusca(1)">⬇️</button>
            </div>
            
            <div id="mensagens-container">
    """

    for msg in lista_mensagens:
        classe_lado = "titular" if msg["remetente"] == titular_oficial else "outro"
        html_content += f'<div class="msg-wrapper {classe_lado}"><div class="mensagem" id="msg-{lista_mensagens.index(msg)}">'
        html_content += f'<div class="remetente">{msg["remetente"]}</div>'
        
        if msg["tipo"] == "midia":
            nome_arq = mapa_nomes.get(msg["nome_arquivo"], msg["nome_arquivo"])
            extensao = nome_arq.lower()
            
            if extensao.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                html_content += f'<a href="{nome_arq}" target="_blank"><img src="{nome_arq}" style="max-width:300px; border-radius:5px;" alt="Imagem Anexada" /></a>'
            elif extensao.endswith(('.mp4', '.mov', '.avi')):
                html_content += f'<br><video controls style="max-width:300px; border-radius:5px;"><source src="{nome_arq}">Vídeo não suportado.</video>'
            elif extensao.endswith(('.opus', '.mp3', '.ogg', '.wav', '.m4a')):
                html_content += f'<br><audio controls style="max-width:300px;"><source src="{nome_arq}">Áudio não suportado.</audio>'
            else:
                html_content += f'<div class="texto">📎 <a href="{nome_arq}" target="_blank">{nome_arq}</a></div>'
            
            if "transcricao" in msg and msg["transcricao"]:
                html_content += f'<div class="caixa-transcricao">IA TRANSCRIÇÃO (OFFLINE): {msg["transcricao"]}</div>'
        else:
            html_content += f'<div class="texto">{msg["conteudo"]}</div>'
            
        html_content += f'<span class="timestamp">{msg["timestamp"]}</span></div></div>'

    html_content += """
            </div>
        </div>

        <script>
            let matches = [];
            let currentIndex = -1;

            document.getElementById("searchInput").addEventListener("input", function() {
                let filter = this.value.toLowerCase();
                let mensagens = document.getElementsByClassName("mensagem");
                
                matches = [];
                currentIndex = -1;
                for (let i = 0; i < mensagens.length; i++) {
                    mensagens[i].classList.remove("msg-highlight", "msg-active");
                }

                if (filter.trim() === "") {
                    atualizarInterface(false);
                    return;
                }

                for (let i = 0; i < mensagens.length; i++) {
                    let textoMensagem = mensagens[i].innerText || mensagens[i].textContent;
                    if (textoMensagem.toLowerCase().indexOf(filter) > -1) {
                        mensagens[i].classList.add("msg-highlight");
                        matches.push(mensagens[i]);
                    }
                }

                if (matches.length > 0) {
                    currentIndex = 0;
                    atualizarInterface(true);
                    focarMensagem();
                } else {
                    atualizarInterface(false);
                }
            });

            function navegarBusca(direcao) {
                if (matches.length === 0) return;
                
                currentIndex += direcao;
                if (currentIndex < 0) currentIndex = matches.length - 1;
                if (currentIndex >= matches.length) currentIndex = 0;
                
                atualizarInterface(true);
                focarMensagem();
            }

            function atualizarInterface(temResultados) {
                let btnPrev = document.getElementById("btnPrev");
                let btnNext = document.getElementById("btnNext");
                let contador = document.getElementById("searchCount");
                
                if (temResultados) {
                    contador.innerText = (currentIndex + 1) + " / " + matches.length;
                    btnPrev.disabled = false;
                    btnNext.disabled = false;
                } else {
                    contador.innerText = "0 / 0";
                    btnPrev.disabled = true;
                    btnNext.disabled = true;
                }
            }

            function focarMensagem() {
                matches.forEach(m => m.classList.remove("msg-active"));
                
                let alvo = matches[currentIndex];
                alvo.classList.add("msg-active");
                alvo.scrollIntoView({behavior: "smooth", block: "center"});
            }
        </script>
    </body></html>
    """

    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(html_content)

# --- INTERFACE GRÁFICA (GUI) ---
class AppWhatsAppForensic:
    def __init__(self, root):
        self.root = root
        self.root.title("WhatsApp Constructor - Indexação e Transcrição Forense")
        self.root.geometry("600x750")
        self.root.configure(padx=20, pady=10)

        self.pasta_entrada = tk.StringVar()
        self.pasta_saida = tk.StringVar()
        self.usar_transcricao = tk.BooleanVar(value=False)
        self.modelo_selecionado = tk.StringVar(value="turbo")
        self.incluir_certidao = tk.BooleanVar(value=True) 
        
        self.nome_titular = tk.StringVar() # Variável para capturar o titular
        self.nome_relatorio = tk.StringVar(value="Evidencia_WhatsApp_01")
        
        self.nome_relator = tk.StringVar()
        self.cargo_relator = tk.StringVar()
        self.masp_relator = tk.StringVar()

        frame_ident = tk.LabelFrame(root, text="Dados do Relatório & Identificação", padx=10, pady=10)
        frame_ident.pack(fill="x", pady=(0, 10))

        # Checkbox para alternar a obrigatoriedade da certidão
        chk_cert = tk.Checkbutton(frame_ident, text="Incluir Certidão Pericial e Assinatura no PDF", 
                                  variable=self.incluir_certidao, command=self.toggle_certidao, font=("Arial", 9, "bold"))
        chk_cert.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Label(frame_ident, text="Nome da Exportação (Obrigatório):").grid(row=1, column=0, sticky="w", pady=(0,5))
        tk.Entry(frame_ident, textvariable=self.nome_relatorio, width=30).grid(row=1, column=1, padx=5, pady=(0,5), sticky="w")

        # --- NOVO CAMPO: Titular do Celular ---
        tk.Label(frame_ident, text="Titular do Celular (Fica na Direita):").grid(row=2, column=0, sticky="w", pady=(0,10))
        tk.Entry(frame_ident, textvariable=self.nome_titular, width=30).grid(row=2, column=1, padx=5, pady=(0,10), sticky="w")

        tk.Label(frame_ident, text="Nome do Policial/Relator:").grid(row=3, column=0, sticky="w")
        self.entry_nome = tk.Entry(frame_ident, textvariable=self.nome_relator, width=40)
        self.entry_nome.grid(row=3, column=1, padx=5, pady=2, sticky="w")

        tk.Label(frame_ident, text="Cargo:").grid(row=4, column=0, sticky="w")
        self.entry_cargo = tk.Entry(frame_ident, textvariable=self.cargo_relator, width=40)
        self.entry_cargo.grid(row=4, column=1, padx=5, pady=2, sticky="w")

        tk.Label(frame_ident, text="MASP/Matrícula:").grid(row=5, column=0, sticky="w")
        self.entry_masp = tk.Entry(frame_ident, textvariable=self.masp_relator, width=20)
        self.entry_masp.grid(row=5, column=1, padx=5, pady=2, sticky="w")

        frame_dir = tk.LabelFrame(root, text="Diretórios de Processamento", padx=10, pady=10)
        frame_dir.pack(fill="x", pady=(0, 10))

        tk.Label(frame_dir, text="Origem (Onde está a extração):", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w")
        tk.Entry(frame_dir, textvariable=self.pasta_entrada, state="readonly", width=42).grid(row=1, column=0, pady=(0,5))
        tk.Button(frame_dir, text="Procurar...", command=self.selecionar_entrada).grid(row=1, column=1, padx=(5,0), pady=(0,5))

        tk.Label(frame_dir, text="Destino (Onde os relatórios serão salvos):", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="w")
        tk.Entry(frame_dir, textvariable=self.pasta_saida, state="readonly", width=42).grid(row=3, column=0)
        tk.Button(frame_dir, text="Procurar...", command=self.selecionar_saida).grid(row=3, column=1, padx=(5,0))

        frame_transcricao = tk.LabelFrame(root, text="Extração de Áudio (Whisper Offline)", padx=10, pady=10)
        frame_transcricao.pack(fill="x", pady=(0, 10))
        
        chk_transcricao = tk.Checkbutton(frame_transcricao, text="Transcrever Áudios Localmente", 
                                         variable=self.usar_transcricao, command=self.toggle_opcoes_ia)
        chk_transcricao.pack(anchor="w")
        
        if not WHISPER_DISPONIVEL:
            chk_transcricao.config(state="disabled")
            tk.Label(frame_transcricao, text="Aviso: Biblioteca não instalada (pip install openai-whisper)", fg="red", font=("Arial", 8)).pack(anchor="w")

        frame_modelos = tk.Frame(frame_transcricao)
        frame_modelos.pack(fill="x", pady=(5,0))
        tk.Label(frame_modelos, text="Modelo da IA:").pack(side="left")
        
        modelos = ["medium", "turbo"]
        self.combo_modelos = ttk.Combobox(frame_modelos, values=modelos, textvariable=self.modelo_selecionado, state="disabled", width=15)
        self.combo_modelos.pack(side="left", padx=(10, 0))

        self.label_status = tk.Label(root, text="Pronto para iniciar.", fg="#555", font=("Arial", 9))
        self.label_status.pack(anchor="w")
        
        self.barra_progresso = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=560)
        self.barra_progresso.pack(fill="x", pady=(5, 10))

        self.btn_iniciar = tk.Button(root, text="Iniciar Processamento Forense", bg="#000000", fg="white", font=("Arial", 11, "bold"), 
                  command=self.iniciar_thread, height=2)
        self.btn_iniciar.pack(fill="x")

    def toggle_certidao(self):
        estado = "normal" if self.incluir_certidao.get() else "disabled"
        self.entry_nome.config(state=estado)
        self.entry_cargo.config(state=estado)
        self.entry_masp.config(state=estado)

    def toggle_opcoes_ia(self):
        if self.usar_transcricao.get():
            self.combo_modelos.config(state="readonly")
        else:
            self.combo_modelos.config(state="disabled")

    def selecionar_entrada(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta de origem")
        if pasta: self.pasta_entrada.set(pasta)

    def selecionar_saida(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta de destino")
        if pasta: self.pasta_saida.set(pasta)

    def atualizar_progresso(self, atual, total, mensagem):
        percentual = (atual / total) * 100 if total > 0 else 0
        self.root.after(0, self._set_gui_state, percentual, mensagem)

    def _set_gui_state(self, percentual, mensagem):
        self.barra_progresso["value"] = percentual
        self.label_status.config(text=f"{int(percentual)}% - {mensagem}")

    def iniciar_thread(self):
        entrada = self.pasta_entrada.get()
        saida = self.pasta_saida.get()

        if not entrada or not saida:
            messagebox.showwarning("Atenção", "Selecione as pastas de origem e destino.")
            return

        if not self.nome_relatorio.get():
            messagebox.showwarning("Atenção", "O Nome da Exportação é obrigatório.")
            return

        if self.incluir_certidao.get():
            if not self.nome_relator.get() or not self.cargo_relator.get() or not self.masp_relator.get():
                messagebox.showwarning("Atenção", "Preencha os dados do relator ou desmarque a opção de 'Incluir Certidão'.")
                return

        nome_limpo_relatorio = "".join(x for x in self.nome_relatorio.get() if x.isalnum() or x in "._- ")
        nome_limpo_relatorio = nome_limpo_relatorio.replace(" ", "_")

        self.btn_iniciar.config(state="disabled", bg="#999")
        
        dados_certidao = {
            "nome": self.nome_relator.get(),
            "cargo": self.cargo_relator.get(),
            "masp": self.masp_relator.get()
        }

        # Extrai o nome do titular digitado
        titular_informado = self.nome_titular.get().strip()

        thread = threading.Thread(target=self.executar_processo_background, args=(entrada, saida, dados_certidao, nome_limpo_relatorio, titular_informado))
        thread.start()

    def executar_processo_background(self, entrada, saida, dados_certidao, nome_relatorio, nome_titular_informado):
        try:
            processar_exportacao(
                entrada, 
                saida, 
                self.usar_transcricao.get(), 
                self.modelo_selecionado.get(),
                self.incluir_certidao.get(),
                dados_certidao,
                nome_relatorio,
                nome_titular_informado, # Passa o parâmetro pra frente
                self.atualizar_progresso
            )
            self.root.after(0, self.finalizar_sucesso, saida)
        except Exception as e:
            self.root.after(0, self.finalizar_erro, str(e))

    def finalizar_sucesso(self, pasta_saida):
        self.barra_progresso["value"] = 100
        self.label_status.config(text="100% - Processamento Concluído!")
        self.btn_iniciar.config(state="normal", bg="#128C7E")
        messagebox.showinfo("Sucesso", "Procedimento concluído!\n\nVerifique o PDF Pericial e o HTML na pasta de destino.")
        os.startfile(pasta_saida)

    def finalizar_erro(self, erro_msg):
        self.label_status.config(text="Erro durante o processamento.")
        self.btn_iniciar.config(state="normal", bg="#128C7E")
        messagebox.showerror("Erro de Processamento", f"Ocorreu um erro:\n{erro_msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppWhatsAppForensic(root)
    root.mainloop()