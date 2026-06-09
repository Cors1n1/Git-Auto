import os
import sys
import subprocess

def _ensure_dependencies():
    try:
        import customtkinter
        import google.generativeai
        import dotenv
        import requests
        import pystray
        import PIL
    except ImportError:
        import tkinter as tk
        root = tk.Tk()
        root.title("Git Auto - Configuração Inicial")
        root.geometry("380x150")
        root.eval('tk::PlaceWindow . center')
        tk.Label(root, text="Instalando dependências necessárias...\nIsso só acontece na primeira vez.\n\nPor favor, aguarde alguns instantes...", font=("Segoe UI", 11)).pack(expand=True)
        root.update()
        
        deps = ["customtkinter", "google-generativeai", "python-dotenv", "requests", "pystray", "Pillow"]
        subprocess.run([sys.executable, "-m", "pip", "install"] + deps, capture_output=True)
        root.destroy()
        
        os.execv(sys.executable, ['python'] + sys.argv)

_ensure_dependencies()

import requests
import threading
import json
import time
import datetime
import unicodedata
import re
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pystray
from PIL import Image, ImageDraw, ImageTk, ImageOps
import ctypes
import io

script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, ".env"), override=True)

APP_THEME = os.getenv("APP_THEME", "Dark")
APP_COLOR = os.getenv("APP_COLOR", "Azul")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DATA_DIR = os.path.join(script_dir, "data")
os.makedirs(DATA_DIR, exist_ok=True)

HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
CACHE_PROFILE = os.path.join(DATA_DIR, "profile_cache.json")
CACHE_REPOS = os.path.join(DATA_DIR, "repos_cache.json")
CACHE_AVATAR = os.path.join(DATA_DIR, "avatar_cache.png")
CACHE_EVENTS = os.path.join(DATA_DIR, "events_cache.json")
CACHE_GRAPH = os.path.join(DATA_DIR, "graph_cache.json")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.1-flash-lite')

ctk.set_appearance_mode(APP_THEME)
ctk.set_default_color_theme("blue")

# ── Paleta de cores centralizada ──────────────────────────────────────────────
C = {}

def set_title_bar_color(window, bg_hex, text_hex=None):
    if os.name != 'nt':
        return
    try:
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        bg_hex = bg_hex.lstrip('#')
        r, g, b = int(bg_hex[0:2], 16), int(bg_hex[2:4], 16), int(bg_hex[4:6], 16)
        bg_colorref = 0x00000000 | (b << 16) | (g << 8) | r
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(ctypes.c_int(bg_colorref)), ctypes.sizeof(ctypes.c_int))
        if text_hex:
            text_hex = text_hex.lstrip('#')
            tr, tg, tb = int(text_hex[0:2], 16), int(text_hex[2:4], 16), int(text_hex[4:6], 16)
            text_colorref = 0x00000000 | (tb << 16) | (tg << 8) | tr
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 36, ctypes.byref(ctypes.c_int(text_colorref)), ctypes.sizeof(ctypes.c_int))
    except Exception:
        pass

def update_palette(app_theme, app_color):
    global C
    if app_theme == "GitHub Light": ctk.set_appearance_mode("light")
    else: ctk.set_appearance_mode("dark")
    
    if app_theme == "GitHub Light":
        C.update({
            "bg":          "#ffffff",
            "sidebar":     "#f6f8fa",
            "card":        "#ffffff",
            "card_border": "#d0d7de",
            "input_bg":    "#f6f8fa",
            "green":       "#2da44e",
            "green_dark":  "#1a7f37",
            "blue":        "#0969da",
            "blue_dark":   "#0550ae",
            "orange":      "#bf8700",
            "red":         "#cf222e",
            "red_dark":    "#a40e26",
            "muted":       "#57606a",
            "text":        "#24292f",
            "text_dim":    "#57606a",
            "success_bg":  "#dafbe1",
            "warn_bg":     "#fff8c5",
            "console_bg":  "#f6f8fa",
            "console_fg":  "#24292f",
        })
    elif app_theme == "VSCode Modern":
        C.update({
            "bg":          "#181818",
            "sidebar":     "#1f1f1f",
            "card":        "#1f1f1f",
            "card_border": "#333333",
            "input_bg":    "#2b2b2b",
            "green":       "#4eb071",
            "green_dark":  "#3c8656",
            "blue":        "#007acc",
            "blue_dark":   "#005a9e",
            "orange":      "#d18616",
            "red":         "#f14c4c",
            "red_dark":    "#d13b3b",
            "muted":       "#858585",
            "text":        "#cccccc",
            "text_dim":    "#a0a0a0",
            "success_bg":  "#1e2e23",
            "warn_bg":     "#3b2e1b",
            "console_bg":  "#1e1e1e",
            "console_fg":  "#d4d4d4",
        })
    elif app_theme == "Vercel Black":
        C.update({
            "bg":          "#000000",
            "sidebar":     "#000000",
            "card":        "#0a0a0a",
            "card_border": "#333333",
            "input_bg":    "#000000",
            "green":       "#0070f3",
            "green_dark":  "#0051a2",
            "blue":        "#ededed",
            "blue_dark":   "#a1a1a1",
            "orange":      "#f5a623",
            "red":         "#e00000",
            "red_dark":    "#cc0000",
            "muted":       "#666666",
            "text":        "#ededed",
            "text_dim":    "#a1a1a1",
            "success_bg":  "#001a00",
            "warn_bg":     "#1a1000",
            "console_bg":  "#000000",
            "console_fg":  "#ededed",
        })
    elif app_theme == "Dracula PRO":
        C.update({
            "bg":          "#22212C",
            "sidebar":     "#1E1E28",
            "card":        "#2D2B3B",
            "card_border": "#454158",
            "input_bg":    "#1E1E28",
            "green":       "#80FFEA",
            "green_dark":  "#5CCCBA",
            "blue":        "#8AFF80",
            "blue_dark":   "#6BCC63",
            "orange":      "#FFCA80",
            "red":         "#FF9580",
            "red_dark":    "#CC7766",
            "muted":       "#7970A9",
            "text":        "#F8F8F2",
            "text_dim":    "#B8B4D1",
            "success_bg":  "#2A3D39",
            "warn_bg":     "#3D3126",
            "console_bg":  "#22212C",
            "console_fg":  "#80FFEA",
        })
    elif app_theme == "Catppuccin Mocha":
        C.update({
            "bg":          "#1e1e2e",
            "sidebar":     "#181825",
            "card":        "#313244",
            "card_border": "#45475a",
            "input_bg":    "#11111b",
            "green":       "#a6e3a1",
            "green_dark":  "#94e2d5",
            "blue":        "#89b4fa",
            "blue_dark":   "#89dceb",
            "orange":      "#fab387",
            "red":         "#f38ba8",
            "red_dark":    "#eba0ac",
            "muted":       "#585b70",
            "text":        "#cdd6f4",
            "text_dim":    "#bac2de",
            "success_bg":  "#1f292e",
            "warn_bg":     "#2e222a",
            "console_bg":  "#1e1e2e",
            "console_fg":  "#f5c2e7",
        })
    elif app_theme == "One Dark Pro":
        C.update({
            "bg":          "#282c34",
            "sidebar":     "#21252b",
            "card":        "#2c313a",
            "card_border": "#3e4451",
            "input_bg":    "#1e2227",
            "green":       "#98c379",
            "green_dark":  "#7a9c61",
            "blue":        "#61afef",
            "blue_dark":   "#4e8cbf",
            "orange":      "#d19a66",
            "red":         "#e06c75",
            "red_dark":    "#b3565e",
            "muted":       "#5c6370",
            "text":        "#abb2bf",
            "text_dim":    "#828997",
            "success_bg":  "#2a3328",
            "warn_bg":     "#332b21",
            "console_bg":  "#282c34",
            "console_fg":  "#98c379",
        })
    elif app_theme == "Monokai Pro":
        C.update({
            "bg":          "#2d2a2e",
            "sidebar":     "#221f22",
            "card":        "#3a363b",
            "card_border": "#5b595c",
            "input_bg":    "#19181a",
            "green":       "#a9dc76",
            "green_dark":  "#87b05e",
            "blue":        "#78dce8",
            "blue_dark":   "#60b0ba",
            "orange":      "#fc9867",
            "red":         "#ff6188",
            "red_dark":    "#cc4d6c",
            "muted":       "#727072",
            "text":        "#fcfcfa",
            "text_dim":    "#c1c0c0",
            "success_bg":  "#364528",
            "warn_bg":     "#452b1f",
            "console_bg":  "#2d2a2e",
            "console_fg":  "#a9dc76",
        })
    else: # GitHub Dark (Default)
        C.update({
            "bg":          "#0d1117",
            "sidebar":     "#010409",
            "card":        "#161b22",
            "card_border": "#30363d",
            "input_bg":    "#0d1117",
            "green":       "#238636",
            "green_dark":  "#2ea043",
            "blue":        "#58a6ff",
            "blue_dark":   "#3182ce",
            "orange":      "#d29922",
            "red":         "#f85149",
            "red_dark":    "#da3633",
            "muted":       "#8b949e",
            "text":        "#c9d1d9",
            "text_dim":    "#b1bac4",
            "success_bg":  "#12241b",
            "warn_bg":     "#292000",
            "console_bg":  "#0d1117",
            "console_fg":  "#58a6ff",
        })

    # A Cor de destaque manual só funciona nos temas flexíveis.
    if app_theme in ["GitHub Dark", "GitHub Light", "VSCode Modern", "Vercel Black"]:
        if app_color == "Verde":
            C["blue"], C["blue_dark"] = C["green"], C["green_dark"]
        elif app_color == "Laranja":
            C["blue"], C["blue_dark"] = C["orange"], "#d68910"
        elif app_color == "Vermelho":
            C["blue"], C["blue_dark"] = C["red"], C["red_dark"]
        elif app_color == "Roxo":
            C["blue"], C["blue_dark"] = "#8b5cf6", "#7c3aed"

update_palette(APP_THEME, APP_COLOR)

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
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))

        # Cabeçalho
        hdr = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Criar Novo Repositório",
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
        raw_name = self.entry_name.get().strip()
        if not raw_name:
            self.entry_name.configure(border_color=C["red"])
            return
            
        # Limpa o nome: remove acentos, troca espaços por hífens, e remove caracteres inválidos
        name = unicodedata.normalize('NFKD', raw_name).encode('ASCII', 'ignore').decode('ASCII')
        name = re.sub(r'[^a-zA-Z0-9_\-\.]', '-', name)
        name = re.sub(r'-+', '-', name).strip('-').lower()
        
        self.result = {
            "name": name,
            "description": self.entry_desc.get().strip(),
            "private": self.sw_private.get() == 1,
        }
        self.destroy()

class TimeMachineDialog(ctk.CTkToplevel):
    def __init__(self, parent, commit_info, repo_name):
        super().__init__(parent)
        self.repo_name = repo_name
        self.title("Aviso Crítico")
        self.geometry("450x540")
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=C["bg"])
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))
        self.result = False
        
        # Header
        ctk.CTkLabel(self, text="MÁQUINA DO TEMPO", font=ctk.CTkFont("Segoe UI", 20, "bold"), text_color=C["red"]).pack(pady=(25, 5))
        
        # Message
        msg_frame = ctk.CTkFrame(self, fg_color="transparent")
        msg_frame.pack(fill="x", padx=30, pady=10)
        
        warn_txt = "Isso vai APAGAR todas as alterações não salvas e arquivos recém-criados.\n\nO projeto retornará EXATAMENTE ao estado do seguinte commit:"
        ctk.CTkLabel(msg_frame, text=warn_txt, font=ctk.CTkFont("Segoe UI", 13), text_color=C["text"], justify="center", wraplength=380).pack()
        
        # Commit info pill
        pill = ctk.CTkFrame(self, fg_color=C["input_bg"], corner_radius=8, border_width=1, border_color=C["card_border"])
        pill.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(pill, text=f"📌 {commit_info}", font=ctk.CTkFont("Consolas", 11), text_color=C["blue"], wraplength=360).pack(padx=15, pady=15)
        
        ctk.CTkLabel(self, text="Essa ação NÃO pode ser desfeita.", font=ctk.CTkFont("Segoe UI", 13, "bold"), text_color=C["red"]).pack(pady=(0, 10))
        
        # Validation Input
        val_frame = ctk.CTkFrame(self, fg_color="transparent")
        val_frame.pack(fill="x", padx=30, pady=(5, 10))
        ctk.CTkLabel(val_frame, text=f"Digite o nome da pasta para confirmar:\n( {repo_name} )", font=ctk.CTkFont("Segoe UI", 12), text_color=C["text_dim"]).pack(pady=(0, 5))
        
        self.entry_var = ctk.StringVar()
        self.entry_var.trace_add("write", self._check_validation)
        self.entry_val = ctk.CTkEntry(val_frame, textvariable=self.entry_var, font=ctk.CTkFont("Consolas", 12), fg_color=C["input_bg"], border_color=C["card_border"], justify="center")
        self.entry_val.pack(fill="x", padx=20)
        
        # Buttons
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=(10, 20))
        
        ctk.CTkButton(btns, text="Cancelar", width=120, height=36, font=ctk.CTkFont("Segoe UI", 12), fg_color=C["card_border"], hover_color=C["muted"], text_color=C["text"], command=self.destroy).pack(side="left", padx=10)
        self.btn_confirm = ctk.CTkButton(btns, text="💥 SIM, DESCARTAR TUDO", width=200, height=36, font=ctk.CTkFont("Segoe UI", 12, "bold"), fg_color=C["red_dark"], hover_color=C["red"], state="disabled", command=self._confirm)
        self.btn_confirm.pack(side="left", padx=10)
        
    def _check_validation(self, *args):
        if self.entry_var.get().strip() == self.repo_name:
            self.btn_confirm.configure(state="normal")
        else:
            self.btn_confirm.configure(state="disabled")
        
    def _confirm(self):
        self.result = True
        self.destroy()

class DiffViewerDialog(ctk.CTkToplevel):
    def __init__(self, parent, diff_text):
        super().__init__(parent)
        self.title("Diff Lado a Lado")
        self.geometry("1200x700")
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=C["bg"])
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))
        
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(header_frame, text="Visualizador de Diferenças", font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=C["text"]).pack(side="left")
        
        self.parse_diff_text(diff_text)
        files = list(self.diffs_by_file.keys())
        
        if files:
            self.file_selector = ctk.CTkOptionMenu(header_frame, values=files, command=self._on_file_select, width=350, font=ctk.CTkFont("Segoe UI", 12), fg_color=C["card"], button_color=C["card_border"])
            self.file_selector.pack(side="right")
        else:
            self.file_selector = ctk.CTkOptionMenu(header_frame, values=["Nenhum arquivo alterado"], width=350, state="disabled")
            self.file_selector.pack(side="right")
        
        # Titles frame
        titles = ctk.CTkFrame(self, fg_color="transparent")
        titles.pack(fill="x", padx=20, pady=(10, 0))
        titles.grid_columnconfigure(0, weight=1)
        titles.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(titles, text="Original", font=ctk.CTkFont("Segoe UI", 12), text_color=C["text_dim"]).grid(row=0, column=0, sticky="w", padx=10)
        ctk.CTkLabel(titles, text="Modificado", font=ctk.CTkFont("Segoe UI", 12), text_color=C["text_dim"]).grid(row=0, column=1, sticky="w", padx=10)
        
        # Textboxes container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=(5, 10))
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(2, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        font_code = ctk.CTkFont("Consolas", 13)
        
        self.tb_left = ctk.CTkTextbox(container, font=font_code, fg_color=C["console_bg"], text_color=C["text"], border_width=0, wrap="none")
        self.tb_left.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        
        # Divisor
        divisor = ctk.CTkFrame(container, width=1, fg_color=C["card_border"])
        divisor.grid(row=0, column=1, sticky="ns")
        
        self.tb_right = ctk.CTkTextbox(container, font=font_code, fg_color=C["console_bg"], text_color=C["text"], border_width=0, wrap="none")
        self.tb_right.grid(row=0, column=2, sticky="nsew", padx=(2, 0))
        
        # Configure tags (Estilo VSCode)
        for tb in [self.tb_left, self.tb_right]:
            tb.tag_config("deletion", background="#511d1d", foreground="#f48771")
            tb.tag_config("addition", background="#1d3b26", foreground="#61cc86")
            tb.tag_config("header", foreground="#569cd6")
            tb.tag_config("info", foreground="#858585")
            tb.tag_config("blank", foreground=C["console_bg"], background=C["console_bg"])
            
            # Bind sync scroll
            tb.bind("<MouseWheel>", self.sync_scroll)
        
        if files:
            self._on_file_select(files[0])
        else:
            self.insert_diff_side_by_side("")
            self.tb_left.configure(state="disabled")
            self.tb_right.configure(state="disabled")
        
        # Bottom bar
        btn_close = ctk.CTkButton(self, text="Fechar Lente", width=120, height=36, font=ctk.CTkFont("Segoe UI", 12, "bold"), fg_color=C["card_border"], hover_color=C["muted"], text_color=C["text"], command=self.destroy)
        btn_close.pack(pady=(10, 20))

    def sync_scroll(self, event):
        delta = int(-1 * (event.delta / 120))
        self.tb_left._textbox.yview_scroll(delta, "units")
        self.tb_right._textbox.yview_scroll(delta, "units")
        return "break"
        
    def parse_diff_text(self, text):
        self.diffs_by_file = {}
        if not text.strip():
            return
            
        current_file = None
        current_lines = []
        
        for line in text.split('\n'):
            if line.startswith('diff --git '):
                if current_file:
                    self.diffs_by_file[current_file] = '\n'.join(current_lines)
                parts = line.split(' ')
                if len(parts) >= 4:
                    current_file = parts[-1][2:] if parts[-1].startswith('b/') else parts[-1]
                else:
                    current_file = "Desconhecido"
                current_lines = [line]
            else:
                if current_file:
                    current_lines.append(line)
                    
        if current_file:
            self.diffs_by_file[current_file] = '\n'.join(current_lines)

    def _on_file_select(self, filename):
        self.tb_left.configure(state="normal")
        self.tb_right.configure(state="normal")
        self.tb_left.delete("1.0", "end")
        self.tb_right.delete("1.0", "end")
        
        diff_text = self.diffs_by_file.get(filename, "")
        self.insert_diff_side_by_side(diff_text)
        
        self.tb_left.configure(state="disabled")
        self.tb_right.configure(state="disabled")
        
    def insert_diff_side_by_side(self, diff_text):
        if not diff_text.strip():
            self.tb_left.insert("end", " Nenhuma diferença encontrada.", "info")
            self.tb_right.insert("end", " Nenhuma diferença encontrada.", "info")
            return
            
        del_buf = []
        add_buf = []
        
        def flush_buffers():
            n = max(len(del_buf), len(add_buf))
            for i in range(n):
                dl = del_buf[i] if i < len(del_buf) else ""
                al = add_buf[i] if i < len(add_buf) else ""
                
                if dl:
                    self.tb_left.insert("end", dl + "\n", "deletion")
                else:
                    self.tb_left.insert("end", "\n", "blank")
                    
                if al:
                    self.tb_right.insert("end", al + "\n", "addition")
                else:
                    self.tb_right.insert("end", "\n", "blank")
            del_buf.clear()
            add_buf.clear()
            
        lines = diff_text.split('\n')
        for line in lines:
            if line.startswith('diff --git') or line.startswith('+++') or line.startswith('---'):
                flush_buffers()
                self.tb_left.insert("end", "\n" + line + "\n", "header")
                self.tb_right.insert("end", "\n" + line + "\n", "header")
            elif line.startswith('@@'):
                flush_buffers()
                self.tb_left.insert("end", "\n" + line + "\n", "info")
                self.tb_right.insert("end", "\n" + line + "\n", "info")
            elif line.startswith('-'):
                del_buf.append(line)
            elif line.startswith('+'):
                add_buf.append(line)
            else: 
                flush_buffers()
                self.tb_left.insert("end", line + "\n")
                self.tb_right.insert("end", line + "\n")
        flush_buffers()

class ReleaseManagerDialog(ctk.CTkToplevel):
    def __init__(self, parent, repo_path):
        super().__init__(parent)
        self.parent_app = parent
        self.repo_path = repo_path
        self.title("Versões (Releases)")
        self.geometry("700x750")
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=C["bg"])
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))
        
        # Header
        ctk.CTkLabel(self, text="Lançar Versão", font=ctk.CTkFont("Segoe UI", 20, "bold"), text_color=C["orange"]).pack(pady=(20, 5))
        ctk.CTkLabel(self, text="Crie um 'Patch Note' oficial e publico no GitHub.", font=ctk.CTkFont("Segoe UI", 12), text_color=C["text_dim"]).pack(pady=(0, 20))
        
        # Inputs
        inputs_frame = ctk.CTkFrame(self, fg_color="transparent")
        inputs_frame.pack(fill="x", padx=30)
        
        ctk.CTkLabel(inputs_frame, text="Tag da Versão (ex: v1.0.0):", font=ctk.CTkFont("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        self.entry_tag = ctk.CTkEntry(inputs_frame, width=150, font=ctk.CTkFont("Consolas", 12), fg_color=C["input_bg"], border_color=C["card_border"])
        self.entry_tag.grid(row=1, column=0, sticky="w", pady=(5, 15), padx=(0, 20))
        self.entry_tag.insert(0, "v1.0.0")
        
        ctk.CTkLabel(inputs_frame, text="Título do Lançamento:", font=ctk.CTkFont("Segoe UI", 12, "bold")).grid(row=0, column=1, sticky="w")
        self.entry_title = ctk.CTkEntry(inputs_frame, width=400, font=ctk.CTkFont("Segoe UI", 12), fg_color=C["input_bg"], border_color=C["card_border"])
        self.entry_title.grid(row=1, column=1, sticky="ew", pady=(5, 15))
        self.entry_title.insert(0, "Lançamento Oficial")
        
        # Generator Button
        self.btn_gen = ctk.CTkButton(self, text="Gerar Notas com IA", height=36, font=ctk.CTkFont("Segoe UI", 12, "bold"), fg_color=C["blue"], hover_color=C["blue_dark"], command=self._generate_notes)
        self.btn_gen.pack(fill="x", padx=30, pady=(0, 5))
        
        self.progress_ai = ctk.CTkProgressBar(self, mode="indeterminate", fg_color=C["input_bg"], progress_color=C["orange"], height=4)
        self.progress_ai.set(0)
        # We don't pack the progress bar yet.
        ctk.CTkFrame(self, height=10, fg_color="transparent").pack() # Spacing
        
        # Textbox
        ctk.CTkLabel(self, text="Notas da Versão (Markdown):", font=ctk.CTkFont("Segoe UI", 12, "bold")).pack(anchor="w", padx=30)
        self.tb_notes = ctk.CTkTextbox(self, font=ctk.CTkFont("Consolas", 12), fg_color=C["input_bg"], text_color=C["text"], border_width=1, border_color=C["card_border"])
        self.tb_notes.pack(fill="both", expand=True, padx=30, pady=(5, 20))
        
        # Bottom Buttons
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=(0, 20))
        
        ctk.CTkButton(btns, text="Cancelar", width=120, height=36, fg_color=C["card_border"], hover_color=C["muted"], text_color=C["text"], command=self.destroy).pack(side="left", padx=10)
        ctk.CTkButton(btns, text="Publicar no GitHub", width=180, height=36, font=ctk.CTkFont("Segoe UI", 12, "bold"), fg_color=C["orange"], hover_color="#d68910", text_color="#ffffff", command=self._publish).pack(side="left", padx=10)
        
    def _generate_notes(self):
        self.btn_gen.configure(text="Gerando...", state="disabled")
        self.progress_ai.pack(fill="x", padx=30, pady=(0, 10))
        self.progress_ai.start()
        self.update()
        
        import threading
        def task():
            try:
                import subprocess
                prev_tag = subprocess.run("git describe --tags --abbrev=0", shell=True, capture_output=True, text=True, cwd=self.repo_path).stdout.strip()
                
                cmd = f"git log {prev_tag}..HEAD --oneline" if prev_tag else "git log --oneline"
                commits = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=self.repo_path).stdout.strip()
                
                if not commits:
                    self.parent_app.after(0, lambda: self._set_notes("Nenhum commit novo encontrado desde o último lançamento."))
                    return
                    
                import google.generativeai as genai
                prompt = f"Gere o 'Release Note' técnico em Markdown baseado nestes commits.\nProibido: usar introduções corporativas, saudações, conclusões, gírias ou emojis.\nEstrutura EXIGIDA:\n1. A PRIMEIRA LINHA deve ser estritamente um Título curto e profissional para o Lançamento (ex: Atualização de Interface e Refatoração).\n2. A SEGUNDA LINHA em diante deve ser um parágrafo direto ao ponto explicando o foco da versão.\n3. O resto deve ser um cabeçalho 'Resumo de Alterações' seguido de uma lista em bullet points.\n\nCommits:\n{commits}"
                
                model = genai.GenerativeModel("gemini-3.5-flash")
                resp = model.generate_content(prompt)
                
                text = resp.text.strip()
                lines = text.split("\n", 1)
                title_gen = lines[0].replace("#", "").replace("*", "").strip() if lines else ""
                body_gen = lines[1].strip() if len(lines) > 1 else text
                
                self.parent_app.after(0, lambda: self._set_notes(body_gen, title=title_gen))
            except Exception as e:
                error_msg = str(e)
                self.parent_app.after(0, lambda msg=error_msg: self._set_notes(f"Erro ao gerar notas: {msg}"))
            finally:
                def _reset_ui():
                    self.btn_gen.configure(text="Gerar Notas com IA", state="normal")
                    self.progress_ai.stop()
                    self.progress_ai.pack_forget()
                self.parent_app.after(0, _reset_ui)
                
        threading.Thread(target=task, daemon=True).start()
        
    def _set_notes(self, text, title=None):
        if title is not None:
            self.entry_title.delete(0, "end")
            self.entry_title.insert(0, title)
        self.tb_notes.delete("1.0", "end")
        self.tb_notes.insert("end", text)
        
    def _publish(self):
        tag = self.entry_tag.get().strip()
        title = self.entry_title.get().strip()
        body = self.tb_notes.get("1.0", "end").strip()
        
        if not tag or not title:
            from tkinter import messagebox
            messagebox.showerror("Erro", "Tag e Título são obrigatórios!")
            return
            
        import threading
        def task():
            try:
                import subprocess
                import requests
                import os
                import json
                
                self.parent_app.log(f"[SYS] Criando tag local {tag}...", "info")
                subprocess.run(f'git tag -a {tag} -m "{title}"', shell=True, check=True, cwd=self.repo_path)
                
                self.parent_app.log(f"[SYS] Enviando tag {tag} para o repositório remoto...", "info")
                subprocess.run(f'git push origin {tag}', shell=True, check=True, cwd=self.repo_path)
                
                remote_url = subprocess.run("git config --get remote.origin.url", shell=True, capture_output=True, text=True, cwd=self.repo_path).stdout.strip()
                if not remote_url:
                    self.parent_app.log("[ERRO] Repositório remoto não encontrado. O release local foi criado.", "error")
                    return
                    
                if "github.com" not in remote_url:
                    self.parent_app.log("[SYS] O remote não é GitHub. O release local foi criado.", "warn")
                    return
                    
                parts = remote_url.replace(".git", "").split("/")
                if remote_url.startswith("git@"):
                    parts = remote_url.split(":")[-1].replace(".git", "").split("/")
                    
                owner, repo = parts[-2], parts[-1]
                
                token = os.environ.get("GITHUB_TOKEN", "")
                if not token:
                    try:
                        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            token = data.get("github_token", "")
                    except:
                        pass
                        
                if not token:
                    self.parent_app.log("[ERRO] Token do GitHub não encontrado. Tag enviada, mas Release não publicado na aba Releases.", "error")
                    return
                    
                self.parent_app.log(f"[SYS] Publicando release na aba Releases do GitHub...", "info")
                headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
                payload = {"tag_name": tag, "name": title, "body": body, "draft": False, "prerelease": False}
                
                response = requests.post(f"https://api.github.com/repos/{owner}/{repo}/releases", json=payload, headers=headers)
                if response.status_code == 201:
                    url = response.json().get("html_url")
                    self.parent_app.log(f"🏆 Lançamento {tag} publicado com sucesso! Link: {url}", "success")
                else:
                    self.parent_app.log(f"[ERRO] Falha na API do GitHub: {response.status_code} - {response.text}", "error")
                    
            except Exception as e:
                self.parent_app.log(f"[ERRO] Falha ao publicar: {str(e)}", "error")
            finally:
                self.parent_app.after(0, self.destroy)
                
        threading.Thread(target=task, daemon=True).start()

class GitignoreDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gerador de .gitignore")
        self.geometry("400x450")
        self.transient(parent)
        self.grab_set()
        
        self.configure(fg_color=C["bg"])
        
        ctk.CTkLabel(self, text="Gerar .gitignore", font=ctk.CTkFont("Segoe UI", 18, "bold"), text_color=C["text"]).pack(pady=(20, 5))
        ctk.CTkLabel(self, text="Selecione as tecnologias do seu projeto:", font=ctk.CTkFont("Segoe UI", 12), text_color=C["text_dim"]).pack(pady=(0, 10))
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=C["input_bg"], border_width=1, border_color=C["card_border"])
        self.scroll.pack(fill="both", expand=True, padx=30, pady=10)
        
        templates = ["Python", "Node.js", "React/Next.js", "Java", "C++", "Godot", "Unity", "Generico"]
        self.checkboxes = {}
        
        for t in templates:
            var = ctk.IntVar(value=1 if t == "Python" else 0)
            cb = ctk.CTkCheckBox(self.scroll, text=t, variable=var, font=ctk.CTkFont("Segoe UI", 13), text_color=C["text"], fg_color=C["blue"], hover_color=C["blue_dark"])
            cb.pack(anchor="w", padx=10, pady=8)
            self.checkboxes[t] = var
        
        self.result = None
        
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=20)
        
        ctk.CTkButton(btns, text="Cancelar", width=100, fg_color=C["card_border"], hover_color=C["red_dark"], command=self.destroy).pack(side="left", padx=10)
        ctk.CTkButton(btns, text="Gerar Arquivo", width=120, font=ctk.CTkFont("Segoe UI", 12, "bold"), fg_color=C["blue"], hover_color=C["blue_dark"], command=self._confirm).pack(side="left", padx=10)
        
    def _confirm(self):
        self.result = [t for t, var in self.checkboxes.items() if var.get() == 1]
        self.destroy()

class ProjectReadmeDialog(ctk.CTkToplevel):
    def __init__(self, parent, project_path):
        super().__init__(parent)
        self.title("Visão Geral do Projeto")
        self.geometry("800x600")
        self.transient(parent)
        self.grab_set()
        
        self.configure(fg_color=C["bg"])
        
        lbl_title = ctk.CTkLabel(self, text=f"📦 {os.path.basename(project_path)}", font=ctk.CTkFont("Segoe UI", 20, "bold"), text_color=C["text"])
        lbl_title.pack(pady=(20, 10), padx=20, anchor="w")

        self.textbox = ctk.CTkTextbox(self, font=ctk.CTkFont("Consolas", 13), fg_color=C["card"], text_color=C["text"], border_color=C["card_border"], border_width=1, corner_radius=10, wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        content = self._get_or_generate_readme(project_path)
        self.textbox.insert("0.0", content)
        self.textbox.configure(state="disabled")

        ctk.CTkButton(self, text="Entendido!", height=40, font=ctk.CTkFont("Segoe UI", 13, "bold"), fg_color=C["blue"], hover_color=C["blue_dark"], command=self.destroy).pack(pady=(0, 20), padx=20)

    def _get_or_generate_readme(self, path):
        # Tenta encontrar um README real
        for name in ["README.md", "README.txt", "readme.md", "Readme.md"]:
            p = os.path.join(path, name)
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        content = f.read()
                        return f"--- 📄 {name} encontrado ---\n\n{content}"
                except: pass
        
        # Se não houver, gera um passo-a-passo baseado na análise da pasta
        files = os.listdir(path) if os.path.exists(path) else []
        summary = "Nenhum arquivo README encontrado no repositório.\n\n"
        summary += "--- 🤖 ANÁLISE AUTOMÁTICA DO PROJETO ---\n"
        
        if "requirements.txt" in files or "setup.py" in files or "Pipfile" in files or "release.py" in files or any(f.endswith(".py") for f in files):
            summary += "\n🐍 PROJETO PYTHON DETECTADO.\n\n"
            summary += "Passo a passo genérico para rodar:\n"
            summary += "1. Abra o terminal na pasta do projeto.\n"
            summary += "2. Crie um ambiente virtual (recomendado):\n"
            summary += "   python -m venv venv\n"
            summary += "3. Ative o ambiente:\n"
            summary += "   Windows: venv\\Scripts\\activate\n"
            summary += "   Linux/Mac: source venv/bin/activate\n"
            if "requirements.txt" in files:
                summary += "4. Instale as dependências:\n"
                summary += "   pip install -r requirements.txt\n"
            summary += "5. Execute o script principal (ex: python main.py)\n"
        elif "package.json" in files:
            summary += "\n📦 PROJETO NODE.JS / JAVASCRIPT DETECTADO.\n\n"
            summary += "Passo a passo genérico para rodar:\n"
            summary += "1. Abra o terminal na pasta do projeto.\n"
            summary += "2. Instale as dependências:\n"
            summary += "   npm install   (ou yarn install)\n"
            summary += "3. Inicie o projeto:\n"
            summary += "   npm start     (ou npm run dev)\n"
        elif "pom.xml" in files or "build.gradle" in files:
            summary += "\n☕ PROJETO JAVA DETECTADO.\n\n"
            summary += "Passo a passo genérico para compilar/rodar:\n"
            if "pom.xml" in files:
                summary += "Este projeto usa Maven. Execute:\n"
                summary += "mvn clean install\n"
            else:
                summary += "Este projeto usa Gradle. Execute:\n"
                summary += "gradle build\n"
        else:
            summary += "\n🔍 PROJETO GENÉRICO.\n\n"
            summary += "Não foi possível identificar um ecossistema específico.\n"
            summary += "Explore os arquivos para entender a estrutura e localizar o arquivo principal.\n"
        
        return summary


class CloneProjectView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        # Título Elegante
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(40, 20))
        ctk.CTkLabel(hdr, text="O que você deseja clonar?", font=ctk.CTkFont("Segoe UI", 24, "bold"), text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(hdr, text="Baixe projetos do GitHub diretamente para sua máquina local.", font=ctk.CTkFont("Segoe UI", 13), text_color=C["text_dim"]).pack(anchor="w")

        # Botões de Seleção de Modo (API vs URL)
        self.mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.mode_frame.pack(fill="x", padx=40, pady=(0, 20))
        
        self.btn_mode_api = ctk.CTkButton(self.mode_frame, text="Meus Repositórios (API)", height=44, font=ctk.CTkFont("Segoe UI", 13, "bold"), corner_radius=8, command=lambda: self.set_mode("api"))
        self.btn_mode_api.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_mode_url = ctk.CTkButton(self.mode_frame, text="Via URL (HTTPS/SSH)", height=44, font=ctk.CTkFont("Segoe UI", 13, "bold"), corner_radius=8, command=lambda: self.set_mode("url"))
        self.btn_mode_url.pack(side="left", fill="x", expand=True, padx=(10, 0))

        # Container principal dos painéis
        self.container = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16, border_width=1, border_color=C["card_border"])
        self.container.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frame_api = ctk.CTkFrame(self.container, fg_color="transparent")
        self.frame_url = ctk.CTkFrame(self.container, fg_color="transparent")

        self.selected_repo_url = None
        self._build_api_tab(self.frame_api)
        self._build_url_tab(self.frame_url)
        
        self.set_mode("api")

    def set_mode(self, mode):
        if mode == "api":
            self.btn_mode_api.configure(fg_color=C["blue"], hover_color=C["blue_dark"], text_color="#ffffff")
            self.btn_mode_url.configure(fg_color=C["input_bg"], hover_color=C["card_border"], text_color=C["text_dim"])
            self.frame_url.grid_forget()
            self.frame_api.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        else:
            self.btn_mode_url.configure(fg_color=C["blue"], hover_color=C["blue_dark"], text_color="#ffffff")
            self.btn_mode_api.configure(fg_color=C["input_bg"], hover_color=C["card_border"], text_color=C["text_dim"])
            self.frame_api.grid_forget()
            self.frame_url.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)

    def _build_url_tab(self, frame):
        # Container centralizado para evitar muito espaço vazio
        center_frame = ctk.CTkFrame(frame, fg_color="transparent")
        center_frame.pack(expand=True, fill="x", padx=10)

        ctk.CTkLabel(center_frame, text="URL do Repositório (HTTPS ou SSH):", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=C["text_dim"]).pack(anchor="w", pady=(0, 5))
        self.entry_url = ctk.CTkEntry(center_frame, height=36, font=ctk.CTkFont("Consolas", 11), fg_color=C["input_bg"], border_color=C["card_border"], text_color=C["text"])
        self.entry_url.pack(fill="x", pady=(0, 20))

        self.entry_dest_url = self._build_destination_selector(center_frame)
        
        ctk.CTkButton(center_frame, text="Clonar Projeto", height=40, font=ctk.CTkFont("Segoe UI", 13, "bold"), fg_color=C["blue"], hover_color=C["blue_dark"], command=self._confirm_url).pack(fill="x", pady=(10, 0))

    def _build_api_tab(self, frame):
        if not GITHUB_TOKEN:
            ctk.CTkLabel(frame, text="GitHub Token não configurado.\n\nConfigure nas Configurações para usar este recurso.", font=ctk.CTkFont("Segoe UI", 12), text_color=C["text_dim"], justify="center").pack(expand=True)
            return

        bottom_frame = ctk.CTkFrame(frame, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x")

        self.entry_dest_api = self._build_destination_selector(bottom_frame)
        self.btn_confirm_api = ctk.CTkButton(bottom_frame, text="Clonar Selecionado", height=40, font=ctk.CTkFont("Segoe UI", 13, "bold"), fg_color=C["blue"], hover_color=C["blue_dark"], command=self._confirm_api)
        self.btn_confirm_api.pack(fill="x", pady=10)

        ctk.CTkLabel(frame, text="Meus Repositórios:", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=C["text_dim"]).pack(anchor="w", pady=(5, 5))
        
        self.repo_listbox = ctk.CTkScrollableFrame(frame, fg_color=C["input_bg"])
        self.repo_listbox.pack(fill="both", expand=True, pady=(0, 10))
        
        threading.Thread(target=self._load_repos, daemon=True).start()

    def _build_destination_selector(self, parent):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(container, text="Pasta de Destino Local:", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=C["text_dim"]).pack(anchor="w", pady=(0, 5))
        
        dest_frame = ctk.CTkFrame(container, fg_color="transparent")
        dest_frame.pack(fill="x")
        entry_dest = ctk.CTkEntry(dest_frame, height=36, font=ctk.CTkFont("Consolas", 11), fg_color=C["input_bg"], border_color=C["card_border"], text_color=C["text"])
        entry_dest.pack(side="left", fill="x", expand=True, padx=(0, 10))
        entry_dest.insert(0, os.path.expanduser("~/Desktop"))
        ctk.CTkButton(dest_frame, text="...", width=40, height=36, fg_color=C["card_border"], hover_color=C["blue"], text_color=C["text"], command=lambda e=entry_dest: self._browse(e)).pack(side="left")
        return entry_dest

    def _browse(self, entry):
        d = filedialog.askdirectory(title="Selecione a pasta destino")
        if d:
            entry.delete(0, "end")
            entry.insert(0, d)

    def _load_repos(self):
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        try:
            resp = requests.get(f"https://api.github.com/user/repos?sort=updated&per_page=100", headers=headers, timeout=5)
            if resp.status_code == 200:
                repos = resp.json()
                self.after(0, lambda: self._populate_repos(repos))
            else:
                self.after(0, lambda: self._show_error("Falha ao carregar da API."))
        except Exception:
            self.after(0, lambda: self._show_error("Erro de conexão com o GitHub."))

    def _show_error(self, msg):
        for w in self.repo_listbox.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.repo_listbox, text=msg, text_color=C["red"]).pack(pady=10)

    def _populate_repos(self, repos):
        for w in self.repo_listbox.winfo_children():
            w.destroy()
        if not repos:
            ctk.CTkLabel(self.repo_listbox, text="Nenhum repositório encontrado.", text_color=C["muted"]).pack(pady=10)
            return
            
        self.repo_buttons = []
        for r in repos:
            btn = ctk.CTkButton(self.repo_listbox, text=f"📦 {r['full_name']}", anchor="w", fg_color="transparent", hover_color=C["card_border"], text_color=C["text"], command=lambda url=r['clone_url']: self._select_repo(url))
            btn.pack(fill="x", pady=2)
            btn._my_url = r['clone_url']
            self.repo_buttons.append(btn)

    def _select_repo(self, url):
        self.selected_repo_url = url
        for b in self.repo_buttons:
            if b._my_url == url:
                b.configure(fg_color=C["blue_dark"], text_color="#ffffff")
            else:
                b.configure(fg_color="transparent", text_color=C["text"])
        # Apenas remove a linha de state="normal" que agora é redundante

    def _confirm_url(self):
        url = self.entry_url.get().strip()
        
        # Limpa âncoras e parâmetros caso a URL tenha sido copiada do navegador com seções do README
        if "#" in url:
            url = url.split("#")[0]
            
        dest = self.entry_dest_url.get().strip()
        if not url or not dest:
            messagebox.showwarning("Aviso", "Preencha a URL e a pasta de destino.")
            return
        self.app.start_clone_process({"url": url, "dest": dest})

    def _confirm_api(self):
        dest = self.entry_dest_api.get().strip()
        if not self.selected_repo_url or not dest:
            messagebox.showwarning("Aviso", "Selecione um repositório e a pasta destino.")
            return
        self.app.start_clone_process({"url": self.selected_repo_url, "dest": dest})


# ── Diálogo de Histórico de Commits/Pushes ──────────────────────────────────────────
class BranchManagerView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Folder Indicator
        self.info_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16, border_width=1, border_color=C["blue"])
        self.info_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        
        self.lbl_current_repo = ctk.CTkLabel(self.info_frame, text="Nenhum diretório selecionado", font=ctk.CTkFont("Consolas", 14, "bold"), text_color=C["text"])
        self.lbl_current_repo.pack(side="left", padx=20, pady=15, fill="x", expand=True, anchor="w")
        
        btn_change_folder = ctk.CTkButton(self.info_frame, text="Trocar Pasta", width=120, height=36, font=ctk.CTkFont("Segoe UI", 12, "bold"), fg_color=C["blue"], hover_color=C["blue_dark"], command=self.change_folder)
        btn_change_folder.pack(side="right", padx=20, pady=15)
        
        # New Branch Input
        new_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16, border_width=1, border_color=C["card_border"])
        new_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=20)
        
        lbl_title = ctk.CTkLabel(new_frame, text="Nova Branch", font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=C["text"])
        lbl_title.pack(anchor="w", padx=20, pady=(20, 10))
        
        input_container = ctk.CTkFrame(new_frame, fg_color="transparent")
        input_container.pack(fill="x", padx=20, pady=(0, 20))
        
        self.entry_new = ctk.CTkEntry(input_container, placeholder_text="Nome da nova branch...", height=40)
        self.entry_new.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        btn_create = ctk.CTkButton(input_container, text="Criar Branch", height=40, font=ctk.CTkFont("Segoe UI", 12, "bold"), command=self.create_branch)
        btn_create.pack(side="left")
        
        # List of branches
        list_container = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16, border_width=1, border_color=C["card_border"])
        list_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        lbl_list = ctk.CTkLabel(list_container, text="Branches Disponíveis", font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=C["text"])
        lbl_list.pack(anchor="w", padx=20, pady=(20, 10))
        
        self.list_frame = ctk.CTkScrollableFrame(list_container, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
    def get_repo_path(self):
        return self.app.entry_folder.get().strip()
        
    def change_folder(self):
        self.app.browse_folder()
        self.load_branches()
        
    def load_branches(self):
        for child in self.list_frame.winfo_children():
            child.destroy()
            
        repo = self.get_repo_path()
        if not repo or not os.path.exists(repo):
            self.lbl_current_repo.configure(text="Nenhum diretório selecionado")
            ctk.CTkLabel(self.list_frame, text="Nenhum diretório selecionado.").pack(pady=20)
            return
            
        self.lbl_current_repo.configure(text=f"📁 Gerenciando: {repo}")
        
        original_cwd = os.getcwd()
        try:
            os.chdir(repo)
            branches_str = self.app.run_command("git branch", check=False)
            if not branches_str:
                ctk.CTkLabel(self.list_frame, text="Não é um repositório git válido.").pack(pady=20)
                return
                
            branches = branches_str.split('\n')
            for b in branches:
                if not b.strip(): continue
                is_current = b.startswith('*')
                b_name = b.replace('*', '').strip()
                
                item = ctk.CTkFrame(self.list_frame, fg_color=C["card_border"] if is_current else "transparent")
                item.pack(fill="x", pady=2)
                
                lbl_name = ctk.CTkLabel(item, text=b_name, font=ctk.CTkFont("Segoe UI", 14, "bold" if is_current else "normal"), text_color=C["text"] if is_current else C["text_dim"])
                lbl_name.pack(side="left", padx=10, pady=12)
                
                if not is_current:
                    btn_del = ctk.CTkButton(item, text="Excluir", width=30, height=30, fg_color="transparent", hover_color=C["red_dark"], command=lambda name=b_name: self.delete_branch(name))
                    btn_del.pack(side="right", padx=5)
                    
                    btn_chk = ctk.CTkButton(item, text="Mudar para Branch", height=30, fg_color=C["muted"], hover_color=C["blue"], command=lambda name=b_name: self.checkout_branch(name))
                    btn_chk.pack(side="right", padx=15)
                else:
                    ctk.CTkLabel(item, text="(Você está aqui)", font=ctk.CTkFont("Segoe UI", 12), text_color=C["blue"]).pack(side="right", padx=15)
                    
        finally:
            os.chdir(original_cwd)
            self.app.update_branch_status()
            
    def create_branch(self):
        name = self.entry_new.get().strip()
        if not name: return
        repo = self.get_repo_path()
        original_cwd = os.getcwd()
        try:
            os.chdir(repo)
            self.app.run_command(f"git checkout -b {name}", check=False)
            self.entry_new.delete(0, "end")
            self.load_branches()
        finally:
            os.chdir(original_cwd)
            
    def checkout_branch(self, name):
        repo = self.get_repo_path()
        original_cwd = os.getcwd()
        try:
            os.chdir(repo)
            
            # AUTO-SAVE MÁGICO: Garante que nada fique boiando antes de mudar de branch
            self.app.run_command("git add .", check=False)
            status = self.app.run_command("git status --porcelain", check=False)
            if status.strip():
                # Temos arquivos pendentes! Faz um commit automático de segurança.
                current_branch = self.app.run_command("git branch --show-current", check=False)
                self.app.run_command(f'git commit -m "Auto-save: Mudança de branch saindo da {current_branch}"', check=False)
                
            self.app.run_command(f"git checkout {name}", check=False)
            self.load_branches()
        finally:
            os.chdir(original_cwd)
            
    def delete_branch(self, name):
        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja apagar a branch '{name}'?\nIsso não pode ser desfeito."):
            repo = self.get_repo_path()
            original_cwd = os.getcwd()
            try:
                os.chdir(repo)
                self.app.run_command(f"git branch -D {name}", check=False)
                self.load_branches()
            finally:
                os.chdir(original_cwd)


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


class HelpDialog(ctk.CTkToplevel):
    def __init__(self, master, topic):
        super().__init__(master)
        self.title("Ajuda de Configuração")
        self.geometry("450x380")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color=C["bg"])
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))
        
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        if topic == "github_token":
            title = "Como obter o GitHub Token?"
            text = (
                "1. Acesse o GitHub no navegador e faça login.\n"
                "2. Vá em Settings > Developer settings > Personal access tokens > Tokens (classic).\n"
                "3. Clique em 'Generate new token (classic)'.\n"
                "4. Dê um nome (ex: Git Auto) e defina a validade (Expiration).\n"
                "5. Marque a caixa 'repo' (Controle de código e tarefas).\n"
                "6. Marque a caixa 'admin:org' (Obrigatório para gerenciar permissões de colaboradores).\n"
                "7. Marque a caixa 'user' (Necessário para carregar seu avatar e perfil).\n"
                "8. Clique em 'Generate token' no fim da página.\n"
                "9. Copie o token gerado (começa com ghp_...) e cole aqui."
            )
        elif topic == "gemini_key":
            title = "Como obter a Gemini API Key?"
            text = (
                "1. Acesse https://aistudio.google.com/ e faça login com sua conta Google.\n"
                "2. No menu superior, clique em 'Get API key'.\n"
                "3. Clique no botão azul 'Create API key'.\n"
                "4. Copie a chave gerada e cole aqui.\n\n"
                "A chave é gratuita e permite que a Inteligência Artificial gere os nomes dos commits automaticamente para você."
            )
        else:
            title = "Ajuda"
            text = ""

        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 15))
        
        textbox = ctk.CTkTextbox(frame, font=ctk.CTkFont("Segoe UI", 12), fg_color=C["input_bg"], text_color=C["text"], wrap="word")
        textbox.pack(fill="both", expand=True)
        textbox.insert("0.0", text)
        textbox.configure(state="disabled")
        
        ctk.CTkButton(frame, text="Entendi", height=32, font=ctk.CTkFont("Segoe UI", 12, "bold"), fg_color=C["blue"], hover_color=C["blue_dark"], command=self.destroy).pack(fill="x", pady=(15, 0))


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Configurações do Git Auto")
        self.geometry("450x520")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color=C["bg"])
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Credenciais (Salvas localmente no .env)", font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 15))
        
        def create_field_header(parent, label_text, help_topic=None):
            h_frame = ctk.CTkFrame(parent, fg_color="transparent")
            h_frame.pack(fill="x", pady=(0, 4))
            ctk.CTkLabel(h_frame, text=label_text, font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=C["text_dim"]).pack(side="left")
            if help_topic:
                ctk.CTkButton(h_frame, text="?", width=20, height=20, corner_radius=10, 
                              fg_color=C["card_border"], hover_color=C["blue"], text_color=C["text"], 
                              command=lambda t=help_topic: HelpDialog(self, t)).pack(side="left", padx=10)

        create_field_header(frame, "GitHub Username")
        self.entry_user = ctk.CTkEntry(frame, height=36, font=ctk.CTkFont("Consolas", 11), fg_color=C["input_bg"], border_color=C["card_border"], text_color=C["text"])
        self.entry_user.pack(fill="x", pady=(0, 15))
        self.entry_user.insert(0, GITHUB_USERNAME)

        create_field_header(frame, "GitHub Token", "github_token")
        self.entry_github = ctk.CTkEntry(frame, height=36, font=ctk.CTkFont("Consolas", 11), fg_color=C["input_bg"], border_color=C["card_border"], text_color=C["text"], show="*")
        self.entry_github.pack(fill="x", pady=(0, 15))
        self.entry_github.insert(0, GITHUB_TOKEN)
        
        create_field_header(frame, "Gemini API Key", "gemini_key")
        self.entry_gemini = ctk.CTkEntry(frame, height=36, font=ctk.CTkFont("Consolas", 11), fg_color=C["input_bg"], border_color=C["card_border"], text_color=C["text"], show="*")
        self.entry_gemini.pack(fill="x", pady=(0, 20))
        self.entry_gemini.insert(0, GEMINI_API_KEY)
        
        ctk.CTkFrame(frame, height=1, fg_color=C["card_border"]).pack(fill="x", pady=(5, 15))
        
        ctk.CTkLabel(frame, text="Aparência Visual", font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 10))
        
        theme_frame = ctk.CTkFrame(frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(theme_frame, text="Tema:", font=ctk.CTkFont("Segoe UI", 12), text_color=C["text_dim"]).pack(side="left", padx=(0, 10))
        self.opt_theme = ctk.CTkOptionMenu(theme_frame, values=["GitHub Dark", "GitHub Light", "VSCode Modern", "Vercel Black", "Dracula PRO", "Catppuccin Mocha", "One Dark Pro", "Monokai Pro"], fg_color=C["input_bg"], button_color=C["card_border"], text_color=C["text"])
        self.opt_theme.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.opt_theme.set(APP_THEME)
        
        ctk.CTkLabel(theme_frame, text="Destaque:", font=ctk.CTkFont("Segoe UI", 12), text_color=C["text_dim"]).pack(side="left", padx=(0, 10))
        self.opt_color = ctk.CTkOptionMenu(theme_frame, values=["Azul", "Verde", "Laranja", "Roxo", "Vermelho"], fg_color=C["input_bg"], button_color=C["card_border"], text_color=C["text"])
        self.opt_color.pack(side="left", fill="x", expand=True)
        self.opt_color.set(APP_COLOR)
        
        ctk.CTkButton(frame, text="Salvar Credenciais e Tema  ✓", height=36, font=ctk.CTkFont("Segoe UI", 12, "bold"), fg_color=C["blue"], hover_color=C["blue_dark"], command=self.save).pack(fill="x")
        
    def save(self):
        gh_user = self.entry_user.get().strip()
        gh_tok = self.entry_github.get().strip()
        gem_key = self.entry_gemini.get().strip()
        app_theme = self.opt_theme.get()
        app_color = self.opt_color.get()
        
        with open(".env", "w", encoding="utf-8") as f:
            f.write(f'APP_THEME="{app_theme}"\n')
            f.write(f'APP_COLOR="{app_color}"\n')
            f.write(f'GITHUB_TOKEN="{gh_tok}"\n')
            f.write(f'GITHUB_USERNAME="{gh_user}"\n')
            f.write(f'GEMINI_API_KEY="{gem_key}"\n')
            
        os.environ["GITHUB_TOKEN"] = gh_tok
        os.environ["GITHUB_USERNAME"] = gh_user
        os.environ["GEMINI_API_KEY"] = gem_key
        os.environ["APP_THEME"] = app_theme
        os.environ["APP_COLOR"] = app_color
        
        global GITHUB_TOKEN, GITHUB_USERNAME, GEMINI_API_KEY, APP_THEME, APP_COLOR
        GITHUB_TOKEN = gh_tok
        GITHUB_USERNAME = gh_user
        GEMINI_API_KEY = gem_key
        
        if gem_key:
            genai.configure(api_key=gem_key)
            
        if hasattr(self.master, "log"):
            self.master.log("[SYS] Configurações salvas e aplicadas.", "success")
            
        app_ref = self.master
        self.destroy()
            
        if app_theme != APP_THEME or app_color != APP_COLOR:
            APP_THEME = app_theme
            APP_COLOR = app_color
            update_palette(app_theme, app_color)
            if hasattr(app_ref, "apply_theme"):
                app_ref.after(10, app_ref.apply_theme)



class CollaboratorManagerDialog(ctk.CTkToplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Colaboradores")
        self.geometry("500x600")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.configure(fg_color=C["bg"])
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))
        
        # Build history mapping
        self.history_map = {}
        for item in load_history():
            path = item.get("path", "")
            if os.path.exists(path):
                name = os.path.basename(path)
                self.history_map[name] = path
                
        self.current_path = self.app.workspace_var.get()
        current_name = os.path.basename(self.current_path) if self.current_path else ""
        if current_name and current_name not in self.history_map:
            self.history_map[current_name] = self.current_path
            
        self.owner = None
        self.repo = None
        
        # Header Card
        self.header_card = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16, border_width=1, border_color=C["card_border"])
        self.header_card.pack(fill="x", padx=20, pady=(20, 10))
        
        lbl_title = ctk.CTkLabel(self.header_card, text="Gerenciar Colaboradores", font=ctk.CTkFont("Segoe UI", 20, "bold"), text_color=C["text"])
        lbl_title.pack(pady=(15, 5))
        
        # Project Selector
        selector_frame = ctk.CTkFrame(self.header_card, fg_color="transparent")
        selector_frame.pack(pady=(5, 15))
        
        ctk.CTkLabel(selector_frame, text="Projeto:", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=C["text_dim"]).pack(side="left", padx=(0, 10))
        
        self.opt_project = ctk.CTkOptionMenu(selector_frame, values=list(self.history_map.keys()), width=160, fg_color=C["input_bg"], text_color=C["text"], button_color=C["blue"], button_hover_color=C["blue_dark"], command=self._on_project_change)
        self.opt_project.pack(side="left")
        if current_name in self.history_map:
            self.opt_project.set(current_name)
            
        btn_browse = ctk.CTkButton(selector_frame, text="Procurar...", width=80, fg_color=C["card_border"], text_color=C["text"], hover_color=C["muted"], command=self._browse_folder)
        btn_browse.pack(side="left", padx=(10, 0))
            
        self.lbl_repo_info = ctk.CTkLabel(self.header_card, text="", font=ctk.CTkFont("Segoe UI", 12), text_color=C["blue"])
        self.lbl_repo_info.pack(pady=(0, 15))
        
        # Invite Section
        invite_frame = ctk.CTkFrame(self, fg_color="transparent")
        invite_frame.pack(fill="x", padx=20, pady=(10, 5))
        
        self.entry_username = ctk.CTkEntry(invite_frame, placeholder_text="Digite o @username", width=180, fg_color=C["input_bg"], text_color=C["text"], border_color=C["card_border"])
        self.entry_username.pack(side="left", padx=(0, 10))
        
        self.opt_perm = ctk.CTkOptionMenu(invite_frame, values=["Leitura (Pull)", "Escrita (Push)", "Triagem", "Manutenção", "Admin"], width=130, fg_color=C["input_bg"], button_color=C["card_border"], text_color=C["text"])
        self.opt_perm.pack(side="left", padx=(0, 10))
        self.opt_perm.set("Escrita (Push)")
        
        btn_invite = ctk.CTkButton(invite_frame, text="Convidar", width=90, fg_color=C["blue"], hover_color=C["blue_dark"], text_color="#ffffff", command=self._invite)
        btn_invite.pack(side="left", expand=True, fill="x")
        
        self.lbl_status = ctk.CTkLabel(self, text="", font=ctk.CTkFont("Segoe UI", 12))
        self.lbl_status.pack(pady=(0, 10))
        
        # List Section
        ctk.CTkLabel(self, text="Colaboradores Atuais:", font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color=C["text"], anchor="w").pack(fill="x", padx=20, pady=(0, 10))
        
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["card_border"])
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        if self.current_path:
            self._update_repo_context()

    def _on_project_change(self, selected_name):
        self.current_path = self.history_map.get(selected_name)
        self._update_repo_context()

    def _browse_folder(self):
        folder = ctk.filedialog.askdirectory(title="Selecione a Pasta do Projeto")
        if folder:
            import os
            if not os.path.isdir(os.path.join(folder, ".git")):
                self.lbl_repo_info.configure(text="Esta pasta não é um repositório Git (.git).", text_color=C["red"])
                return
                
            self.app.save_to_history(folder)
            name = os.path.basename(folder)
            self.history_map[name] = folder
            
            values = list(self.history_map.keys())
            self.opt_project.configure(values=values)
            self.opt_project.set(name)
            self._on_project_change(name)

    def _update_repo_context(self):
        self.owner = None
        self.repo = None
        try:
            import re, subprocess
            out = subprocess.run('git config --get remote.origin.url', cwd=self.current_path, shell=True, capture_output=True, text=True).stdout.strip()
            m = re.search(r'github\.com[:/]([^/]+)/([^.]+)', out)
            if m:
                self.owner, self.repo = m.groups()
                if self.repo.endswith('.git'):
                    self.repo = self.repo[:-4]
        except:
            pass
            
        if self.owner and self.repo:
            self.lbl_repo_info.configure(text=f"Conectado: {self.owner}/{self.repo}", text_color=C["blue"])
            self._load_collaborators()
        else:
            self.lbl_repo_info.configure(text="Repositório GitHub não detectado neste projeto.", text_color=C["red"])
            for widget in self.list_frame.winfo_children():
                widget.destroy()

    def _load_collaborators(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        
        lbl_loading = ctk.CTkLabel(self.list_frame, text="Carregando colaboradores...", text_color=C["text_dim"])
        lbl_loading.pack(pady=20)
        
        def task():
            import requests, os
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                self.app.after(0, lambda: lbl_loading.configure(text="Erro: GITHUB_TOKEN não configurado."))
                return
                
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/collaborators"
            
            try:
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    self.app.after(0, lambda d=data: self._populate_list(d))
                else:
                    self.app.after(0, lambda: lbl_loading.configure(text=f"Erro ao carregar ({resp.status_code})"))
            except Exception as e:
                self.app.after(0, lambda: lbl_loading.configure(text="Erro de conexão"))
                
        import threading
        threading.Thread(target=task, daemon=True).start()
        
    def _populate_list(self, data):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
            
        if not data:
            ctk.CTkLabel(self.list_frame, text="Nenhum colaborador encontrado.", text_color=C["text_dim"]).pack(pady=20)
            return
            
        perm_reverse_map = {"read": "Leitura (Pull)", "write": "Escrita (Push)", "admin": "Admin", "maintain": "Manutenção", "triage": "Triagem"}
        for user in data:
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=8)
            
            ctk.CTkLabel(row, text=user.get("login", ""), font=ctk.CTkFont("Segoe UI", 15, "bold"), text_color=C["text"]).pack(side="left", padx=10)
            
            role_name = user.get("role_name", "read").lower()
            current_ui_perm = perm_reverse_map.get(role_name, "Leitura (Pull)")
            
            opt = ctk.CTkOptionMenu(row, values=["Leitura (Pull)", "Escrita (Push)", "Triagem", "Manutenção", "Admin"], width=130, height=28, font=ctk.CTkFont("Segoe UI", 11, "bold"), fg_color=C["bg"], button_color=C["card_border"], text_color=C["blue"], command=lambda v, u=user.get("login", ""): self._update_permission(u, v))
            opt.set(current_ui_perm)
            opt.pack(side="right", padx=10)

    def _update_permission(self, username, new_ui_perm):
        perm_map = {"Leitura (Pull)": "pull", "Escrita (Push)": "push", "Triagem": "triage", "Manutenção": "maintain", "Admin": "admin"}
        perm = perm_map.get(new_ui_perm, "push")
        self.lbl_status.configure(text=f"Atualizando permissão de {username}...", text_color=C["text_dim"])
        
        def task():
            import requests, os
            token = os.getenv("GITHUB_TOKEN")
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/collaborators/{username}"
            try:
                resp = requests.put(url, headers=headers, json={"permission": perm})
                if resp.status_code in [201, 204]:
                    self.app.after(0, lambda: self.lbl_status.configure(text=f"✅ Permissão de @{username} atualizada!", text_color=C["green"]))
                else:
                    self.app.after(0, lambda: self.lbl_status.configure(text="❌ Erro ao atualizar permissão.", text_color=C["red"]))
            except:
                self.app.after(0, lambda: self.lbl_status.configure(text="❌ Falha de conexão.", text_color=C["red"]))
        import threading
        threading.Thread(target=task, daemon=True).start()

    def _invite(self):
        username = self.entry_username.get().strip()
        if not username:
            return
            
        if username.startswith("@"):
            username = username[1:]
            
        perm_map = {"Leitura (Pull)": "pull", "Escrita (Push)": "push", "Triagem": "triage", "Manutenção": "maintain", "Admin": "admin"}
        perm = perm_map.get(self.opt_perm.get(), "push")
            
        self.lbl_status.configure(text="Enviando convite...", text_color=C["text_dim"])
            
        def task():
            import requests, os
            token = os.getenv("GITHUB_TOKEN")
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/collaborators/{username}"
            
            try:
                resp = requests.put(url, headers=headers, json={"permission": perm})
                if resp.status_code in [201, 204]:
                    self.app.after(0, lambda: self.lbl_status.configure(text=f"✅ Convite enviado para @{username} com permissão: {perm}!", text_color=C["green"]))
                    self.app.after(0, self._load_collaborators)
                    self.app.after(0, lambda: self.entry_username.delete(0, "end"))
                else:
                    err = resp.json().get('message', 'Erro desconhecido')
                    self.app.after(0, lambda: self.lbl_status.configure(text=f"❌ Erro: {err}", text_color=C["red"]))
            except Exception as e:
                self.app.after(0, lambda: self.lbl_status.configure(text="❌ Falha de conexão.", text_color=C["red"]))
                
        import threading
        threading.Thread(target=task, daemon=True).start()

class HoverTooltip:
    def __init__(self, parent):
        self.tw = ctk.CTkToplevel(parent)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_attributes("-topmost", True)
        self.tw.withdraw()
        
        self.frame = ctk.CTkFrame(self.tw, fg_color=C["card_border"], corner_radius=6)
        self.frame.pack()
        self.lbl = ctk.CTkLabel(self.frame, text="", font=ctk.CTkFont("Segoe UI", 11), text_color=C["text"])
        self.lbl.pack(padx=8, pady=4)
        
        self.is_visible = False

    def show(self, text, x, y):
        self.lbl.configure(text=text)
        self.tw.geometry(f"+{x+15}+{y+15}")
        if not self.is_visible:
            self.tw.deiconify()
            self.is_visible = True

    def hide(self):
        if self.is_visible:
            self.tw.withdraw()
            self.is_visible = False

class NewIssueDialog(ctk.CTkToplevel):
    def __init__(self, parent, repo_name, edit_mode=False, initial_title="", initial_body=""):
        super().__init__(parent)
        self.result = None
        self.edit_mode = edit_mode
        self.title("Editar Tarefa" if edit_mode else "Nova Tarefa")
        self.geometry("500x450")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color=C["bg"])
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))

        # Header
        hdr = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        hdr_text = f"Editar Tarefa em {repo_name}" if edit_mode else f"Nova Tarefa em {repo_name}"
        ctk.CTkLabel(hdr, text=hdr_text, font=ctk.CTkFont("Segoe UI", 18, "bold"), text_color=C["text"]).pack(side="left", padx=20, pady=15)
        
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Título:", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=C["text_dim"]).pack(anchor="w")
        self.entry_title = ctk.CTkEntry(frame, height=36, font=ctk.CTkFont("Segoe UI", 12), fg_color=C["input_bg"], border_color=C["card_border"], text_color=C["text"])
        self.entry_title.pack(fill="x", pady=(5, 15))
        if initial_title: self.entry_title.insert(0, initial_title)
        
        ctk.CTkLabel(frame, text="Descrição:", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=C["text_dim"]).pack(anchor="w")
        self.txt_body = ctk.CTkTextbox(frame, height=120, font=ctk.CTkFont("Segoe UI", 12), fg_color=C["input_bg"], border_color=C["card_border"], border_width=1, text_color=C["text"])
        self.txt_body.pack(fill="x", pady=(5, 20))
        if initial_body: self.txt_body.insert("1.0", initial_body)
        
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom")
        ctk.CTkButton(btn_frame, text="Cancelar", width=100, height=36, fg_color="transparent", border_width=1, border_color=C["card_border"], hover_color=C["card"], text_color=C["text"], command=self.destroy).pack(side="left")
        
        btn_text = "Salvar" if edit_mode else "Criar Tarefa"
        ctk.CTkButton(btn_frame, text=btn_text, width=120, height=36, fg_color=C["blue"], hover_color=C["blue_dark"], command=self.confirm).pack(side="right")
        self.entry_title.focus()

    def confirm(self):
        title = self.entry_title.get().strip()
        body = self.txt_body.get("1.0", "end").strip()
        if not title:
            from tkinter import messagebox
            messagebox.showwarning("Aviso", "O título não pode estar vazio.")
            return
        self.result = {"title": title, "body": body}
        self.destroy()

class IssueDetailsDialog(ctk.CTkToplevel):
    def __init__(self, parent, issue_data, issues_view):
        super().__init__(parent)
        self.issue_data = issue_data
        self.issues_view = issues_view
        
        self.title(f"Issue #{issue_data['number']}")
        self.geometry("650x700")
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color=C["bg"])
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))
        
        # Add Comment Input at the bottom
        add_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=80)
        add_frame.pack(fill="x", side="bottom")
        add_frame.pack_propagate(False)
        
        self.entry_comment = ctk.CTkEntry(add_frame, placeholder_text="Escreva um comentário...", font=ctk.CTkFont("Segoe UI", 12), fg_color=C["input_bg"], border_color=C["card_border"])
        self.entry_comment.pack(side="left", fill="x", expand=True, padx=(20, 10), pady=20)
        
        ctk.CTkButton(add_frame, text="Comentar", width=100, height=36, font=ctk.CTkFont("Segoe UI", 12, "bold"), fg_color=C["blue"], hover_color=C["blue_dark"], command=self.post_comment).pack(side="right", padx=(0, 20), pady=20)
        
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.build_ui()
        self.load_comments()

    def build_ui(self):
        for w in self.main_scroll.winfo_children(): w.destroy()
        
        # Header (State + Title)
        hdr = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 10))
        
        is_open = self.issue_data["state"] == "open"
        state_color = C["green"] if is_open else C["red"]
        ctk.CTkLabel(hdr, text=self.issue_data["state"].upper(), font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=state_color).pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(hdr, text=self.issue_data["title"], font=ctk.CTkFont("Segoe UI", 18, "bold"), text_color=C["text"], wraplength=500, justify="left").pack(side="left", fill="x", expand=True)
        
        # Body
        body_text = self.issue_data.get("body") or "*Sem descrição*"
        ctk.CTkLabel(self.main_scroll, text=body_text, font=ctk.CTkFont("Segoe UI", 13), text_color=C["text_dim"], justify="left", wraplength=550).pack(anchor="w", pady=(0, 20))
        
        # Action Buttons
        actions = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        actions.pack(fill="x", pady=(0, 20))
        
        ctk.CTkButton(actions, text="Editar", width=80, height=30, fg_color="transparent", border_width=1, border_color=C["card_border"], hover_color=C["muted"], text_color=C["text"], command=self.edit_issue).pack(side="left", padx=(0, 10))
        
        if is_open:
            ctk.CTkButton(actions, text="Concluir Tarefa", width=120, height=30, fg_color=C["green"], hover_color="#207a3c", command=lambda: self.toggle_state("closed")).pack(side="left", padx=(0, 10))
        else:
            ctk.CTkButton(actions, text="Reabrir Tarefa", width=120, height=30, fg_color=C["orange"], hover_color="#cc6600", command=lambda: self.toggle_state("open")).pack(side="left", padx=(0, 10))
            
        ctk.CTkButton(actions, text="Dica do Gemini", width=120, height=30, fg_color=C["blue"], hover_color=C["blue_dark"], command=self.ask_gemini).pack(side="left")
        
        self.ai_frame = ctk.CTkFrame(self.main_scroll, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["blue"])
        
        # Comments divider
        ctk.CTkFrame(self.main_scroll, height=1, fg_color=C["card_border"]).pack(fill="x", pady=20)
        ctk.CTkLabel(self.main_scroll, text="Comentários", font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color=C["text"]).pack(anchor="w", pady=(0, 10))
        
        self.comments_container = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.comments_container.pack(fill="x", pady=(0, 10))

    def ask_gemini(self):
        self.ai_frame.pack(fill="x", pady=10)
        for w in self.ai_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(self.ai_frame, text="Analisando com Inteligência Artificial...", font=ctk.CTkFont(slant="italic"), text_color=C["blue"]).pack(pady=15)
        
        def task():
            try:
                prompt = f"Eu tenho uma tarefa no meu projeto chamada '{self.issue_data['title']}'. A descrição é: {self.issue_data.get('body', '')}. Me dê uma dica rápida e direta de programador de como eu poderia resolver ou começar a resolver isso."
                if not GEMINI_API_KEY:
                    self.winfo_exists() and self.after(0, lambda: self.show_ai_result("Erro: Chave do Gemini não configurada."))
                    return
                resp = model.generate_content(prompt)
                self.winfo_exists() and self.after(0, lambda: self.show_ai_result(resp.text))
            except Exception as e:
                self.winfo_exists() and self.after(0, lambda: self.show_ai_result("Falha na IA."))
        import threading
        threading.Thread(target=task, daemon=True).start()
        
    def show_ai_result(self, text):
        for w in self.ai_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(self.ai_frame, text="Dica do Gemini", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=C["blue"]).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(self.ai_frame, text=text, font=ctk.CTkFont("Segoe UI", 12), text_color=C["text"], justify="left", wraplength=480).pack(anchor="w", padx=15, pady=(0, 15))

    def load_comments(self):
        for w in self.comments_container.winfo_children(): w.destroy()
        ctk.CTkLabel(self.comments_container, text="Carregando...", text_color=C["text_dim"]).pack(pady=10)
        
        def task():
            import requests, os
            token = os.getenv("GITHUB_TOKEN")
            username = os.getenv("GITHUB_USERNAME")
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            url = f"https://api.github.com/repos/{username}/{self.issues_view.current_repo}/issues/{self.issue_data['number']}/comments"
            try:
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    comments = r.json()
                    self.winfo_exists() and self.after(0, lambda: self.render_comments(comments))
                else:
                    self.winfo_exists() and self.after(0, lambda: self.render_comments([]))
            except:
                self.winfo_exists() and self.after(0, lambda: self.render_comments([]))
        import threading
        threading.Thread(target=task, daemon=True).start()

    def render_comments(self, comments):
        for w in self.comments_container.winfo_children(): w.destroy()
        if not comments:
            ctk.CTkLabel(self.comments_container, text="Nenhum comentário ainda.", text_color=C["muted"]).pack(pady=10)
            return
            
        for c in comments:
            c_frame = ctk.CTkFrame(self.comments_container, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["card_border"])
            c_frame.pack(fill="x", pady=5)
            
            hdr = ctk.CTkFrame(c_frame, fg_color="transparent")
            hdr.pack(fill="x", padx=15, pady=(10, 5))
            user = c.get("user", {}).get("login", "alguém")
            date = c.get("created_at", "").split("T")[0]
            ctk.CTkLabel(hdr, text=user, font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color=C["text"]).pack(side="left")
            ctk.CTkLabel(hdr, text=date, font=ctk.CTkFont("Segoe UI", 10), text_color=C["muted"]).pack(side="right")
            
            body = c.get("body", "")
            ctk.CTkLabel(c_frame, text=body, font=ctk.CTkFont("Segoe UI", 12), text_color=C["text_dim"], justify="left", wraplength=500).pack(anchor="w", padx=15, pady=(0, 15))

    def post_comment(self):
        text = self.entry_comment.get().strip()
        if not text: return
        self.entry_comment.delete(0, "end")
        
        def task():
            import requests, os
            token = os.getenv("GITHUB_TOKEN")
            username = os.getenv("GITHUB_USERNAME")
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            url = f"https://api.github.com/repos/{username}/{self.issues_view.current_repo}/issues/{self.issue_data['number']}/comments"
            requests.post(url, headers=headers, json={"body": text})
            self.winfo_exists() and self.after(0, self.load_comments)
        import threading
        threading.Thread(target=task, daemon=True).start()

    def toggle_state(self, new_state):
        def task():
            import requests, os
            token = os.getenv("GITHUB_TOKEN")
            username = os.getenv("GITHUB_USERNAME")
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            url = f"https://api.github.com/repos/{username}/{self.issues_view.current_repo}/issues/{self.issue_data['number']}"
            r = requests.patch(url, headers=headers, json={"state": new_state})
            if r.status_code == 200:
                self.issue_data["state"] = new_state
                self.winfo_exists() and self.after(0, self.build_ui)
                self.winfo_exists() and self.after(0, lambda: self.issues_view.load_issues_for_repo(self.issues_view.current_repo))
        import threading
        threading.Thread(target=task, daemon=True).start()

    def edit_issue(self):
        dialog = NewIssueDialog(self, self.issues_view.current_repo, edit_mode=True, initial_title=self.issue_data["title"], initial_body=self.issue_data.get("body", ""))
        self.wait_window(dialog)
        if dialog.result:
            title, body = dialog.result["title"], dialog.result["body"]
            def task():
                import requests, os
                token = os.getenv("GITHUB_TOKEN")
                username = os.getenv("GITHUB_USERNAME")
                headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
                url = f"https://api.github.com/repos/{username}/{self.issues_view.current_repo}/issues/{self.issue_data['number']}"
                r = requests.patch(url, headers=headers, json={"title": title, "body": body})
                if r.status_code == 200:
                    self.issue_data["title"] = title
                    self.issue_data["body"] = body
                    self.winfo_exists() and self.after(0, self.build_ui)
                    self.winfo_exists() and self.after(0, lambda: self.issues_view.load_issues_for_repo(self.issues_view.current_repo))
            import threading
            threading.Thread(target=task, daemon=True).start()

class IssuesView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.current_repo = None
        self.issues_data = []
        
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(hdr, text="Tarefas", font=ctk.CTkFont("Segoe UI", 24, "bold"), text_color=C["text"]).pack(side="left")
        
        self.btn_new = ctk.CTkButton(hdr, text="Nova Tarefa", height=32, fg_color=C["blue"], hover_color=C["blue_dark"], font=ctk.CTkFont("Segoe UI", 12, "bold"), command=self.open_new_issue)
        self.btn_new.pack(side="right")
        
        # Repositories dropdown
        repo_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=8, height=60)
        repo_frame.pack(fill="x", padx=20, pady=10)
        repo_frame.pack_propagate(False)
        
        ctk.CTkLabel(repo_frame, text="Projeto:", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=C["text_dim"]).pack(side="left", padx=(15, 10))
        self.repo_combo = ctk.CTkOptionMenu(repo_frame, values=["Carregando..."], width=250, fg_color=C["input_bg"], button_color=C["card_border"], command=self.load_issues_for_repo)
        self.repo_combo.pack(side="left", pady=15)
        
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
    def load_repos(self):
        import os, json
        if os.path.exists(CACHE_REPOS):
            try:
                with open(CACHE_REPOS, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    names = [r["name"] for r in data[:15]]
                    if names:
                        self.repo_combo.configure(values=names)
                        if not self.current_repo:
                            self.repo_combo.set(names[0])
                            self.load_issues_for_repo(names[0])
                    else:
                        self.repo_combo.configure(values=["Nenhum repositório"])
            except: pass

    def load_issues_for_repo(self, repo_name):
        self.current_repo = repo_name
        for w in self.list_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(self.list_frame, text="Carregando tarefas...", text_color=C["text_dim"]).pack(pady=40)
        
        def task():
            import requests, os
            token = os.getenv("GITHUB_TOKEN")
            username = os.getenv("GITHUB_USERNAME")
            if not token or not username:
                self.app.after(0, lambda: self.show_error("Credenciais do GitHub ausentes."))
                return
                
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            url = f"https://api.github.com/repos/{username}/{repo_name}/issues?state=all&per_page=20"
            try:
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    issues = [i for i in r.json() if "pull_request" not in i]
                    self.app.after(0, lambda: self.render_issues(issues))
                else:
                    self.app.after(0, lambda: self.show_error(f"Erro da API: {r.status_code}"))
            except:
                self.app.after(0, lambda: self.show_error("Erro de conexão."))
        import threading
        threading.Thread(target=task, daemon=True).start()

    def render_issues(self, issues):
        self.issues_data = issues
        for w in self.list_frame.winfo_children(): w.destroy()
        
        if not issues:
            ctk.CTkLabel(self.list_frame, text="✨ Nenhuma tarefa aberta neste projeto. Tudo limpo!", font=ctk.CTkFont("Segoe UI", 14), text_color=C["muted"]).pack(pady=60)
            return
            
        for issue in issues:
            is_open = issue["state"] == "open"
            
            # Card principal SUPER compacto (1 linha apenas)
            card = ctk.CTkFrame(self.list_frame, fg_color=C["card"], corner_radius=6, border_width=1, border_color=C["card_border"], height=46)
            card.pack(fill="x", pady=4, padx=5)
            card.pack_propagate(False) # Impede que o card cresça desnecessariamente
            
            # Ícone de Status
            status_icon = "🟢" if is_open else "🟣"
            ctk.CTkLabel(card, text=status_icon, font=ctk.CTkFont("Segoe UI", 12)).pack(side="left", padx=(15, 10))
            
            # Título
            title = issue["title"]
            if len(title) > 45: title = title[:42] + "..."
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont("Segoe UI", 13, "bold"), text_color=C["text"]).pack(side="left")
            
            # Info meta (número, autor)
            user = issue.get("user", {}).get("login", "alguém")
            meta_text = f"  #{issue['number']} aberto por {user}"
            ctk.CTkLabel(card, text=meta_text, font=ctk.CTkFont("Segoe UI", 11), text_color=C["text_dim"]).pack(side="left", padx=(0, 10))
            
            # Botão "Abrir" alinhado à direita
            ctk.CTkButton(card, text="Abrir  →", width=80, height=26, font=ctk.CTkFont("Segoe UI", 11, "bold"), fg_color=C["input_bg"], hover_color=C["blue"], text_color=C["text"], command=lambda i=issue: self.open_issue_details(i)).pack(side="right", padx=(10, 15))
            
            # Labels (Tags) na direita, antes do botão
            for lbl in reversed(issue.get("labels", [])[:2]): # max 2 labels
                color_hex = f"#{lbl.get('color', '333333')}"
                ctk.CTkLabel(card, text=f" {lbl.get('name')} ", font=ctk.CTkFont("Segoe UI", 10, "bold"), fg_color=color_hex, text_color="#111111" if int(color_hex[1:], 16) > 0x888888 else "#ffffff", corner_radius=4).pack(side="right", padx=2)

    def show_error(self, msg):
        for w in self.list_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(self.list_frame, text=msg, text_color=C["red"]).pack(pady=40)

    def open_new_issue(self):
        if not self.current_repo: return
        dialog = NewIssueDialog(self, self.current_repo)
        self.wait_window(dialog)
        if dialog.result:
            self.create_issue(dialog.result["title"], dialog.result["body"])
            
    def open_issue_details(self, issue):
        IssueDetailsDialog(self.app, issue, self)

    def create_issue(self, title, body):
        import requests, os, threading
        token = os.getenv("GITHUB_TOKEN")
        username = os.getenv("GITHUB_USERNAME")
        
        def task():
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
            url = f"https://api.github.com/repos/{username}/{self.current_repo}/issues"
            try:
                r = requests.post(url, headers=headers, json={"title": title, "body": body})
                if r.status_code == 201:
                    self.app.after(0, lambda: self.app.log(f"[SYS] Tarefa '{title}' criada com sucesso!", "success"))
                    self.app.after(2000, lambda: self.load_issues_for_repo(self.current_repo))
                else:
                    self.app.after(0, lambda: self.app.log(f"[ERRO] Falha ao criar tarefa ({r.status_code})", "error"))
            except:
                pass
        threading.Thread(target=task, daemon=True).start()


class DashboardView(ctk.CTkScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.loaded = False
        self.graph_data_map = {}
        self.tooltip = HoverTooltip(self)
        
        self.header = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16, border_width=1, border_color=C["card_border"])
        self.header.pack(fill="x", pady=(0, 15))
        
        self.lbl_avatar = ctk.CTkLabel(self.header, text="", width=80, height=80)
        self.lbl_avatar.pack(side="left", padx=20, pady=20)
        
        info_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, pady=20)
        
        self.btn_collab = ctk.CTkButton(self.header, text="Colaboradores", width=140, fg_color=C["blue"], hover_color=C["blue_dark"], command=self.open_collab_dialog)
        self.btn_collab.pack(side="right", padx=20, pady=20)
        
        self.lbl_name = ctk.CTkLabel(info_frame, text="Carregando Perfil...", font=ctk.CTkFont("Segoe UI", 24, "bold"), text_color=C["text"])
        self.lbl_name.pack(anchor="w")
        self.lbl_username = ctk.CTkLabel(info_frame, text="@...", font=ctk.CTkFont("Segoe UI", 14), text_color=C["blue"])
        self.lbl_username.pack(anchor="w")
        self.lbl_bio = ctk.CTkLabel(info_frame, text="", font=ctk.CTkFont("Segoe UI", 12), text_color=C["text_dim"])
        self.lbl_bio.pack(anchor="w", pady=(5, 0))
        
        self.details_frame = ctk.CTkFrame(info_frame, fg_color="transparent", height=24)
        self.details_frame.pack(anchor="w", pady=(10, 0))
        
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0, 15))
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        self.stat_repos_pub = self._build_stat_card(self.stats_frame, 0, "Repositórios Públicos", "-")
        self.stat_repos_priv = self._build_stat_card(self.stats_frame, 1, "Repositórios Privados", "-")
        self.stat_followers = self._build_stat_card(self.stats_frame, 2, "Seguidores", "-")
        self.stat_following = self._build_stat_card(self.stats_frame, 3, "Seguindo", "-")
        
        # Contribution Graph Frame
        self.graph_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16, border_width=1, border_color=C["card_border"])
        self.graph_frame.pack(fill="x", pady=(0, 15))
        
        graph_header = ctk.CTkFrame(self.graph_frame, fg_color="transparent")
        graph_header.pack(fill="x", padx=20, pady=(15, 5))
        self.lbl_contributions = ctk.CTkLabel(graph_header, text="Contribuições no Último Ano", font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color=C["text"])
        self.lbl_contributions.pack(side="left")
        
        self.graph_canvas = ctk.CTkCanvas(self.graph_frame, bg=C["card"], highlightthickness=0, height=120)
        self.graph_canvas.pack(fill="x", padx=20, pady=(5, 15))
        
        # Recent Projects
        self.recent_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16, border_width=1, border_color=C["card_border"])
        self.recent_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.recent_frame, text="Últimos Projetos Atualizados", font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color=C["text"]).pack(anchor="w", padx=20, pady=(15, 10))
        
        self.repos_container = ctk.CTkScrollableFrame(self.recent_frame, fg_color="transparent")
        self.repos_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def open_collab_dialog(self):
        if not self.app.workspace_var.get():
            self.app._show_inline_confirmation("Aviso", "Selecione um projeto primeiro.")
            return
        CollaboratorManagerDialog(self, self.app)
        
    def _build_stat_card(self, parent, col, title, value):
        card = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=16, border_width=1, border_color=C["card_border"])
        card.grid(row=0, column=col, sticky="nsew", padx=8)
        lbl_val = ctk.CTkLabel(card, text=value, font=ctk.CTkFont("Segoe UI", 32, "bold"), text_color=C["blue"])
        lbl_val.pack(pady=(20, 2))
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=C["text_dim"]).pack(pady=(0, 20))
        return lbl_val

    def load_profile(self):
        if self.loaded: return
        self.loaded = True
        
        try:
            if os.path.exists(CACHE_PROFILE):
                with open(CACHE_PROFILE, "r", encoding="utf-8") as f:
                    self._update_ui_user(json.load(f))
            if os.path.exists(CACHE_REPOS):
                with open(CACHE_REPOS, "r", encoding="utf-8") as f:
                    self._update_ui_repos(json.load(f))
            if os.path.exists(CACHE_GRAPH):
                with open(CACHE_GRAPH, "r", encoding="utf-8") as f:
                    self._update_ui_graph(json.load(f))
            if os.path.exists(CACHE_AVATAR):
                with open(CACHE_AVATAR, "rb") as f:
                    self.lbl_avatar.configure(image=self._create_circular_image(f.read()))
        except:
            pass
            
        threading.Thread(target=self._fetch_data_thread, daemon=True).start()
        
    def _create_circular_image(self, img_data):
        img = Image.open(io.BytesIO(img_data)).convert("RGBA")
        img = img.resize((80, 80), Image.Resampling.LANCZOS)
        mask = Image.new('L', (80, 80), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 80, 80), fill=255)
        result = Image.new('RGBA', (80, 80), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask)
        return ctk.CTkImage(light_image=result, dark_image=result, size=(80, 80))

    def _fetch_data_thread(self):
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        try:
            resp = requests.get("https://api.github.com/user", headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # Fetch repos with per_page=100 to calculate private repos and get recent ones
                all_repos = []
                page = 1
                while True:
                    repos_resp = requests.get(f"https://api.github.com/user/repos?sort=updated&per_page=100&page={page}", headers=headers, timeout=10)
                    if repos_resp.status_code == 200:
                        batch = repos_resp.json()
                        if not batch: break
                        all_repos.extend(batch)
                        if len(batch) < 100: break
                        page += 1
                    else:
                        break
                
                # Update private repos count
                private_count = sum(1 for r in all_repos if r.get('private'))
                data['total_private_repos'] = private_count
                
                try:
                    with open(CACHE_PROFILE, "w", encoding="utf-8") as f:
                        json.dump(data, f)
                except: pass
                
                avatar_resp = requests.get(data.get("avatar_url", ""), timeout=10)
                if avatar_resp.status_code == 200:
                    try:
                        with open(CACHE_AVATAR, "wb") as f:
                            f.write(avatar_resp.content)
                    except: pass
                    ctk_img = self._create_circular_image(avatar_resp.content)
                    self.app.after(0, lambda: self.lbl_avatar.configure(image=ctk_img))
                
                self.app.after(0, lambda: self._update_ui_user(data))
                
                # Update Recent Repos UI (only top 5)
                top_repos = all_repos[:5]
                try:
                    with open(CACHE_REPOS, "w", encoding="utf-8") as f:
                        json.dump(top_repos, f)
                except: pass
                self.app.after(0, lambda: self._update_ui_repos(top_repos))
                
                # Fetch GraphQL Contribution Graph
                query = """
                query {
                  user(login: "%s") {
                    contributionsCollection {
                      contributionCalendar {
                        totalContributions
                        weeks {
                          contributionDays {
                            contributionCount
                            date
                          }
                        }
                      }
                    }
                  }
                }
                """ % data.get('login')
                graphql_resp = requests.post("https://api.github.com/graphql", json={"query": query}, headers=headers, timeout=10)
                if graphql_resp.status_code == 200:
                    graph_data = graphql_resp.json()
                    try:
                        with open(CACHE_GRAPH, "w", encoding="utf-8") as f:
                            json.dump(graph_data, f)
                    except: pass
                    self.app.after(0, lambda: self._update_ui_graph(graph_data))
        except Exception as e:
            pass
            
    def _update_ui_user(self, data):
        self.lbl_name.configure(text=data.get("name") or data.get("login") or "Usuário")
        self.lbl_username.configure(text=f"@{data.get('login', '')}")
        self.lbl_bio.configure(text=data.get("bio") or "")
        
        for child in self.details_frame.winfo_children():
            child.destroy()
            
        details = []
        if data.get("location"): details.append(f"📍 {data['location']}")
        if data.get("company"): details.append(f"🏢 {data['company']}")
        if data.get("blog"): details.append(f"🌐 {data['blog']}")
        if data.get("created_at"):
            try:
                dt = datetime.datetime.strptime(data["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                details.append(f"📅 Membro desde {dt.year}")
            except Exception:
                pass

        for text in details:
            # We add a bit of padding around the text
            lbl = ctk.CTkLabel(self.details_frame, text=f" {text} ", font=ctk.CTkFont("Segoe UI", 11), 
                               fg_color=C["card_border"], corner_radius=6, text_color=C["text"])
            lbl.pack(side="left", padx=(0, 10))
        
        self.stat_repos_pub.configure(text=str(data.get("public_repos", 0)))
        self.stat_repos_priv.configure(text=str(data.get("total_private_repos", 0)))
        self.stat_followers.configure(text=str(data.get("followers", 0)))
        self.stat_following.configure(text=str(data.get("following", 0)))

    def _update_ui_repos(self, repos):
        for child in self.repos_container.winfo_children():
            child.destroy()
            
        for repo in repos:
            item = ctk.CTkFrame(self.repos_container, fg_color="transparent")
            item.pack(fill="x", pady=5)
            
            ctk.CTkLabel(item, text=repo.get("name", ""), font=ctk.CTkFont("Segoe UI", 13, "bold"), text_color=C["text"]).pack(side="left", padx=10)
            
            pvt = repo.get("private", False)
            badge_color = C["red_dark"] if pvt else C["green_dark"]
            badge_text = "Privado" if pvt else "Público"
            
            ctk.CTkLabel(item, text=badge_text, font=ctk.CTkFont("Segoe UI", 10), fg_color=badge_color, corner_radius=4, text_color="#ffffff").pack(side="left", padx=5)
            
            url = repo.get("clone_url", "")
            btn = ctk.CTkButton(item, text="Baixar / Selecionar", width=120, height=28, font=ctk.CTkFont("Segoe UI", 11), fg_color=C["muted"], hover_color=C["blue"], command=lambda u=url: self._select_repo(u))
            btn.pack(side="right", padx=10)
            
    def _update_ui_graph(self, graph_data):
        self.graph_canvas.delete("all")
        self.graph_data_map.clear()
        try:
            cal = graph_data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
            total = cal["totalContributions"]
            self.lbl_contributions.configure(text=f"{total} contribuições no último ano")
            
            weeks = cal["weeks"]
            
            # Constants
            sq_size = 11
            gap = 3
            
            # Width and height calculations
            canvas_w = self.graph_canvas.winfo_width()
            if canvas_w < 10: canvas_w = 750
            
            total_w = len(weeks) * (sq_size + gap)
            start_x = (canvas_w - total_w) / 2
            if start_x < 0: start_x = 10
            
            start_y = 10
            
            is_dark = ctk.get_appearance_mode() == "Dark"
            
            c_empty = "#161b22" if is_dark else "#ebedf0"
            c1 = "#0e4429" if is_dark else "#9be9a8"
            c2 = "#006d32" if is_dark else "#40c463"
            c3 = "#26a641" if is_dark else "#30a14e"
            c4 = "#39d353" if is_dark else "#216e39"
            
            for col_idx, week in enumerate(weeks):
                days = week["contributionDays"]
                x0 = start_x + col_idx * (sq_size + gap)
                x1 = x0 + sq_size
                
                for day in days:
                    dt = datetime.datetime.strptime(day["date"], "%Y-%m-%d")
                    # Sunday is 0 in weekday() if we use %w, but python weekday() has Monday = 0
                    # GitHub uses Sunday = 0
                    # Let's calculate:
                    row_idx = (dt.weekday() + 1) % 7
                    
                    y0 = start_y + row_idx * (sq_size + gap)
                    y1 = y0 + sq_size
                    
                    count = day["contributionCount"]
                    if count == 0: color = c_empty
                    elif count <= 3: color = c1
                    elif count <= 6: color = c2
                    elif count <= 10: color = c3
                    else: color = c4
                    
                    rect_id = self.graph_canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=color, width=0, tags="square")
                    
                    # Format text: "5 contributions on 2026-06-09"
                    txt_count = f"{count} contribuições" if count != 1 else "1 contribuição"
                    if count == 0: txt_count = "Nenhuma contribuição"
                    
                    # Brazilian date format
                    br_date = dt.strftime("%d/%m/%Y")
                    raw_date = dt.strftime("%Y-%m-%d")
                    self.graph_data_map[rect_id] = (f"{txt_count} em {br_date}", raw_date, count)
                    
            self.graph_canvas.tag_bind("square", "<Enter>", self._on_sq_enter)
            self.graph_canvas.tag_bind("square", "<Leave>", self._on_sq_leave)
            self.graph_canvas.tag_bind("square", "<Motion>", self._on_sq_motion)
            self.graph_canvas.tag_bind("square", "<Button-1>", self._on_sq_click)
                    
        except Exception as e:
            pass

    def _on_sq_enter(self, event):
        item = self.graph_canvas.find_withtag("current")
        if item:
            data = self.graph_data_map.get(item[0], None)
            if data:
                self.tooltip.show(data[0], event.x_root, event.y_root)

    def _on_sq_leave(self, event):
        self.tooltip.hide()

    def _on_sq_motion(self, event):
        item = self.graph_canvas.find_withtag("current")
        if item:
            data = self.graph_data_map.get(item[0], None)
            if data and self.tooltip.tw:
                self.tooltip.tw.geometry(f"+{event.x_root+15}+{event.y_root+15}")

    def _on_sq_click(self, event):
        item = self.graph_canvas.find_withtag("current")
        if item:
            data = self.graph_data_map.get(item[0], None)
            if data and data[2] > 0:
                raw_date = data[1]
                br_date = data[0].split(" em ")[1]
                login = ""
                if os.path.exists(CACHE_PROFILE):
                    try:
                        with open(CACHE_PROFILE, "r", encoding="utf-8") as f:
                            login = json.load(f).get("login", "")
                    except: pass
                if login:
                    ContributionDetailsDialog(self.app, login, raw_date, br_date)

    def _select_repo(self, clone_url):
        self.app.switch_main_view("clone")
        self.app.clone_view.entry_url.delete(0, "end")
        self.app.clone_view.entry_url.insert(0, clone_url)

class ContributionDetailsDialog(ctk.CTkToplevel):
    def __init__(self, parent, login, raw_date, br_date):
        super().__init__(parent, fg_color=C["bg"])
        self.title(f"Detalhes - {br_date}")
        self.geometry("450x500")
        self.minsize(400, 400)
        self.transient(parent)
        self.grab_set()
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))
        
        self.login = login
        self.raw_date = raw_date
        
        self.header = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0)
        self.header.pack(fill="x")
        ctk.CTkLabel(self.header, text=f"Atividade em {br_date}", font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=C["text"]).pack(pady=15)
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.lbl_status = ctk.CTkLabel(self.scroll, text="Buscando detalhes na nuvem...", text_color=C["text_dim"])
        self.lbl_status.pack(pady=40)
        
        import threading
        threading.Thread(target=self._fetch_details, daemon=True).start()

    def _fetch_details(self):
        from_dt = f"{self.raw_date}T00:00:00Z"
        to_dt = f"{self.raw_date}T23:59:59Z"
        
        query = """
        query {
          user(login: "%s") {
            contributionsCollection(from: "%s", to: "%s") {
              commitContributionsByRepository {
                repository { nameWithOwner }
                contributions(first: 100) {
                  nodes { commitCount }
                }
              }
              issueContributions(first: 100) {
                nodes { issue { title, repository { nameWithOwner } } }
              }
              pullRequestContributions(first: 100) {
                nodes { pullRequest { title, repository { nameWithOwner } } }
              }
            }
          }
        }
        """ % (self.login, from_dt, to_dt)
        
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        try:
            resp = requests.post("https://api.github.com/graphql", json={"query": query}, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                self.after(0, lambda: self._render_details(data))
            else:
                self.after(0, lambda: self.lbl_status.configure(text="❌ Erro ao buscar dados."))
        except:
            self.after(0, lambda: self.lbl_status.configure(text="❌ Falha de conexão."))

    def _render_details(self, data):
        self.lbl_status.destroy()
        
        try:
            col = data["data"]["user"]["contributionsCollection"]
            commits_by_repo = col["commitContributionsByRepository"]
            issues = col["issueContributions"]["nodes"]
            prs = col["pullRequestContributions"]["nodes"]
            
            has_data = False
            
            if commits_by_repo:
                has_data = True
                ctk.CTkLabel(self.scroll, text="📝 Commits", font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color=C["green"]).pack(anchor="w", pady=(0, 5), padx=5)
                for repo_group in commits_by_repo:
                    repo_name = repo_group["repository"]["nameWithOwner"]
                    count = sum(node["commitCount"] for node in repo_group["contributions"]["nodes"])
                    txt = f"{count} commit{'s' if count>1 else ''} em {repo_name}"
                    
                    card = ctk.CTkFrame(self.scroll, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["card_border"])
                    card.pack(fill="x", pady=4, padx=5)
                    ctk.CTkLabel(card, text=txt, font=ctk.CTkFont("Segoe UI", 12), text_color=C["text_dim"]).pack(anchor="w", padx=15, pady=10)
                    
                ctk.CTkFrame(self.scroll, height=1, fg_color=C["card_border"]).pack(fill="x", pady=15, padx=5)
                
            if issues:
                has_data = True
                ctk.CTkLabel(self.scroll, text="🐛 Issues Criadas", font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color=C["red"]).pack(anchor="w", pady=(0, 5), padx=5)
                for issue in issues:
                    iss = issue["issue"]
                    txt = f"{iss['title']} ({iss['repository']['nameWithOwner']})"
                    
                    card = ctk.CTkFrame(self.scroll, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["card_border"])
                    card.pack(fill="x", pady=4, padx=5)
                    ctk.CTkLabel(card, text=txt, font=ctk.CTkFont("Segoe UI", 12), text_color=C["text_dim"], wraplength=350, justify="left").pack(anchor="w", padx=15, pady=10)
                    
                ctk.CTkFrame(self.scroll, height=1, fg_color=C["card_border"]).pack(fill="x", pady=15, padx=5)
                
            if prs:
                has_data = True
                ctk.CTkLabel(self.scroll, text="🔄 Pull Requests", font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color="#a371f7").pack(anchor="w", pady=(0, 5), padx=5)
                for pr in prs:
                    p = pr["pullRequest"]
                    txt = f"{p['title']} ({p['repository']['nameWithOwner']})"
                    
                    card = ctk.CTkFrame(self.scroll, fg_color=C["card"], corner_radius=8, border_width=1, border_color=C["card_border"])
                    card.pack(fill="x", pady=4, padx=5)
                    ctk.CTkLabel(card, text=txt, font=ctk.CTkFont("Segoe UI", 12), text_color=C["text_dim"], wraplength=350, justify="left").pack(anchor="w", padx=15, pady=10)
                    
                ctk.CTkFrame(self.scroll, height=1, fg_color=C["card_border"]).pack(fill="x", pady=15, padx=5)
                
            if not has_data:
                ctk.CTkLabel(self.scroll, text="Nenhum detalhe encontrado.", text_color=C["text_dim"]).pack(pady=20)
                
        except Exception as e:
            ctk.CTkLabel(self.scroll, text="❌ Erro ao processar dados.", text_color=C["red"]).pack(pady=20)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Git Auto  |  AI Repository Manager")
        self.geometry("1180x740")
        self.minsize(900, 600)
        self.configure(fg_color=C["bg"])
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self.workspace_var = ctk.StringVar(value=os.getcwd())

        self._build_sidebar()
        self._build_main()

        # Linha Premium Superior
        self.top_line = ctk.CTkFrame(self, height=3, fg_color=C["blue"], corner_radius=0)
        self.top_line.place(relx=0, rely=0, relwidth=1)

        try:
            self.iconbitmap(os.path.join(DATA_DIR, "icon.ico"))
        except: pass

        self.setup_tray()

        self.load_history_ui()
        self.log("Sistema inicializado. Interface pronta.", "info")
        
        if not GEMINI_API_KEY or not GITHUB_TOKEN or not GITHUB_USERNAME:
            self.after(500, self.prompt_first_setup)
            
        # Screensaver
        self.idle_after_id = None
        self.screensaver_active = False
        self.screensaver_frame = None
        self.bind("<Any-Key>", self._reset_idle)
        self.bind("<Any-Button>", self._reset_idle)
        self.bind("<Motion>", self._reset_idle)
        self._reset_idle()

    def _reset_idle(self, event=None):
        if self.screensaver_active:
            import time
            if hasattr(self, 'ss_start_time') and time.time() - self.ss_start_time < 0.5:
                pass # Ignora eventos (como o ButtonRelease) logo após ativar
            else:
                if event and hasattr(event, 'type'):
                    if event.type.name in ("ButtonPress", "ButtonRelease", "KeyPress", "KeyRelease"):
                        self._hide_screensaver()
                else:
                    self._hide_screensaver()
            
        if self.idle_after_id:
            self.after_cancel(self.idle_after_id)
        # 15 minutos = 900000 ms
        self.idle_after_id = self.after(900000, self.show_screensaver)
        
    def _hide_screensaver(self):
        if self.screensaver_frame:
            self.screensaver_frame.destroy()
            self.screensaver_frame = None
        self.screensaver_active = False
        
    def show_screensaver(self):
        if self.screensaver_active: return
        import time, random, tkinter as tk
        self.ss_start_time = time.time()
        self.ss_last_time = None  # Reset so it immediately draws the clock
        self.screensaver_active = True
        
        self.screensaver_frame = ctk.CTkToplevel(self, fg_color="#0d1117")
        self.screensaver_frame.overrideredirect(True)
        
        # Calculate exact app window size including titlebar
        x = self.winfo_x()
        y = self.winfo_y()
        root_x = self.winfo_rootx()
        root_y = self.winfo_rooty()
        border_w = root_x - x
        title_h = root_y - y
        
        total_w = self.winfo_width() + 2 * border_w
        total_h = self.winfo_height() + title_h + border_w
        
        self.screensaver_frame.geometry(f"{total_w}x{total_h}+{x}+{y}")
        self.screensaver_frame.attributes("-topmost", True)
        
        # Grid canvas
        self.ss_canvas = tk.Canvas(self.screensaver_frame, bg="#0d1117", highlightthickness=0)
        self.ss_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Bind events
        self.screensaver_frame.bind("<Any-Key>", self._reset_idle)
        self.screensaver_frame.bind("<Any-Button>", self._reset_idle)
        self.ss_canvas.bind("<Any-Key>", self._reset_idle)
        self.ss_canvas.bind("<Any-Button>", self._reset_idle)
        
        # GitHub dark/grey palette for isometric cards
        self.gh_colors = ["#161b22", "#21262d", "#30363d", "#010409"]
        self.nodes = []
        
        # Create ~60 floating panels
        for _ in range(60):
            w = random.randint(40, 150)
            h = random.randint(30, 80)
            x = random.randint(0, 2000)
            y = random.randint(0, 1200)
            color = random.choice(self.gh_colors)
            rect = self.ss_canvas.create_rectangle(x, y, x+w, y+h, fill=color, outline="#30363d", width=1)
            # Store ID and diagonal speed
            speed = random.uniform(0.3, 1.2)
            self.nodes.append({"id": rect, "speed": speed})
            
        # Draw some faint lines connecting nodes to look like a network
        self.lines = []
        for _ in range(25):
            x1, y1 = random.randint(0, 2000), random.randint(0, 1200)
            x2, y2 = x1 + random.randint(-200, 200), y1 + random.randint(-200, 200)
            line = self.ss_canvas.create_line(x1, y1, x2, y2, fill="#21262d", width=1)
            speed = random.uniform(0.3, 0.8)
            self.lines.append({"id": line, "speed": speed})
            
        # Draw central background box on canvas
        self.logo_bg_id = self.ss_canvas.create_rectangle(-1000, -1000, -1000, -1000, fill="#0d1117", outline="#30363d", width=1, tags="logo")
        
        # Load Octocat image
        try:
            from PIL import Image, ImageTk, ImageOps
            import os
            img_path = os.path.join(os.path.dirname(__file__), "data", "octocat.png")
            if os.path.exists(img_path):
                pil_img = Image.open(img_path).convert("RGBA").resize((130, 130))
                
                # Invert colors so it matches the white circle with black octocat
                r,g,b,a = pil_img.split()
                rgb_img = Image.merge('RGB', (r,g,b))
                inverted_rgb = ImageOps.invert(rgb_img)
                pil_img = Image.merge('RGBA', inverted_rgb.split() + (a,))
                
                # Make it a perfect circle using an alpha mask
                mask = Image.new("L", pil_img.size, 0)
                from PIL import ImageDraw
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, 130, 130), fill=255)
                pil_img.putalpha(mask)
                
                self.octo_img_tk = ImageTk.PhotoImage(pil_img)
            else:
                self.octo_img_tk = None
        except Exception:
            self.octo_img_tk = None
            
        # Draw white circle if image fails
        self.logo_circle_id = self.ss_canvas.create_oval(-1000, -1000, -1000, -1000, fill="#ffffff", outline="", tags="logo")
        
        if hasattr(self, 'octo_img_tk') and self.octo_img_tk:
            self.logo_img_id = self.ss_canvas.create_image(-1000, -1000, image=self.octo_img_tk, anchor="center", tags="logo")
            self.logo_text_id = None
        else:
            self.logo_img_id = None
            self.logo_text_id = self.ss_canvas.create_text(-1000, -1000, text="⬡", font=("Segoe UI", 70), fill="#000000", anchor="center", tags="logo")
            
        self.logo_label_id = self.ss_canvas.create_text(-1000, -1000, text="G I T   A U T O", font=("Segoe UI", 24, "bold"), fill="#ffffff", anchor="center", tags="logo")
        self.logo_time_id = self.ss_canvas.create_text(-1000, -1000, text="", font=("Segoe UI", 16), fill="#8b949e", anchor="center", tags="logo")
        
        self._animate_screensaver()
        
    def _animate_screensaver(self):
        if not self.screensaver_active or not self.screensaver_frame or not self.screensaver_frame.winfo_exists():
            return
            
        import random
        sw = self.screensaver_frame.winfo_width()
        sh = self.screensaver_frame.winfo_height()
        
        if sw > 0 and sh > 0:
            cx, cy = sw / 2, sh / 2
            
            # Update logo positions
            bw, bh = 320, 280
            self.ss_canvas.coords(self.logo_bg_id, cx - bw/2, cy - bh/2, cx + bw/2, cy + bh/2)
            cw, ch = 130, 130
            self.ss_canvas.coords(self.logo_circle_id, cx - cw/2, cy - ch/2 - 30, cx + cw/2, cy + ch/2 - 30)
            
            if hasattr(self, 'logo_img_id') and self.logo_img_id:
                self.ss_canvas.coords(self.logo_img_id, cx, cy - 30)
            if hasattr(self, 'logo_text_id') and self.logo_text_id:
                self.ss_canvas.coords(self.logo_text_id, cx, cy - 35)
                
            self.ss_canvas.coords(self.logo_label_id, cx, cy + 80)
            self.ss_canvas.coords(self.logo_time_id, cx, cy + 115)
            
            # Update clock
            import time
            now = time.strftime("%H:%M")
            if not hasattr(self, 'ss_last_time') or self.ss_last_time != now:
                self.ss_last_time = now
                self.ss_canvas.itemconfig(self.logo_time_id, text=now)
            
            # Ensure logo is always on top
            self.ss_canvas.tag_raise("logo")
            for item in self.nodes + self.lines:
                # Move diagonally up-left
                self.ss_canvas.move(item["id"], -item["speed"], -item["speed"] * 0.7)
                coords = self.ss_canvas.coords(item["id"])
                if coords:
                    if len(coords) == 4: # Rectangle or line
                        x1, y1, x2, y2 = coords
                        # If completely off-screen top-left
                        if x2 < 0 or y2 < 0:
                            w = x2 - x1
                            h = y2 - y1
                            new_x = sw + random.randint(0, 300)
                            new_y = sh + random.randint(0, 300)
                            self.ss_canvas.coords(item["id"], new_x, new_y, new_x+w, new_y+h)
                            
        self.after(30, self._animate_screensaver)
            
    def apply_theme(self):
        current_path = self.workspace_var.get()
        
        if hasattr(self, 'sidebar'):
            self.sidebar.destroy()
        if hasattr(self, 'main_frame'):
            self.main_frame.destroy()
        if hasattr(self, 'top_line'):
            self.top_line.destroy()
            
        self.workspace_var = ctk.StringVar(value=current_path)
            
        self.configure(fg_color=C["bg"])
        set_title_bar_color(self, C["bg"], C["text"])
            
        self._build_sidebar()
        self._build_main()
        
        # Recria a Linha Premium
        self.top_line = ctk.CTkFrame(self, height=3, fg_color=C["blue"], corner_radius=0)
        self.top_line.place(relx=0, rely=0, relwidth=1)
        
        self.entry_folder.delete(0, "end")
        self.entry_folder.insert(0, current_path)
        self.load_history_ui()
        self.update_branch_status()
            
    def prompt_first_setup(self):
        messagebox.showinfo("Bem-vindo ao Git Auto", "Parece que é a sua primeira vez aqui (ou faltam credenciais)!\n\nPor favor, insira o seu Username, Token do GitHub e Chave do Gemini para habilitar todas as funções.")
        self.open_settings()

    # ── SIDEBAR ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color=C["sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(6, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(24, 0))
        
        logo_lbl = ctk.CTkLabel(logo_frame, text="⬡ Git Auto", font=ctk.CTkFont("Segoe UI", 22, "bold"), text_color=C["text"], cursor="hand2")
        logo_lbl.pack(anchor="w")
        logo_lbl.bind("<Button-1>", lambda e: self.restart_app())
        
        ctk.CTkLabel(logo_frame, text="AI-Powered Repository Manager", font=ctk.CTkFont("Segoe UI", 11), text_color=C["text_dim"]).pack(anchor="w")

        # Sidebar Dashboard Button
        self.btn_sidebar_dash = ctk.CTkButton(
            self.sidebar, text="Meu Perfil", height=38, 
            font=ctk.CTkFont("Segoe UI", 13, "bold"), 
            fg_color=C["card"], hover_color=C["card_border"], 
            text_color=C["blue"], border_width=1, border_color=C["card_border"],
            command=lambda: self.switch_main_view("dashboard"))
        self.btn_sidebar_dash.grid(row=1, column=0, sticky="ew", padx=20, pady=(20, 0))

        # Separador
        ctk.CTkFrame(self.sidebar, height=1, fg_color=C["card_border"]).grid(
            row=2, column=0, sticky="ew", padx=0, pady=16)

        # Status pill
        self.status_pill = ctk.CTkFrame(self.sidebar, fg_color=C["card"], corner_radius=20, height=36)
        self.status_pill.grid(row=3, column=0, padx=20, sticky="ew")
        self.status_pill.pack_propagate(False)
        self.status_dot = ctk.CTkLabel(self.status_pill, text="●", font=ctk.CTkFont(size=12), text_color=C["muted"])
        self.status_dot.pack(side="left", padx=(14, 4))
        self.status_label = ctk.CTkLabel(self.status_pill, text="Aguardando", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=C["text_dim"])
        self.status_label.pack(side="left")

        # Progress bar
        self.progressbar = ctk.CTkProgressBar(self.sidebar, mode="indeterminate", height=3, corner_radius=0, progress_color=C["blue"], fg_color=C["card_border"])
        self.progressbar.grid(row=4, column=0, sticky="ew", padx=0, pady=(12, 0))
        self.progressbar.set(0)

        # Histórico
        hist_hdr = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        hist_hdr.grid(row=5, column=0, sticky="new", padx=20, pady=(20, 8))
        hist_hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(hist_hdr, text="PROJETOS RECENTES",
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=C["muted"]).grid(row=0, column=0, sticky="w")

        self.btn_add_project = ctk.CTkButton(
            hist_hdr, text="+ Adicionar", width=70, height=22,
            font=ctk.CTkFont("Segoe UI", 10, "bold"),
            fg_color=C["card"], hover_color=C["card_border"], text_color=C["text_dim"],
            command=self.add_local_project)
        self.btn_add_project.grid(row=0, column=1, sticky="e", padx=(0, 5))

        self.btn_clear_history = ctk.CTkButton(
            hist_hdr, text="Limpar", width=50, height=22,
            font=ctk.CTkFont("Segoe UI", 10),
            fg_color="transparent", border_width=1,
            border_color=C["card_border"],
            text_color=C["text_dim"], hover_color=C["red_dark"],
            command=self.clear_all_history)
        self.btn_clear_history.grid(row=0, column=2, sticky="e")

        self.history_frame = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            scrollbar_button_color=C["muted"],
            scrollbar_button_hover_color=C["text_dim"])
        self.history_frame.grid(row=6, column=0, sticky="nsew",
                                padx=10, pady=(0, 10))

        # Configurações e Sair (Lado a Lado)
        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.grid(row=7, column=0, sticky="ew", padx=20, pady=(10, 20))
        bottom_frame.grid_columnconfigure(0, weight=0)
        bottom_frame.grid_columnconfigure(1, weight=1)
        bottom_frame.grid_columnconfigure(2, weight=1)

        self.btn_ss = ctk.CTkButton(
            bottom_frame, text="💤", width=32, height=32,
            font=ctk.CTkFont("Segoe UI", 14),
            fg_color="transparent", hover_color=C["card_border"], text_color=C["text_dim"],
            command=self.show_screensaver)
        self.btn_ss.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.btn_settings = ctk.CTkButton(
            bottom_frame, text="Config", height=32,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color="transparent", hover_color=C["card_border"], text_color=C["text_dim"],
            command=self.open_settings)
        self.btn_settings.grid(row=0, column=1, sticky="ew", padx=(0, 5))

        self.btn_shutdown = ctk.CTkButton(
            bottom_frame, text="Sair", height=32,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color="transparent", hover_color="#8b0000", text_color="#ff4444",
            command=self.shutdown_app)
        self.btn_shutdown.grid(row=0, column=2, sticky="ew")

    def shutdown_app(self):
        self.quit()
        self.destroy()
        os._exit(0)

    def restart_app(self):
        # Soft refresh to avoid abrupt window flashing
        try:
            self.load_history_ui()
            if hasattr(self, "dashboard_view"):
                self.dashboard_view.load_profile()
            if hasattr(self, "issues_view"):
                self.issues_view.load_repos()
            if hasattr(self, "branch_manager_view"):
                self.branch_manager_view.load_branches()
            self.log("[SYS] Dados recarregados (Soft Refresh) com sucesso!", "success")
        except Exception as e:
            self.log(f"[ERRO] Falha ao recarregar: {e}", "error")

    def _build_main(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=28, pady=28)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.nav_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.nav_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        self.btn_nav_push = ctk.CTkButton(self.nav_frame, text="Repositórios", font=ctk.CTkFont("Segoe UI", 14, "bold"), height=42, fg_color=C["blue"], hover_color=C["blue_dark"], text_color="#ffffff", corner_radius=10, command=lambda: self.switch_main_view("push"))
        self.btn_nav_push.pack(side="left", padx=(0, 10))

        self.btn_nav_clone = ctk.CTkButton(self.nav_frame, text="Clonagem", font=ctk.CTkFont("Segoe UI", 14, "bold"), height=42, fg_color=C["card"], hover_color=C["card_border"], text_color=C["text_dim"], corner_radius=10, command=lambda: self.switch_main_view("clone"))
        self.btn_nav_clone.pack(side="left", padx=(0, 10))

        self.btn_branch = ctk.CTkButton(
            self.nav_frame, text="Branch: --", font=ctk.CTkFont("Segoe UI", 14, "bold"), height=42, 
            fg_color=C["card"], hover_color=C["card_border"], text_color=C["text_dim"], 
            corner_radius=10, command=lambda: self.switch_main_view("branch"))
        self.btn_branch.pack(side="left", padx=(0, 10))

        self.btn_nav_pull = ctk.CTkButton(
            self.nav_frame, text="Sincronizar", font=ctk.CTkFont("Segoe UI", 14, "bold"), height=42, 
            fg_color=C["card"], hover_color=C["card_border"], text_color=C["text_dim"], 
            corner_radius=10, command=lambda: self.switch_main_view("pull"))
        self.btn_nav_pull.pack(side="left", padx=(0, 10))

        self.btn_nav_issues = ctk.CTkButton(
            self.nav_frame, text="Tarefas", font=ctk.CTkFont("Segoe UI", 14, "bold"), height=42, 
            fg_color=C["card"], hover_color=C["card_border"], text_color=C["text_dim"], 
            corner_radius=10, command=lambda: self.switch_main_view("issues"))
        self.btn_nav_issues.pack(side="left", padx=(0, 10))

        # Container de Conteúdo
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.grid(row=2, column=0, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.tab_push = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.tab_push.grid(row=0, column=0, sticky="nsew")
        self.tab_push.grid_rowconfigure(2, weight=1)
        self.tab_push.grid_columnconfigure(0, weight=1)
        
        self.tab_clone = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        
        self.clone_view = CloneProjectView(self.tab_clone, self)
        self.clone_view.pack(fill="both", expand=True)
        
        self.tab_branch = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.branch_manager_view = BranchManagerView(self.tab_branch, self)
        self.branch_manager_view.pack(fill="both", expand=True)

        self.tab_dash = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.dashboard_view = DashboardView(self.tab_dash, self)
        self.dashboard_view.pack(fill="both", expand=True)

        self.tab_issues = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.issues_view = IssuesView(self.tab_issues, self)
        self.issues_view.pack(fill="both", expand=True)

        self.tab_pull = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self._build_pull_tab()

        # ── 1. Workspace card ─────────────────────────────────────────────────
        ws = ctk.CTkFrame(self.tab_push, fg_color=C["card"],
                          corner_radius=16, border_width=1,
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
            text_color=C["text"], textvariable=self.workspace_var, placeholder_text="Selecione o caminho do projeto...")
        self.entry_folder.grid(row=1, column=0, columnspan=2,
                               sticky="ew", padx=20, pady=(0, 18))

        self.btn_browse = ctk.CTkButton(
            ws, text="Procurar", width=130, height=42,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=C["muted"], hover_color=C["blue"],
            command=self.browse_folder)
        self.btn_browse.grid(row=1, column=2, padx=(0, 20), pady=(0, 18))

        ws_actions = ctk.CTkFrame(ws, fg_color="transparent")
        ws_actions.grid(row=2, column=0, columnspan=3, sticky="ew", padx=20, pady=(0, 16))
        
        # Alinhando à direita para melhor aproveitamento do espaço (ordem inversa no pack)
        self.btn_release = ctk.CTkButton(
            ws_actions, text="Lançar Versão", height=28, width=120,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color="transparent", hover_color=C["card"], text_color=C["orange"],
            border_width=1, border_color=C["card_border"], 
            command=self.open_release_manager)
        self.btn_release.pack(side="right", padx=(10, 0))

        self.btn_time_machine = ctk.CTkButton(
            ws_actions, text="Máquina do Tempo", height=28, width=130,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color="transparent", hover_color=C["warn_bg"], text_color=C["red"],
            border_width=1, border_color=C["card_border"], 
            command=self.discard_changes)
        self.btn_time_machine.pack(side="right", padx=(10, 0))

        self.btn_gitignore = ctk.CTkButton(
            ws_actions, text="Gerar .gitignore", height=28, width=120,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color="transparent", hover_color=C["card"], text_color=C["text_dim"],
            border_width=1, border_color=C["card_border"], 
            command=self.open_gitignore_generator)
        self.btn_gitignore.pack(side="right", padx=(0, 0))

        # ── 2. Action cards ───────────────────────────────────────────────────
        self.actions_frame = ctk.CTkFrame(self.tab_push, fg_color="transparent")
        self.actions_frame.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        self.actions_frame.grid_columnconfigure((0, 1), weight=1)

        # Card — Atualizar
        cu = ctk.CTkFrame(self.actions_frame, fg_color=C["card"], corner_radius=12,
                          border_width=1, border_color=C["card_border"])
        cu.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        cu.grid_columnconfigure(0, weight=1)

        top_u = ctk.CTkFrame(cu, fg_color="transparent")
        top_u.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))
        
        txt_u = ctk.CTkFrame(top_u, fg_color="transparent")
        txt_u.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(txt_u, text="Atualizar Projeto Existente",
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(txt_u, text="Sincroniza mudanças locais, gera o README com IA e faz o Push automático.",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=C["text_dim"], wraplength=300, justify="left").pack(anchor="w", pady=(4, 0))

        self.btn_diff = ctk.CTkButton(
            cu, text="Visualizar Diferenças", height=32,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=C["input_bg"], hover_color=C["card_border"], text_color=C["text_dim"],
            corner_radius=6, command=self.open_diff_viewer)
        self.btn_diff.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))

        self.btn_update = ctk.CTkButton(
            cu, text="Executar Fluxo", height=36,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=C["blue"], hover_color=C["blue_dark"], text_color="#1a1b26",
            corner_radius=6, command=self.start_update_thread)
        self.btn_update.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))


        # Card — Novo Projeto
        cn = ctk.CTkFrame(self.actions_frame, fg_color=C["card"], corner_radius=12,
                          border_width=1, border_color=C["card_border"])
        cn.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        cn.grid_columnconfigure(0, weight=1)

        top_n = ctk.CTkFrame(cn, fg_color="transparent")
        top_n.grid(row=0, column=0, sticky="ew", padx=24, pady=(24, 16))
        
        txt_n = ctk.CTkFrame(top_n, fg_color="transparent")
        txt_n.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(txt_n, text="Criar Novo Projeto",
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(txt_n, text="Inicia o repositório no GitHub, estrutura o README e publica o código.",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=C["text_dim"], wraplength=300, justify="left").pack(anchor="w", pady=(4, 0))

        # Espaçador para manter os botões primários alinhados na mesma altura
        spacer = ctk.CTkFrame(cn, fg_color="transparent", height=32)
        spacer.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))

        self.btn_new = ctk.CTkButton(
            cn, text="Criar e Enviar", height=36,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=C["green"], hover_color=C["green_dark"], text_color="#1a1b26",
            corner_radius=6, command=self.start_new_project_thread)
        self.btn_new.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))

        # ── 3. Tabs (Console e Histórico) ─────────────────────────────────────
        self.tabs = ctk.CTkTabview(self.tab_push, fg_color=C["card"],
                                   corner_radius=16, border_width=1,
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

    def setup_tray(self):
        import pystray
        menu = (
            pystray.MenuItem("Abrir Git Auto", self.restore_window),
            pystray.MenuItem("Sair", self.quit_app),
        )
        try:
            from PIL import Image
            img = Image.open(os.path.join(DATA_DIR, "icon.ico"))
        except Exception:
            img = self.create_image()
            
        self.tray_icon = pystray.Icon("Git Auto", img, "Git Auto em execução", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_to_tray(self):
        self.withdraw()

    def restore_window(self, icon=None, item=None):
        self.after(0, self.deiconify)

    def quit_app(self, icon=None, item=None):
        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()
        self.shutdown_app()

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

            # Card Premium do Histórico (Vertical)
            card = ctk.CTkFrame(self.history_frame, fg_color=C["card"],
                                corner_radius=10, border_width=1, border_color=C["card_border"])
            card.pack(fill="x", pady=6, padx=4)
            
            icon_color = C["green"] if status == "ok" else C["red"]
            
            # Linha superior: Ícone, Nome e Fechar
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(12, 0))
            
            ctk.CTkLabel(top_row, text="●", font=ctk.CTkFont(size=14), text_color=icon_color).pack(side="left", padx=(0, 8))
            
            btn_title = ctk.CTkButton(top_row, text=folder_name, 
                                      font=ctk.CTkFont("Segoe UI", 14, "bold"), 
                                      text_color=C["text"], fg_color="transparent", hover_color=C["card_border"],
                                      anchor="w", command=lambda p=path: self.set_folder_from_history(p))
            btn_title.pack(side="left", fill="x", expand=True)
            
            ctk.CTkButton(top_row, text="✕", width=24, height=24,
                          font=ctk.CTkFont("Segoe UI", 12, "bold"),
                          fg_color="transparent", hover_color=C["card_border"], text_color=C["text_dim"],
                          corner_radius=4,
                          command=lambda p=path: self.remove_from_history(p)).pack(side="right")
                          
            # Meio: Data e Status
            mid_row = ctk.CTkFrame(card, fg_color="transparent")
            mid_row.pack(fill="x", padx=12, pady=(0, 12))
            
            status_text = "Sincronizado" if status == "ok" else "Falhou"
            ctk.CTkLabel(mid_row, text=f"🕐 {date}   •   {status_text}", 
                         font=ctk.CTkFont("Segoe UI", 11), 
                         text_color=icon_color if status != "ok" else C["text_dim"]).pack(side="left", padx=(20, 0))

    def open_project_history(self, path):
        self.set_folder_from_history(path)

    def open_settings(self):
        SettingsDialog(self)

    def set_folder_from_history(self, path):
        self.entry_folder.delete(0, "end")
        self.entry_folder.insert(0, path)
        self.log(f"[INFO] Diretório carregado: {path}", "info")
        self.load_project_commits(path)

    def update_branch_status(self):
        repo = self.entry_folder.get().strip()
        if not os.path.exists(os.path.join(repo, ".git")):
            self.btn_branch.configure(text="Branch: --")
            return
        branch = self.run_command(f'git -C "{repo}" rev-parse --abbrev-ref HEAD', check=False)
        self.btn_branch.configure(text=f"🔀 Branch: {branch}")

    def load_project_commits(self, path):
        self.tabs.set("Histórico de Pushes (Local)")
        for w in self.project_history_scroll.winfo_children():
            w.destroy()
            
        self.update_branch_status()
        if not os.path.isdir(os.path.join(path, ".git")):
            ctk.CTkLabel(self.project_history_scroll, text="Repositório Git não inicializado.", text_color=C["muted"]).pack(pady=40)
            return
            
        cmd = f'git -C "{path}" log --remotes --format="%H|%ad|%an|%s" --date=format:"%d/%m/%Y %H:%M"'
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
            lines = [l for l in res.stdout.strip().splitlines() if l.strip()]
        except Exception:
            lines = []
            
        if not lines:
            ctk.CTkLabel(self.project_history_scroll, text="Nenhum push efetuado neste repositório ainda.", text_color=C["muted"]).pack(pady=40)
            return
            
        folder_name = os.path.basename(path)
        
        for line in lines:
            parts = line.split("|", 3)
            if len(parts) < 4: continue
            c_hash, date, author, msg = parts
            
            container = ctk.CTkFrame(self.project_history_scroll, fg_color=C["card"], corner_radius=6, border_width=1, border_color=C["card_border"])
            container.pack(fill="x", pady=4)
            
            details_frame = ctk.CTkFrame(container, fg_color="transparent")
            
            def toggle_details(df=details_frame, h=c_hash, p=path, a=author):
                if df.winfo_ismapped():
                    df.pack_forget()
                else:
                    if not df.winfo_children():
                        ctk.CTkLabel(df, text=f"Hash: {h[:7]}   |   Autor: {a}", font=ctk.CTkFont("Consolas", 10), text_color=C["text_dim"]).pack(anchor="w", padx=14, pady=(8, 6))
                        
                        cmd_stat = f'git -C "{p}" show --name-status --format="%B|||SPLIT|||" {h}'
                        try:
                            stat_res = subprocess.run(cmd_stat, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
                            out = stat_res.stdout.strip()
                            if "|||SPLIT|||" in out:
                                msg_part, files_part = out.split("|||SPLIT|||", 1)
                            else:
                                msg_part, files_part = out, ""
                                
                            msg_part = msg_part.strip()
                            files_part = files_part.strip()
                            
                            if msg_part:
                                msg_box = ctk.CTkTextbox(df, height=80, font=ctk.CTkFont("Segoe UI", 13), fg_color="transparent", text_color=C["text"], border_width=0)
                                msg_box.pack(fill="x", padx=10, pady=(0, 4))
                                msg_box.insert("1.0", msg_part)
                                msg_box.configure(state="disabled")
                                
                            if files_part:
                                ctk.CTkLabel(df, text="Arquivos Alterados:", font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color=C["text_dim"]).pack(anchor="w", padx=14, pady=(2, 2))
                                box = ctk.CTkTextbox(df, height=70, font=ctk.CTkFont("Consolas", 11), fg_color=C["console_bg"], text_color=C["text_dim"], border_width=1, border_color=C["card_border"], corner_radius=6)
                                box.pack(fill="x", padx=14, pady=(0, 14))
                                box.insert("1.0", files_part)
                                box.configure(state="disabled")
                        except Exception:
                            pass
                    df.pack(fill="x", expand=True)
            
            btn_text = f"✓   {folder_name}   •   {date}   (Clique para expandir)"
            
            btn = ctk.CTkButton(container, text=btn_text, anchor="w", height=38,
                                fg_color="transparent", hover_color=C["input_bg"],
                                text_color=C["green"],
                                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                command=toggle_details)
            btn.pack(side="top", fill="x")

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

    def add_local_project(self):
        folder = filedialog.askdirectory(title="Selecione a pasta do Repositório Git")
        if folder:
            if not os.path.isdir(os.path.join(folder, ".git")):
                messagebox.showwarning("Aviso", "Esta pasta não contém um repositório Git válido (.git).")
                return
            self.save_to_history(folder)
            self.log(f"[SYS] Projeto local adicionado ao histórico: {folder}", "success")
            messagebox.showinfo("Sucesso", "Projeto adicionado à barra lateral!")

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
            self.workspace_var.set(folder)
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
            self.generate_specific_gitignore(["Generico"], silent=True)

    def open_gitignore_generator(self):
        dialog = GitignoreDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self.generate_specific_gitignore(dialog.result)

    def discard_changes(self):
        repo = self.entry_folder.get().strip()
        if not repo or not os.path.exists(os.path.join(repo, ".git")):
            self._show_error("Esta pasta não é um repositório Git válido.")
            return
            
        repo_name = os.path.basename(os.path.abspath(repo))

        # Obter informações do último commit
        commit_info_text = "Nenhum commit encontrado (Estado Inicial)"
        try:
            info_meta = self.run_command(f'git -C "{repo}" log -1 --format="%h | %cd" --date=format:"%d/%m/%Y às %H:%M"', check=False)
            info_msg = self.run_command(f'git -C "{repo}" log -1 --format="%s"', check=False)
            
            if info_meta and "fatal" not in info_meta.lower():
                if len(info_msg) > 70:
                    info_msg = info_msg[:67] + "..."
                commit_info_text = f"🕒 {info_meta}\n📝 {info_msg}"
        except Exception:
            pass
            
        dialog = TimeMachineDialog(self, commit_info_text, repo_name)
        self.wait_window(dialog)
        
        if dialog.result:
            original_cwd = os.getcwd()
            try:
                os.chdir(repo)
                self.log("[SYS] ⏳ Rebobinando arquivos para o último commit...", "warn")
                self.run_command("git reset --hard", check=False)
                self.run_command("git clean -fd", check=False)
                self.log("[SYS] ⏪ Máquina do Tempo ativada! Todas as mudanças não salvas foram apagadas com sucesso.", "success")
                messagebox.showinfo("Sucesso", "A máquina do tempo foi ativada.\nTodos os arquivos retornaram ao estado do último commit.")
            except Exception as e:
                self.log(f"[ERRO] Falha ao executar a Máquina do Tempo: {str(e)}", "error")
            finally:
                os.chdir(original_cwd)

    def open_diff_viewer(self):
        repo = self.entry_folder.get().strip()
        if not repo or not os.path.exists(os.path.join(repo, ".git")):
            self._show_error("Esta pasta não é um repositório Git válido.")
            return
            
        original_cwd = os.getcwd()
        try:
            os.chdir(repo)
            self.run_command("git add -N .", check=False) # Adiciona arquivos não rastreados pro diff funcionar
            diff_output = self.run_command("git diff", check=False)
        except Exception as e:
            diff_output = f"Erro ao gerar diff: {str(e)}"
        finally:
            os.chdir(original_cwd)
            
        dialog = DiffViewerDialog(self, diff_output)
        self.wait_window(dialog)

    def open_release_manager(self):
        repo = self.entry_folder.get().strip()
        if not repo or not os.path.exists(os.path.join(repo, ".git")):
            self._show_error("Selecione um repositório Git válido primeiro.")
            return
        
        dialog = ReleaseManagerDialog(self, repo)
        self.wait_window(dialog)

    def generate_specific_gitignore(self, template_names, silent=False):
        base_ignores = "# Ambiente / SO\n.env\n.env.*\n!.env.example\n.DS_Store\nThumbs.db\ndesktop.ini\n\n# IDEs\n.vscode/\n.idea/\n\n"
        
        templates = {
            "Python": "# Python\n__pycache__/\n*.py[cod]\n*$py.class\nvenv/\n.venv/\nenv/\n.env/\nbuild/\ndist/\n*.egg-info/\n*.log\n",
            "Node.js": "# Node\nnode_modules/\nnpm-debug.log\nyarn-error.log\nbuild/\ndist/\ncoverage/\n",
            "Java": "# Java\n*.class\n*.log\n*.jar\n*.war\n*.nar\n*.ear\n*.zip\n*.tar.gz\n*.rar\n# Maven/Gradle\ntarget/\nbuild/\n.gradle/\n",
            "C++": "# C++\n*.o\n*.obj\n*.exe\n*.dll\n*.so\n*.dylib\n*.out\n*.app\n# CMake\nCMakeCache.txt\nCMakeFiles/\ncmake_install.cmake\nMakefile\nbin/\nbuild/\n",
            "React/Next.js": "# React / Next.js\nnode_modules/\n.pnp\n.pnp.js\ncoverage/\nbuild/\n.next/\nout/\n.env.local\n.env.development.local\n.env.test.local\n.env.production.local\n",
            "Godot": "# Godot\n.godot/\n*.translation\nexport_presets.cfg\n",
            "Unity": "# Unity\n[Ll]ibrary/\n[Tt]emp/\n[Oo]bj/\n[Bb]uild/\n[Bb]uilds/\n[Ll]ogs/\n[Uu]ser[Ss]ettings/\n*.csproj\n*.unityproj\n*.sln\n*.suo\n*.tmp\n*.user\n*.userprefs\n*.pidb\n*.booproj\n*.svd\n*.pdb\n*.mdb\n*.opendb\n*.VC.db\n.consulo/\n*.ds_store\n",
            "Generico": "# Generic\nbuild/\ndist/\n*.log\ntmp/\n"
        }
        
        selected_content = "\n".join(templates.get(t, "") for t in template_names)
        if not selected_content.strip():
            selected_content = templates["Generico"]
            
        content = base_ignores + selected_content
        
        path = self.entry_folder.get()
        if not path or not os.path.exists(path):
            if not silent: self.log("[ERRO] Diretório inválido para gerar .gitignore.", "error")
            return
            
        git_ignore_path = os.path.join(path, ".gitignore")
        
        try:
            with open(git_ignore_path, "w", encoding="utf-8") as f:
                f.write(content)
            if not silent: 
                names_str = ", ".join(template_names)
                self.log(f"[SYS] .gitignore ({names_str}) gerado com sucesso.", "success")
        except Exception as e:
            if not silent: 
                self.log(f"[ERRO] Falha ao criar .gitignore: {e}", "error")

    def get_code_changes(self):
        self.ensure_gitignore()
        self.run_command("git add .")
        has_commits = self.run_command("git rev-parse HEAD", check=False)
        if not has_commits:
            return self.run_command("git diff --cached $(git hash-object -t tree /dev/null)")
        return self.run_command("git diff --cached")

    # ── IA / FALLBACK ─────────────────────────────────────────────────────────
    def generate_readme(self, diff):
        self.log("[IA] Analisando código para atualizar documentação…", "info")
        current_readme = ""
        if os.path.exists("README.md"):
            with open("README.md", "r", encoding="utf-8") as f:
                current_readme = f.read()

        today = datetime.datetime.now().strftime("%d/%m/%Y")
        
        # Build project tree (max depth 2 to avoid huge tokens)
        def build_tree(dir_path, prefix="", depth=0):
            if depth > 2: return ""
            ignored = {".git", "__pycache__", "node_modules", ".venv", "venv", "env", "dist", "build"}
            try:
                entries = [e for e in os.listdir(dir_path) if e not in ignored]
            except:
                return ""
            entries.sort(key=lambda x: (not os.path.isdir(os.path.join(dir_path, x)), x))
            tree_str = ""
            for i, entry in enumerate(entries):
                is_last = (i == len(entries) - 1)
                tree_str += prefix + ("└── " if is_last else "├── ") + entry + "\n"
                full_path = os.path.join(dir_path, entry)
                if os.path.isdir(full_path) and entry != "data":
                    tree_str += build_tree(full_path, prefix + ("    " if is_last else "│   "), depth + 1)
            return tree_str
            
        tree = ".\n" + build_tree(os.getcwd())
        
        deps_content = ""
        if os.path.exists("requirements.txt"):
            try:
                with open("requirements.txt", "r", encoding="utf-8") as f:
                    deps_content = "\n--- DEPENDÊNCIAS ATUAIS (requirements.txt) ---\n" + f.read()[:2000]
            except: pass
        elif os.path.exists("package.json"):
            try:
                with open("package.json", "r", encoding="utf-8") as f:
                    import json
                    pkg = json.load(f)
                    deps = pkg.get("dependencies", {})
                    deps_content = "\n--- DEPENDÊNCIAS ATUAIS (package.json) ---\n" + json.dumps(deps, indent=2)
            except: pass
        
        auto_setup_rule = """
IMPORTANTE: Verifique se o código possui mecanismos de auto-instalação (ex: instala dependências sozinho) ou auto-configuração (ex: pede tokens de API via interface gráfica em vez de exigir criação manual de arquivo .env).
Se sim, nas instruções de "Como Usar" ou "Configuração", documente que a instalação/configuração é AUTOMÁTICA ao executar o script principal. NÃO peça para o usuário rodar `pip install` ou criar arquivos `.env` manualmente nesses casos.
"""

        if not current_readme.strip():
            # README não existe ou está vazio: cria do zero
            prompt = f"""Você é um desenvolvedor sênior. Crie um README.md curto e objetivo para este novo projeto, baseado no git diff inicial, na estrutura de arquivos e nas dependências abaixo.
Retorne APENAS o markdown final, sem blocos de código (```markdown).
{auto_setup_rule}

--- ESTRUTURA DE ARQUIVOS ---
{tree}
{deps_content}

--- GIT DIFF ---
{diff}
"""
        else:
            # README já existe: atualiza estrutura e adiciona changelog
            prompt = f"""Você é um desenvolvedor sênior mantenedor deste projeto.
Abaixo está o README ATUAL, a NOVA ESTRUTURA de pastas, as DEPENDÊNCIAS e o GIT DIFF com as mais recentes modificações de código.

{auto_setup_rule}

SUA TAREFA É RETORNAR O README COMPLETO ATUALIZADO:
1. Mantenha todo o histórico de atualizações antigas intacto.
2. Atualize a seção de "Estrutura do Projeto" substituindo a antiga pela nova estrutura (pode adicionar breves comentários nos arquivos principais).
3. Atualize a seção de "Dependências" (se existir) com base na lista de DEPENDÊNCIAS ATUAIS informada abaixo.
4. Caso não exista a tag "## 📋 Histórico de Atualizações", crie-a no final do arquivo.
5. Ao final do Histórico de Atualizações, adicione a nova atualização de hoje usando EXATAMENTE o formato estrito:

### 🔄 Atualização ({today})
- [Resumo direto da ação 1 baseado no DIFF]
- [Resumo direto da ação 2 baseado no DIFF]

Retorne APENAS o texto markdown do README completo final, sem a tag ```markdown em volta.

--- NOVA ESTRUTURA DE ARQUIVOS ---
{tree}
{deps_content}

--- GIT DIFF DAS ALTERAÇÕES ---
{diff}

--- README ATUAL ---
{current_readme}
"""
        retry_delays = [15, 30, 60, 120]
        for attempt in range(4):
            try:
                response = model.generate_content(prompt)
                content  = response.text.strip()
                if content.startswith("```markdown"):
                    content = content.replace("```markdown", "", 1)
                if content.startswith("```"):
                    content = content.replace("```", "", 1)
                if content.endswith("```"):
                    content = content[::-1].replace("```"[::-1], "", 1)[::-1]
                    
                # Extrai o resumo para exibir no commit in-line
                ai_summary = "Atualização documentada via Git Auto"
                if "### 🔄 Atualização" in content:
                    parts = content.split("### 🔄 Atualização")
                    if len(parts) > 1:
                        last_update = parts[-1]
                        lines = [line.strip("- *").strip() for line in last_update.split("\n") if line.strip().startswith("-")]
                        if lines: ai_summary = lines[0]
                
                return content.strip(), ai_summary

            except google_exceptions.ResourceExhausted as e:
                err = str(e)
                if "PerDay" in err or "per_day" in err.lower():
                    self.log("⚠ Cota diária de IA esgotada. Usando fallback local…", "warn")
                    self.log("  Adicione billing em https://ai.dev/rate-limit para remover o limite.", "debug")
                    return None, None
                wait = retry_delays[attempt] if attempt < len(retry_delays) else 120
                self.log(f"[IA] Rate-limit. Tentativa {attempt+1}/4 — aguardando {wait}s…", "warn")
                if attempt < 3:
                    time.sleep(wait)
                else:
                    self.log("Limite persistente. Usando fallback local.", "warn")
                    return None, None

            except google_exceptions.GoogleAPIError as e:
                self.log(f"[IA] Erro API: {type(e).__name__} — {e}", "error")
                return None, None
            except Exception as e:
                self.log(f"[IA] Erro inesperado: {type(e).__name__} — {e}", "error")
                return None, None
        return None, None

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
git clone https://github.com/{os.getenv("GITHUB_USERNAME", "seu-usuario")}/{project_name}.git
cd {project_name}
```

## Contribuição

Contribuições são bem-vindas! Abra uma *issue* ou envie um *pull request*.

## Licença

Distribuído sob a licença MIT.
"""
        self.log("[SYS] README local gerado com sucesso.", "info")
        return readme, "Commit automático via Git Auto (Fallback)"

    # ── WORKFLOW ──────────────────────────────────────────────────────────────
    def execute_workflow(self, project_path, commit_message=None):
        self.run_command("git add README.md")
        
        if not commit_message:
            commit_message = "docs: atualiza documentação via IA [skip ci]"
            
        msg_file = os.path.join(project_path, ".git", "AUTO_MSG")
        with open(msg_file, "w", encoding="utf-8") as f:
            f.write(commit_message)
            
        self.run_command(f'git commit -F ".git/AUTO_MSG"', check=False)
        if os.path.exists(msg_file):
            os.remove(msg_file)
            
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

    def ask_inline_commit_preview(self, suggested_commit, title="📝 Revisão do Commit"):
        """Pausa a thread atual e mostra um banner para edição da mensagem de commit."""
        self._preview_result = None
        self._preview_event = threading.Event()
        self.after(0, self._show_inline_commit_preview, title, suggested_commit)
        self._preview_event.wait()
        return self._preview_result

    def _show_inline_commit_preview(self, title, suggested_commit):
        # Esconde os cards de ação temporariamente
        self.actions_frame.grid_forget()
        
        # Cria o painel de confirmação integrado
        self.preview_frame = ctk.CTkFrame(self.main_frame, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["blue"])
        self.preview_frame.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        self.preview_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.preview_frame, text=title, font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=C["blue"]).pack(pady=(15, 5))
        ctk.CTkLabel(self.preview_frame, text="A IA sugeriu a mensagem abaixo. Edite se desejar antes de enviar:", font=ctk.CTkFont("Segoe UI", 13), text_color=C["text"]).pack(pady=(0, 10))
        
        self.commit_textbox = ctk.CTkTextbox(self.preview_frame, height=80, font=ctk.CTkFont("Consolas", 13), fg_color=C["input_bg"], border_color=C["card_border"], border_width=1, text_color=C["text"])
        self.commit_textbox.pack(fill="x", padx=20, pady=(0, 15))
        self.commit_textbox.insert("0.0", suggested_commit)
        
        btns = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        btns.pack(pady=(0, 15))
        
        ctk.CTkButton(btns, text="Cancelar", width=110, height=36,
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      fg_color=C["card_border"], hover_color=C["red_dark"], text_color=C["text"],
                      command=lambda: self._resolve_preview(None)).pack(side="left", padx=10)
                      
        ctk.CTkButton(btns, text="Confirmar Push", width=150, height=36,
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      fg_color=C["green_dark"], hover_color=C["green"], text_color="white",
                      command=lambda: self._resolve_preview(self.commit_textbox.get("0.0", "end").strip())).pack(side="left", padx=10)

    def _resolve_preview(self, result):
        self.preview_frame.destroy()
        # Restaura os cards de ação originais
        self.actions_frame.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        self._preview_result = result
        self._preview_event.set()

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

            new_readme, ai_summary = self.generate_readme(diff)
            if not new_readme:
                new_readme, ai_summary = self.generate_readme_fallback()
            if not new_readme:
                self.log("[ERRO] Não foi possível gerar README. Abortando.", "error")
                return

            final_commit_msg = self.ask_inline_commit_preview(ai_summary)
            if final_commit_msg:
                with open("README.md", "w", encoding="utf-8") as f:
                    f.write(new_readme + "\n")
                self.log("[SYS] README.md salvo.", "info")
                self.execute_workflow(path, commit_message=final_commit_msg)
            else:
                self.log("[SYS] Operação cancelada pelo usuário.", "info")
        finally:
            self.set_processing_state(False)

    def start_clone_process(self, opts: dict):
        self.set_processing_state(True)
        threading.Thread(target=self.clone_repo, args=(opts,), daemon=True).start()

    def clone_repo(self, opts: dict):
        url = opts["url"]
        dest = opts["dest"]
        try:
            repo_name = url.rstrip("/").split("/")[-1]
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
                
            self.log(f"[SYS] Iniciando clonagem de {repo_name}...", "info")
            os.makedirs(dest, exist_ok=True)
            os.chdir(dest)
            
            cmd = f'git clone "{url}"'
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if proc.returncode == 0:
                self.log(f"[GIT] Clonado com sucesso para: {dest}", "success")
                final_path = os.path.join(dest, repo_name)
                self.after(0, lambda p=final_path: self._autoload_cloned_project(p))
            else:
                self.log(f"[ERRO] Falha ao clonar: {proc.stderr}", "error")
        except Exception as e:
            self.log(f"[ERRO] Exceção na clonagem: {e}", "error")
        finally:
            self.after(0, lambda: self.set_processing_state(False))

    def _autoload_cloned_project(self, path):
        if os.path.exists(path):
            self.workspace_var.set(path)
            self.log(f"[SYS] Projeto '{os.path.basename(path)}' carregado no workspace.", "info")
            self.save_to_history(path)
            self.switch_main_view("push")
            
            # Exibe o resumo ou README
            ProjectReadmeDialog(self, path)

    def _build_pull_tab(self):
        container = ctk.CTkFrame(self.tab_pull, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(container, text="Atualizar Projeto Local", font=ctk.CTkFont("Segoe UI", 28, "bold"), text_color=C["text"]).pack(pady=(0, 10))
        ctk.CTkLabel(container, text="Puxe as últimas atualizações do GitHub para a sua máquina.\nO Auto-save irá proteger seus arquivos locais antes de baixar.", font=ctk.CTkFont("Segoe UI", 14), text_color=C["text_dim"], justify="center").pack(pady=(0, 20))
        
        ws = ctk.CTkFrame(container, fg_color=C["card"], corner_radius=16, border_width=1, border_color=C["card_border"])
        ws.pack(fill="x", pady=(0, 20))
        ws.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(ws, text="DIRETÓRIO DO PROJETO", font=ctk.CTkFont("Segoe UI", 10, "bold"), text_color=C["muted"]).grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(16, 6))
        
        self.entry_folder_pull = ctk.CTkEntry(ws, height=42, font=ctk.CTkFont("Consolas", 12), fg_color=C["input_bg"], border_color=C["card_border"], text_color=C["text"], textvariable=self.workspace_var)
        self.entry_folder_pull.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 18))
        
        btn_browse_pull = ctk.CTkButton(ws, text="Procurar", width=130, height=42, font=ctk.CTkFont("Segoe UI", 13, "bold"), fg_color=C["muted"], hover_color=C["blue"], command=self.browse_folder)
        btn_browse_pull.grid(row=1, column=2, padx=(0, 20), pady=(0, 18))
        
        self.btn_action_pull = ctk.CTkButton(
            container, text="Puxar Alterações", width=300, height=50,
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            fg_color=C["blue"], hover_color=C["blue_dark"], text_color="#ffffff",
            command=self._pull_code)
        self.btn_action_pull.pack(pady=(0, 30))
        
        self.pull_console = ctk.CTkTextbox(container, width=600, height=200, font=ctk.CTkFont("Consolas", 12), fg_color=C["console_bg"], text_color=C["console_fg"], border_width=1, border_color=C["card_border"])
        self.pull_console.pack()
        self.pull_console.insert("end", "> Pronto para sincronizar...\n")
        self.pull_console.configure(state="disabled")

    def _pull_code(self):
        path = self.entry_folder.get()
        if not path or not os.path.isdir(os.path.join(path, ".git")):
            self._log_pull("> [ERRO] O diretório atual não é um repositório Git válido.")
            return
            
        self.btn_action_pull.configure(state="disabled", text="⏳ Sincronizando...")
        
        def task():
            try:
                # 1. Proteger: Auto-save de eventuais mudanças locais
                self._log_pull("> [1/2] Salvando alterações locais...")
                subprocess.run('git add .', cwd=path, shell=True, capture_output=True)
                diff = subprocess.run('git diff --staged', cwd=path, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace').stdout
                if diff.strip():
                    self._log_pull("> Alterações detectadas. Criando Auto-save...")
                    subprocess.run(['git', 'commit', '-m', f"Auto-save antes de Pull ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})"], cwd=path, capture_output=True, encoding='utf-8', errors='replace')
                else:
                    self._log_pull("> Nada local pendente de salvamento.")
                    
                # 2. Executar Pull
                self._log_pull("> [2/2] Baixando da nuvem (git pull origin HEAD)...")
                proc = subprocess.run('git pull origin HEAD', cwd=path, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
                
                if proc.returncode == 0:
                    self._log_pull("> ✅ Sucesso! Projeto atualizado.\n" + proc.stdout)
                else:
                    self._log_pull(">  Falha no Pull:\n" + proc.stderr)
            except Exception as e:
                self._log_pull(f"> [ERRO] {str(e)}")
            finally:
                self.after(0, lambda: self.btn_action_pull.configure(state="normal", text="Puxar Alterações"))
                
        threading.Thread(target=task, daemon=True).start()
        
    def _log_pull(self, msg):
        self.after(0, self._insert_pull_log, msg)
        
    def _insert_pull_log(self, msg):
        self.pull_console.configure(state="normal")
        self.pull_console.insert("end", msg + "\n")
        self.pull_console.see("end")
        self.pull_console.configure(state="disabled")

    def switch_main_view(self, view):
        self.btn_nav_push.configure(fg_color=C["card"], hover_color=C["card_border"], text_color=C["text_dim"])
        self.btn_nav_clone.configure(fg_color=C["card"], hover_color=C["card_border"], text_color=C["text_dim"])
        if hasattr(self, "btn_branch"):
            self.btn_branch.configure(fg_color=C["card"], hover_color=C["card_border"], text_color=C["text_dim"])
        if hasattr(self, "btn_nav_pull"):
            self.btn_nav_pull.configure(fg_color=C["card"], hover_color=C["card_border"], text_color=C["text_dim"])
        if hasattr(self, "btn_nav_issues"):
            self.btn_nav_issues.configure(fg_color=C["card"], hover_color=C["card_border"], text_color=C["text_dim"])
        
        self.tab_push.grid_forget()
        self.tab_clone.grid_forget()
        if hasattr(self, "tab_pull"):
            self.tab_pull.grid_forget()
        if hasattr(self, "tab_dash"):
            self.tab_dash.grid_forget()
        if hasattr(self, "tab_branch"):
            self.tab_branch.grid_forget()
        if hasattr(self, "tab_issues"):
            self.tab_issues.grid_forget()

        if view == "push":
            self.btn_nav_push.configure(fg_color=C["blue"], hover_color=C["blue_dark"], text_color="#ffffff")
            self.tab_push.grid(row=0, column=0, sticky="nsew")
        elif view == "clone":
            self.btn_nav_clone.configure(fg_color=C["blue"], hover_color=C["blue_dark"], text_color="#ffffff")
            self.tab_clone.grid(row=0, column=0, sticky="nsew")
        elif view == "pull":
            if hasattr(self, "btn_nav_pull"):
                self.btn_nav_pull.configure(fg_color=C["blue"], hover_color=C["blue_dark"], text_color="#ffffff")
            if hasattr(self, "tab_pull"):
                self.tab_pull.grid(row=0, column=0, sticky="nsew")
        elif view == "branch":
            if hasattr(self, "btn_branch"):
                self.btn_branch.configure(fg_color=C["blue"], hover_color=C["blue_dark"], text_color="#ffffff")
            self.tab_branch.grid(row=0, column=0, sticky="nsew")
            self.branch_manager_view.load_branches()
        elif view == "dashboard":
            self.tab_dash.grid(row=0, column=0, sticky="nsew")
            self.dashboard_view.load_profile()
        elif view == "issues":
            if hasattr(self, "btn_nav_issues"):
                self.btn_nav_issues.configure(fg_color=C["blue"], hover_color=C["blue_dark"], text_color="#ffffff")
            self.tab_issues.grid(row=0, column=0, sticky="nsew")
            self.issues_view.load_repos()

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
                if GITHUB_USERNAME and GITHUB_TOKEN:
                    remote_url = remote_url.replace("https://github.com", f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com")
                
                self.log(f"[GITHUB] Repositório criado: {resp.json()['clone_url']}", "success")
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
            new_readme, ai_summary = self.generate_readme(diff)
            if not new_readme:
                new_readme, ai_summary = self.generate_readme_fallback()
            if not new_readme:
                self.log("[ERRO] Não foi possível gerar README. Abortando.", "error")
                return

            final_commit_msg = self.ask_inline_commit_preview(ai_summary, title="🚀 Finalizar Setup")
            if final_commit_msg:
                with open("README.md", "w", encoding="utf-8") as f:
                    f.write(new_readme + "\n")
                self.execute_workflow(path, commit_message=final_commit_msg)
            else:
                self.log("[SYS] Upload cancelado pelo usuário.", "info")
        finally:
            self.set_processing_state(False)



if __name__ == "__main__":
    import ctypes
    import sys
    import os

    # Prevenir múltiplas instâncias e trazer janela para frente
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    
    mutex = kernel32.CreateMutexW(None, False, "GitAutoSingleInstanceMutex")
    last_error = kernel32.GetLastError()
    
    DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    pid_file = os.path.join(DATA_DIR, "pid.txt")
    
    if last_error == 183:  # ERROR_ALREADY_EXISTS
        try:
            with open(pid_file, "r") as f:
                target_pid = int(f.read().strip())
                
            EnumWindows = user32.EnumWindows
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
            
            def foreach_window(hwnd, lParam):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:  # Garante que é a janela real com título, e não processos ocultos do Tkinter
                        pid = ctypes.c_ulong()
                        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                        if pid.value == target_pid:
                            if user32.IsIconic(hwnd):
                                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                            
                            # Força a janela a pular para frente de todas as outras (TopMost)
                            user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 3) # HWND_TOPMOST
                            user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 3) # HWND_NOTOPMOST
                            user32.SetForegroundWindow(hwnd)
                            return False # Para de buscar
                return True
                
            EnumWindows(EnumWindowsProc(foreach_window), 0)
        except Exception:
            pass
        sys.exit(0)

    # Salva o PID para instâncias futuras acharem a janela
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    app = App()
    app.mainloop()