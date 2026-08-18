import os
import base64

def gerar_html(lista_mensagens, caminho_saida, mapa_nomes, nomes_extras, remetentes_validos):
    lista_alvos = nomes_extras.get("alvos", [])
    
    titular_oficial = ""
    if lista_alvos:
        nome_primeiro_alvo = lista_alvos[0]['nome'].strip().lower()
        for rem in remetentes_validos:
            if nome_primeiro_alvo in rem.lower():
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
    
    caminho_logo = nomes_extras.get("logo", "")
    html_logo_tag = ""
    if caminho_logo and os.path.exists(caminho_logo):
        try:
            with open(caminho_logo, "rb") as img_file:
                b64_string = base64.b64encode(img_file.read()).decode('utf-8')
                ext = caminho_logo.split('.')[-1].lower()
                mime = "image/png" if ext == "png" else "image/jpeg"
                html_logo_tag = f'<img src="data:{mime};base64,{b64_string}" style="height: 50px; margin-right: 20px; object-fit: contain;">'
        except Exception:
            pass

    html_content = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{nomes_extras["relatorio"]}</title>
        <style>
            body {{ font-family: 'Segoe UI', -apple-system, Arial, sans-serif; background-color: #111b21; margin: 0; padding: 0; color: #e9edef; }}
            
            .header {{ background-color: #202c33; color: #e9edef; position: sticky; top: 0; z-index: 1001; box-shadow: 0 2px 5px rgba(0,0,0,0.2); display: flex; flex-direction: column; border-bottom: 1px solid #2a3942; }}
            .header-info {{ padding: 15px 25px; display: flex; align-items: center; }}
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
                padding: 15px; height: calc(100vh - 130px); overflow-y: auto; position: sticky; top: 130px; 
                box-sizing: border-box; 
            }}
            
            .btn-export-list {{
                background-color: #00a884; color: #111b21; padding: 12px; border-radius: 8px; border: none; width: 100%;
                cursor: pointer; font-weight: bold; font-size: 13px; margin-bottom: 20px; text-transform: uppercase;
                transition: background 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                display: block; text-align: center; text-decoration: none; box-sizing: border-box;
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
                position: sticky; top: 145px; 
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
            
            .btn-pdf {{ background-color: #005c4b; color: white; }}
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
            
            .print-media-label {{ display: none; font-size: 12.5px; color: #00a884; font-weight: 600; margin-bottom: 4px; word-break: break-all; }}
            
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
                * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
                .header, .search-bar-container, .tab-buttons, .sidebar {{ display: none !important; }}
                body {{ background-color: #111b21 !important; color: #e9edef !important; }}
                .main-wrapper {{ display: block !important; }}
                .chat-area {{ padding: 0 !important; max-width: 100% !important; margin: 0 !important; }}
                .msg-wrapper {{ page-break-inside: avoid; }}
                .media-box audio, .media-box video {{ display: none !important; }}
                .print-media-label {{ display: block !important; }} 
                .tab-content {{ display: block !important; }} 
                #tab-galeria {{ display: none !important; }} 

                /* --- MODO CLARO (ECONOMIA DE TINTA) --- */
                body.print-light {{ background-color: white !important; color: black !important; }}
                body.print-light .mensagem {{ background-color: white !important; color: black !important; border: 1px solid #ccc !important; box-shadow: none !important; }}
                body.print-light .texto {{ color: black !important; }}
                body.print-light .timestamp {{ color: #555 !important; }}
                body.print-light .remetente {{ color: #000 !important; font-weight: 700 !important; }}
                body.print-light .msg-sistema {{ background-color: #f5f5f5 !important; color: #333 !important; border: 1px solid #ddd !important; }}
                body.print-light .caixa-transcricao {{ background-color: #f9f9f9 !important; color: #222 !important; border-left: 4px solid #00a884 !important; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-info">
                {html_logo_tag}
                <div>
                    <h2 class="header-title">{nomes_extras["relatorio"]} - Leitor Forense</h2>
                    <p class="header-subtitle">Integridade e Cadeia de Custódia Assegurada por Hash Cryptográfico</p>
                </div>
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
                        
                        <div class="filter-group" style="margin-left: auto; gap: 10px; display: flex;">
                            <button id="btnTogglePrint" class="btn-nav" style="background-color: #2a3942; color: #e9edef; border: 1px solid #8696a0;" onclick="togglePrintMode()">🔳 Fundo PDF: Escuro</button>
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
            
            for alvo in lista_alvos:
                if alvo['nome'].lower() in msg["remetente"].lower() and alvo['sufixo'].strip():
                    nome_exibicao = f"{msg['remetente']} ({alvo['sufixo'].strip()})"
                    break

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
                    chat_html += f'<div class="media-box"><span class="print-media-label">🎥 Vídeo anexado: {nome_arq}</span><video controls><source src="{nome_arq}"></video></div>'
                    galeria_html += f'<video controls preload="metadata"><source src="{nome_arq}"></video>'
                elif extensao.endswith(('.opus', '.mp3', '.ogg', '.wav', '.m4a')):
                    chat_html += f'<div class="media-box"><span class="print-media-label">🎵 Áudio anexado: {nome_arq}</span><audio controls><source src="{nome_arq}"></audio></div>'
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

            // --- CONTROLE DE MODO IMPRESSÃO CLARO/ESCURO ---
            let printDark = true;
            function togglePrintMode() {
                printDark = !printDark;
                let btn = document.getElementById("btnTogglePrint");
                if(printDark) {
                    document.body.classList.remove("print-light");
                    btn.innerText = "🔳 Fundo PDF: Escuro";
                    btn.style.backgroundColor = "#2a3942";
                    btn.style.color = "#e9edef";
                } else {
                    document.body.classList.add("print-light");
                    btn.innerText = "🔲 Fundo PDF: Claro";
                    btn.style.backgroundColor = "#e9edef";
                    btn.style.color = "#111b21";
                }
            }
            // ------------------------------------------------

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