import os
import sys
import hashlib
import re

def obter_caminho_recurso(caminho_relativo):
    """Retorna o caminho absoluto para o recurso, compatível com o PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, caminho_relativo)
    return os.path.join(os.path.abspath("."), caminho_relativo)

def configurar_caminho_ffmpeg():
    """Adiciona o FFmpeg embutido ao PATH do Windows para a IA encontrar."""
    if getattr(sys, 'frozen', False):
        caminho_base = sys._MEIPASS
    else:
        caminho_base = os.path.dirname(os.path.abspath(__file__))
    os.environ["PATH"] += os.pathsep + caminho_base

def calcular_hash_sha256(caminho_arquivo):
    """Calcula a assinatura digital SHA-256 de um arquivo."""
    sha256_hash = hashlib.sha256()
    try:
        with open(caminho_arquivo, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        return f"Erro ao calcular hash: {e}"

def limpar_nome_arquivo(nome):
    """Remove caracteres invisíveis que o WhatsApp as vezes insere nos nomes."""
    nome_limpo = re.sub(r'[\u200e\u200f\u202a\u202b\u202c\u200b\u202d\u202e]', '', nome)
    return nome_limpo.strip()

def encontrar_arquivo(nome_procurado, pasta_raiz):
    """Busca o arquivo real na pasta desconsiderando problemas de formatação."""
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

def texto_pdf(texto):
    """Filtra emojis e caracteres especiais não suportados pelas fontes padrão do PDF."""
    if not texto: return ""
    return str(texto).encode('windows-1252', 'replace').decode('windows-1252')