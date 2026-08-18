import os
import sys
import threading
import warnings
import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Importa primeiro o utilitário e configura o FFmpeg antes de carregar o Whisper
from utils import configurar_caminho_ffmpeg, obter_caminho_recurso
configurar_caminho_ffmpeg()

# Importa a lógica pesada e checa se o FPDF está instalado
try:
    from fpdf import FPDF
except ImportError:
    import tkinter.messagebox as mbox
    root = tk.Tk()
    root.withdraw()
    mbox.showerror("Erro de Dependência", "A biblioteca 'fpdf2' não está instalada. Rode: pip install fpdf2")
    sys.exit()

from core_processamento import processar_exportacao, WHISPER_DISPONIVEL

warnings.filterwarnings("ignore")

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
        tw.wm_overrideredirect(True) 
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#202c33", foreground="#e9edef", 
                         relief='solid', borderwidth=1,
                         font=("Segoe UI", 9, "normal"), padx=8, pady=4)
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class AppWhatsAppForensic:
    def __init__(self, root):
        self.root = root
        self.root.title("WhatsApp Constructor - Indexação Forense")
        self.root.geometry("680x880") 
        self.root.configure(bg="#111b21") 

        caminho_icone = obter_caminho_recurso("icone.ico")
        if os.path.exists(caminho_icone):
            self.root.iconbitmap(caminho_icone)

        self.pasta_entrada = tk.StringVar()
        self.pasta_saida = tk.StringVar()
        self.usar_transcricao_audio = tk.BooleanVar(value=False)
        self.usar_transcricao_video = tk.BooleanVar(value=False)
        self.modelo_selecionado = tk.StringVar(value="turbo")
        self.nome_relatorio = tk.StringVar(value="Evidencia_WhatsApp_01")
        
        self.nome_relator = tk.StringVar()
        self.cargo_relator = tk.StringVar()
        self.masp_relator = tk.StringVar()
        
        self.nome_logo_selecionada = tk.StringVar(value="Nenhuma (Sem Logo)")
        self.caminho_logo = tk.StringVar()
        self.mapa_logos_internas = {} 
        
        self.titular_nome = tk.StringVar()
        self.titular_cpf = tk.StringVar()
        self.titular_rg = tk.StringVar()
        
        self.aparelho_marca = tk.StringVar()
        self.aparelho_modelo = tk.StringVar()
        self.aparelho_serial = tk.StringVar()
        self.aparelho_imei = tk.StringVar()
        self.aparelho_linha = tk.StringVar()
        
        self.alvos_vars = []

        self.estilizar_interface()

        self.main_container = tk.Frame(root, bg="#111b21")
        self.main_container.pack(fill="both", expand=True)
        
        self.aba_atual = None
        self.abas_frames = {}
        self.botoes_aba = {}
        self.indicadores_aba = {}
        
        self.tab_bar = tk.Frame(self.main_container, bg="#111b21")
        self.tab_bar.pack(fill="x", padx=10, pady=(15, 0))
        
        linha_sep = tk.Frame(self.main_container, bg="#2a3942", height=2)
        linha_sep.pack(fill="x", padx=10)
        
        self.content_area = tk.Frame(self.main_container, bg="#111b21")
        self.content_area.pack(fill="both", expand=True, padx=10, pady=(10, 10))

        self.criar_aba("proc", "⚙️ Processamento")
        self.criar_aba("dados", "📄 Dados & Certidão")
        self.criar_aba("alvos", "🎯 Alvos HTML")

        self.construir_aba_processamento()
        self.construir_aba_dados()
        self.construir_aba_alvos()
        
        self.alternar_aba("proc")

    def estilizar_interface(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TProgressbar', thickness=15, troughcolor="#202c33", background="#00a884", bordercolor="#111b21")
        style.configure('TCombobox', font=('Segoe UI', 10), fieldbackground="#2a3942", background="#202c33", foreground="#e9edef", bordercolor="#2a3942")
        style.map('TCombobox', fieldbackground=[('readonly', '#2a3942')], foreground=[('readonly', '#e9edef')])

    def criar_aba(self, id_aba, texto):
        btn_frame = tk.Frame(self.tab_bar, bg="#111b21")
        btn_frame.pack(side="left", padx=(0, 5))

        btn = tk.Label(btn_frame, text=texto, font=("Segoe UI", 10, "bold"), 
                       bg="#111b21", fg="#8696a0", padx=15, pady=8, cursor="hand2")
        btn.pack(side="top")
        
        indicador = tk.Frame(btn_frame, bg="#111b21", height=3)
        indicador.pack(side="bottom", fill="x")

        content = tk.Frame(self.content_area, bg="#111b21")
        
        self.abas_frames[id_aba] = content
        self.botoes_aba[id_aba] = btn
        self.indicadores_aba[id_aba] = indicador

        btn.bind("<Button-1>", lambda e: self.alternar_aba(id_aba))
        btn.bind("<Enter>", lambda e, id=id_aba: self.hover_aba(id, True))
        btn.bind("<Leave>", lambda e, id=id_aba: self.hover_aba(id, False))

    def alternar_aba(self, id_aba_ativa):
        self.aba_atual = id_aba_ativa
        for id_aba, frame in self.abas_frames.items():
            if id_aba == id_aba_ativa:
                frame.pack(fill="both", expand=True)
                self.botoes_aba[id_aba].config(fg="#00a884", bg="#202c33")
                self.indicadores_aba[id_aba].config(bg="#00a884")
                self.botoes_aba[id_aba].master.config(bg="#202c33")
            else:
                frame.pack_forget()
                self.botoes_aba[id_aba].config(fg="#8696a0", bg="#111b21")
                self.indicadores_aba[id_aba].config(bg="#111b21")
                self.botoes_aba[id_aba].master.config(bg="#111b21")

    def hover_aba(self, id_aba, is_hover):
        if id_aba == self.aba_atual: return
        if is_hover:
            self.botoes_aba[id_aba].config(bg="#202c33")
            self.botoes_aba[id_aba].master.config(bg="#202c33")
        else:
            self.botoes_aba[id_aba].config(bg="#111b21")
            self.botoes_aba[id_aba].master.config(bg="#111b21")

    def criar_scrollable_frame(self, parent_tab):
        canvas = tk.Canvas(parent_tab, bg="#111b21", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(parent_tab, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollable_frame = tk.Frame(canvas, bg="#111b21", padx=15, pady=10)
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        def _on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        return scrollable_frame

    def construir_aba_processamento(self):
        frame = self.criar_scrollable_frame(self.abas_frames["proc"])
        
        frame_dir = tk.LabelFrame(frame, text=" Diretórios de Processamento ", padx=15, pady=10, bg="#202c33", fg="#00a884", font=("Segoe UI", 10, "bold"), bd=1, relief="solid")
        frame_dir.pack(fill="x", pady=(0, 15))

        tk.Label(frame_dir, text="Origem (Pasta com txt):", bg="#202c33", fg="#e9edef", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w")
        entry_ent = tk.Entry(frame_dir, textvariable=self.pasta_entrada, state="readonly", width=48, font=("Segoe UI", 10), bg="#2a3942", fg="#e9edef", readonlybackground="#2a3942", relief="flat", highlightthickness=1, highlightbackground="#3a4b55")
        entry_ent.grid(row=1, column=0, pady=(2, 6), sticky="w")
        tk.Button(frame_dir, text="Procurar...", command=self.selecionar_entrada, bg="#2a3942", fg="#00a884", activebackground="#3a4b55", activeforeground="#00c298", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").grid(row=1, column=1, padx=(10, 0), pady=(2, 6))

        tk.Label(frame_dir, text="Destino (Onde os relatórios serão gravados):", bg="#202c33", fg="#e9edef", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w")
        entry_sai = tk.Entry(frame_dir, textvariable=self.pasta_saida, state="readonly", width=48, font=("Segoe UI", 10), bg="#2a3942", fg="#e9edef", readonlybackground="#2a3942", relief="flat", highlightthickness=1, highlightbackground="#3a4b55")
        entry_sai.grid(row=3, column=0, pady=(2, 2), sticky="w")
        tk.Button(frame_dir, text="Procurar...", command=self.selecionar_saida, bg="#2a3942", fg="#00a884", activebackground="#3a4b55", activeforeground="#00c298", font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2").grid(row=3, column=1, padx=(10, 0), pady=(2, 2))

        frame_transcricao = tk.LabelFrame(frame, text=" Transcrição de Mídia (Whisper Offline) ", padx=15, pady=10, bg="#202c33", fg="#00a884", font=("Segoe UI", 10, "bold"), bd=1, relief="solid")
        frame_transcricao.pack(fill="x", pady=(0, 15))
        
        chk_transcricao_audio = tk.Checkbutton(frame_transcricao, text="Transcrever Áudios Localmente", 
                                         variable=self.usar_transcricao_audio, command=self.toggle_opcoes_ia,
                                         bg="#202c33", activebackground="#202c33", activeforeground="#e9edef", fg="#e9edef", selectcolor="#111b21", font=("Segoe UI", 10))
        chk_transcricao_audio.pack(anchor="w", pady=(0, 2))

        chk_transcricao_video = tk.Checkbutton(frame_transcricao, text="Transcrever Vídeos (Pode ser muito demorado)", 
                                         variable=self.usar_transcricao_video, command=self.toggle_opcoes_ia,
                                         bg="#202c33", activebackground="#202c33", activeforeground="#e9edef", fg="#e9edef", selectcolor="#111b21", font=("Segoe UI", 10))
        chk_transcricao_video.pack(anchor="w", pady=(0, 5))
        
        if not WHISPER_DISPONIVEL:
            chk_transcricao_audio.config(state="disabled")
            chk_transcricao_video.config(state="disabled")
            tk.Label(frame_transcricao, text="Aviso: Whisper não instalado.", fg="#ff7a7a", bg="#202c33", font=("Segoe UI", 9, "bold")).pack(anchor="w")

        frame_modelos = tk.Frame(frame_transcricao, bg="#202c33")
        frame_modelos.pack(fill="x", pady=(5, 0))
        tk.Label(frame_modelos, text="Modelo da IA Whisper:", bg="#202c33", fg="#e9edef", font=("Segoe UI", 9)).pack(side="left")
        
        self.combo_modelos = ttk.Combobox(frame_modelos, values=["medium", "turbo"], textvariable=self.modelo_selecionado, state="disabled", width=12)
        self.combo_modelos.pack(side="left", padx=(10, 0))
        
        frame_nome = tk.Frame(frame, bg="#111b21")
        frame_nome.pack(fill="x", pady=(15, 0))
        self.criar_label_entry(frame_nome, "Nome da Exportação (Obrigatório):", self.nome_relatorio, 0, 45, bg_parent="#111b21")
        
        self.label_status = tk.Label(frame, text="Pronto para iniciar.", fg="#8696a0", bg="#111b21", font=("Segoe UI", 10, "italic"))
        self.label_status.pack(anchor="w", pady=(15, 0))
        
        self.barra_progresso = ttk.Progressbar(frame, orient="horizontal", mode="determinate")
        self.barra_progresso.pack(fill="x", pady=(5, 15))

        self.btn_iniciar = tk.Button(frame, text="Iniciar Processamento Forense", bg="#00a884", fg="#111b21", 
                                     activebackground="#00c298", activeforeground="#111b21", font=("Segoe UI", 11, "bold"), 
                                     relief="flat", command=self.iniciar_thread, height=2, cursor="hand2")
        self.btn_iniciar.pack(fill="x")
        
        tk.Label(frame, text="Desenvolvido por Gabriel Henrique Bueno", bg="#111b21", fg="#8696a0", font=("Segoe UI", 8, "italic")).pack(pady=(15, 5))

    def construir_aba_dados(self):
        frame = self.criar_scrollable_frame(self.abas_frames["dados"])
        
        frame_logo = tk.LabelFrame(frame, text=" Personalização Visual (Logo) ", padx=15, pady=10, bg="#202c33", fg="#00a884", font=("Segoe UI", 10, "bold"), bd=1, relief="solid")
        frame_logo.pack(fill="x", pady=(0, 15))
        
        pasta_logos = obter_caminho_recurso("logos")
        opcoes_logo = ["Nenhuma (Sem Logo)"]
        if os.path.exists(pasta_logos):
            for arq in sorted(os.listdir(pasta_logos)):
                if arq.lower().endswith(('.png', '.jpg', '.jpeg')):
                    nome_amigavel = os.path.splitext(arq)[0].replace("_", " ").upper()
                    opcoes_logo.append(nome_amigavel)
                    self.mapa_logos_internas[nome_amigavel] = os.path.join(pasta_logos, arq)
                    
        opcoes_logo.append("Personalizada (Buscar no PC)...")

        tk.Label(frame_logo, text="Selecione o Brasão/Logomarca:", bg="#202c33", fg="#e9edef", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        combo_logo = ttk.Combobox(frame_logo, values=opcoes_logo, textvariable=self.nome_logo_selecionada, state="readonly", width=38, font=("Segoe UI", 10))
        combo_logo.grid(row=1, column=0, pady=(0, 6), sticky="w")
        combo_logo.bind("<<ComboboxSelected>>", self.on_logo_selecionada)
        
        self.lbl_caminho_custom = tk.Label(frame_logo, text="", bg="#202c33", fg="#8696a0", font=("Segoe UI", 8, "italic"))
        self.lbl_caminho_custom.grid(row=2, column=0, columnspan=2, sticky="w")
        
        frame_relator = tk.LabelFrame(frame, text=" Responsável pela Extração/Relatório ", padx=15, pady=10, bg="#202c33", fg="#00a884", font=("Segoe UI", 10, "bold"), bd=1, relief="solid")
        frame_relator.pack(fill="x", pady=(0, 15))
        
        self.criar_label_entry(frame_relator, "Nome do Policial/Relator:", self.nome_relator, 0, 40)
        self.criar_label_entry(frame_relator, "Cargo / Função:", self.cargo_relator, 1, 40)
        self.criar_label_entry(frame_relator, "MASP / Matrícula:", self.masp_relator, 2, 25)
        
        dica_titular = "Esses dados irão enriquecer o preâmbulo do PDF\ne preencher dinamicamente a Certidão Final."
        frame_titular = tk.LabelFrame(frame, text=" Qualificação do Titular do Aparelho ", padx=15, pady=10, bg="#202c33", fg="#00a884", font=("Segoe UI", 10, "bold"), bd=1, relief="solid")
        frame_titular.pack(fill="x", pady=(0, 15))
        
        self.criar_label_entry(frame_titular, "Nome do Proprietário:", self.titular_nome, 0, 40, tooltip_text=dica_titular)
        self.criar_label_entry(frame_titular, "CPF:", self.titular_cpf, 1, 25)
        self.criar_label_entry(frame_titular, "RG:", self.titular_rg, 2, 25)
        
        frame_aparelho = tk.LabelFrame(frame, text=" Identificação do Dispositivo ", padx=15, pady=10, bg="#202c33", fg="#00a884", font=("Segoe UI", 10, "bold"), bd=1, relief="solid")
        frame_aparelho.pack(fill="x", pady=(0, 10))
        
        self.criar_label_entry(frame_aparelho, "Marca:", self.aparelho_marca, 0, 25)
        self.criar_label_entry(frame_aparelho, "Modelo:", self.aparelho_modelo, 1, 40)
        self.criar_label_entry(frame_aparelho, "Nº Série:", self.aparelho_serial, 2, 25)
        self.criar_label_entry(frame_aparelho, "IMEI:", self.aparelho_imei, 3, 25)
        self.criar_label_entry(frame_aparelho, "Linha Associada:", self.aparelho_linha, 4, 25)

    def construir_aba_alvos(self):
        frame = self.criar_scrollable_frame(self.abas_frames["alvos"])
        
        tk.Label(frame, text="Mapeamento de Interlocutores (HTML)", bg="#111b21", fg="#00a884", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(5, 5))
        dica_alvos = "Adicione aqui os nomes das pessoas (como estão no TXT extraído) para destacá-los no chat.\nO PRIMEIRO alvo adicionado na lista será considerado o Titular do aparelho (ficará à direita em verde)."
        tk.Label(frame, text=dica_alvos, bg="#111b21", fg="#8696a0", font=("Segoe UI", 9), justify="left").pack(anchor="w", pady=(0, 15))
        
        self.frame_lista_alvos = tk.Frame(frame, bg="#111b21")
        self.frame_lista_alvos.pack(fill="x")
        
        btn_add_alvo = tk.Button(frame, text="+ Adicionar Novo Alvo", bg="#202c33", fg="#00a884", activebackground="#2a3942", activeforeground="#00c298",
                                 font=("Segoe UI", 9, "bold"), relief="flat", command=self.adicionar_alvo_ui, cursor="hand2")
        btn_add_alvo.pack(anchor="w", pady=15)
        
        self.adicionar_alvo_ui()

    def adicionar_alvo_ui(self):
        f_row = tk.Frame(self.frame_lista_alvos, bg="#202c33", bd=1, relief="solid", padx=10, pady=10)
        f_row.pack(fill="x", pady=5)
        
        var_nome = tk.StringVar()
        var_sufixo = tk.StringVar()
        
        tk.Label(f_row, text="Nome na Conversa:", bg="#202c33", fg="#e9edef", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        tk.Entry(f_row, textvariable=var_nome, width=25, font=("Segoe UI", 10), bg="#2a3942", fg="#e9edef", insertbackground="#e9edef", relief="flat", highlightthickness=1, highlightbackground="#3a4b55").grid(row=0, column=1, padx=10)
        
        tk.Label(f_row, text="Sufixo Opcional:", bg="#202c33", fg="#e9edef", font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w")
        tk.Entry(f_row, textvariable=var_sufixo, width=22, font=("Segoe UI", 10), bg="#2a3942", fg="#e9edef", insertbackground="#e9edef", relief="flat", highlightthickness=1, highlightbackground="#3a4b55").grid(row=0, column=3, padx=10)
        
        btn_remover = tk.Button(f_row, text="Remover", bg="#ff7a7a", fg="#111b21", relief="flat", font=("Segoe UI", 8, "bold"), cursor="hand2",
                                command=lambda f=f_row, v=(var_nome, var_sufixo): self.remover_alvo_ui(f, v))
        btn_remover.grid(row=0, column=4, padx=5)
        
        self.alvos_vars.append((var_nome, var_sufixo))
        
    def remover_alvo_ui(self, frame, vars_tuple):
        frame.destroy()
        if vars_tuple in self.alvos_vars:
            self.alvos_vars.remove(vars_tuple)

    def criar_label_entry(self, parent, text, var, row, width, hint="", tooltip_text="", bg_parent="#202c33"):
        frame_lbl = tk.Frame(parent, bg=bg_parent)
        if hasattr(parent, 'grid_size'): 
            frame_lbl.grid(row=row, column=0, sticky="w", pady=3)
        else:
            frame_lbl.pack(anchor="w", pady=3)
            
        tk.Label(frame_lbl, text=text, bg=bg_parent, fg="#e9edef", font=("Segoe UI", 9)).pack(side="left")
        
        if tooltip_text:
            lbl_help = tk.Label(frame_lbl, text="[?]", bg=bg_parent, fg="#00a884", font=("Segoe UI", 9, "bold"), cursor="question_arrow")
            lbl_help.pack(side="left", padx=(5, 0))
            ToolTip(lbl_help, tooltip_text) 
            
        entry = tk.Entry(parent, textvariable=var, width=width, font=("Segoe UI", 10), bg="#2a3942", fg="#e9edef", insertbackground="#e9edef", relief="flat", highlightthickness=1, highlightbackground="#3a4b55", highlightcolor="#00a884")
        if hasattr(parent, 'grid_size'):
            entry.grid(row=row, column=1, padx=12, pady=3, sticky="w")
            if hint: tk.Label(parent, text=hint, bg=bg_parent, fg="#8696a0", font=("Segoe UI", 8, "italic")).grid(row=row, column=2, sticky="w")
        else:
            entry.pack(anchor="w", padx=15)

    def on_logo_selecionada(self, event=None):
        escolha = self.nome_logo_selecionada.get()
        if escolha == "Nenhuma (Sem Logo)":
            self.caminho_logo.set("")
            self.lbl_caminho_custom.config(text="")
        elif escolha == "Personalizada (Buscar no PC)...":
            arquivo = filedialog.askopenfilename(title="Selecione a Logomarca", filetypes=[("Imagens", "*.png *.jpg *.jpeg")])
            if arquivo:
                self.caminho_logo.set(arquivo)
                nome_arq = os.path.basename(arquivo)
                self.lbl_caminho_custom.config(text=f"Arquivo: {nome_arq}")
            else:
                self.nome_logo_selecionada.set("Nenhuma (Sem Logo)")
                self.caminho_logo.set("")
                self.lbl_caminho_custom.config(text="")
        else:
            self.caminho_logo.set(self.mapa_logos_internas.get(escolha, ""))
            self.lbl_caminho_custom.config(text="")

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
            messagebox.showwarning("Atenção", "Selecione as pastas de origem e destino na aba de Processamento.")
            return

        if not self.nome_relatorio.get():
            messagebox.showwarning("Atenção", "O Nome da Exportação é obrigatório.")
            return

        nome_limpo_relatorio = "".join(x for x in self.nome_relatorio.get() if x.isalnum() or x in "._- ")
        nome_limpo_relatorio = nome_limpo_relatorio.replace(" ", "_")

        self.btn_iniciar.config(state="disabled", bg="#3a4b55")
        
        dados_certidao = {
            "nome": self.nome_relator.get().strip(),
            "cargo": self.cargo_relator.get().strip(),
            "masp": self.masp_relator.get().strip()
        }
        
        dados_aparelho = {
            "titular_nome": self.titular_nome.get().strip(),
            "titular_cpf": self.titular_cpf.get().strip(),
            "titular_rg": self.titular_rg.get().strip(),
            "aparelho_marca": self.aparelho_marca.get().strip(),
            "aparelho_modelo": self.aparelho_modelo.get().strip(),
            "aparelho_serial": self.aparelho_serial.get().strip(),
            "aparelho_imei": self.aparelho_imei.get().strip(),
            "aparelho_linha": self.aparelho_linha.get().strip()
        }
        
        lista_alvos = []
        for var_nome, var_sufixo in self.alvos_vars:
            if var_nome.get().strip():
                lista_alvos.append({
                    "nome": var_nome.get().strip(),
                    "sufixo": var_sufixo.get().strip()
                })

        nomes_extras = {
            "relatorio": nome_limpo_relatorio,
            "alvos": lista_alvos,
            "logo": self.caminho_logo.get().strip() 
        }

        thread = threading.Thread(target=self.executar_processo_background, args=(entrada, saida, dados_certidao, dados_aparelho, nomes_extras))
        thread.start()

    def executar_processo_background(self, entrada, saida, dados_certidao, dados_aparelho, nomes_extras):
        try:
            processar_exportacao(
                entrada, 
                saida, 
                self.usar_transcricao_audio.get(), 
                self.usar_transcricao_video.get(),
                self.modelo_selecionado.get(),
                True,
                dados_certidao,
                dados_aparelho,
                nomes_extras,
                self.atualizar_progresso
            )
            self.root.after(0, self.finalizar_sucesso, saida)
        except Exception as e:
            self.root.after(0, self.finalizar_erro, str(e))

    def finalizar_sucesso(self, pasta_saida):
        self.barra_progresso["value"] = 100
        self.label_status.config(text="100% - Processamento Concluído!")
        self.btn_iniciar.config(state="normal", bg="#00a884")
        messagebox.showinfo("Sucesso", "Procedimento concluído!\n\nVerifique os arquivos PDF e HTML na pasta de destino.")
        os.startfile(pasta_saida)

    def finalizar_erro(self, erro_msg):
        self.label_status.config(text="Erro durante o processamento.")
        self.btn_iniciar.config(state="normal", bg="#00a884")
        messagebox.showerror("Erro de Processamento", f"Ocorreu um erro:\n{erro_msg}")


if __name__ == "__main__":
    if os.name == 'nt':
        try:
            myappid = 'whatsconstructor.forense.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass
    
    root = tk.Tk()
    app = AppWhatsAppForensic(root)
    root.mainloop()