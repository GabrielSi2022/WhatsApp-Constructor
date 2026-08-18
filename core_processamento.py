import os
import re
import sys
import shutil
from datetime import datetime

# Importa as dependências dos outros módulos locais
from utils import encontrar_arquivo, limpar_nome_arquivo, calcular_hash_sha256
from gerador_pdf import gerar_pdf_pericial, gerar_pdf_integrantes
from gerador_html import gerar_html

try:
    import whisper
    WHISPER_DISPONIVEL = True
except ImportError:
    WHISPER_DISPONIVEL = False

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

def processar_exportacao(pasta_entrada, pasta_saida, transcrever_audio, transcrever_video, nome_modelo, incluir_certidao, dados_certidao, dados_aparelho, nomes_extras, callback_progresso):
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

    regex_android = r"^(\d{2}/\d{2}/\d{2,4}[ ,]+\d{2}:\d{2}(?::\d{2})?) - (.*?): (.*)"
    regex_ios = r"^\[(\d{2}/\d{2}/\d{2,4}[ ,]+\d{2}:\d{2}:\d{2})\] (.*?): (.*)"
    regex_android_sys = r"^(\d{2}/\d{2}/\d{2,4}[ ,]+\d{2}:\d{2}(?::\d{2})?) - (.*)"
    regex_ios_sys = r"^\[(\d{2}/\d{2}/\d{2,4}[ ,]+\d{2}:\d{2}:\d{2})\] (.*)"

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

    caminho_html = os.path.join(pasta_saida, nome_arquivo_html)
    gerar_html(mensagens, caminho_html, mapa_nomes_reais, nomes_extras, remetentes_validos)
    
    hash_html = calcular_hash_sha256(caminho_html)
    registro_hashes.append(f"\n[ARQUIVO RECONSTRUÍDO - HTML] {nome_arquivo_html}\nSHA256: {hash_html}\n")

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

    caminho_pdf = os.path.join(pasta_saida, nome_arquivo_pdf)
    gerar_pdf_pericial(
        caminho_pdf, 
        incluir_certidao,
        dados_certidao, 
        dados_aparelho,
        registro_hashes, 
        data_hora_atual, 
        nome_modelo if usar_transcricao else None,
        nome_arquivo_html,
        nomes_extras
    )

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