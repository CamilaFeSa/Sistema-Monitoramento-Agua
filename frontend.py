import csv
from tkinter import filedialog, messagebox

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import requests
from scipy.interpolate import make_interp_spline

# Configuração visual padrão (Tema escuro e cor principal azul)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AppTCC(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Qualidade da Água")
        self.geometry("1280x760")
        self.minsize(1120, 680)

        # Estrutura principal: Grid dividida em Menu Lateral (esquerda) e Conteúdo (direita)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- MENU LATERAL ---
        self.frame_menu = ctk.CTkFrame(self, width=230, corner_radius=0)
        self.frame_menu.grid(row=0, column=0, sticky="nsew")
        self.frame_menu.grid_rowconfigure(4, weight=1)

        lbl_logo = ctk.CTkLabel(
            self.frame_menu,
            text="SISTEMA\nIoT & IA",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        lbl_logo.grid(row=0, column=0, padx=24, pady=(28, 36))

        self.btn_visao_geral = ctk.CTkButton(
            self.frame_menu,
            text="Visão Geral",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.abrir_visao_geral,
        )
        self.btn_visao_geral.grid(row=1, column=0, padx=22, pady=10, sticky="ew")

        self.btn_historico = ctk.CTkButton(
            self.frame_menu,
            text="Histórico",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.abrir_historico,
        )
        self.btn_historico.grid(row=2, column=0, padx=22, pady=10, sticky="ew")

        self.btn_config = ctk.CTkButton(
            self.frame_menu,
            text="Configurações",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.abrir_configuracoes,
        )
        self.btn_config.grid(row=3, column=0, padx=22, pady=10, sticky="ew")

        # Status do Servidor no rodapé do menu
        self.lbl_status_api = ctk.CTkLabel(
            self.frame_menu,
            text="Verificando API...",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="gray",
        )
        self.lbl_status_api.grid(row=5, column=0, padx=20, pady=24, sticky="s")

        # --- ÁREA DE CONTEÚDO PRINCIPAL ---
        self.frame_conteudo = ctk.CTkFrame(self, corner_radius=12)
        self.frame_conteudo.grid(row=0, column=1, padx=24, pady=24, sticky="nsew")

        # Inicia abrindo a primeira tela
        self.abrir_visao_geral()
        self.verificar_api()

    def limpar_conteudo(self):
        # Remove tudo que estiver na tela principal antes de carregar a nova
        for widget in self.frame_conteudo.winfo_children():
            widget.destroy()

    def abrir_visao_geral(self):
        self.limpar_conteudo()
        lbl_titulo = ctk.CTkLabel(
            self.frame_conteudo,
            text="Dashboard em Tempo Real",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        lbl_titulo.pack(anchor="w", padx=24, pady=(22, 12))

        # --- CONTAINER SUPERIOR (Bloco Sensores + Bloco IA) ---
        frame_top = ctk.CTkFrame(self.frame_conteudo, fg_color="transparent")
        frame_top.pack(fill="x", padx=24, pady=6)
        frame_top.grid_columnconfigure(0, weight=3)
        frame_top.grid_columnconfigure(1, weight=2)

        # 1. BLOCO DOS SENSORES (Esquerda)
        bloco_sensores = ctk.CTkFrame(
            frame_top, fg_color="#1f2937", corner_radius=12
        )
        bloco_sensores.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        ctk.CTkLabel(
            bloco_sensores,
            text="Indicadores Visuais Atuais",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#d4d4d8",
        ).pack(anchor="w", padx=18, pady=(14, 8))

        f_cards_sens = ctk.CTkFrame(bloco_sensores, fg_color="transparent")
        f_cards_sens.pack(fill="both", expand=True, padx=12, pady=(0, 16))
        f_cards_sens.grid_columnconfigure((0, 1, 2), weight=1, uniform="cards_sensores")

        def criar_card_sensor(parent, col, titulo, unidade):
            card = ctk.CTkFrame(
                parent,
                fg_color="#111827",
                corner_radius=10,
                border_width=1,
                border_color="#374151",
            )
            card.grid(row=0, column=col, sticky="nsew", padx=6, pady=6)
            topo = ctk.CTkFrame(card, fg_color="transparent")
            topo.pack(fill="x", padx=12, pady=(12, 0))
            ctk.CTkLabel(
                topo, text=titulo, font=ctk.CTkFont(size=16, weight="bold")
            ).pack(side="left")
            badge = ctk.CTkLabel(
                topo,
                text="--",
                font=ctk.CTkFont(size=12, weight="bold"),
                corner_radius=5,
                padx=8,
                pady=3,
            )
            badge.pack(side="right")
            f_val = ctk.CTkFrame(card, fg_color="transparent")
            f_val.pack(fill="x", padx=12, pady=(8, 16))
            lbl_val = ctk.CTkLabel(
                f_val, text="--", font=ctk.CTkFont(size=38, weight="bold")
            )
            lbl_val.pack(side="left")
            ctk.CTkLabel(
                f_val,
                text=f" {unidade}",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).pack(side="left", pady=(16, 0))
            return lbl_val, badge

        self.lbl_ph, self.bdg_ph = criar_card_sensor(f_cards_sens, 0, "pH", "")
        self.lbl_turb, self.bdg_turb = criar_card_sensor(
            f_cards_sens, 1, "Turbidez", "NTU"
        )
        self.lbl_tds, self.bdg_tds = criar_card_sensor(
            f_cards_sens, 2, "TDS", "ppm"
        )

        # 2. BLOCO IA & REGRAS (Direita)
        bloco_ia = ctk.CTkFrame(frame_top, fg_color="#1f2937", corner_radius=12)
        bloco_ia.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(
            bloco_ia,
            text="Análise & IA",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#d4d4d8",
        ).pack(anchor="w", padx=18, pady=(14, 8))

        f_cards_ia = ctk.CTkFrame(bloco_ia, fg_color="transparent")
        f_cards_ia.pack(fill="both", expand=True, padx=12, pady=(0, 16))
        f_cards_ia.grid_columnconfigure((0, 1), weight=1, uniform="cards_ia")

        # Card: Referência / Regras
        card_reg = ctk.CTkFrame(
            f_cards_ia,
            fg_color="#111827",
            corner_radius=10,
            border_width=1,
            border_color="#374151",
        )
        card_reg.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        ctk.CTkLabel(
            card_reg,
            text="Faixa de Referência:",
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=12, pady=(12, 0))
        self.lbl_class_reg = ctk.CTkLabel(
            card_reg,
            text="--",
            font=ctk.CTkFont(size=17, weight="bold"),
            wraplength=170,
            justify="left",
        )
        self.lbl_class_reg.pack(anchor="w", padx=12, pady=(4, 0))
        self.lbl_sub_reg = ctk.CTkLabel(
            card_reg,
            text="Aguardando...",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.lbl_sub_reg.pack(anchor="w", padx=12, pady=(2, 12))

        # Card: IA
        card_ml = ctk.CTkFrame(
            f_cards_ia,
            fg_color="#111827",
            corner_radius=10,
            border_width=1,
            border_color="#374151",
        )
        card_ml.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        ctk.CTkLabel(
            card_ml,
            text="Classificação da IA:",
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=12, pady=(12, 0))
        self.lbl_class_ia = ctk.CTkLabel(
            card_ml,
            text="--",
            font=ctk.CTkFont(size=17, weight="bold"),
            wraplength=170,
            justify="left",
        )
        self.lbl_class_ia.pack(anchor="w", padx=12, pady=(4, 0))
        self.lbl_sub_ia = ctk.CTkLabel(
            card_ml,
            text="Aguardando...",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.lbl_sub_ia.pack(anchor="w", padx=12, pady=(2, 12))

        # --- GRAFICO INFERIOR ---
        self.bloco_grafico = ctk.CTkFrame(
            self.frame_conteudo, fg_color="#1f2937", corner_radius=12
        )
        self.bloco_grafico.pack(fill="both", expand=True, padx=24, pady=12)
        ctk.CTkLabel(
            self.bloco_grafico,
            text="Evolução dos Sensores",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#d4d4d8",
        ).pack(anchor="w", padx=18, pady=(12, 0))

        self.figura_grafico = plt.Figure(
            figsize=(9, 3.0), dpi=100, facecolor="#1f2937"
        )
        self.ax = self.figura_grafico.add_subplot(111)
        self.ax_tds = self.ax.twinx()
        self.ax.set_facecolor("#1f2937")
        self.ax.tick_params(colors="gray", labelsize=9)
        self.ax_tds.tick_params(axis="y", colors="gray", labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        for spine in self.ax_tds.spines.values():
            spine.set_visible(False)

        self.canvas_grafico = FigureCanvasTkAgg(
            self.figura_grafico, master=self.bloco_grafico
        )
        self.canvas_grafico.get_tk_widget().pack(
            fill="both", expand=True, padx=14, pady=(0, 14)
        )

        # Inicia ciclo de busca dos dados
        self.atualizar_dados_dashboard()

    def atualizar_dados_dashboard(self):
        if hasattr(self, "lbl_ph") and self.lbl_ph.winfo_exists():
            try:
                # 1. ATUALIZA OS CARDS SUPERIORES
                resp_status = requests.get(
                    "http://127.0.0.1:8000/api/sensores/status", timeout=3
                )
                if resp_status.status_code == 200:
                    dados = resp_status.json()
                    ph = float(dados.get("ph", 0))
                    turb = float(dados.get("turbidez_ntu", 0))
                    tds = float(dados.get("tds_ppm", 0))

                    self.lbl_ph.configure(text=f"{ph:.2f}")
                    self.lbl_turb.configure(text=f"{turb:.1f}")
                    self.lbl_tds.configure(text=f"{tds:.0f}")

                    def config_badge(badge_widget, dentro_cond, lim_cond):
                        if dentro_cond:
                            badge_widget.configure(
                                text="Na faixa",
                                fg_color="#064e3b",
                                text_color="#34d399",
                            )
                        elif lim_cond:
                            badge_widget.configure(
                                text="No limite",
                                fg_color="#713f12",
                                text_color="#facc15",
                            )
                        else:
                            badge_widget.configure(
                                text="Fora da faixa",
                                fg_color="#7f1d1d",
                                text_color="#f87171",
                            )

                    config_badge(
                        self.bdg_ph,
                        6.5 <= ph <= 8.0,
                        6.0 <= ph <= 9.0,
                    )
                    config_badge(
                        self.bdg_turb,
                        turb <= 5.0,
                        turb <= 100.0,
                    )
                    config_badge(
                        self.bdg_tds,
                        tds <= 250.0,
                        tds <= 500.0,
                    )

                    class_regra = dados.get("classificacao_regras") or "Sem dados"
                    class_ia = dados.get("classificacao_ia", "Sem dados")
                    conf_ia = dados.get("confianca_ia", "0%")

                    def cor_texto(texto):
                        t = (texto or "").lower()
                        if "dentro da faixa" in t or "na faixa" in t:
                            return "#34d399"
                        elif (
                            "no limite" in t
                            or "limítrofe" in t
                            or "limitrofe" in t
                        ):
                            return "#facc15"
                        elif "fora da faixa" in t:
                            return "#f87171"
                        return "gray"

                    partes_regra = class_regra.split("(")
                    self.lbl_class_reg.configure(
                        text=partes_regra[0].strip(),
                        text_color=cor_texto(class_regra),
                    )
                    if len(partes_regra) > 1:
                        self.lbl_sub_reg.configure(
                            text=f"({partes_regra[1].rstrip(')')})"
                        )
                    else:
                        self.lbl_sub_reg.configure(text="Parâmetro de referência")

                    self.lbl_class_ia.configure(
                        text=class_ia, text_color=cor_texto(class_ia)
                    )
                    self.lbl_sub_ia.configure(text=f"({conf_ia} Confiança)")

                # 2. ATUALIZA O GRÁFICO INFERIOR
                resp_hist = requests.get(
                    "http://127.0.0.1:8000/api/sensores/historico", timeout=3
                )
                if resp_hist.status_code == 200:
                    historico = resp_hist.json().get("historico", [])
                    historico = historico[:15][::-1]
                    if historico:
                        tempos = [
                            h.get("horario").split(" ")[1][:5] for h in historico
                        ]
                        valores_ph = [h.get("ph") for h in historico]
                        valores_turb = [h.get("turbidez_ntu") for h in historico]
                        valores_tds = [h.get("tds_ppm") for h in historico]

                        self.ax.clear()
                        self.ax_tds.clear()
                        self.ax.set_facecolor("#1f2937")
                        self.ax.tick_params(
                            axis="both", colors="gray", labelsize=9
                        )
                        self.ax_tds.tick_params(
                            axis="y", colors="gray", labelsize=9
                        )
                        for spine in self.ax.spines.values():
                            spine.set_visible(False)
                        for spine in self.ax_tds.spines.values():
                            spine.set_visible(False)

                        x = np.arange(len(tempos))

                        if len(tempos) >= 4:
                            x_smooth = np.linspace(x.min(), x.max(), 300)

                            y_ph_smooth = make_interp_spline(
                                x, valores_ph, k=3
                            )(x_smooth)
                            y_turb_smooth = make_interp_spline(
                                x, valores_turb, k=3
                            )(x_smooth)
                            y_tds_smooth = make_interp_spline(
                                x, valores_tds, k=3
                            )(x_smooth)

                            self.ax.plot(
                                x_smooth,
                                y_ph_smooth,
                                color="#34d399",
                                linewidth=2.2,
                                label="pH",
                            )
                            self.ax.plot(
                                x_smooth,
                                y_turb_smooth,
                                color="#facc15",
                                linewidth=2.2,
                                label="Turbidez (NTU)",
                            )
                            self.ax_tds.plot(
                                x_smooth,
                                y_tds_smooth,
                                color="#60a5fa",
                                linewidth=2.2,
                                label="TDS (ppm)",
                            )

                            self.ax.fill_between(
                                x_smooth,
                                y_ph_smooth,
                                color="#34d399",
                                alpha=0.08,
                            )
                            self.ax.fill_between(
                                x_smooth,
                                y_turb_smooth,
                                color="#facc15",
                                alpha=0.08,
                            )
                            self.ax_tds.fill_between(
                                x_smooth,
                                y_tds_smooth,
                                color="#60a5fa",
                                alpha=0.06,
                            )

                            self.ax.scatter(
                                x, valores_ph, color="#34d399", s=24, zorder=5
                            )
                            self.ax.scatter(
                                x, valores_turb, color="#facc15", s=24, zorder=5
                            )
                            self.ax_tds.scatter(
                                x, valores_tds, color="#60a5fa", s=24, zorder=5
                            )
                        else:
                            self.ax.plot(
                                x,
                                valores_ph,
                                color="#34d399",
                                marker="o",
                                linewidth=2.2,
                                markersize=5,
                                label="pH",
                            )
                            self.ax.plot(
                                x,
                                valores_turb,
                                color="#facc15",
                                marker="o",
                                linewidth=2.2,
                                markersize=5,
                                label="Turbidez (NTU)",
                            )
                            self.ax_tds.plot(
                                x,
                                valores_tds,
                                color="#60a5fa",
                                marker="o",
                                linewidth=2.2,
                                markersize=5,
                                label="TDS (ppm)",
                            )

                            self.ax.fill_between(
                                x, valores_ph, color="#34d399", alpha=0.08
                            )
                            self.ax.fill_between(
                                x, valores_turb, color="#facc15", alpha=0.08
                            )
                            self.ax_tds.fill_between(
                                x, valores_tds, color="#60a5fa", alpha=0.06
                            )

                        linhas = self.ax.get_lines() + self.ax_tds.get_lines()
                        nomes = [linha.get_label() for linha in linhas]
                        self.ax.legend(
                            linhas,
                            nomes,
                            loc="lower center",
                            bbox_to_anchor=(0.5, 1.08),
                            ncol=3,
                            facecolor="#1f2937",
                            edgecolor="#374151",
                            labelcolor="#d4d4d8",
                            fontsize=9,
                            framealpha=0.95,
                        )

                        self.ax.set_ylabel(
                            "pH / Turbidez (NTU)", color="gray", fontsize=9
                        )
                        self.ax_tds.set_ylabel(
                            "TDS (ppm)", color="gray", fontsize=9
                        )
                        self.ax_tds.yaxis.set_label_position("right")
                        self.ax_tds.yaxis.tick_right()
                        self.ax.set_xticks(x)
                        self.ax.set_xticklabels(
                            tempos, rotation=0, ha="center", fontsize=9
                        )

                        self.figura_grafico.subplots_adjust(
                            left=0.08, right=0.92, bottom=0.18, top=0.78
                        )
                        self.canvas_grafico.draw()

            except Exception:
                pass
            self.after(3000, self.atualizar_dados_dashboard)

    def abrir_historico(self):
        self.limpar_conteudo()

        # --- TOPO: Títulos, Busca e Botão Exportar ---
        frame_topo = ctk.CTkFrame(self.frame_conteudo, fg_color="transparent")
        frame_topo.pack(fill="x", padx=24, pady=(22, 12))
        frame_titulos = ctk.CTkFrame(frame_topo, fg_color="transparent")
        frame_titulos.pack(side="left")
        ctk.CTkLabel(
            frame_titulos,
            text="Histórico de Leituras",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            frame_titulos,
            text="Visualização dos últimos registros do banco de dados (Neon Cloud) - Consumindo /api/sensores/historico",
            text_color="gray",
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w")

        frame_botoes = ctk.CTkFrame(frame_topo, fg_color="transparent")
        frame_botoes.pack(side="right", fill="y")
        self.busca = ctk.CTkEntry(
            frame_botoes,
            placeholder_text="Buscar por data...",
            width=180,
            height=38,
            font=ctk.CTkFont(size=13),
        )
        self.busca.pack(side="left", padx=10)
        self.busca.bind("<KeyRelease>", self.filtrar_historico)
        btn_exportar = ctk.CTkButton(
            frame_botoes,
            text="+ Exportar para CSV",
            fg_color="#10b981",
            hover_color="#059669",
            text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            command=self.exportar_csv,
        )
        btn_exportar.pack(side="left")

        # --- TABELA CUSTOMIZADA (GRID) ---
        self.frame_tabela = ctk.CTkScrollableFrame(
            self.frame_conteudo,
            corner_radius=12,
            fg_color="#111827",
            border_width=1,
            border_color="#27272a",
        )
        self.frame_tabela.pack(fill="both", expand=True, padx=24, pady=12)

        pesos = [1, 2, 1, 1, 1, 2, 2, 1]
        for i, p in enumerate(pesos):
            self.frame_tabela.grid_columnconfigure(i, weight=p)

        # --- RODAPÉ ---
        frame_rodape = ctk.CTkFrame(self.frame_conteudo, fg_color="transparent")
        frame_rodape.pack(fill="x", padx=24, pady=(0, 22))
        ctk.CTkLabel(
            frame_rodape,
            text="Mostrando registros carregados do banco na nuvem",
            text_color="gray",
            font=ctk.CTkFont(size=13),
        ).pack(side="left")
        ctk.CTkLabel(
            frame_rodape,
            text="((•)) PostgreSQL (Neon Cloud): Conectado",
            text_color="#10b981",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="right")

        self.carregar_dados_historico()

    def desenhar_cabecalho_tabela(self):
        colunas = [
            "ID",
            "Data / Hora",
            "pH",
            "Turbidez (NTU)",
            "TDS (ppm)",
            "Faixa de Referência",
            "IA & Confiança",
            "Status",
        ]
        for i, col in enumerate(colunas):
            lbl = ctk.CTkLabel(
                self.frame_tabela,
                text=col,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#a1a1aa",
                anchor="w",
            )
            lbl.grid(row=0, column=i, sticky="ew", padx=10, pady=(12, 16))

    def carregar_dados_historico(self):
        try:
            resposta = requests.get(
                "http://127.0.0.1:8000/api/sensores/historico", timeout=3
            )
            if resposta.status_code == 200:
                dados = resposta.json()
                self.dados_historico_completos = dados.get("historico", [])
                self.renderizar_tabela(self.dados_historico_completos)
        except Exception as e:
            print("Erro ao carregar histórico:", e)

    def filtrar_historico(self, event=None):
        termo = self.busca.get().lower()
        if not termo:
            self.renderizar_tabela(self.dados_historico_completos)
            return

        dados_filtrados = [
            linha
            for linha in self.dados_historico_completos
            if termo in str(linha.get("horario", "")).lower()
        ]
        self.renderizar_tabela(dados_filtrados)

    def exportar_csv(self):
        if (
            not hasattr(self, "dados_historico_completos")
            or not self.dados_historico_completos
        ):
            messagebox.showwarning("Aviso", "Não há dados para exportar.")
            return

        arquivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Arquivos CSV", "*.csv")],
            title="Salvar Histórico como CSV",
            initialfile="historico_qualidade_agua.csv",
        )

        if arquivo:
            try:
                with open(
                    arquivo, mode="w", newline="", encoding="utf-8-sig"
                ) as f:
                    writer = csv.writer(f, delimiter=";")
                    writer.writerow([
                        "ID",
                        "Data/Hora",
                        "pH",
                        "Turbidez (NTU)",
                        "TDS (ppm)",
                        "Faixa de Referencia",
                        "Classificacao IA",
                        "Confianca IA",
                        "Status",
                    ])

                    for linha in self.dados_historico_completos:
                        writer.writerow([
                            linha.get("id", ""),
                            linha.get("horario", ""),
                            f"{linha.get('ph'):.2f}",
                            f"{linha.get('turbidez_ntu'):.2f}",
                            f"{linha.get('tds_ppm'):.0f}",
                            linha.get("classificacao_regras") or "",
                            linha.get("classificacao_ia", ""),
                            linha.get("confianca_ia", ""),
                            linha.get("status", ""),
                        ])
                messagebox.showinfo(
                    "Sucesso",
                    f"Relatório exportado com sucesso!\nSalvo em: {arquivo}",
                )
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao exportar:\n{e}")

    def renderizar_tabela(self, lista_dados):
        for widget in self.frame_tabela.winfo_children():
            widget.destroy()
        self.desenhar_cabecalho_tabela()

        def normalizar_status_curto(st):
            s = (st or "").strip()
            sl = s.lower()
            if "dentro da faixa" in sl or s == "Normal":
                return "Na faixa"
            elif (
                "no limite" in sl
                or "limítrofe" in sl
                or "limitrofe" in sl
                or s == "Alerta"
            ):
                return "No limite"
            elif "fora da faixa" in sl or s == "Crítico":
                return "Fora da faixa"
            return s or "--"

        def get_badge_colors(texto):
            tl = (texto or "").lower()
            if "dentro da faixa" in tl or tl in ("na faixa", "normal"):
                return "#064e3b", "#34d399"
            elif (
                "no limite" in tl
                or "limítrofe" in tl
                or "limitrofe" in tl
                or tl == "alerta"
            ):
                return "#713f12", "#facc15"
            elif "fora da faixa" in tl or tl in (
                "fora da faixa",
                "crítico",
                "critico",
            ):
                return "#7f1d1d", "#f87171"
            return "transparent", "#d4d4d8"

        for row_idx, linha in enumerate(lista_dados, start=1):
            id_val = str(linha.get("id", ""))
            data_val = str(linha.get("horario", ""))
            ph_val = f"{linha.get('ph'):.2f}"
            turb_val = f"{linha.get('turbidez_ntu'):.2f}"
            tds_val = f"{linha.get('tds_ppm'):.0f}"
            class_regra = linha.get("classificacao_regras") or "Sem dados"
            class_ia = linha.get("classificacao_ia", "Sem dados")
            conf = linha.get("confianca_ia", "0%")
            ia_full = f"{class_ia} ({conf})"
            status_curto = normalizar_status_curto(linha.get("status", ""))

            ctk.CTkLabel(
                self.frame_tabela,
                text=id_val,
                font=ctk.CTkFont(size=13),
                text_color="#d4d4d8",
                anchor="w",
            ).grid(row=row_idx, column=0, sticky="ew", padx=10, pady=9)
            ctk.CTkLabel(
                self.frame_tabela,
                text=data_val,
                font=ctk.CTkFont(size=13),
                text_color="#d4d4d8",
                anchor="w",
            ).grid(row=row_idx, column=1, sticky="ew", padx=10, pady=9)
            ctk.CTkLabel(
                self.frame_tabela,
                text=ph_val,
                font=ctk.CTkFont(size=13),
                text_color="#d4d4d8",
                anchor="w",
            ).grid(row=row_idx, column=2, sticky="ew", padx=10, pady=9)
            ctk.CTkLabel(
                self.frame_tabela,
                text=turb_val,
                font=ctk.CTkFont(size=13),
                text_color="#d4d4d8",
                anchor="w",
            ).grid(row=row_idx, column=3, sticky="ew", padx=10, pady=9)
            ctk.CTkLabel(
                self.frame_tabela,
                text=tds_val,
                font=ctk.CTkFont(size=13),
                text_color="#d4d4d8",
                anchor="w",
            ).grid(row=row_idx, column=4, sticky="ew", padx=10, pady=9)

            bg_reg, fg_reg = get_badge_colors(class_regra)
            ctk.CTkLabel(
                self.frame_tabela,
                text=class_regra,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=fg_reg,
                fg_color=bg_reg,
                corner_radius=6,
                padx=8,
                pady=3,
            ).grid(row=row_idx, column=5, sticky="w", padx=10, pady=9)

            bg_ia, fg_ia = get_badge_colors(class_ia)
            ctk.CTkLabel(
                self.frame_tabela,
                text=ia_full,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=fg_ia,
                fg_color=bg_ia,
                corner_radius=6,
                padx=8,
                pady=3,
            ).grid(row=row_idx, column=6, sticky="w", padx=10, pady=9)

            bg_st, fg_st = get_badge_colors(status_curto)
            ctk.CTkLabel(
                self.frame_tabela,
                text=status_curto,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=fg_st,
                fg_color=bg_st,
                corner_radius=6,
                padx=10,
                pady=3,
            ).grid(row=row_idx, column=7, sticky="w", padx=10, pady=9)

    def abrir_configuracoes(self):
        self.limpar_conteudo()
        lbl_titulo = ctk.CTkLabel(
            self.frame_conteudo,
            text="Configurações",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        lbl_titulo.pack(anchor="w", padx=24, pady=(22, 6))
        ctk.CTkLabel(
            self.frame_conteudo,
            text="Gerenciamento de conexões, status da infraestrutura e parâmetros da IA",
            text_color="gray",
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=24, pady=(0, 22))

        def add_info_row(
            parent, label, value, row, cor_texto="#d4d4d8", cor_fundo="transparent"
        ):
            lbl_tit = ctk.CTkLabel(
                parent,
                text=label,
                text_color="gray",
                font=ctk.CTkFont(size=14),
            )
            lbl_tit.grid(row=row, column=0, sticky="w", padx=18, pady=10)
            lbl_val = ctk.CTkLabel(
                parent,
                text=value,
                text_color=cor_texto,
                fg_color=cor_fundo,
                corner_radius=6,
                padx=10,
                pady=3,
                font=ctk.CTkFont(size=14, weight="bold"),
            )
            lbl_val.grid(row=row, column=1, sticky="e", padx=18, pady=10)
            parent.grid_columnconfigure(1, weight=1)

        # --- GRID SUPERIOR (2 Cards Idênticos) ---
        frame_top = ctk.CTkFrame(self.frame_conteudo, fg_color="transparent")
        frame_top.pack(fill="x", padx=24, pady=12)
        frame_top.grid_columnconfigure(0, weight=1, uniform="colunas_topo")
        frame_top.grid_columnconfigure(1, weight=1, uniform="colunas_topo")

        # Card 1: MQTT
        card_mqtt = ctk.CTkFrame(
            frame_top, corner_radius=12, fg_color="#1f2937"
        )
        card_mqtt.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        ctk.CTkLabel(
            card_mqtt,
            text="Conexão MQTT",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=18, pady=(18, 10))
        f_mqtt_info = ctk.CTkFrame(card_mqtt, fg_color="transparent")
        f_mqtt_info.pack(fill="both", expand=True, pady=(4, 12))
        add_info_row(
            f_mqtt_info,
            "Broker:",
            "broker.hivemq.com",
            0,
            cor_texto="#34d399",
            cor_fundo="#064e3b",
        )
        add_info_row(f_mqtt_info, "Porta:", "1883", 1)
        add_info_row(
            f_mqtt_info,
            "Status da Conexão:",
            "Conectado",
            2,
            cor_texto="#34d399",
            cor_fundo="#064e3b",
        )

        # Card 2: Banco de Dados Neon
        card_neon = ctk.CTkFrame(
            frame_top, corner_radius=12, fg_color="#1f2937"
        )
        card_neon.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        ctk.CTkLabel(
            card_neon,
            text="Banco de Dados (Neon Cloud)",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=18, pady=(18, 10))
        f_neon_info = ctk.CTkFrame(card_neon, fg_color="transparent")
        f_neon_info.pack(fill="both", expand=True, pady=(4, 12))
        add_info_row(f_neon_info, "Provedor:", "PostgreSQL na Nuvem", 0)
        add_info_row(
            f_neon_info,
            "Status:",
            "Online (Pool ativo)",
            1,
            cor_texto="#34d399",
            cor_fundo="#064e3b",
        )
        add_info_row(
            f_neon_info,
            "Conexão:",
            "Ativa",
            2,
            cor_texto="#34d399",
            cor_fundo="#064e3b",
        )

        # --- GRID INFERIOR (1 Card Largo com 2 colunas dentro) ---
        card_ia = ctk.CTkFrame(
            self.frame_conteudo, corner_radius=12, fg_color="#1f2937"
        )
        card_ia.pack(fill="x", padx=24, pady=12)
        ctk.CTkLabel(
            card_ia,
            text="Inteligência Artificial & Faixa de Referência",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=18, pady=(18, 8))

        frame_ia_inner = ctk.CTkFrame(card_ia, fg_color="transparent")
        frame_ia_inner.pack(fill="x", pady=(4, 14))
        frame_ia_inner.grid_columnconfigure(0, weight=1, uniform="colunas_base")
        frame_ia_inner.grid_columnconfigure(1, weight=1, uniform="colunas_base")

        # Lado Esquerdo: Status IA
        col_ia = ctk.CTkFrame(frame_ia_inner, fg_color="transparent")
        col_ia.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        ctk.CTkLabel(
            col_ia,
            text="Status do Modelo IA",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#d4d4d8",
        ).pack(anchor="w", padx=18, pady=(6, 10))
        f_ia_info = ctk.CTkFrame(col_ia, fg_color="transparent")
        f_ia_info.pack(fill="both", expand=True)
        add_info_row(f_ia_info, "Modelo:", "water_model.pkl", 0)
        add_info_row(
            f_ia_info,
            "Status:",
            "Carregado com sucesso",
            1,
            cor_texto="#34d399",
            cor_fundo="#064e3b",
        )
        add_info_row(f_ia_info, "Algoritmo:", "Scikit-Learn Random Forest", 2)

        # Lado Direito: Faixas de Referência
        col_regras = ctk.CTkFrame(frame_ia_inner, fg_color="transparent")
        col_regras.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        ctk.CTkLabel(
            col_regras,
            text="Faixas de Referência",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#d4d4d8",
        ).pack(anchor="w", padx=18, pady=(6, 10))
        f_reg_info = ctk.CTkFrame(col_regras, fg_color="transparent")
        f_reg_info.pack(fill="both", expand=True)
        add_info_row(f_reg_info, "pH:", "6.0 a 9.0", 0)
        add_info_row(f_reg_info, "Turbidez:", "<= 100.0 NTU", 1)
        add_info_row(f_reg_info, "TDS:", "<= 500 ppm", 2)

    def verificar_api(self):
        try:
            resposta = requests.get("http://127.0.0.1:8000/", timeout=3)
            if resposta.status_code == 200:
                self.lbl_status_api.configure(
                    text="🟢 API Online", text_color="green"
                )
        except Exception:
            self.lbl_status_api.configure(
                text="🔴 API Offline", text_color="red"
            )
        self.after(5000, self.verificar_api)


if __name__ == "__main__":
    app = AppTCC()
    app.mainloop()