import customtkinter as ctk
import requests
import tkinter.ttk as ttk
import csv
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from scipy.interpolate import make_interp_spline

# Configuração visual padrão (Tema escuro e cor principal azul)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class AppTCC(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Qualidade da Água")
        self.geometry("1100x650")
        
        # Estrutura principal: Grid dividida em Menu Lateral (esquerda) e Conteúdo (direita)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- MENU LATERAL ---
        self.frame_menu = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.frame_menu.grid(row=0, column=0, sticky="nsew")
        self.frame_menu.grid_rowconfigure(4, weight=1)

        lbl_logo = ctk.CTkLabel(self.frame_menu, text="SISTEMA\nIoT & IA", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_logo.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.btn_visao_geral = ctk.CTkButton(self.frame_menu, text="Visão Geral", command=self.abrir_visao_geral)
        self.btn_visao_geral.grid(row=1, column=0, padx=20, pady=10)

        self.btn_historico = ctk.CTkButton(self.frame_menu, text="Histórico", command=self.abrir_historico)
        self.btn_historico.grid(row=2, column=0, padx=20, pady=10)

        self.btn_config = ctk.CTkButton(self.frame_menu, text="Configurações", command=self.abrir_configuracoes)
        self.btn_config.grid(row=3, column=0, padx=20, pady=10)

        # Status do Servidor no rodapé do menu
        self.lbl_status_api = ctk.CTkLabel(self.frame_menu, text="Verificando API...", text_color="gray")
        self.lbl_status_api.grid(row=5, column=0, padx=20, pady=20, sticky="s")

        # --- ÁREA DE CONTEÚDO PRINCIPAL ---
        self.frame_conteudo = ctk.CTkFrame(self, corner_radius=10)
        self.frame_conteudo.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # Inicia abrindo a primeira tela
        self.abrir_visao_geral()
        self.verificar_api()

    def limpar_conteudo(self):
        # Remove tudo que estiver na tela principal antes de carregar a nova
        for widget in self.frame_conteudo.winfo_children():
            widget.destroy()

    def abrir_visao_geral(self):
        self.limpar_conteudo()
        lbl_titulo = ctk.CTkLabel(self.frame_conteudo, text="Dashboard em Tempo Real", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_titulo.pack(anchor="w", padx=20, pady=(20, 10))

        # --- CONTAINER SUPERIOR (Bloco Sensores + Bloco IA) ---
        frame_top = ctk.CTkFrame(self.frame_conteudo, fg_color="transparent")
        frame_top.pack(fill="x", padx=20, pady=5)
        # Proporção: Sensores ocupam mais espaço (weight=3) que a IA (weight=2)
        frame_top.grid_columnconfigure(0, weight=3) 
        frame_top.grid_columnconfigure(1, weight=2)

        # 1. BLOCO DOS SENSORES (Esquerda)
        bloco_sensores = ctk.CTkFrame(frame_top, fg_color="#1f2937", corner_radius=10)
        bloco_sensores.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(bloco_sensores, text="Indicadores Visuais Atuais", font=ctk.CTkFont(size=14, weight="bold"), text_color="#d4d4d8").pack(anchor="w", padx=15, pady=(10, 5))

        f_cards_sens = ctk.CTkFrame(bloco_sensores, fg_color="transparent")
        f_cards_sens.pack(fill="both", expand=True, padx=10, pady=(0, 15))
        f_cards_sens.grid_columnconfigure((0,1,2), weight=1, uniform="cards_sensores")

        def criar_card_sensor(parent, col, titulo, unidade):
            card = ctk.CTkFrame(parent, fg_color="#111827", corner_radius=8, border_width=1, border_color="#374151")
            card.grid(row=0, column=col, sticky="nsew", padx=5, pady=5)
            
            topo = ctk.CTkFrame(card, fg_color="transparent")
            topo.pack(fill="x", padx=10, pady=(10, 0))
            ctk.CTkLabel(topo, text=titulo, font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
            badge = ctk.CTkLabel(topo, text="--", font=ctk.CTkFont(size=10, weight="bold"), corner_radius=4, padx=6, pady=2)
            badge.pack(side="right")
            
            f_val = ctk.CTkFrame(card, fg_color="transparent")
            f_val.pack(fill="x", padx=10, pady=(5, 15))
            lbl_val = ctk.CTkLabel(f_val, text="--", font=ctk.CTkFont(size=32, weight="bold"))
            lbl_val.pack(side="left")
            ctk.CTkLabel(f_val, text=f" {unidade}", font=ctk.CTkFont(size=12), text_color="gray").pack(side="left", pady=(15, 0))
            
            return lbl_val, badge

        self.lbl_ph, self.bdg_ph = criar_card_sensor(f_cards_sens, 0, "pH", "")
        self.lbl_turb, self.bdg_turb = criar_card_sensor(f_cards_sens, 1, "Turbidez", "NTU")
        self.lbl_tds, self.bdg_tds = criar_card_sensor(f_cards_sens, 2, "TDS", "ppm")

        # 2. BLOCO IA & REGRAS (Direita)
        bloco_ia = ctk.CTkFrame(frame_top, fg_color="#1f2937", corner_radius=10)
        bloco_ia.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(bloco_ia, text="Análise & IA", font=ctk.CTkFont(size=14, weight="bold"), text_color="#d4d4d8").pack(anchor="w", padx=15, pady=(10, 5))

        f_cards_ia = ctk.CTkFrame(bloco_ia, fg_color="transparent")
        f_cards_ia.pack(fill="both", expand=True, padx=10, pady=(0, 15))
        f_cards_ia.grid_columnconfigure((0,1), weight=1, uniform="cards_ia")

        # Card: Regras
        card_reg = ctk.CTkFrame(f_cards_ia, fg_color="#111827", corner_radius=8, border_width=1, border_color="#374151")
        card_reg.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(card_reg, text="Classificação por Regras:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=(10, 0))
        self.lbl_class_reg = ctk.CTkLabel(card_reg, text="--", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_class_reg.pack(anchor="w", padx=10, pady=(2, 0))
        self.lbl_sub_reg = ctk.CTkLabel(card_reg, text="Aguardando...", font=ctk.CTkFont(size=10), text_color="gray")
        self.lbl_sub_reg.pack(anchor="w", padx=10, pady=(0, 10))

        # Card: IA
        card_ml = ctk.CTkFrame(f_cards_ia, fg_color="#111827", corner_radius=8, border_width=1, border_color="#374151")
        card_ml.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(card_ml, text="Classificação da IA:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=(10, 0))
        self.lbl_class_ia = ctk.CTkLabel(card_ml, text="--", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_class_ia.pack(anchor="w", padx=10, pady=(2, 0))
        self.lbl_sub_ia = ctk.CTkLabel(card_ml, text="Aguardando...", font=ctk.CTkFont(size=10), text_color="gray")
        self.lbl_sub_ia.pack(anchor="w", padx=10, pady=(0, 10))

        # --- GRAFICO INFERIOR ---
        self.bloco_grafico = ctk.CTkFrame(self.frame_conteudo, fg_color="#1f2937", corner_radius=10)
        self.bloco_grafico.pack(fill="both", expand=True, padx=20, pady=10)
        ctk.CTkLabel(self.bloco_grafico, text="Evolução dos Sensores", font=ctk.CTkFont(size=14, weight="bold"), text_color="#d4d4d8").pack(anchor="w", padx=15, pady=(10, 0))
        
        # Preparando a tela em branco do Matplotlib com o fundo escuro do dashboard
        self.figura_grafico = plt.Figure(figsize=(8, 2.5), dpi=100, facecolor='#1f2937')
        self.ax = self.figura_grafico.add_subplot(111)
        self.ax.set_facecolor('#1f2937')
        self.ax.tick_params(colors='gray')
        for spine in self.ax.spines.values():
            spine.set_visible(False) # Remove as bordas do gráfico
            
        self.canvas_grafico = FigureCanvasTkAgg(self.figura_grafico, master=self.bloco_grafico)
        self.canvas_grafico.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Inicia ciclo de busca dos dados
        self.atualizar_dados_dashboard()

    def atualizar_dados_dashboard(self):
        if hasattr(self, 'lbl_ph') and self.lbl_ph.winfo_exists():
            try:
                # 1. ATUALIZA OS CARDS SUPERIORES
                resp_status = requests.get("http://127.0.0.1:8000/api/sensores/status")
                if resp_status.status_code == 200:
                    dados = resp_status.json()
                    
                    ph = float(dados.get('ph', 0))
                    turb = float(dados.get('turbidez_ntu', 0))
                    tds = float(dados.get('tds_ppm', 0))
                    
                    self.lbl_ph.configure(text=f"{ph:.2f}")
                    self.lbl_turb.configure(text=f"{turb:.1f}")
                    self.lbl_tds.configure(text=f"{tds:.0f}")

                    # Lógica para mudar a cor da etiqueta (Badge) Ideal/Alerta/Crítico
                    def config_badge(badge_widget, ideal_cond, alerta_cond):
                        if ideal_cond:
                            badge_widget.configure(text="Ideal", fg_color="#064e3b", text_color="#34d399")
                        elif alerta_cond:
                            badge_widget.configure(text="Alerta", fg_color="#713f12", text_color="#facc15")
                        else:
                            badge_widget.configure(text="Crítico", fg_color="#7f1d1d", text_color="#f87171")

                    config_badge(self.bdg_ph, 6.5 <= ph <= 8.0, 6.0 <= ph <= 8.5)
                    config_badge(self.bdg_turb, turb <= 5.0, turb <= 15.0)
                    config_badge(self.bdg_tds, tds < 500, tds < 800)

                    # Textos da IA e Regras
                    class_regra = dados.get('classificacao_regras', 'Sem dados')
                    class_ia = dados.get('classificacao_ia', 'Sem dados')
                    conf_ia = dados.get('confianca_ia', '0%')

                    def cor_texto(texto):
                        if "Excelente" in texto: return "#34d399"
                        elif "Atenção" in texto: return "#facc15"
                        elif "Crítica" in texto: return "#f87171"
                        return "gray"

                    # Separa o texto da classificação do texto em parênteses
                    partes_regra = class_regra.split("(")
                    self.lbl_class_reg.configure(text=partes_regra[0].strip(), text_color=cor_texto(class_regra))
                    if len(partes_regra) > 1:
                        self.lbl_sub_reg.configure(text=f"({partes_regra[1]}") 
                    else:
                        self.lbl_sub_reg.configure(text="")
                    
                    self.lbl_class_ia.configure(text=class_ia, text_color=cor_texto(class_ia))
                    self.lbl_sub_ia.configure(text=f"({conf_ia} Confiança)")

                # 2. ATUALIZA O GRÁFICO INFERIOR
                resp_hist = requests.get("http://127.0.0.1:8000/api/sensores/historico")
                if resp_hist.status_code == 200:
                    historico = resp_hist.json().get("historico", [])
                    historico = historico[:15][::-1] # Pega os últimos 15 registros em ordem cronológica
                    
                    if historico:
                        tempos = [h.get("horario").split(" ")[1][:5] for h in historico] # Pega apenas HH:MM
                        valores_ph = [h.get("ph") for h in historico]
                        valores_turb = [h.get("turbidez_ntu") for h in historico]

                        self.ax.clear()
                        self.ax.set_facecolor('#1f2937')
                        self.ax.tick_params(colors='gray', labelsize=8)
                        for spine in self.ax.spines.values():
                            spine.set_visible(False)
                            
                        # Desenha as linhas do pH e Turbidez
                        x = np.arange(len(tempos))
                        
                        # Se tivermos 4 ou mais pontos, criamos a onda suave (spline)
                        if len(tempos) >= 4:
                            # Cria 300 pontos virtuais para suavizar a curva
                            x_smooth = np.linspace(x.min(), x.max(), 300)
                            
                            spl_ph = make_interp_spline(x, valores_ph, k=3)
                            y_ph_smooth = spl_ph(x_smooth)
                            
                            spl_turb = make_interp_spline(x, valores_turb, k=3)
                            y_turb_smooth = spl_turb(x_smooth)
                            
                            # Desenha as linhas curvas (ondas)
                            self.ax.plot(x_smooth, y_ph_smooth, color="#34d399", linewidth=2)
                            self.ax.plot(x_smooth, y_turb_smooth, color="#facc15", linewidth=2)
                            
                            # Preenche o fundo debaixo da onda (Efeito Luminoso)
                            self.ax.fill_between(x_smooth, y_ph_smooth, color="#34d399", alpha=0.1)
                            self.ax.fill_between(x_smooth, y_turb_smooth, color="#facc15", alpha=0.1)
                            
                            # Coloca os pontinhos reais em cima da onda
                            self.ax.scatter(x, valores_ph, color="#34d399", s=20, zorder=5)
                            self.ax.scatter(x, valores_turb, color="#facc15", s=20, zorder=5)
                            
                        else:
                            # Fallback: Se tiver 3 ou menos pontos, faz linha normal mas JÁ com o preenchimento
                            self.ax.plot(x, valores_ph, color="#34d399", marker='o', linewidth=2, markersize=4)
                            self.ax.plot(x, valores_turb, color="#facc15", marker='o', linewidth=2, markersize=4)
                            
                            # Preenchimento luminoso
                            self.ax.fill_between(x, valores_ph, color="#34d399", alpha=0.1)
                            self.ax.fill_between(x, valores_turb, color="#facc15", alpha=0.1)

                        # Limpa eixo X para não amontoar os textos
                        self.ax.set_xticks(x)
                        self.ax.set_xticklabels(tempos, rotation=0, ha='center', fontsize=8)
                        
                        self.figura_grafico.tight_layout()
                        self.canvas_grafico.draw()

            except Exception as e:
                pass
            
            self.after(3000, self.atualizar_dados_dashboard)

    def abrir_historico(self):
        self.limpar_conteudo()

        # --- TOPO: Títulos, Busca e Botão Exportar ---
        frame_topo = ctk.CTkFrame(self.frame_conteudo, fg_color="transparent")
        frame_topo.pack(fill="x", padx=20, pady=(20, 10))
        
        frame_titulos = ctk.CTkFrame(frame_topo, fg_color="transparent")
        frame_titulos.pack(side="left")
        ctk.CTkLabel(frame_titulos, text="Histórico de Leituras", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(frame_titulos, text="Visualização dos últimos registros do banco de dados (Neon Cloud) - Consumindo /api/sensores/historico", text_color="gray", font=ctk.CTkFont(size=12)).pack(anchor="w")

        frame_botoes = ctk.CTkFrame(frame_topo, fg_color="transparent")
        frame_botoes.pack(side="right", fill="y")
        
        self.busca = ctk.CTkEntry(frame_botoes, placeholder_text="Buscar por data...", width=150, height=35)
        self.busca.pack(side="left", padx=10)
        self.busca.bind("<KeyRelease>", self.filtrar_historico) # Dispara a busca ao digitar
        
        btn_exportar = ctk.CTkButton(frame_botoes, text="+ Exportar para CSV", fg_color="#10b981", hover_color="#059669", text_color="white", font=ctk.CTkFont(weight="bold"), height=35, command=self.exportar_csv)
        btn_exportar.pack(side="left")

        # --- TABELA CUSTOMIZADA (GRID) ---
        # Usamos um ScrollableFrame para permitir rolagem e ter o fundo escuro arredondado
        self.frame_tabela = ctk.CTkScrollableFrame(self.frame_conteudo, corner_radius=10, fg_color="#111827", border_width=1, border_color="#27272a")
        self.frame_tabela.pack(fill="both", expand=True, padx=20, pady=10)

        # Configurar a largura das colunas no grid
        pesos = [1, 2, 1, 1, 1, 2, 2, 1]
        for i, p in enumerate(pesos):
            self.frame_tabela.grid_columnconfigure(i, weight=p)

        # --- RODAPÉ ---
        frame_rodape = ctk.CTkFrame(self.frame_conteudo, fg_color="transparent")
        frame_rodape.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(frame_rodape, text="Mostrando registros carregados do banco na nuvem", text_color="gray", font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkLabel(frame_rodape, text="((•)) PostgreSQL (Neon Cloud): Conectado", text_color="#10b981", font=ctk.CTkFont(size=12, weight="bold")).pack(side="right")

        # Chama a função que vai preencher as linhas
        self.carregar_dados_historico()

    def desenhar_cabecalho_tabela(self):
        # Nomes das colunas exatamente como no Mockup
        colunas = ["ID", "Data / Hora", "pH", "Turbidez (NTU)", "TDS (ppm)", "Classificação por Regras", "IA & Confiança", "Status"]
        for i, col in enumerate(colunas):
            lbl = ctk.CTkLabel(self.frame_tabela, text=col, font=ctk.CTkFont(size=12, weight="bold"), text_color="#a1a1aa", anchor="w")
            lbl.grid(row=0, column=i, sticky="ew", padx=10, pady=(10, 15))

    def carregar_dados_historico(self):
        try:
            resposta = requests.get("http://127.0.0.1:8000/api/sensores/historico")
            if resposta.status_code == 200:
                dados = resposta.json()
                # Guarda os dados completos na memória do aplicativo
                self.dados_historico_completos = dados.get("historico", [])
                self.renderizar_tabela(self.dados_historico_completos)
        except Exception as e:
            print("Erro ao carregar histórico:", e)

    def filtrar_historico(self, event=None):
        termo = self.busca.get().lower()
        # Se a busca estiver vazia, mostra tudo
        if not termo:
            self.renderizar_tabela(self.dados_historico_completos)
            return

        # Filtra os dados olhando para a data/hora
        dados_filtrados = [
            linha for linha in self.dados_historico_completos 
            if termo in str(linha.get("horario", "")).lower()
        ]
        self.renderizar_tabela(dados_filtrados)

    def exportar_csv(self):
        if not hasattr(self, 'dados_historico_completos') or not self.dados_historico_completos:
            messagebox.showwarning("Aviso", "Não há dados para exportar.")
            return

        # Abre a janela padrão do Windows para escolher onde salvar o ficheiro
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Arquivos CSV", "*.csv")],
            title="Salvar Histórico como CSV",
            initialfile="historico_qualidade_agua.csv"
        )

        if arquivo:
            try:
                # Cria e escreve o ficheiro CSV
                with open(arquivo, mode='w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f, delimiter=';') # Ponto e vírgula é melhor para abrir no Excel em PT-BR
                    writer.writerow(["ID", "Data/Hora", "pH", "Turbidez (NTU)", "TDS (ppm)", "Classificacao Regras", "Classificacao IA", "Confianca IA", "Status"])

                    for linha in self.dados_historico_completos:
                        writer.writerow([
                            linha.get("id", ""),
                            linha.get("horario", ""),
                            f"{linha.get('ph'):.2f}",
                            f"{linha.get('turbidez_ntu'):.2f}",
                            f"{linha.get('tds_ppm'):.0f}",
                            linha.get("classificacao_regras", ""),
                            linha.get("classificacao_ia", ""),
                            linha.get("confianca_ia", ""),
                            linha.get("status", "")
                        ])
                messagebox.showinfo("Sucesso", f"Relatório exportado com sucesso!\nSalvo em: {arquivo}")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao exportar:\n{e}")

    def renderizar_tabela(self, lista_dados):
        # Limpa a tela
        for widget in self.frame_tabela.winfo_children():
            widget.destroy()
            
        self.desenhar_cabecalho_tabela()
        
        # Desenha as linhas usando a lista (que pode ser a completa ou a filtrada)
        for row_idx, linha in enumerate(lista_dados, start=1):
            id_val = str(linha.get("id", ""))
            data_val = str(linha.get("horario", ""))
            ph_val = f"{linha.get('ph'):.2f}"
            turb_val = f"{linha.get('turbidez_ntu'):.2f}"
            tds_val = f"{linha.get('tds_ppm'):.0f}"
            
            class_regra = linha.get("classificacao_regras", "Sem dados")
            class_ia = linha.get("classificacao_ia", "Sem dados")
            conf = linha.get("confianca_ia", "0%")
            ia_full = f"{class_ia} ({conf})"
            status = linha.get("status", "")
            
            def get_badge_colors(texto):
                if "Excelente" in texto or status == "Normal":
                    return "#064e3b", "#34d399" 
                elif "Atenção" in texto or status == "Alerta":
                    return "#713f12", "#facc15" 
                elif "Crítica" in texto or status == "Crítico":
                    return "#7f1d1d", "#f87171" 
                return "transparent", "#d4d4d8"

            ctk.CTkLabel(self.frame_tabela, text=id_val, font=ctk.CTkFont(size=12), text_color="#d4d4d8", anchor="w").grid(row=row_idx, column=0, sticky="ew", padx=10, pady=8)
            ctk.CTkLabel(self.frame_tabela, text=data_val, font=ctk.CTkFont(size=12), text_color="#d4d4d8", anchor="w").grid(row=row_idx, column=1, sticky="ew", padx=10, pady=8)
            ctk.CTkLabel(self.frame_tabela, text=ph_val, font=ctk.CTkFont(size=12), text_color="#d4d4d8", anchor="w").grid(row=row_idx, column=2, sticky="ew", padx=10, pady=8)
            ctk.CTkLabel(self.frame_tabela, text=turb_val, font=ctk.CTkFont(size=12), text_color="#d4d4d8", anchor="w").grid(row=row_idx, column=3, sticky="ew", padx=10, pady=8)
            ctk.CTkLabel(self.frame_tabela, text=tds_val, font=ctk.CTkFont(size=12), text_color="#d4d4d8", anchor="w").grid(row=row_idx, column=4, sticky="ew", padx=10, pady=8)
            
            bg_reg, fg_reg = get_badge_colors(class_regra)
            ctk.CTkLabel(self.frame_tabela, text=class_regra, font=ctk.CTkFont(size=11, weight="bold"), text_color=fg_reg, fg_color=bg_reg, corner_radius=5, padx=8, pady=2).grid(row=row_idx, column=5, sticky="w", padx=10, pady=8)

            bg_ia, fg_ia = get_badge_colors(class_ia)
            ctk.CTkLabel(self.frame_tabela, text=ia_full, font=ctk.CTkFont(size=11, weight="bold"), text_color=fg_ia, fg_color=bg_ia, corner_radius=5, padx=8, pady=2).grid(row=row_idx, column=6, sticky="w", padx=10, pady=8)

            bg_st, fg_st = get_badge_colors(status)
            ctk.CTkLabel(self.frame_tabela, text=status, font=ctk.CTkFont(size=11, weight="bold"), text_color=fg_st, fg_color=bg_st, corner_radius=5, padx=10, pady=2).grid(row=row_idx, column=7, sticky="w", padx=10, pady=8)

    def abrir_configuracoes(self):
        self.limpar_conteudo()
        
        lbl_titulo = ctk.CTkLabel(self.frame_conteudo, text="Configurações", font=ctk.CTkFont(size=24, weight="bold"))
        lbl_titulo.pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(self.frame_conteudo, text="Gerenciamento de conexões, status da infraestrutura e parâmetros da IA", text_color="gray").pack(anchor="w", padx=20, pady=(0, 20))

        # Função auxiliar para criar linhas de informação padronizadas
        def add_info_row(parent, label, value, row, cor_texto="#d4d4d8", cor_fundo="transparent"):
            lbl_tit = ctk.CTkLabel(parent, text=label, text_color="gray", font=ctk.CTkFont(size=13))
            lbl_tit.grid(row=row, column=0, sticky="w", padx=15, pady=8)
            
            lbl_val = ctk.CTkLabel(parent, text=value, text_color=cor_texto, fg_color=cor_fundo, corner_radius=5, padx=8, pady=2, font=ctk.CTkFont(size=13, weight="bold"))
            lbl_val.grid(row=row, column=1, sticky="e", padx=15, pady=8)
            parent.grid_columnconfigure(1, weight=1)

        # --- GRID SUPERIOR (2 Cards Idênticos) ---
        frame_top = ctk.CTkFrame(self.frame_conteudo, fg_color="transparent")
        frame_top.pack(fill="x", padx=20, pady=10)
        # O parâmetro 'uniform' é o segredo para deixar os dois lados do mesmo tamanho
        frame_top.grid_columnconfigure(0, weight=1, uniform="colunas_topo")
        frame_top.grid_columnconfigure(1, weight=1, uniform="colunas_topo")

        # Card 1: MQTT
        card_mqtt = ctk.CTkFrame(frame_top, corner_radius=10, fg_color="#1f2937")
        card_mqtt.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(card_mqtt, text="Conexão MQTT (Mosquitto)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        f_mqtt_info = ctk.CTkFrame(card_mqtt, fg_color="transparent")
        f_mqtt_info.pack(fill="both", expand=True, pady=5)
        add_info_row(f_mqtt_info, "Broker:", "localhost", 0, cor_texto="#34d399", cor_fundo="#064e3b")
        add_info_row(f_mqtt_info, "Porta:", "1883", 1)
        add_info_row(f_mqtt_info, "Tópico Subscrito:", "tcc/sensores/agua", 2)
        add_info_row(f_mqtt_info, "Mensagens Recebidas:", "1.248", 3, cor_texto="#fbbf24", cor_fundo="#713f12")

        # Card 2: Banco de Dados Neon
        card_neon = ctk.CTkFrame(frame_top, corner_radius=10, fg_color="#1f2937")
        card_neon.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(card_neon, text="Banco de Dados (Neon Cloud)", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        f_neon_info = ctk.CTkFrame(card_neon, fg_color="transparent")
        f_neon_info.pack(fill="both", expand=True, pady=5)
        add_info_row(f_neon_info, "Provedor:", "PostgreSQL na Nuvem", 0)
        add_info_row(f_neon_info, "Status:", "Online (Pool ativo)", 1, cor_texto="#34d399", cor_fundo="#064e3b")
        add_info_row(f_neon_info, "Tabelas Criadas:", "leituras", 2)
        add_info_row(f_neon_info, "Total de Registros:", "2.341", 3)

       # --- GRID INFERIOR (1 Card Largo com 2 colunas dentro) ---
        card_ia = ctk.CTkFrame(self.frame_conteudo, corner_radius=10, fg_color="#1f2937")
        card_ia.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(card_ia, text="Inteligência Artificial & Regras de Qualidade", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 5))
        
        # Divisão interna do card largo
        frame_ia_inner = ctk.CTkFrame(card_ia, fg_color="transparent")
        frame_ia_inner.pack(fill="x", pady=5)
        frame_ia_inner.grid_columnconfigure(0, weight=1, uniform="colunas_base")
        frame_ia_inner.grid_columnconfigure(1, weight=1, uniform="colunas_base")
        
        # Lado Esquerdo: Status IA
        col_ia = ctk.CTkFrame(frame_ia_inner, fg_color="transparent")
        col_ia.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(col_ia, text="Status do Modelo IA", font=ctk.CTkFont(size=14), text_color="#d4d4d8").pack(anchor="w", padx=15, pady=(5, 10))
        
        # CORREÇÃO: Sub-frame dedicado apenas para o grid das informações
        f_ia_info = ctk.CTkFrame(col_ia, fg_color="transparent")
        f_ia_info.pack(fill="both", expand=True)
        add_info_row(f_ia_info, "Modelo:", "water_model.pkl", 0)
        add_info_row(f_ia_info, "Status:", "Carregado com sucesso", 1, cor_texto="#34d399", cor_fundo="#064e3b")
        add_info_row(f_ia_info, "Algoritmo:", "Scikit-Learn Random Forest", 2)
        
        # Lado Direito: Limites de Qualidade
        col_regras = ctk.CTkFrame(frame_ia_inner, fg_color="transparent")
        col_regras.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(col_regras, text="Limites de Qualidade (Regras)", font=ctk.CTkFont(size=14), text_color="#d4d4d8").pack(anchor="w", padx=15, pady=(5, 10))
        
        # CORREÇÃO: Sub-frame dedicado apenas para o grid das informações
        f_reg_info = ctk.CTkFrame(col_regras, fg_color="transparent")
        f_reg_info.pack(fill="both", expand=True)
        add_info_row(f_reg_info, "pH:", "6.5 a 8.0", 0)
        add_info_row(f_reg_info, "Turbidez:", "<= 5.0 NTU", 1)
        add_info_row(f_reg_info, "TDS:", "< 500 ppm", 2)

    def verificar_api(self):
        # Tenta conectar na sua API rodando no fundo
        try:
            resposta = requests.get("http://127.0.0.1:8000/")
            if resposta.status_code == 200:
                self.lbl_status_api.configure(text="🟢 API Online", text_color="green")
        except:
            self.lbl_status_api.configure(text="🔴 API Offline", text_color="red")
        
        # Repete a verificação a cada 5 segundos
        self.after(5000, self.verificar_api)

if __name__ == "__main__":
    app = AppTCC()
    app.mainloop()