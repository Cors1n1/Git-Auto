import os
import subprocess
import requests
import threading
import json
import time
import datetime
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pystray
from PIL import Image, ImageDraw

script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, ".env"))

API_KEY     = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER  = os.getenv("GITHUB_USERNAME")
HISTORY_FILE = os.path.join(script_dir, "history.json")

if not API_KEY or not GITHUB_TOKEN or not GITHUB_USER:
    import tkinter as _tk
    _root = _tk.Tk(); _root.withdraw()
    messagebox.showerror("Configuração incompleta",
        "Verifique se GEMINI_API_KEY, GITHUB_TOKEN e GITHUB_USERNAME\nestão definidos no arquivo .env")
    exit(1)

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-3.1-flash-lite')

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Paleta de cores centralizada ──────────────────────────────────────────────
C = {
    "bg":          "#0f1117",
    "sidebar":     "#13151c",
    "card":        "#1a1d27",
    "card_border": "#252836",
    "input_bg":    "#1e2130",
    "green":       "#2ecc71",
    "green_dark":  "#27ae60",
    "blue":        "#3b82f6",
    "blue_dark":   "#2563eb",
    "orange":      "#f39c12",
    "red":         "#e74c3c",
    "red_dark":    "#c0392b",
    "muted":       "#4b5563",
    "text":        "#e2e8f0",
    "text_dim":    "#94a3b8",
    "success_bg":  "#0d2818",
    "warn_bg":     "#2c1a04",
    "console_bg":  "#080b10",
    "console_fg":  "#a3e635",
}

def load_history() -> list:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_history(data: list):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Dialog "Novo Projeto" ──────────────────────────────────────────────────────
class NewProjectDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        self.title("Novo Repositório")
        self.geometry("480x340")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color=C["bg"])

        # Cabeçalho
        hdr = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🚀  Criar Novo Repositório",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=C["text"]).pack(side="left", padx=20, pady=15)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=20)

        # Nome do repositório
        ctk.CTkLabel(body, text="Nome do repositório",
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=C["text_dim"]).pack(anchor="w")
        self.entry_name = ctk.CTkEntry(body, height=40,
                                       font=ctk.CTkFont("Consolas", 13),
                                       fg_color=C["input_bg"],
                                       border_color=C["card_border"],
                                       text_color=C["text"],
                                       placeholder_text="ex: meu-projeto-incrivel")
        self.entry_name.pack(fill="x", pady=(4, 16))
        self.entry_name.bind("<Return>", lambda e: self._confirm())

        # Descrição
        ctk.CTkLabel(body, text="Descrição  (opcional)",
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=C["text_dim"]).pack(anchor="w")
        self.entry_desc = ctk.CTkEntry(body, height=36,
                                       font=ctk.CTkFont("Segoe UI", 12),
                                       fg_color=C["input_bg"],
                                       border_color=C["card_border"],
                                       text_color=C["text"],
                                       placeholder_text="Breve descrição do projeto...")
        self.entry_desc.pack(fill="x", pady=(4, 16))

        # Opções inline
        opts = ctk.CTkFrame(body, fg_color="transparent")
        opts.pack(fill="x", pady=(0, 20))
        self.sw_private = ctk.CTkSwitch(opts, text="  Repositório Privado",
                                        font=ctk.CTkFont("Segoe UI", 12),
                                        progress_color=C["blue"],
                                        button_color=C["text"],
                                        text_color=C["text_dim"])
        self.sw_private.pack(side="left")

        # Botões
        btns = ctk.CTkFrame(body, fg_color="transparent")
        btns.pack(fill="x")
        btns.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(btns, text="Cancelar", height=40,
                      fg_color=C["muted"], hover_color=C["red_dark"],
                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      command=self.destroy).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(btns, text="✓  Criar e Enviar", height=40,
                      fg_color=C["green_dark"], hover_color=C["green"],
                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      command=self._confirm).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        self.entry_name.focus()

    def _confirm(self):
        name = self.entry_name.get().strip().replace(" ", "-")
        if not name:
            self.entry_name.configure(border_color=C["red"])
            return
        self.result = {
            "name": name,
            "description": self.entry_desc.get().strip(),
            "private": self.sw_private.get() == 1,
        }
        self.destroy()


# ── Diálogo de Histórico de Commits/Pushes ──────────────────────────────────────────
class ProjectHistoryDialog(ctk.CTkToplevel):
    """Exibe o histórico completo de commits/pushes de um repositório local."""

    def __init__(self, parent, path: str):
        super().__init__(parent)
        self.path = path
        folder_name = os.path.basename(path)
        self.title(f"Histórico  —  {folder_name}")
        self.geometry("680x520")
        self.minsize(500, 380)
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color=C["bg"])

        # Cabeçalho
        hdr = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=f"⏳  Histórico de Commits — {folder_name}",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=C["text"]).pack(side="left", padx=20, pady=14)

        # Barra de info (caminho)
        info = ctk.CTkFrame(self, fg_color=C["input_bg"], corner_radius=0, height=30)
        info.pack(fill="x")
        info.pack_propagate(False)
        ctk.CTkLabel(info, text=path,
                     font=ctk.CTkFont("Consolas", 10),
                     text_color=C["muted"]).pack(side="left", padx=14, pady=6)

        # Cabeçalho da tabela
        col_hdr = ctk.CTkFrame(self, fg_color=C["card_border"], corner_radius=0, height=28)
        col_hdr.pack(fill="x")
        col_hdr.pack_propagate(False)
        for txt, w in [("Hash", 70), ("Data", 140), ("Autor", 140), ("Mensagem", 0)]:
            ctk.CTkLabel(col_hdr, text=txt,
                         font=ctk.CTkFont("Segoe UI", 10, "bold"),
                         text_color=C["text_dim"],
                         width=w if w else 1).pack(side="left", padx=(10, 0), pady=5)

        # Scroll de commits
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                        scrollbar_button_color=C["muted"])
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # Rodapé
        footer = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=46)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        self.count_label = ctk.CTkLabel(footer, text="Carregando...",
                                        font=ctk.CTkFont("Segoe UI", 11),
                                        text_color=C["text_dim"])
        self.count_label.pack(side="left", padx=16, pady=12)
        ctk.CTkButton(footer, text="Fechar", width=90, height=30,
                      font=ctk.CTkFont("Segoe UI", 11),
                      fg_color=C["muted"], hover_color=C["red_dark"],
                      command=self.destroy).pack(side="right", padx=16, pady=8)

        self._load_commits(scroll)

    def _load_commits(self, container):
        if not os.path.isdir(os.path.join(self.path, ".git")):
            ctk.CTkLabel(container,
                         text="⚠  Esta pasta não é um repositório Git.",
                         font=ctk.CTkFont("Segoe UI", 13),
                         text_color=C["orange"]).pack(pady=40)
            self.count_label.configure(text="Repositório inválido")
            return

        fmt = "%H|%ad|%an|%s"
        date_fmt = "%d/%m/%Y %H:%M"
        cmd = f'git -C "{self.path}" log --format="{fmt}" --date=format:"{date_fmt}" --all'

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True,
                                    text=True, encoding="utf-8", errors="replace")
            lines = [l for l in result.stdout.strip().splitlines() if l.strip()]
        except Exception as e:
            ctk.CTkLabel(container,
                         text=f"Erro ao ler o log: {e}",
                         text_color=C["red"]).pack(pady=20)
            return

        if not lines:
            ctk.CTkLabel(container,
                         text="Nenhum commit encontrado neste repositório.",
                         font=ctk.CTkFont("Segoe UI", 12),
                         text_color=C["muted"]).pack(pady=40)
            self.count_label.configure(text="0 commits")
            return

        # Verifica quais hashes foram enviados ao remote
        pushed_cmd = f'git -C "{self.path}" log --remotes --format="%H"'
        try:
            pushed_res = subprocess.run(pushed_cmd, shell=True, capture_output=True,
                                        text=True, encoding="utf-8", errors="replace")
            pushed_hashes = set(pushed_res.stdout.strip().splitlines())
        except Exception:
            pushed_hashes = set()

        for i, raw in enumerate(lines):
            parts = raw.split("|", 3)
            if len(parts) < 4:
                continue
            h_full, date, author, msg = parts
            h_short = h_full[:7]
            pushed = h_full in pushed_hashes

            row = ctk.CTkFrame(container,
                               fg_color=C["card"] if i % 2 == 0 else C["input_bg"],
                               corner_radius=0)
            row.pack(fill="x", pady=0)

            # Hash + badge push
            hash_frame = ctk.CTkFrame(row, fg_color="transparent", width=70)
            hash_frame.pack(side="left", padx=(10, 0), pady=6)
            hash_frame.pack_propagate(False)
            ctk.CTkLabel(hash_frame, text=h_short,
                         font=ctk.CTkFont("Consolas", 11),
                         text_color=C["blue"]).pack(anchor="w")
            if pushed:
                ctk.CTkLabel(hash_frame, text="↑ push",
                             font=ctk.CTkFont("Segoe UI", 8),
                             text_color=C["green"]).pack(anchor="w")

            # Data
            ctk.CTkLabel(row, text=date, width=140,
                         font=ctk.CTkFont("Consolas", 11),
                         text_color=C["text_dim"]).pack(side="left", padx=(10, 0))

            # Autor
            ctk.CTkLabel(row, text=author[:18], width=130,
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=C["text_dim"]).pack(side="left", padx=(10, 0))

            # Mensagem
            ctk.CTkLabel(row, text=msg[:80] + ("…" if len(msg) > 80 else ""),
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=C["text"],
                         anchor="w").pack(side="left", padx=(10, 6), fill="x", expand=True)

        pushed_count = sum(1 for l in lines if l.split("|")[0] in pushed_hashes)
        self.count_label.configure(
            text=f"{len(lines)} commits  │  {pushed_count} enviados ao remote")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Git Auto  |  AI Repository Manager")
        self.geometry("1180x740")
        self.minsize(900, 600)
        self.configure(fg_color=C["bg"])
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self._build_sidebar()
        self._build_main()

        self.load_history_ui()
        self.log("Sistema inicializado. Interface pronta.", "info")

    # ── SIDEBAR ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0,
                                    fg_color=C["sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(4, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(24, 0))
        ctk.CTkLabel(logo_frame, text="⬡ Git Auto",
                     font=ctk.CTkFont("Segoe UI", 22, "bold"),
                     text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="AI-Powered Repository Manager",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=C["text_dim"]).pack(anchor="w")

        # Separador
        ctk.CTkFrame(self.sidebar, height=1, fg_color=C["card_border"]).grid(
            row=1, column=0, sticky="ew", padx=0, pady=16)

        # Status pill
        self.status_pill = ctk.CTkFrame(self.sidebar, fg_color=C["card"],
                                        corner_radius=20, height=36)
        self.status_pill.grid(row=2, column=0, padx=20, sticky="ew")
        self.status_pill.pack_propagate(False)
        self.status_dot = ctk.CTkLabel(self.status_pill, text="●",
                                       font=ctk.CTkFont(size=12),
                                       text_color=C["muted"])
        self.status_dot.pack(side="left", padx=(14, 4))
        self.status_label = ctk.CTkLabel(self.status_pill, text="Aguardando",
                                         font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                         text_color=C["text_dim"])
        self.status_label.pack(side="left")

        # Progress bar
        self.progressbar = ctk.CTkProgressBar(self.sidebar, mode="indeterminate",
                                              height=3, corner_radius=0,
                                              progress_color=C["blue"],
                                              fg_color=C["card_border"])
        self.progressbar.grid(row=3, column=0, sticky="ew", padx=0, pady=(12, 0))
        self.progressbar.set(0)

        # Histórico
        hist_hdr = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        hist_hdr.grid(row=4, column=0, sticky="new", padx=20, pady=(20, 8))
        hist_hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(hist_hdr, text="PROJETOS RECENTES",
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=C["muted"]).grid(row=0, column=0, sticky="w")

        self.btn_clear_history = ctk.CTkButton(
            hist_hdr, text="Limpar tudo", width=80, height=22,
            font=ctk.CTkFont("Segoe UI", 10),
            fg_color="transparent", border_width=1,
            border_color=C["card_border"],
            text_color=C["text_dim"], hover_color=C["red_dark"],
            command=self.clear_all_history)
        self.btn_clear_history.grid(row=0, column=1, sticky="e")

        self.history_frame = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            scrollbar_button_color=C["muted"],
            scrollbar_button_hover_color=C["text_dim"])
        self.history_frame.grid(row=4, column=0, sticky="nsew",
                                padx=10, pady=(52, 10))

    # ── ÁREA PRINCIPAL ────────────────────────────────────────────────────────
    def _build_main(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=28, pady=28)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # ── 1. Workspace card ─────────────────────────────────────────────────
        ws = ctk.CTkFrame(self.main_frame, fg_color=C["card"],
                          corner_radius=12, border_width=1,
                          border_color=C["card_border"])
        ws.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        ws.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(ws, text="DIRETÓRIO DO PROJETO",
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=C["muted"]).grid(
            row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(16, 6))

        self.entry_folder = ctk.CTkEntry(
            ws, height=42, font=ctk.CTkFont("Consolas", 12),
            fg_color=C["input_bg"], border_color=C["card_border"],
            text_color=C["text"], placeholder_text="Selecione o caminho do projeto...")
        self.entry_folder.insert(0, os.getcwd())
        self.entry_folder.grid(row=1, column=0, columnspan=2,
                               sticky="ew", padx=20, pady=(0, 18))

        self.btn_browse = ctk.CTkButton(
            ws, text="📂  Procurar", width=130, height=42,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=C["muted"], hover_color=C["blue"],
            command=self.browse_folder)
        self.btn_browse.grid(row=1, column=2, padx=(0, 20), pady=(0, 18))

        # ── 2. Action cards ───────────────────────────────────────────────────
        self.actions_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.actions_frame.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        self.actions_frame.grid_columnconfigure((0, 1), weight=1)

        # Card — Atualizar
        cu = ctk.CTkFrame(self.actions_frame, fg_color=C["card"], corner_radius=12,
                          border_width=1, border_color="#1e3a5f")
        cu.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        cu.grid_columnconfigure(0, weight=1)

        top_u = ctk.CTkFrame(cu, fg_color="transparent")
        top_u.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 0))
        ctk.CTkLabel(top_u, text="🔄", font=ctk.CTkFont(size=26)).pack(side="left", padx=(0, 10))
        txt_u = ctk.CTkFrame(top_u, fg_color="transparent")
        txt_u.pack(side="left")
        ctk.CTkLabel(txt_u, text="Atualizar Projeto",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=C["blue"]).pack(anchor="w")
        ctk.CTkLabel(txt_u, text="Detecta mudanças, gera/atualiza README via IA e faz push.",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=C["text_dim"]).pack(anchor="w")

        self.btn_update = ctk.CTkButton(
            cu, text="Executar Fluxo  →", height=44,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=C["blue_dark"], hover_color=C["blue"],
            corner_radius=8, command=self.start_update_thread)
        self.btn_update.grid(row=1, column=0, sticky="ew",
                             padx=20, pady=(14, 18))

        # Card — Novo Projeto
        cn = ctk.CTkFrame(self.actions_frame, fg_color=C["card"], corner_radius=12,
                          border_width=1, border_color="#1a3d2b")
        cn.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        cn.grid_columnconfigure(0, weight=1)

        top_n = ctk.CTkFrame(cn, fg_color="transparent")
        top_n.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 0))
        ctk.CTkLabel(top_n, text="🚀", font=ctk.CTkFont(size=26)).pack(side="left", padx=(0, 10))
        txt_n = ctk.CTkFrame(top_n, fg_color="transparent")
        txt_n.pack(side="left")
        ctk.CTkLabel(txt_n, text="Novo Projeto",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=C["green"]).pack(anchor="w")
        ctk.CTkLabel(txt_n, text="Cria repositório no GitHub, gera README e faz push.",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=C["text_dim"]).pack(anchor="w")

        self.btn_new = ctk.CTkButton(
            cn, text="Criar e Enviar  →", height=44,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=C["green_dark"], hover_color=C["green"],
            corner_radius=8, command=self.start_new_project_thread)
        self.btn_new.grid(row=1, column=0, sticky="ew",
                          padx=20, pady=(14, 18))

        # ── 3. Tabs (Console e Histórico) ─────────────────────────────────────
        self.tabs = ctk.CTkTabview(self.main_frame, fg_color=C["card"],
                                   corner_radius=12, border_width=1,
                                   border_color=C["card_border"],
                                   text_color=C["text_dim"],
                                   segmented_button_selected_color=C["blue_dark"],
                                   segmented_button_selected_hover_color=C["blue"],
                                   segmented_button_unselected_color=C["input_bg"],
                                   segmented_button_unselected_hover_color=C["card_border"])
        self.tabs.grid(row=2, column=0, sticky="nsew")
        
        self.tabs.add("Log de Execução")
        self.tabs.add("Histórico de Pushes (Local)")
        
        tab_log = self.tabs.tab("Log de Execução")
        tab_log.grid_rowconfigure(1, weight=1)
        tab_log.grid_columnconfigure(0, weight=1)
        
        con_hdr = ctk.CTkFrame(tab_log, fg_color="transparent")
        con_hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        con_hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(con_hdr, text=">_ Saída de Comando",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=C["text"]).grid(row=0, column=0, sticky="w")

        self.btn_clear_log = ctk.CTkButton(
            con_hdr, text="Limpar", width=70, height=26,
            font=ctk.CTkFont("Segoe UI", 11),
            fg_color="transparent", border_width=1,
            border_color=C["card_border"],
            text_color=C["text_dim"], hover_color=C["muted"],
            command=self.clear_log)
        self.btn_clear_log.grid(row=0, column=1, sticky="e")

        self.console = ctk.CTkTextbox(
            tab_log,
            font=ctk.CTkFont("Consolas", 12),
            fg_color=C["console_bg"],
            text_color=C["console_fg"],
            wrap="word", corner_radius=0)
        self.console.grid(row=1, column=0, sticky="nsew",
                          padx=10, pady=(4, 10))
                          
        # Aba Histórico
        tab_hist = self.tabs.tab("Histórico de Pushes (Local)")
        tab_hist.grid_rowconfigure(0, weight=1)
        tab_hist.grid_columnconfigure(0, weight=1)
        
        self.project_history_scroll = ctk.CTkScrollableFrame(tab_hist, fg_color="transparent")
        self.project_history_scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # ── SYSTEM TRAY ───────────────────────────────────────────────────────────
    def create_image(self):
        img = Image.new("RGB", (64, 64), color=(15, 17, 23))
        dc  = ImageDraw.Draw(img)
        dc.rectangle([14, 14, 50, 50], fill=(59, 130, 246))
        return img

    def hide_to_tray(self):
        self.withdraw()
        menu = (
            pystray.MenuItem("Abrir Git Auto", self.restore_window),
            pystray.MenuItem("Sair", self.quit_app),
        )
        self.tray_icon = pystray.Icon("Git Auto", self.create_image(),
                                      "Git Auto em execução", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def restore_window(self, icon, item):
        self.tray_icon.stop()
        self.after(0, self.deiconify)

    def quit_app(self, icon, item):
        self.tray_icon.stop()
        self.quit()

    # ── HISTÓRICO ─────────────────────────────────────────────────────────────
    def load_history_ui(self):
        for w in self.history_frame.winfo_children():
            w.destroy()

        history = load_history()

        if not history:
            ctk.CTkLabel(self.history_frame,
                         text="Nenhum projeto ainda.\nUse 'Novo Projeto' para começar.",
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=C["muted"], justify="center").pack(pady=30)
            return

        for entry in reversed(history):
            # Suporte a entradas antigas (só string) e novas (dict)
            if isinstance(entry, str):
                entry = {"path": entry, "date": "", "branch": "", "status": "ok"}

            path   = entry.get("path", "")
            date   = entry.get("date", "")
            branch = entry.get("branch", "master")
            status = entry.get("status", "ok")   # "ok" | "erro"

            folder_name  = os.path.basename(path)
            display_path = path if len(path) <= 32 else f"…{path[-29:]}"
            exists       = os.path.isdir(path)

            # Card Premium do Histórico
            card = ctk.CTkFrame(self.history_frame, fg_color="#181b21",
                                corner_radius=8, border_width=1, border_color="#2b2e38")
            card.pack(fill="x", pady=6, padx=2)
            card.grid_columnconfigure(1, weight=1)
            
            icon_color = "#2ecc71" if status == "ok" else "#e74c3c"
            
            # Barra lateral colorida (Indicador de Status)
            status_bar = ctk.CTkFrame(card, fg_color=icon_color, width=4, corner_radius=4)
            status_bar.grid(row=0, column=0, sticky="ns", pady=8, padx=(6, 0))
            
            # Informações principais
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.grid(row=0, column=1, sticky="w", padx=12, pady=12)
            
            ctk.CTkLabel(info_frame, text=folder_name, 
                         font=ctk.CTkFont("Segoe UI", 13, "bold"), 
                         text_color="#e2e8f0").pack(anchor="w")
                         
            status_text = "Sincronizado" if status == "ok" else "Erro no último push"
            ctk.CTkLabel(info_frame, text=f"{date}  •  {status_text}", 
                         font=ctk.CTkFont("Segoe UI", 10), 
                         text_color=icon_color if status != "ok" else "#94a3b8").pack(anchor="w", pady=(2, 0))

            # Ações rápidas
            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.grid(row=0, column=2, sticky="e", padx=(0, 10))
            
            ctk.CTkButton(actions, text="Abrir", width=60, height=28,
                          font=ctk.CTkFont("Segoe UI", 11, "bold"),
                          fg_color="#2563eb", hover_color="#3b82f6", text_color="white",
                          corner_radius=6,
                          command=lambda p=path: self.set_folder_from_history(p)).pack(side="left", padx=(0, 5))
                          
            ctk.CTkButton(actions, text="✕", width=28, height=28,
                          font=ctk.CTkFont("Segoe UI", 12, "bold"),
                          fg_color="transparent", hover_color="#c0392b", text_color="#94a3b8",
                          corner_radius=6,
                          command=lambda p=path: self.remove_from_history(p)).pack(side="left")

    def open_project_history(self, path):
        self.set_folder_from_history(path)
        dialog = ProjectHistoryDialog(self, path)

    def set_folder_from_history(self, path):
        self.entry_folder.delete(0, "end")
        self.entry_folder.insert(0, path)
        self.log(f"[INFO] Diretório carregado: {path}", "info")
        self.load_project_commits(path)

    def load_project_commits(self, path):
        self.tabs.set("Histórico de Pushes (Local)")
        for w in self.project_history_scroll.winfo_children():
            w.destroy()
            
        if not os.path.isdir(os.path.join(path, ".git")):
            ctk.CTkLabel(self.project_history_scroll, text="Repositório Git não inicializado.", text_color=C["muted"]).pack(pady=40)
            return
            
        cmd = f'git -C "{path}" log --remotes --format="%ad" --date=format:"%d/%m/%Y %H:%M"'
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
            lines = [l for l in res.stdout.strip().splitlines() if l.strip()]
        except Exception:
            lines = []
            
        if not lines:
            ctk.CTkLabel(self.project_history_scroll, text="Nenhum push efetuado neste repositório ainda.", text_color=C["muted"]).pack(pady=40)
            return
            
        folder_name = os.path.basename(path)
        
        for date in lines:
            card = ctk.CTkFrame(self.project_history_scroll, fg_color="transparent")
            card.pack(fill="x", pady=2)
            
            btn_text = f"✓   {folder_name}   •   {date}   (Sucesso)"
            
            btn = ctk.CTkButton(card, text=btn_text, anchor="w", height=34,
                                fg_color=C["input_bg"], hover_color=C["card_border"],
                                text_color=C["green"],
                                font=ctk.CTkFont("Segoe UI", 12, "bold"))
            btn.pack(side="left", fill="x", expand=True, padx=4)

    def save_to_history(self, current_path, branch="master", status="ok"):
        history = load_history()
        # Remove entrada antiga do mesmo caminho
        history = [e for e in history
                   if (e if isinstance(e, str) else e.get("path")) != current_path]
        history.append({
            "path":   current_path,
            "date":   datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            "branch": branch,
            "status": status,
        })
        save_history(history)
        self.after(0, self.load_history_ui)

    def remove_from_history(self, target_path):
        history = load_history()
        history = [e for e in history
                   if (e if isinstance(e, str) else e.get("path")) != target_path]
        save_history(history)
        self.load_history_ui()
        self.log(f"[SYS] Removido do histórico: {target_path}", "info")

    def clear_all_history(self):
        if messagebox.askyesno("Limpar histórico",
                               "Remover todos os projetos do histórico?\n(Os arquivos locais não serão apagados.)"):
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
            self.load_history_ui()
            self.log("[SYS] Histórico limpo.", "info")

    # ── ESTADOS / LOG ─────────────────────────────────────────────────────────
    def set_processing_state(self, active: bool):
        state = "disabled" if active else "normal"
        for btn in (self.btn_update, self.btn_new,
                    self.btn_browse, self.btn_clear_history):
            btn.configure(state=state)

        if active:
            self.progressbar.start()
            self.status_pill.configure(fg_color=C["warn_bg"])
            self.status_dot.configure(text_color=C["orange"])
            self.status_label.configure(text="Processando…", text_color=C["orange"])
        else:
            self.progressbar.stop()
            self.progressbar.set(0)
            self.status_pill.configure(fg_color=C["card"])
            self.status_dot.configure(text_color=C["muted"])
            self.status_label.configure(text="Aguardando", text_color=C["text_dim"])

    def log(self, text: str, level: str = "info"):
        """Insere linha no console com prefixo colorido."""
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        prefix_map = {
            "info":    ("▸", C["console_fg"]),
            "warn":    ("⚠", C["orange"]),
            "error":   ("✖", C["red"]),
            "success": ("✔", C["green"]),
            "debug":   ("·", C["muted"]),
        }
        sym, color = prefix_map.get(level, ("▸", C["console_fg"]))
        line = f"[{ts}] {sym}  {text}\n"
        self.console.insert("end", line)
        self.console.see("end")

    def clear_log(self):
        self.console.delete("1.0", "end")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.entry_folder.delete(0, "end")
            self.entry_folder.insert(0, folder)
            self.log(f"[INFO] Pasta selecionada: {folder}", "info")
            self.load_project_commits(folder)

    # ── GIT HELPERS ───────────────────────────────────────────────────────────
    def run_command(self, command, check=True):
        try:
            result = subprocess.run(
                command, shell=True, check=check,
                capture_output=True, text=True,
                encoding="utf-8", errors="replace")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            if check:
                self.log(f"[ERRO] {command}\n{e.stderr.strip()}", "error")
            return ""

    def ensure_gitignore(self):
        if not os.path.exists(".gitignore"):
            conteudo = """# Ambiente
.env
.env.*
!.env.example

# IDEs
.vscode/
.idea/

# SO
.DS_Store
Thumbs.db
desktop.ini

# Python
__pycache__/
*.pyc
*.pyd
*.pyo

# Virtualenvs
venv/
.venv/
env/
.env/

# Build
*.log
build/
dist/
*.egg
*.egg-info/
"""
            with open(".gitignore", "w", encoding="utf-8") as f:
                f.write(conteudo)
            self.log("[SYS] .gitignore gerado.", "info")

    def get_code_changes(self):
        self.ensure_gitignore()
        self.run_command("git add .")
        has_commits = self.run_command("git rev-parse HEAD", check=False)
        if not has_commits:
            return self.run_command("git diff --cached $(git hash-object -t tree /dev/null)")
        return self.run_command("git diff --cached")

    # ── IA / FALLBACK ─────────────────────────────────────────────────────────
    def generate_readme(self, diff):
        self.log("[IA] Analisando código e gerando README…", "info")
        current_readme = ""
        if os.path.exists("README.md"):
            with open("README.md", "r", encoding="utf-8") as f:
                current_readme = f.read()

        prompt = f"""Você é um desenvolvedor back-end sênior. Baseado neste git diff, crie ou
atualize o README.md do projeto. Se o README atual estiver vazio, crie do zero.
Retorne APENAS o markdown final, sem blocos (```markdown).

--- README ATUAL ---
{current_readme}

--- GIT DIFF ---
{diff}
"""
        retry_delays = [15, 30, 60, 120]
        for attempt in range(4):
            try:
                response = model.generate_content(prompt)
                content  = response.text.strip()
                if content.startswith("```markdown"):
                    content = content.replace("```markdown", "", 1)
                if content.endswith("```"):
                    content = content[::-1].replace("```"[::-1], "", 1)[::-1]
                return content

            except google_exceptions.ResourceExhausted as e:
                err = str(e)
                if "PerDay" in err or "per_day" in err.lower():
                    self.log("⚠ Cota diária de IA esgotada. Usando fallback local…", "warn")
                    self.log("  Adicione billing em https://ai.dev/rate-limit para remover o limite.", "debug")
                    return None
                wait = retry_delays[attempt] if attempt < len(retry_delays) else 120
                self.log(f"[IA] Rate-limit. Tentativa {attempt+1}/4 — aguardando {wait}s…", "warn")
                if attempt < 3:
                    time.sleep(wait)
                else:
                    self.log("Limite persistente. Usando fallback local.", "warn")
                    return None

            except google_exceptions.GoogleAPIError as e:
                self.log(f"[IA] Erro API: {type(e).__name__} — {e}", "error")
                return None
            except Exception as e:
                self.log(f"[IA] Erro inesperado: {type(e).__name__} — {e}", "error")
                return None
        return None

    def generate_readme_fallback(self):
        self.log("[SYS] Gerando README a partir da estrutura local…", "info")
        cwd          = os.getcwd()
        project_name = os.path.basename(cwd)
        extensions   = {}
        all_files    = []
        ignored_dirs = {".git", "__pycache__", "node_modules", ".venv",
                        "venv", "env", "dist", "build"}

        for root, dirs, files in os.walk(cwd):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for fname in files:
                rel = os.path.relpath(os.path.join(root, fname), cwd)
                all_files.append(rel)
                ext = os.path.splitext(fname)[1].lower()
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1

        lang_map = {
            ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
            ".java": "Java", ".cs": "C#", ".cpp": "C++", ".c": "C",
            ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
            ".swift": "Swift", ".kt": "Kotlin", ".html": "HTML/CSS",
        }
        detected_lang = "Não identificada"
        if extensions:
            top_ext = max(extensions, key=extensions.get)
            detected_lang = lang_map.get(top_ext, top_ext.lstrip(".").upper())

        deps_section = ""
        if os.path.exists("requirements.txt"):
            try:
                with open("requirements.txt", encoding="utf-8") as f:
                    deps = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                if deps:
                    deps_section = "\n## Dependências\n\n```\n" + "\n".join(deps[:20]) + "\n```\n"
            except Exception:
                pass
        elif os.path.exists("package.json"):
            try:
                with open("package.json", encoding="utf-8") as f:
                    pkg = json.load(f)
                dl = list(pkg.get("dependencies", {}).keys())
                if dl:
                    deps_section = "\n## Dependências\n\n" + "\n".join(f"- `{d}`" for d in dl[:20]) + "\n"
            except Exception:
                pass

        bad_exts  = {".pyc", ".pyo", ".pyd", ".log", ".lock",
                     ".png", ".jpg", ".ico", ".gif", ".woff", ".ttf"}
        key_files = [f for f in all_files
                     if not any(f.endswith(e) for e in bad_exts)
                     and len(f.split(os.sep)) <= 3]
        files_section = ""
        if key_files:
            files_section = ("\n## Estrutura do Projeto\n\n```\n"
                             + "\n".join(sorted(key_files)[:30]) + "\n```\n")

        readme = f"""# {project_name}

> Documentação gerada automaticamente pelo Git Auto.

## Sobre o Projeto

Repositório **{project_name}**.

- **Linguagem principal:** {detected_lang}
- **Total de arquivos:** {len(all_files)}
{deps_section}{files_section}
## Como Usar

```bash
git clone https://github.com/{GITHUB_USER}/{project_name}.git
cd {project_name}
```

## Contribuição

Contribuições são bem-vindas! Abra uma *issue* ou envie um *pull request*.

## Licença

Distribuído sob a licença MIT.
"""
        self.log("[SYS] README local gerado com sucesso.", "info")
        return readme

    # ── WORKFLOW ──────────────────────────────────────────────────────────────
    def execute_workflow(self, project_path):
        self.run_command("git add README.md")
        self.run_command('git commit -m "docs: atualiza documentação via IA [skip ci]"',
                         check=False)
        branch = self.run_command("git branch --show-current") or "master"
        self.log(f"[GIT] Push → branch '{branch}'…", "info")
        try:
            subprocess.run(
                f"git push -u origin {branch}",
                shell=True, check=True, capture_output=True,
                text=True, encoding="utf-8", errors="replace")
            self.log("✔  Processo finalizado com sucesso! 🎉", "success")
            self.save_to_history(project_path, branch=branch, status="ok")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Push falhou: {e.stderr.strip()}", "error")
            self.log("Verifique o remote: git remote -v", "warn")
            self.save_to_history(project_path, branch=branch, status="erro")
            return False

    # ── THREADS E CONFIRMAÇÕES INLINE ─────────────────────────────────────────
    def ask_inline_confirmation(self, title, message):
        """Pausa a thread atual e mostra um banner de confirmação na UI principal."""
        self._confirm_result = None
        self._confirm_event = threading.Event()
        self.after(0, self._show_inline_confirmation, title, message)
        self._confirm_event.wait()
        return self._confirm_result

    def _show_inline_confirmation(self, title, message):
        # Esconde os cards de ação temporariamente
        self.actions_frame.grid_forget()
        
        # Cria o painel de confirmação integrado
        self.confirm_frame = ctk.CTkFrame(self.main_frame, fg_color=C["warn_bg"], corner_radius=12, border_width=1, border_color=C["orange"])
        self.confirm_frame.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        self.confirm_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.confirm_frame, text=title, font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=C["orange"]).pack(pady=(15, 5))
        ctk.CTkLabel(self.confirm_frame, text=message, font=ctk.CTkFont("Segoe UI", 13), text_color=C["text"]).pack(pady=(0, 20))
        
        btns = ctk.CTkFrame(self.confirm_frame, fg_color="transparent")
        btns.pack(pady=(0, 15))
        
        ctk.CTkButton(btns, text="Cancelar", width=110, height=36,
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      fg_color=C["card_border"], hover_color=C["red_dark"], text_color=C["text"],
                      command=lambda: self._resolve_confirmation(False)).pack(side="left", padx=10)
                      
        ctk.CTkButton(btns, text="Confirmar ✓", width=110, height=36,
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      fg_color=C["green_dark"], hover_color=C["green"], text_color="white",
                      command=lambda: self._resolve_confirmation(True)).pack(side="left", padx=10)

    def _resolve_confirmation(self, result):
        self.confirm_frame.destroy()
        # Restaura os cards de ação originais
        self.actions_frame.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        self._confirm_result = result
        self._confirm_event.set()

    def start_update_thread(self):
        self.set_processing_state(True)
        threading.Thread(target=self.update_existing_project, daemon=True).start()

    def update_existing_project(self):
        path = self.entry_folder.get()
        try:
            os.chdir(path)
            if not os.path.isdir(".git"):
                self.log("[AVISO] Pasta não é um repositório git. Use 'Novo Projeto'.", "warn")
                return

            diff = self.get_code_changes()
            if not diff:
                self.log("[AVISO] Nenhuma alteração detectada.", "warn")
                return

            new_readme = self.generate_readme(diff) or self.generate_readme_fallback()
            if not new_readme:
                self.log("[ERRO] Não foi possível gerar README. Abortando.", "error")
                return

            if self.ask_inline_confirmation("⚠️ Confirmar Ação",
                                            "Documentação gerada com sucesso.\n"
                                            "Salvar README.md, comitar e fazer push remoto agora?"):
                with open("README.md", "w", encoding="utf-8") as f:
                    f.write(new_readme + "\n")
                self.log("[SYS] README.md salvo.", "info")
                self.execute_workflow(path)
            else:
                self.log("[SYS] Operação cancelada pelo usuário.", "info")
        finally:
            self.set_processing_state(False)

    def start_new_project_thread(self):
        dialog = NewProjectDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self.set_processing_state(True)
            threading.Thread(target=self.create_new_project,
                             args=(dialog.result,), daemon=True).start()

    def create_new_project(self, opts: dict):
        path      = self.entry_folder.get()
        repo_name = opts["name"]
        try:
            os.chdir(path)
            self.log(f"[SYS] Configurando: {repo_name}", "info")

            if not os.path.isdir(".git"):
                self.run_command("git init")
                self.log("[GIT] Repositório local inicializado.", "info")

            # Cria no GitHub
            headers = {"Authorization": f"Bearer {GITHUB_TOKEN}",
                       "Accept": "application/vnd.github.v3+json"}
            payload = {"name": repo_name,
                       "private": opts["private"],
                       "description": opts.get("description", "")}
            resp = requests.post("https://api.github.com/user/repos",
                                 json=payload, headers=headers)

            if resp.status_code == 201:
                remote_url = resp.json()["clone_url"]
                self.log(f"[GITHUB] Repositório criado: {remote_url}", "success")
                existing = self.run_command("git remote", check=False)
                if "origin" in existing.split():
                    self.run_command("git remote remove origin", check=False)
                    self.log("[GIT] Remote anterior removido.", "info")
                self.run_command(f"git remote add origin {remote_url}")
                self.log(f"[GIT] Remote configurado → {remote_url}", "info")
                time.sleep(3)
            else:
                msg = resp.json().get("message", "Erro desconhecido")
                err = resp.json().get("errors", "")
                self.log(f"[GITHUB] Erro: {msg} | {err}", "error")
                return

            diff = self.get_code_changes()
            new_readme = self.generate_readme(diff) or self.generate_readme_fallback()
            if not new_readme:
                self.log("[ERRO] Não foi possível gerar README. Abortando.", "error")
                return

            if self.ask_inline_confirmation("🚀 Finalizar Setup",
                                            f"O repositório '{repo_name}' foi criado no GitHub!\n"
                                            "Deseja fazer o upload dos arquivos agora?"):
                with open("README.md", "w", encoding="utf-8") as f:
                    f.write(new_readme + "\n")
                self.execute_workflow(path)
            else:
                self.log("[SYS] Upload cancelado pelo usuário.", "info")
        finally:
            self.set_processing_state(False)


if __name__ == "__main__":
    app = App()
    app.mainloop()