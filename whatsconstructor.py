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

# --- CLASSES DO GERADOR DE PDF PERICIAL ---
class RelatorioForensePDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 14)
        self.cell(0, 10, 'RELATÓRIO TÉCNICO DE INDEXAÇÃO E INTEGRIDADE DE DADOS', 0, 1, 'C')
        self.set_font('helvetica', 'I', 10)
        self.cell(0, 5, 'Extração Lógica - WhatsApp', 0, 1, 'C')
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
        "imutabilidade das provas. Para consolidar essa garantia, o sistema gera automaticamente um documento "
        "dedicado (identificado pelo sufixo '_Hashes_Gerais.txt'), que centraliza o resumo criptográfico dos "
        "principais artefatos processados. Transcrições de áudio, quando aplicáveis, são processadas offline."
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
        pdf.cell(0, 10, '4. CERTIDÃO DE EXTRAÇÃO E INDEXAÇÃO', 0, 1)
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
        
        # --- NOVO BLOCO DE ASSINATURA PROTEGIDO CONTRA QUEBRA DE PÁGINA ---
        if pdf.get_y() > 230:
            pdf.add_page()
        else:
            pdf.ln(20) 
            
        # Adicionando a Data Oficial alinhada à direita
        meses = {
            "01": "janeiro", "02": "fevereiro", "03": "março", "04": "abril",
            "05": "maio", "06": "junho", "07": "julho", "08": "agosto",
            "09": "setembro", "10": "outubro", "11": "novembro", "12": "dezembro"
        }
        partes_data = data_hora_atual.split(" ")[0].split("/")
        data_extenso = f"{partes_data[0]} de {meses[partes_data[1]]} de {partes_data[2]}"
        
        pdf.set_font('helvetica', '', 11)
        pdf.cell(0, 5, data_extenso, 0, 1, 'R')
        pdf.ln(25) # Espaço mais generoso para a assinatura física
        
        # Desenhando a linha e as credenciais centralizadas
        pdf.line(55, pdf.get_y(), 155, pdf.get_y())
        pdf.ln(2)
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(0, 5, f"{dados_certidao['nome'].upper()}", 0, 1, 'C')
        pdf.set_font('helvetica', '', 10)
        pdf.cell(0, 5, f"{dados_certidao['cargo']} - MASP/Matrícula: {dados_certidao['masp']}", 0, 1, 'C')
        
    pdf.output(caminho_saida)

def gerar_pdf_integrantes(caminho_saida, remetentes, nomes_extras, dados_certidao, data_hora_atual, incluir_certidao):
    pdf = RelatorioForensePDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, 'ANEXO - RELAÇÃO DE INTEGRANTES DA CONVERSA', 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('helvetica', '', 10)
    pdf.cell(0, 6, f"Data/Hora de Geração: {data_hora_atual}", 0, 1)
    pdf.cell(0, 6, f"Referência da Evidência: {nomes_extras['relatorio']}", 0, 1)
    pdf.ln(10)
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 8, f"Total de Interlocutores Identificados no Relatório: {len(remetentes)}", 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('helvetica', '', 11)
    for i, rem in enumerate(sorted(remetentes), 1):
        pdf.cell(0, 8, f"{i}. {rem}", 0, 1)
        
    if incluir_certidao:
        # --- NOVO BLOCO DE ASSINATURA PROTEGIDO ---
        if pdf.get_y() > 230:
            pdf.add_page()
        else:
            pdf.ln(20)
            
        meses = {
            "01": "janeiro", "02": "fevereiro", "03": "março", "04": "abril",
            "05": "maio", "06": "junho", "07": "julho", "08": "agosto",
            "09": "setembro", "10": "outubro", "11": "novembro", "12": "dezembro"
        }
        partes_data = data_hora_atual.split(" ")[0].split("/")
        data_extenso = f"{partes_data[0]} de {meses[partes_data[1]]} de {partes_data[2]}"
        
        pdf.set_font('helvetica', '', 11)
        pdf.cell(0, 5, data_extenso, 0, 1, 'R')
        pdf.ln(25) 

        pdf.line(55, pdf.get_y(), 155, pdf.get_y())
        pdf.ln(2)
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(0, 5, f"{dados_certidao['nome'].upper()}", 0, 1, 'C')
        pdf.set_font('helvetica', '', 10)
        pdf.cell(0, 5, f"{dados_certidao['cargo']} - MASP/Matrícula: {dados_certidao['masp']}", 0, 1, 'C')
        
    pdf.output(caminho_saida)

def processar_exportacao(pasta_entrada, pasta_saida, transcrever_audio, transcrever_video, nome_modelo, incluir_certidao, dados_certidao, nomes_extras, callback_progresso):
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

    arquivos_reais = []
    for r, d, files in os.walk(pasta_entrada):
        for f in files:
            if f.endswith(".txt") or f.lower() in ("desktop.ini", "thumbs.db", ".ds_store"):
                continue
            arquivos_reais.append(f)

    mensagens = []
    arquivos_midia_referenciados = []

    regex_android = r"^(\d{2}/\d{2}/\d{4}[ ,]+\d{2}:\d{2}(?::\d{2})?) - (.*?): (.*)"
    regex_ios = r"^\[(\d{2}/\d{2}/\d{4}[ ,]+\d{2}:\d{2}:\d{2})\] (.*?): (.*)"
    regex_android_sys = r"^(\d{2}/\d{2}/\d{4}[ ,]+\d{2}:\d{2}(?::\d{2})?) - (.*)"
    regex_ios_sys = r"^\[(\d{2}/\d{2}/\d{4}[ ,]+\d{2}:\d{2}:\d{2})\] (.*)"

    with open(arquivo_txt, 'r', encoding='utf-8') as f:
        for linha in f:
            linha_limpa = re.sub(r'[\u200e\u200f\u202a-\u202e\u200b]', '', linha).rstrip('\r\n')
            if not linha_limpa:
                continue

            match = re.match(regex_android, linha_limpa)
            if not match:
                match = re.match(regex_ios, linha_limpa)
                
            if match:
                timestamp, remetente, conteudo = match.groups()
                remetente_limpo = limpar_nome_arquivo(remetente)
                conteudo_limpo = conteudo.strip()
                
                msg_sistema_markers = [
                    "as mensagens e ligações são protegidas",
                    "messages and calls are end-to-end encrypted",
                    "está na sua lista de contatos",
                    "is on your contacts list"
                ]
                if any(m in conteudo_limpo.lower() for m in msg_sistema_markers):
                    mensagens.append({
                        "timestamp": timestamp,
                        "remetente": "",
                        "conteudo": conteudo_limpo,
                        "tipo": "sistema",
                        "nome_arquivo": None
                    })
                    continue 

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
                        nome_tentativa = conteudo_limpo
                        for m in marcadores:
                            nome_tentativa = re.sub(re.escape(m), '', nome_tentativa, flags=re.IGNORECASE)
                        nome_tentativa = nome_tentativa.replace('\u200e', '').replace('\u202a', '').replace('\u202c', '').strip(' ._')
                        
                        if nome_tentativa:
                            caminho_enc, nome_real_enc = encontrar_arquivo(nome_tentativa, pasta_entrada)
                            if caminho_enc:
                                nome_arquivo = nome_tentativa
                                tipo = "midia"
                            else:
                                match_arq = re.search(r'([a-zA-Z0-9_\-\s\.]+\.[\w_]*)', conteudo_limpo)
                                if match_arq:
                                    nome_arquivo = match_arq.group(1).strip()
                                    tipo = "midia"

                if nome_arquivo and nome_arquivo not in arquivos_midia_referenciados:
                    arquivos_midia_referenciados.append(nome_arquivo)

                mensagens.append({
                    "timestamp": timestamp,
                    "remetente": remetente_limpo,
                    "conteudo": conteudo_limpo,
                    "tipo": tipo,
                    "nome_arquivo": nome_arquivo
                })
            else:
                match_sys = re.match(regex_android_sys, linha_limpa)
                if not match_sys:
                    match_sys = re.match(regex_ios_sys, linha_limpa)
                
                if match_sys:
                    timestamp, conteudo_sys = match_sys.groups()
                    mensagens.append({
                        "timestamp": timestamp,
                        "remetente": "",
                        "conteudo": conteudo_sys.strip(),
                        "tipo": "sistema",
                        "nome_arquivo": None
                    })
                else:
                    if mensagens and mensagens[-1]["tipo"] != "sistema":
                        mensagens[-1]["conteudo"] += "\n" + linha_limpa

    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)

    pasta_midia_destino = os.path.join(pasta_saida, "midia")
    if not os.path.exists(pasta_midia_destino):
        os.makedirs(pasta_midia_destino)

    registro_hashes = []
    data_hora_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    mapa_nomes_reais = {}
    hash_txt = "N/A"

    nome_txt_origem = os.path.basename(arquivo_txt)
    caminho_txt_destino = os.path.join(pasta_saida, f"{nomes_extras['relatorio']}_{nome_txt_origem}")
    try:
        shutil.copy2(arquivo_txt, caminho_txt_destino)
        hash_txt = calcular_hash_sha256(caminho_txt_destino)
        registro_hashes.append(f"[FICHEIRO DE TEXTO ORIGEM] {os.path.basename(caminho_txt_destino)}\nSHA256: {hash_txt}\n")
    except Exception as e:
        registro_hashes.append(f"[FICHEIRO DE TEXTO ORIGEM] Falha ao copiar original: {e}\n")

    remetentes_validos = list(set(msg["remetente"] for msg in mensagens if msg.get("tipo") != "sistema" and msg.get("remetente")))

    extensoes_lista = []
    if transcrever_audio:
        extensoes_lista.extend(['.opus', '.mp3', '.ogg', '.wav', '.m4a'])
    if transcrever_video:
        extensoes_lista.extend(['.mp4', '.mov', '.avi'])
        
    extensoes_transcrever = tuple(extensoes_lista)
    usar_transcricao = bool(extensoes_transcrever)

    audios_para_transcrever = []
    if usar_transcricao:
        audios_para_transcrever = [m for m in arquivos_midia_referenciados if m.lower().endswith(extensoes_transcrever)]
        
    total_midias = len(arquivos_midia_referenciados)
    total_passos = total_midias + len(audios_para_transcrever)
    passos_concluidos = 0

    for nome_midia in arquivos_midia_referenciados:
        caminho_origem, nome_real = encontrar_arquivo(nome_midia, pasta_entrada)
        
        if caminho_origem:
            caminho_destino = os.path.join(pasta_midia_destino, nome_real)
            shutil.copy2(caminho_origem, caminho_destino)
            hash_arquivo = calcular_hash_sha256(caminho_destino)
            registro_hashes.append(f"midia/{nome_real}\nSHA256: {hash_arquivo}\n")
            mapa_nomes_reais[nome_midia] = "midia/" + nome_real
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
                if nome_real.lower().endswith(extensoes_transcrever):
                    caminho_destino = os.path.join(pasta_saida, *nome_real.split('/'))
                    
                    if os.path.exists(caminho_destino):
                        transcricoes_feitas += 1
                        if callback_progresso: 
                            callback_progresso(passos_concluidos, total_passos, f"A transcrever mídia {transcricoes_feitas}/{len(audios_para_transcrever)}...")
                        
                        try:
                            resultado = modelo_ia.transcribe(caminho_destino, language="pt", fp16=False)
                            texto_transcrito = resultado["text"].strip()
                            
                            ignorar_transcricao = False
                            if "segments" in resultado and resultado["segments"]:
                                no_speech_probs = [seg.get("no_speech_prob", 0.0) for seg in resultado["segments"]]
                                avg_no_speech = sum(no_speech_probs) / len(no_speech_probs)
                                if avg_no_speech > 0.60:
                                    ignorar_transcricao = True
                                    
                            if ignorar_transcricao or not texto_transcrito:
                                msg["transcricao"] = "[Mídia sem fala detectável]"
                            else:
                                msg["transcricao"] = texto_transcrito
                        except Exception as e:
                            msg["transcricao"] = f"[Erro na transcrição: {str(e)}]"
                        
                        passos_concluidos += 1

    if callback_progresso: callback_progresso(total_passos, total_passos, "A gerar relatórios finais...")

    nome_arquivo_html = f"{nomes_extras['relatorio']}_Leitor_Forense.html"
    nome_arquivo_pdf = f"{nomes_extras['relatorio']}_Relatorio_Análise.pdf"
    nome_arquivo_pdf_integrantes = f"{nomes_extras['relatorio']}_Relacao_Integrantes.pdf"

    # 1. Geração do HTML
    caminho_html = os.path.join(pasta_saida, nome_arquivo_html)
    gerar_html(mensagens, caminho_html, mapa_nomes_reais, nomes_extras, remetentes_validos)
    
    hash_html = calcular_hash_sha256(caminho_html)
    registro_hashes.append(f"\n[ARQUIVO RECONSTRUÍDO - HTML] {nome_arquivo_html}\nSHA256: {hash_html}\n")

    # 2. Geração do PDF de Integrantes (NOVO)
    caminho_pdf_integrantes = os.path.join(pasta_saida, nome_arquivo_pdf_integrantes)
    gerar_pdf_integrantes(
        caminho_pdf_integrantes, 
        remetentes_validos, 
        nomes_extras, 
        dados_certidao, 
        data_hora_atual, 
        incluir_certidao
    )
    hash_pdf_integrantes = calcular_hash_sha256(caminho_pdf_integrantes)
    registro_hashes.append(f"\n[ANEXO - RELAÇÃO DE INTEGRANTES] {nome_arquivo_pdf_integrantes}\nSHA256: {hash_pdf_integrantes}\n")

    # 3. Geração do PDF Principal de Análise
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

    # --- GERAÇÃO DO ARQUIVO TXT COM HASHES GERAIS ---
    hash_pdf = calcular_hash_sha256(caminho_pdf)
    nome_txt_hashes = f"{nomes_extras['relatorio']}_Hashes_Gerais.txt"
    caminho_txt_hashes = os.path.join(pasta_saida, nome_txt_hashes)
    
    conteudo_hashes = (
        f"===============================================================\n"
        f"          RESUMO GERAL DE INTEGRIDADE (HASH SHA-256)           \n"
        f"===============================================================\n\n"
        f"1. ARQUIVO DE TEXTO ORIGEM (Evidência Copiada)\n"
        f"   Nome: {os.path.basename(caminho_txt_destino)}\n"
        f"   Hash: {hash_txt}\n\n"
        f"2. LEITOR FORENSE RECONSTRUÍDO (Interface HTML Interativa)\n"
        f"   Nome: {nome_arquivo_html}\n"
        f"   Hash: {hash_html}\n\n"
        f"3. ANEXO - RELAÇÃO DE INTEGRANTES (Documento Auxiliar)\n"
        f"   Nome: {nome_arquivo_pdf_integrantes}\n"
        f"   Hash: {hash_pdf_integrantes}\n\n"
        f"4. RELATÓRIO ANÁLISE (Documento Formal)\n"
        f"   Nome: {nome_arquivo_pdf}\n"
        f"   Hash: {hash_pdf}\n\n"
        f"===============================================================\n"
        f"Nota: A listagem individual detalhada constando as assinaturas \n"
        f"digitais de todas as mídias anexas (imagens, áudios, vídeos) \n"
        f"encontra-se formalizada dentro do Relatório Análise (PDF).  \n"
        f"===============================================================\n"
    )
    
    with open(caminho_txt_hashes, "w", encoding="utf-8") as f:
        f.write(conteudo_hashes)

def gerar_html(lista_mensagens, caminho_saida, mapa_nomes, nomes_extras, remetentes_validos):
    titular_oficial = ""
    alvo2_oficial = ""
    
    if nomes_extras["titular_nome"]:
        nome_titular_limpo = nomes_extras["titular_nome"].strip().lower()
        for rem in remetentes_validos:
            if nome_titular_limpo in rem.lower():
                titular_oficial = rem
                break
                
    if not titular_oficial:
        for rem in remetentes_validos:
            if rem.lower() in ["você", "voce", "you"]:
                titular_oficial = rem
                break
                
    if not titular_oficial:
        for msg in lista_mensagens:
            if msg.get("tipo") != "sistema" and msg.get("remetente"):
                titular_oficial = msg["remetente"]
                break
                
    if nomes_extras["alvo2_nome"]:
        nome_alvo2_limpo = nomes_extras["alvo2_nome"].strip().lower()
        for rem in remetentes_validos:
            if nome_alvo2_limpo in rem.lower():
                alvo2_oficial = rem
                break

    cores_disponiveis = [
        "#53bdeb", "#ff7a7a", "#ff9f5e", "#d874ff", "#44c688", 
        "#ffb02e", "#c5a47e", "#9fa0ff", "#a370e7", "#ff6b9e", 
        "#65d1d6", "#a6e373", "#ffc83d", "#8da8b8"
    ]
    mapa_cores = {}
    i_cor = 0
    for rem in remetentes_validos:
        if rem != titular_oficial:
            mapa_cores[rem] = cores_disponiveis[i_cor % len(cores_disponiveis)]
            i_cor += 1

    nome_pdf_integrantes = f"{nomes_extras['relatorio']}_Relacao_Integrantes.pdf"

    html_content = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{nomes_extras["relatorio"]}</title>
        <style>
            body {{ font-family: 'Segoe UI', -apple-system, Arial, sans-serif; background-color: #111b21; margin: 0; padding: 0; color: #e9edef; }}
            
            .header {{ background-color: #202c33; color: #e9edef; position: sticky; top: 0; z-index: 1001; box-shadow: 0 2px 5px rgba(0,0,0,0.2); display: flex; flex-direction: column; border-bottom: 1px solid #2a3942; }}
            .header-info {{ padding: 15px 25px; }}
            .header-title {{ margin: 0; font-size: 18px; font-weight: 500; color: #e9edef; }}
            .header-subtitle {{ margin: 0; font-size: 12px; color: #8696a0; margin-top: 5px; }}
            
            .tab-buttons {{ display: flex; padding: 0 25px; background: #202c33; }}
            .tab-btn {{ background: none; border: none; color: #8696a0; padding: 12px 20px; cursor: pointer; font-size: 14px; font-weight: 600; border-bottom: 3px solid transparent; transition: all 0.2s; outline: none; }}
            .tab-btn:hover {{ color: #e9edef; background: rgba(255,255,255,0.05); }}
            .tab-btn.active {{ color: #00a884; border-bottom: 3px solid #00a884; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
            
            .main-wrapper {{ display: flex; width: 100%; align-items: flex-start; }}
            
            .sidebar {{ 
                width: 280px; min-width: 280px; background-color: #111b21; border-right: 1px solid #2a3942; 
                padding: 15px; height: calc(100vh - 75px); overflow-y: auto; position: sticky; top: 75px; 
                box-sizing: border-box; 
            }}
            
            .btn-export-list {{
                background-color: #00a884; color: #111b21; padding: 12px; border-radius: 8px; border: none; width: 100%;
                cursor: pointer; font-weight: bold; font-size: 13px; margin-bottom: 20px; text-transform: uppercase;
                transition: background 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                display: block; text-align: center; text-decoration: none; box-sizing: border-box; /* Adicionado para suportar tag <a> */
            }}
            .btn-export-list:hover {{ background-color: #00c298; }}
            
            .sidebar-title {{ color: #8696a0; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }}
            
            .participant-item {{
                padding: 10px 12px; border-radius: 8px; color: #e9edef; font-size: 14px; margin-bottom: 5px;
                cursor: pointer; transition: all 0.2s; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            }}
            .participant-item:hover {{ background-color: #202c33; }}
            .participant-item.active-filter {{ background-color: #202c33; color: #00a884; font-weight: 600; border-left: 4px solid #00a884; border-radius: 4px; }}
            
            .chat-area {{ flex-grow: 1; padding: 20px; max-width: 950px; margin: 0 auto; box-sizing: border-box; }}
            
            .search-bar-container {{ 
                position: sticky; top: 90px; 
                background: #202c33; 
                padding: 12px 18px; border-radius: 12px; 
                box-shadow: 0 6px 16px rgba(0,0,0,0.4); 
                display: flex; gap: 15px; align-items: center; justify-content: space-between;
                z-index: 1000; margin-bottom: 25px; flex-wrap: wrap; 
                border: 1px solid #2a3942;
            }}
            .filter-group {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
            .divider {{ width: 1px; height: 24px; background: #2a3942; margin: 0 4px; }}
            
            .search-box {{ 
                padding: 9px 16px; border: 1px solid #2a3942; border-radius: 20px; 
                font-size: 13px; outline: none; background-color: #2a3942; 
                color: #e9edef; transition: all 0.3s; min-width: 220px;
            }}
            .search-box::placeholder {{ color: #8696a0; }}
            .search-box:focus {{ background-color: #111b21; border-color: #00a884; box-shadow: 0 0 0 1px #00a884; }}
            
            .date-input {{ 
                padding: 8px 12px; border: 1px solid #2a3942; border-radius: 8px; 
                font-size: 13px; background-color: #2a3942; color: #e9edef; outline: none; 
                color-scheme: dark; 
            }}
            .date-input:focus {{ border-color: #00a884; }}
            
            .search-count {{ font-weight: 600; color: #8696a0; min-width: 50px; text-align: center; font-size: 13px; }}

            .btn-icon {{
                background: #2a3942; color: #8696a0; border: none; border-radius: 50%;
                width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
                cursor: pointer; transition: all 0.2s; font-size: 12px;
            }}
            .btn-icon:hover:not(:disabled) {{ background: #3a4b55; color: #e9edef; }}
            .btn-icon:disabled {{ opacity: 0.3; cursor: not-allowed; }}

            .btn-nav {{ padding: 8px 16px; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 13px; transition: all 0.2s; white-space: nowrap; }}
            
            .btn-filter {{ background-color: #00a884; color: #111b21; }}
            .btn-filter:hover {{ background-color: #00c298; }}
            
            .btn-clear {{ background-color: #374151; color: #e9edef; }}
            .btn-clear:hover {{ background-color: #ef4444; color: white; }}
            
            .btn-pdf {{ background-color: #005c4b; color: white; margin-left: auto; }}
            .btn-pdf:hover {{ background-color: #00735e; }}
            
            .date-label {{ color: #8696a0; font-size: 13px; font-weight: 500; }}

            .msg-wrapper {{ display: flex; margin-bottom: 6px; width: 100%; }}
            .titular {{ justify-content: flex-end; }}
            .outro {{ justify-content: flex-start; }}
            .sistema-wrapper {{ justify-content: center; margin: 15px 0; }}
            
            .mensagem {{ padding: 8px 12px 6px 12px; border-radius: 8px; max-width: 70%; position: relative; box-shadow: 0 1px 1px rgba(0,0,0,0.2); font-size: 14.5px; word-wrap: break-word; }}
            .titular .mensagem {{ background-color: #005c4b; border-top-right-radius: 0; }}
            .outro .mensagem {{ background-color: #202c33; border-top-left-radius: 0; }}
            .msg-sistema {{ background-color: #182229; color: #8696a0; font-size: 12.5px; padding: 6px 14px; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); max-width: 85%; text-align: center; border: 1px solid #2a3942; }}
            
            .remetente {{ font-weight: 600; font-size: 12.5px; margin-bottom: 4px; display: block; }}
            .texto {{ color: #e9edef; line-height: 1.45; white-space: pre-wrap; }}
            .timestamp {{ font-size: 10.5px; color: #8696a0; text-align: right; margin-top: 4px; display: block; }}
            
            .caixa-transcricao {{ margin-top: 8px; padding: 8px 12px; background-color: #182229; border-left: 4px solid #00a884; border-radius: 4px; font-size: 13px; color: #aebac1; font-style: italic; }}
            
            .media-box {{ margin-top: 6px; margin-bottom: 4px; display: block; }}
            .media-box img, .media-box video {{ max-width: 100%; max-height: 360px; border-radius: 6px; display: block; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }}
            .media-box audio {{ width: 280px; display: block; margin-top: 5px; }}
            
            .msg-highlight {{ border: 2px solid #00a884 !important; background-color: rgba(0, 168, 132, 0.15) !important; }}
            .msg-active {{ box-shadow: 0 0 15px 5px rgba(0, 168, 132, 0.4) !important; }}
            
            .galeria-container {{ max-width: 1100px; margin: 0 auto; padding: 25px; }}
            .galeria-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; }}
            .galeria-item {{ background: #202c33; padding: 12px; border-radius: 10px; box-shadow: 0 3px 6px rgba(0,0,0,0.2); display: flex; flex-direction: column; justify-content: space-between; align-items: center; text-align: center; transition: transform 0.2s; border: 1px solid #2a3942; }}
            .galeria-item:hover {{ transform: translateY(-3px); box-shadow: 0 6px 12px rgba(0,0,0,0.3); border-color: #00a884; }}
            .galeria-item img, .galeria-item video {{ max-width: 100%; max-height: 160px; border-radius: 6px; object-fit: cover; }}
            .galeria-item audio {{ width: 100%; margin-top: 10px; }}
            .galeria-meta {{ font-size: 12px; color: #8696a0; margin-top: 12px; font-weight: 500; border-top: 1px solid #2a3942; padding-top: 8px; width: 100%; }}
            .doc-icon {{ font-size: 35px; word-break: break-all; margin: 20px 0; }}
            .doc-icon a {{ font-size: 13px; text-decoration: none; color: #00a884; display: block; margin-top: 8px; }}
            
            @media (max-width: 900px) {{
                .main-wrapper {{ flex-direction: column; }}
                .sidebar {{ width: 100%; height: auto; border-right: none; border-bottom: 1px solid #2a3942; position: relative; top: 0; }}
            }}
            
            @media print {{
                .header, .search-bar-container, .tab-buttons, .sidebar {{ display: none !important; }}
                body {{ background-color: white !important; color: black !important; }}
                .chat-container, .chat-area {{ padding: 0 !important; max-width: 100% !important; }}
                .msg-wrapper {{ page-break-inside: avoid; }}
                .mensagem {{ box-shadow: none !important; border: 1px solid #ddd; background-color: white !important; }}
                .texto, .timestamp, .remetente {{ color: black !important; }}
                .media-box audio, .media-box video {{ display: none !important; }}
                .tab-content {{ display: block !important; }} 
                #tab-galeria {{ display: none !important; }} 
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-info">
                <h2 class="header-title">{nomes_extras["relatorio"]} - Leitor Forense</h2>
                <p class="header-subtitle">Integridade e Cadeia de Custódia Assegurada por Hash Cryptográfico</p>
            </div>
            <div class="tab-buttons">
                <button id="btn-tab-chat" class="tab-btn active" onclick="openTab('chat')">💬 Conversação</button>
                <button id="btn-tab-galeria" class="tab-btn" onclick="openTab('galeria')">🖼️ Galeria de Mídias</button>
            </div>
        </div>
        
        <div id="tab-chat" class="tab-content active">
            <div class="main-wrapper">
                
                <div class="sidebar">
                    <a href="{nome_pdf_integrantes}" target="_blank" class="btn-export-list">📄 Exportar Lista (PDF)</a>
                    <h3 class="sidebar-title">Integrantes ({len(remetentes_validos)})</h3>
                    <div class="participant-item active-filter" onclick="filtrarRemetente('TODOS')" data-id="TODOS">🧾 Exibir Todos</div>
    """
    
    for rem in sorted(remetentes_validos):
        rem_safe = rem.replace("'", "\\'").replace('"', '&quot;')
        html_content += f'<div class="participant-item" onclick="filtrarRemetente(\'{rem_safe}\')" data-id="{rem_safe}">👤 {rem}</div>'
    
    html_content += f"""
                </div>
                
                <div class="chat-area">
                    <div class="search-bar-container">
                        <div class="filter-group">
                            <input type="text" id="searchInput" class="search-box" placeholder="🔍 Localizar na conversa...">
                            <span id="searchCount" class="search-count">0/0</span>
                            <button id="btnPrev" class="btn-icon" disabled onclick="navegarBusca(-1)">▲</button>
                            <button id="btnNext" class="btn-icon" disabled onclick="navegarBusca(1)">▼</button>
                        </div>
                        
                        <div class="divider"></div>
                        
                        <div class="filter-group">
                            <input type="date" id="dataInicio" class="date-input" title="Data Inicial">
                            <span class="date-label">até</span>
                            <input type="date" id="dataFim" class="date-input" title="Data Final">
                            <button class="btn-nav btn-filter" onclick="aplicarFiltrosGerais()">Filtrar</button>
                            <button class="btn-nav btn-clear" onclick="limparFiltros()">Limpar</button>
                        </div>
                        
                        <div class="filter-group" style="margin-left: auto;">
                            <button class="btn-nav btn-pdf" onclick="window.print()">🖨️ Salvar Chat PDF</button>
                        </div>
                    </div>
                    
                    <div id="mensagens-container">
    """

    chat_html = ""
    galeria_html = '<div class="galeria-container"><div class="galeria-grid">'
    
    for msg in lista_mensagens:
        rem_attr = msg["remetente"].replace("'", "\\'").replace('"', '&quot;') if msg.get("remetente") else ""
        
        if msg.get("tipo") == "sistema":
            chat_html += f'<div class="msg-wrapper sistema-wrapper" data-remetente=""><div class="msg-sistema">{msg["conteudo"]}</div></div>'
        else:
            classe_lado = "titular" if msg["remetente"] == titular_oficial else "outro"
            cor_rem = mapa_cores.get(msg["remetente"], "#53bdeb")
            
            nome_exibicao = msg["remetente"]
            if msg["remetente"] == titular_oficial and nomes_extras["titular_sufixo"]:
                nome_exibicao = f"{msg['remetente']} ({nomes_extras['titular_sufixo']})"
            elif alvo2_oficial and msg["remetente"] == alvo2_oficial and nomes_extras["alvo2_sufixo"]:
                nome_exibicao = f"{msg['remetente']} ({nomes_extras['alvo2_sufixo']})"

            chat_html += f'<div class="msg-wrapper {classe_lado}" data-remetente="{rem_attr}"><div class="mensagem" id="msg-{lista_mensagens.index(msg)}">'
            
            if classe_lado == "outro":
                chat_html += f'<span class="remetente" style="color: {cor_rem};">{nome_exibicao}</span>'
            else:
                chat_html += f'<span class="remetente" style="color: #61d3a3;">{nome_exibicao}</span>'
            
            if msg["tipo"] == "midia":
                nome_arq = mapa_nomes.get(msg["nome_arquivo"], msg["nome_arquivo"])
                extensao = nome_arq.lower()
                
                galeria_html += '<div class="galeria-item">'
                if extensao.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    chat_html += f'<div class="media-box"><a href="{nome_arq}" target="_blank"><img src="{nome_arq}" alt="Imagem" /></a></div>'
                    galeria_html += f'<a href="{nome_arq}" target="_blank"><img src="{nome_arq}" loading="lazy"/></a>'
                elif extensao.endswith(('.mp4', '.mov', '.avi')):
                    chat_html += f'<div class="media-box"><video controls><source src="{nome_arq}"></video></div>'
                    galeria_html += f'<video controls preload="metadata"><source src="{nome_arq}"></video>'
                elif extensao.endswith(('.opus', '.mp3', '.ogg', '.wav', '.m4a')):
                    chat_html += f'<div class="media-box"><audio controls><source src="{nome_arq}"></audio></div>'
                    galeria_html += f'<audio controls preload="metadata"><source src="{nome_arq}"></audio>'
                else:
                    chat_html += f'<div class="media-box"><div class="texto">📎 <a href="{nome_arq}" target="_blank">{nome_arq}</a></div></div>'
                    nome_curto = nome_arq[:25] + '...' if len(nome_arq) > 25 else nome_arq
                    galeria_html += f'<div class="doc-icon">📎<br><a href="{nome_arq}" target="_blank" title="{nome_arq}">{nome_curto}</a></div>'
                
                galeria_html += f'<div class="galeria-meta">{nome_exibicao}<br>{msg["timestamp"]}</div>'
                galeria_html += '</div>'
                
                if "transcricao" in msg and msg["transcricao"]:
                    chat_html += f'<div class="caixa-transcricao">📝 IA TRANSCRIÇÃO (OFFLINE): "{msg["transcricao"]}"</div>'
            else:
                chat_html += f'<div class="texto">{msg["conteudo"]}</div>'
                
            chat_html += f'<span class="timestamp">{msg["timestamp"]}</span></div></div>'
    
    galeria_html += '</div></div>' 
    
    html_content += chat_html
    
    html_content += f"""
                    </div>
                </div>
            </div>
        </div>
        
        <div id="tab-galeria" class="tab-content">
    """
    
    html_content += galeria_html
    
    html_content += """
        </div>

        <script>
            function openTab(tabName) {
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
                
                document.getElementById('tab-' + tabName).classList.add('active');
                document.getElementById('btn-tab-' + tabName).classList.add('active');
            }


            let matches = [];
            let currentIndex = -1;
            let currentRemetente = 'TODOS';

            function filtrarRemetente(remetente) {
                currentRemetente = remetente;
                document.querySelectorAll('.participant-item').forEach(el => el.classList.remove('active-filter'));
                
                let items = document.querySelectorAll('.participant-item');
                for(let i=0; i<items.length; i++){
                    if(items[i].getAttribute('data-id') === remetente){
                        items[i].classList.add('active-filter');
                        break;
                    }
                }
                aplicarFiltrosGerais();
            }

            function aplicarFiltrosGerais() {
                let strInicio = document.getElementById("dataInicio").value;
                let strFim = document.getElementById("dataFim").value;
                let textoBusca = document.getElementById("searchInput").value.toLowerCase().trim();
                
                let dataInicio = strInicio ? new Date(strInicio + "T00:00:00") : null;
                let dataFim = strFim ? new Date(strFim + "T23:59:59") : null;
                
                let wrappers = document.getElementsByClassName("msg-wrapper");
                matches = [];
                currentIndex = -1;
                
                for(let i = 0; i < wrappers.length; i++) {
                    let wrap = wrappers[i];
                    let isSistema = wrap.classList.contains("sistema-wrapper");
                    let msgRemetente = wrap.getAttribute("data-remetente");
                    
                    let passaRemetente = true;
                    if (currentRemetente !== 'TODOS') {
                        if (isSistema || msgRemetente !== currentRemetente) {
                            passaRemetente = false;
                        }
                    }
                    
                    let passaData = true;
                    if (!isSistema) {
                        let timeSpan = wrap.querySelector(".timestamp");
                        if (timeSpan) {
                            let timeText = timeSpan.innerText.trim();
                            let datePart = timeText.split(" ")[0].replace("[", "").replace(",", "");
                            let partes = datePart.split("/");
                            if (partes.length === 3) {
                                let msgData = new Date(partes[2], partes[1] - 1, partes[0]);
                                if (dataInicio && msgData < dataInicio) passaData = false;
                                if (dataFim && msgData > dataFim) passaData = false;
                            }
                        }
                    }
                    
                    let mostrar = passaRemetente && passaData;
                    wrap.style.display = mostrar ? "flex" : "none";
                    
                    let msgBox = wrap.querySelector('.mensagem') || wrap.querySelector('.msg-sistema');
                    if (msgBox) msgBox.classList.remove("msg-highlight", "msg-active");
                    
                    if (mostrar && textoBusca !== "" && msgBox) {
                        let texto = msgBox.innerText || msgBox.textContent;
                        if (texto.toLowerCase().indexOf(textoBusca) > -1) {
                            msgBox.classList.add("msg-highlight");
                            matches.push(msgBox);
                        }
                    }
                }
                
                if (textoBusca !== "") {
                    if (matches.length > 0) {
                        currentIndex = 0;
                        atualizarInterfaceBusca(true);
                        focarMensagem();
                    } else {
                        atualizarInterfaceBusca(false);
                    }
                } else {
                    document.getElementById("searchCount").innerText = "0/0";
                    document.getElementById("btnPrev").disabled = true;
                    document.getElementById("btnNext").disabled = true;
                }
            }

            function limparFiltros() {
                document.getElementById("dataInicio").value = "";
                document.getElementById("dataFim").value = "";
                document.getElementById("searchInput").value = "";
                filtrarRemetente('TODOS');
            }

            document.getElementById("searchInput").addEventListener("input", aplicarFiltrosGerais);

            function navegarBusca(direcao) {
                if (matches.length === 0) return;
                currentIndex += direcao;
                if (currentIndex < 0) currentIndex = matches.length - 1;
                if (currentIndex >= matches.length) currentIndex = 0;
                atualizarInterfaceBusca(true);
                focarMensagem();
            }

            function atualizarInterfaceBusca(temResultados) {
                let btnPrev = document.getElementById("btnPrev");
                let btnNext = document.getElementById("btnNext");
                let contador = document.getElementById("searchCount");
                
                if (temResultados) {
                    contador.innerText = (currentIndex + 1) + " / " + matches.length;
                    btnPrev.disabled = false;
                    btnNext.disabled = false;
                } else {
                    contador.innerText = "0/0";
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

# --- CLASSE PARA OS BALÕES DE AJUDA (TOOLTIPS) ---
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True) # Remove as bordas da janela
        tw.wm_geometry(f"+{x}+{y}")
        
        # Estilo da caixinha de ajuda
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#202c33", foreground="#e9edef", # Cores escuras para combinar com o seu tema
                         relief='solid', borderwidth=1,
                         font=("Segoe UI", 9, "normal"), padx=8, pady=4)
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

# --- INTERFACE GRÁFICA (GUI) ---
class AppWhatsAppForensic:
    def __init__(self, root):
        self.root = root
        self.root.title("WhatsApp Constructor - Indexação Forense")
        self.root.geometry("680x880") 
        self.root.configure(bg="#f4f6f9")

        self.pasta_entrada = tk.StringVar()
        self.pasta_saida = tk.StringVar()
        self.usar_transcricao_audio = tk.BooleanVar(value=False)
        self.usar_transcricao_video = tk.BooleanVar(value=False)
        self.modelo_selecionado = tk.StringVar(value="turbo")
        self.incluir_certidao = tk.BooleanVar(value=True) 
        self.nome_relatorio = tk.StringVar(value="Evidencia_WhatsApp_01")
        self.nome_titular = tk.StringVar()
        self.sufixo_titular = tk.StringVar()
        self.nome_alvo2 = tk.StringVar()
        self.sufixo_alvo2 = tk.StringVar()
        self.nome_relator = tk.StringVar()
        self.cargo_relator = tk.StringVar()
        self.masp_relator = tk.StringVar()

        self.estilizar_interface()

        self.main_container = tk.Frame(root, bg="#f4f6f9")
        self.main_container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.main_container, bg="#f4f6f9", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_frame = tk.Frame(self.canvas, bg="#f4f6f9", padx=20, pady=15)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )

        def _on_mousewheel(event):
            if event.delta:
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.root.bind_all("<MouseWheel>", _on_mousewheel)

        frame_ident = tk.LabelFrame(self.scrollable_frame, text=" Dados do Relatório & Certidão ", padx=15, pady=10, bg="white", fg="#075e54", font=("Segoe UI", 10, "bold"), bd=1, relief="solid")
        frame_ident.pack(fill="x", pady=(0, 10))

        chk_cert = tk.Checkbutton(frame_ident, text="Incluir Certidão Análise e Assinatura no PDF", 
                                  variable=self.incluir_certidao, command=self.toggle_certidao, 
                                  bg="white", activebackground="white", fg="#111b21", font=("Segoe UI", 9, "bold"))
        chk_cert.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.criar_label_entry(frame_ident, "Nome da Exportação (Obrigatório):", self.nome_relatorio, 1, 35)
        self.criar_label_entry(frame_ident, "Nome do Policial/Relator:", self.nome_relator, 2, 45)
        self.criar_label_entry(frame_ident, "Cargo / Função:", self.cargo_relator, 3, 45)
        self.criar_label_entry(frame_ident, "MASP / Matrícula:", self.masp_relator, 4, 25)

        frame_alvos = tk.LabelFrame(self.scrollable_frame, text=" Identificação de Alvos no HTML  ", padx=15, pady=10, bg="white", fg="#075e54", font=("Segoe UI", 10, "bold"), bd=1, relief="solid")
        frame_alvos.pack(fill="x", pady=(0, 10))
        
        # Textos explicativos para as Tooltips
        dica_titular = "O Titular é o dono do aparelho periciado.\nAs mensagens dele aparecerão alinhadas à direita\n(cor verde), simulando a tela real do aplicativo."
        dica_sufixo_titular = "Um texto opcional que aparecerá ao lado do nome do titular\nno relatório. Ex: João (Alvo Principal) ou João (551199999999)"
        dica_alvo2 = "Identifica automaticamente um alvo específico\nna lista de contatos, destacando o nome dele nas conversas."
        
        self.criar_label_entry(frame_alvos, "Titular (Fica na Direita):", self.nome_titular, 0, 30, tooltip_text=dica_titular)
        self.criar_label_entry(frame_alvos, "Adicionar à frente do Titular: (Opcional)", self.sufixo_titular, 1, 30, "(Ex: Número de Telefone)", tooltip_text=dica_sufixo_titular)
        
        ttk.Separator(frame_alvos, orient='horizontal').grid(row=2, column=0, columnspan=3, sticky='ew', pady=8)
        
        self.criar_label_entry(frame_alvos, "Nome 2º Alvo (Opcional):", self.nome_alvo2, 3, 30, "(Digite apenas parte do nome)", tooltip_text=dica_alvo2)
        self.criar_label_entry(frame_alvos, "Adicionar à frente do 2º Alvo: (Opcional)", self.sufixo_alvo2, 4, 30, "(Ex: Alvo Secundário)")

        frame_dir = tk.LabelFrame(self.scrollable_frame, text=" Diretórios de Processamento ", padx=15, pady=10, bg="white", fg="#075e54", font=("Segoe UI", 10, "bold"), bd=1, relief="solid")
        frame_dir.pack(fill="x", pady=(0, 10))

        tk.Label(frame_dir, text="Origem (Pasta com txt):", bg="white", fg="#333333", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        entry_ent = tk.Entry(frame_dir, textvariable=self.pasta_entrada, state="readonly", width=48, font=("Segoe UI", 10), bg="#f8f9fa", relief="flat", bd=2)
        entry_ent.grid(row=1, column=0, pady=(2, 6), sticky="w")
        tk.Button(frame_dir, text="Procurar...", command=self.selecionar_entrada, bg="#e1e9eb", fg="#075e54", activebackground="#d2dfdf", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").grid(row=1, column=1, padx=(10, 0), pady=(2, 6))

        tk.Label(frame_dir, text="Destino (Onde os relatórios serão gravados):", bg="white", fg="#333333", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w")
        entry_sai = tk.Entry(frame_dir, textvariable=self.pasta_saida, state="readonly", width=48, font=("Segoe UI", 10), bg="#f8f9fa", relief="flat", bd=2)
        entry_sai.grid(row=3, column=0, pady=(2, 2), sticky="w")
        tk.Button(frame_dir, text="Procurar...", command=self.selecionar_saida, bg="#e1e9eb", fg="#075e54", activebackground="#d2dfdf", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").grid(row=3, column=1, padx=(10, 0), pady=(2, 2))

        frame_transcricao = tk.LabelFrame(self.scrollable_frame, text=" Transcrição de Mídia (Whisper Offline) ", padx=15, pady=10, bg="white", fg="#075e54", font=("Segoe UI", 10, "bold"), bd=1, relief="solid")
        frame_transcricao.pack(fill="x", pady=(0, 10))
        
        chk_transcricao_audio = tk.Checkbutton(frame_transcricao, text="Transcrever Áudios Localmente", 
                                         variable=self.usar_transcricao_audio, command=self.toggle_opcoes_ia,
                                         bg="white", activebackground="white", fg="#111b21", font=("Segoe UI", 10))
        chk_transcricao_audio.pack(anchor="w", pady=(0, 2))

        chk_transcricao_video = tk.Checkbutton(frame_transcricao, text="Transcrever Vídeos (Pode ser muito demorado)", 
                                         variable=self.usar_transcricao_video, command=self.toggle_opcoes_ia,
                                         bg="white", activebackground="white", fg="#111b21", font=("Segoe UI", 10))
        chk_transcricao_video.pack(anchor="w", pady=(0, 5))
        
        if not WHISPER_DISPONIVEL:
            chk_transcricao_audio.config(state="disabled")
            chk_transcricao_video.config(state="disabled")
            tk.Label(frame_transcricao, text="Aviso: Whisper não instalado.", fg="#dc3545", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")

        frame_modelos = tk.Frame(frame_transcricao, bg="white")
        frame_modelos.pack(fill="x", pady=(5, 0))
        tk.Label(frame_modelos, text="Modelo da IA Whisper:", bg="white", fg="#333333", font=("Segoe UI", 9)).pack(side="left")
        
        self.combo_modelos = ttk.Combobox(frame_modelos, values=["medium", "turbo"], textvariable=self.modelo_selecionado, state="disabled", width=12)
        self.combo_modelos.pack(side="left", padx=(10, 0))

        self.label_status = tk.Label(self.scrollable_frame, text="Pronto para iniciar.", fg="#5c6f78", bg="#f4f6f9", font=("Segoe UI", 10, "italic"))
        self.label_status.pack(anchor="w", pady=(2, 0))
        
        self.barra_progresso = ttk.Progressbar(self.scrollable_frame, orient="horizontal", mode="determinate")
        self.barra_progresso.pack(fill="x", pady=(5, 15))

        self.btn_iniciar = tk.Button(self.scrollable_frame, text="Iniciar Processamento Forense", bg="#128C7E", fg="white", 
                                     activebackground="#0b665c", activeforeground="white", font=("Segoe UI", 11, "bold"), 
                                     relief="flat", command=self.iniciar_thread, height=2, cursor="hand2")
        self.btn_iniciar.pack(fill="x")
        
        tk.Label(self.scrollable_frame, text="Desenvolvido por Gabriel Henrique Bueno", 
                 bg="#f4f6f9", fg="#a0aab2", font=("Segoe UI", 8, "italic")).pack(pady=(15, 5))

    def estilizar_interface(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TProgressbar', thickness=15, troughcolor="#e1e9eb", background="#128C7E")
        style.configure('TCombobox', font=('Segoe UI', 9))

    def criar_label_entry(self, parent, text, var, row, width, hint="", tooltip_text=""):
        # Cria um sub-frame para agrupar o texto principal e o ícone de interrogação
        frame_lbl = tk.Frame(parent, bg="white")
        frame_lbl.grid(row=row, column=0, sticky="w", pady=3)
        
        tk.Label(frame_lbl, text=text, bg="white", fg="#333333", font=("Segoe UI", 9)).pack(side="left")
        
        # Se um texto de ajuda for passado, cria o ícone [?]
        if tooltip_text:
            lbl_help = tk.Label(frame_lbl, text="[?]", bg="white", fg="#128C7E", font=("Segoe UI", 9, "bold"), cursor="question_arrow")
            lbl_help.pack(side="left", padx=(5, 0))
            ToolTip(lbl_help, tooltip_text) # Atrela a caixinha flutuante ao ícone
            
        entry = tk.Entry(parent, textvariable=var, width=width, font=("Segoe UI", 10), relief="solid", bd=1)
        entry.grid(row=row, column=1, padx=12, pady=3, sticky="w")
        
        if hint:
            tk.Label(parent, text=hint, bg="white", fg="#7f8c8d", font=("Segoe UI", 8, "italic")).grid(row=row, column=2, sticky="w")

        if text.startswith("Nome do Policial"): self.entry_nome = entry
        elif text.startswith("Cargo"): self.entry_cargo = entry
        elif text.startswith("MASP"): self.entry_masp = entry

    def toggle_certidao(self):
        estado = "normal" if self.incluir_certidao.get() else "disabled"
        bg_color = "white" if self.incluir_certidao.get() else "#f1f3f5"
        self.entry_nome.config(state=estado, bg=bg_color)
        self.entry_cargo.config(state=estado, bg=bg_color)
        self.entry_masp.config(state=estado, bg=bg_color)

    def toggle_opcoes_ia(self):
        if self.usar_transcricao_audio.get() or self.usar_transcricao_video.get():
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

        self.btn_iniciar.config(state="disabled", bg="#95a5a6")
        
        dados_certidao = {
            "nome": self.nome_relator.get(),
            "cargo": self.cargo_relator.get(),
            "masp": self.masp_relator.get()
        }

        nomes_extras = {
            "relatorio": nome_limpo_relatorio,
            "titular_nome": self.nome_titular.get(),
            "titular_sufixo": self.sufixo_titular.get().strip(),
            "alvo2_nome": self.nome_alvo2.get(),
            "alvo2_sufixo": self.sufixo_alvo2.get().strip()
        }

        thread = threading.Thread(target=self.executar_processo_background, args=(entrada, saida, dados_certidao, nomes_extras))
        thread.start()

    def executar_processo_background(self, entrada, saida, dados_certidao, nomes_extras):
        try:
            processar_exportacao(
                entrada, 
                saida, 
                self.usar_transcricao_audio.get(), 
                self.usar_transcricao_video.get(),
                self.modelo_selecionado.get(),
                self.incluir_certidao.get(),
                dados_certidao,
                nomes_extras,
                self.atualizar_progresso
            )
            self.root.after(0, self.finalizar_sucesso, saida)
        except Exception as e:
            self.root.after(0, self.finalizar_erro, str(e))

    def finalizar_sucesso(self, pasta_saida):
        self.barra_progresso["value"] = 100
        self.label_status.config(text="100% - Processamento Concluído!")
        self.btn_iniciar.config(state="normal", bg="#128C7E")
        messagebox.showinfo("Sucesso", "Procedimento concluído!\n\nVerifique o PDF Análise e o HTML na pasta de destino.")
        os.startfile(pasta_saida)

    def finalizar_erro(self, erro_msg):
        self.label_status.config(text="Erro durante o processamento.")
        self.btn_iniciar.config(state="normal", bg="#128C7E")
        messagebox.showerror("Erro de Processamento", f"Ocorreu um erro:\n{erro_msg}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppWhatsAppForensic(root)
    root.mainloop()