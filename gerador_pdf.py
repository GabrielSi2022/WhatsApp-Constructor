import os
from fpdf import FPDF
from utils import texto_pdf

class RelatorioForensePDF(FPDF):
    def header(self):
        if hasattr(self, 'logo_path') and self.logo_path and os.path.exists(self.logo_path):
            try:
                self.image(self.logo_path, 10, 8, h=24) 
            except Exception:
                pass
                
        self.set_y(13) 
        self.set_x(35) 
        
        self.set_font('helvetica', 'B', 13) 
        self.cell(0, 8, 'RELATÓRIO TÉCNICO DE INDEXAÇÃO E INTEGRIDADE DE DADOS', 0, 1, 'C')
        
        self.set_x(35)
        self.set_font('helvetica', 'I', 10)
        self.cell(0, 5, 'Extração Lógica - WhatsApp', 0, 1, 'C')
        
        self.line(10, 34, 200, 34)
        self.set_y(40) 

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def gerar_pdf_pericial(caminho_saida, incluir_certidao, dados_certidao, dados_aparelho, registro_hashes, data_hora_atual, modelo_ia, nome_html, nomes_extras):
    pdf = RelatorioForensePDF()
    pdf.logo_path = nomes_extras.get("logo", "") 
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    tem_dados_aparelho = any(v for k, v in dados_aparelho.items() if v)
    item_num = 1
    
    if tem_dados_aparelho:
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, f'{item_num}. IDENTIFICAÇÃO DO DISPOSITIVO E TITULAR', 0, 1)
        pdf.set_font('helvetica', '', 10)
        
        if dados_aparelho.get('titular_nome'): pdf.cell(0, 6, texto_pdf(f"Titular/Proprietário: {dados_aparelho['titular_nome']}"), 0, 1)
        if dados_aparelho.get('titular_cpf'): pdf.cell(0, 6, texto_pdf(f"CPF: {dados_aparelho['titular_cpf']}"), 0, 1)
        if dados_aparelho.get('titular_rg'): pdf.cell(0, 6, texto_pdf(f"RG: {dados_aparelho['titular_rg']}"), 0, 1)
        
        marca_modelo = f"{dados_aparelho.get('aparelho_marca', '')} {dados_aparelho.get('aparelho_modelo', '')}".strip()
        if marca_modelo: pdf.cell(0, 6, texto_pdf(f"Aparelho: {marca_modelo}"), 0, 1)
        
        if dados_aparelho.get('aparelho_imei'): pdf.cell(0, 6, texto_pdf(f"IMEI: {dados_aparelho['aparelho_imei']}"), 0, 1)
        if dados_aparelho.get('aparelho_serial'): pdf.cell(0, 6, texto_pdf(f"Nº de Série: {dados_aparelho['aparelho_serial']}"), 0, 1)
        if dados_aparelho.get('aparelho_linha'): pdf.cell(0, 6, texto_pdf(f"Linha Telefônica: {dados_aparelho['aparelho_linha']}"), 0, 1)
        
        pdf.ln(5)
        item_num += 1
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, f'{item_num}. METODOLOGIA E ESCOPO DO PROCEDIMENTO', 0, 1)
    
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
    pdf.multi_cell(0, 5, texto_pdf(metodologia_texto))
    pdf.ln(5)
    item_num += 1

    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, f'{item_num}. INFORMAÇÕES DO PROCESSAMENTO', 0, 1)
    pdf.set_font('helvetica', '', 10)
    pdf.cell(0, 6, texto_pdf(f"Data e Hora do Procedimento: {data_hora_atual}"), 0, 1)
    pdf.cell(0, 6, texto_pdf(f"Modelo de IA Utilizado (Transcrição): {modelo_ia if modelo_ia else 'Nenhum / Não solicitado'}"), 0, 1)
    pdf.cell(0, 6, texto_pdf(f"Ficheiro de Leitura Gerado: {nome_html}"), 0, 1)
    pdf.ln(5)
    item_num += 1

    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, f'{item_num}. REGISTRO DE INTEGRIDADE (HASH SHA-256)', 0, 1)
    pdf.set_font('courier', '', 8)
    
    for registro in registro_hashes:
        pdf.multi_cell(0, 4, texto_pdf(registro))
    item_num += 1
    
    if incluir_certidao:
        pdf.ln(15)
        pdf.set_font('helvetica', 'B', 12)
        pdf.cell(0, 10, f'{item_num}. CERTIDÃO DE INDEXAÇÃO', 0, 1)
        pdf.set_font('helvetica', '', 10)
        
        if tem_dados_aparelho:
            certidao_texto = (
                f"CERTIFICA-SE, para os devidos fins e sob as penas da lei, que foi procedida a indexação, "
                f"cálculo de integridade e o processamento lógico dos dados extraídos do aparelho celular "
            )
            
            marca_modelo = f"{dados_aparelho.get('aparelho_marca', '')} {dados_aparelho.get('aparelho_modelo', '')}".strip()
            if marca_modelo: certidao_texto += f"{marca_modelo}, "
            if dados_aparelho.get('aparelho_serial'): certidao_texto += f"serial {dados_aparelho['aparelho_serial']}, "
            if dados_aparelho.get('aparelho_imei'): certidao_texto += f"IMEI {dados_aparelho['aparelho_imei']}, "
            if dados_aparelho.get('aparelho_linha'): certidao_texto += f"vinculado à linha {dados_aparelho['aparelho_linha']}, "
            if dados_aparelho.get('titular_nome'): certidao_texto += f"de propriedade de {dados_aparelho['titular_nome']}, "
            if dados_aparelho.get('titular_cpf'): certidao_texto += f"portador(a) do CPF {dados_aparelho['titular_cpf']}, "
            if dados_aparelho.get('titular_rg'): certidao_texto += f"RG {dados_aparelho['titular_rg']}, "
            
            certidao_texto = certidao_texto.rstrip(", ") + ". "
            certidao_texto += (
                "Ressalta-se que a extração primária dos dados foi realizada mediante autorização prévia, expressa e "
                "voluntária do(a) proprietário(a). Certifica-se ainda que o processamento garantiu o espelhamento fiel "
                "em relação aos arquivos exportados da origem, conforme registros de Hash descritos neste documento.\n\n"
                "Nada mais havendo a constar, lavra-se o presente relatório que segue devidamente assinado."
            )
        else:
            certidao_texto = (
                f"CERTIFICA-SE, para os devidos fins e sob as penas da lei, que a extração primária dos dados "
                f"foi realizada mediante autorização prévia, expressa e voluntária do(a) proprietário(a) do dispositivo. "
                f"Certifica-se ainda que foi procedida a indexação e o processamento dos dados listados neste "
                f"documento, de forma a garantir a sua integridade e espelhamento fiel em relação aos arquivos "
                f"exportados da origem.\n\n"
                f"Nada mais havendo a constar, lavra-se o presente relatório que segue devidamente assinado."
            )
            
        pdf.multi_cell(0, 5, texto_pdf(certidao_texto))
        
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
        pdf.cell(0, 5, texto_pdf(data_extenso), 0, 1, 'R')
        pdf.ln(25)
        
        pdf.line(55, pdf.get_y(), 155, pdf.get_y())
        pdf.ln(2)
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(0, 5, texto_pdf(f"{dados_certidao['nome'].upper()}"), 0, 1, 'C')
        
        pdf.set_font('helvetica', '', 10)
        detalhes_cargo = []
        if dados_certidao['cargo']: detalhes_cargo.append(dados_certidao['cargo'])
        if dados_certidao['masp']: detalhes_cargo.append(f"MASP/Matrícula: {dados_certidao['masp']}")
        if detalhes_cargo:
            pdf.cell(0, 5, texto_pdf(" - ".join(detalhes_cargo)), 0, 1, 'C')
        
    pdf.output(caminho_saida)

def gerar_pdf_integrantes(caminho_saida, remetentes, nomes_extras, dados_certidao, data_hora_atual, incluir_certidao):
    pdf = RelatorioForensePDF()
    pdf.logo_path = nomes_extras.get("logo", "")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font('helvetica', 'B', 14)
    pdf.cell(0, 10, texto_pdf('ANEXO - RELAÇÃO DE INTEGRANTES DA CONVERSA'), 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('helvetica', '', 10)
    pdf.cell(0, 6, texto_pdf(f"Data/Hora de Geração: {data_hora_atual}"), 0, 1)
    pdf.cell(0, 6, texto_pdf(f"Referência da Evidência: {nomes_extras['relatorio']}"), 0, 1)
    pdf.ln(10)
    
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 8, texto_pdf(f"Total de Interlocutores Identificados no Relatório: {len(remetentes)}"), 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font('helvetica', '', 11)
    for i, rem in enumerate(sorted(remetentes), 1):
        pdf.cell(0, 8, texto_pdf(f"{i}. {rem}"), 0, 1)
        
    if incluir_certidao:
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
        pdf.cell(0, 5, texto_pdf(data_extenso), 0, 1, 'R')
        pdf.ln(25) 

        pdf.line(55, pdf.get_y(), 155, pdf.get_y())
        pdf.ln(2)
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(0, 5, texto_pdf(f"{dados_certidao['nome'].upper()}"), 0, 1, 'C')
        
        pdf.set_font('helvetica', '', 10)
        detalhes_cargo = []
        if dados_certidao['cargo']: detalhes_cargo.append(dados_certidao['cargo'])
        if dados_certidao['masp']: detalhes_cargo.append(f"MASP/Matrícula: {dados_certidao['masp']}")
        if detalhes_cargo:
            pdf.cell(0, 5, texto_pdf(" - ".join(detalhes_cargo)), 0, 1, 'C')
        
    pdf.output(caminho_saida)