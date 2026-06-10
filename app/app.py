"""
app/app.py
Classe principal App — janela, sidebar, main frame e toda a lógica de negócio.
"""
import os
import io
import json
import subprocess
import threading
import time
import datetime

import requests
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw
from google.api_core import exceptions as google_exceptions

import app.config as cfg
from app.config import C, DATA_DIR, HISTORY_FILE, CACHE_REPOS
from app.history import load_history, save_history
from app.theme import set_title_bar_color, update_palette

# ── views & dialogs (imported lazily to avoid circular issues) ────────────────
from views.dashboard_view import DashboardView
from views.clone_view import CloneProjectView
from views.branch_view import BranchManagerView
from views.issues_view import IssuesView
from dialogs.settings import SettingsDialog
from dialogs.new_project import NewProjectDialog
from dialogs.time_machine import TimeMachineDialog
from dialogs.diff_viewer import DiffViewerDialog
from dialogs.gitignore_dialog import GitignoreDialog
from dialogs.release_manager import ReleaseManagerDialog
from dialogs.readme_dialog import ProjectReadmeDialog


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Git Auto  |  AI Repository Manager")
        self.geometry("1180x740")
        self.minsize(900, 600)
        self.workspace_var = ctk.StringVar(value=os.getcwd())
        update_palette(cfg.APP_THEME, cfg.APP_COLOR)

        self.configure(fg_color=C["bg"])
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self._build_sidebar()
        self._build_main()

        self.top_line = ctk.CTkFrame(self, height=3, fg_color=C["blue"], corner_radius=0)
        self.top_line.place(relx=0, rely=0, relwidth=1)

        try:
            self.iconbitmap(os.path.join(DATA_DIR, "icon.ico"))
        except Exception:
            pass

        self.setup_tray()
        self.load_history_ui()
        self.log("Sistema inicializado. Interface pronta.", "info")

        if not cfg.GEMINI_API_KEY or not cfg.GITHUB_TOKEN or not cfg.GITHUB_USERNAME:
            self.after(500, self.prompt_first_setup)

        # Screensaver
        self.idle_after_id    = None
        self.screensaver_active = False
        self.screensaver_frame  = None
        self.bind("<Any-Key>",    self._reset_idle)
        self.bind("<Any-Button>", self._reset_idle)
        self.bind("<Motion>",     self._reset_idle)
        self._reset_idle()

    # ── Screensaver ───────────────────────────────────────────────────────────
    def _reset_idle(self, event=None):
        if self.screensaver_active:
            if hasattr(self, "ss_start_time") and time.time() - self.ss_start_time < 0.5:
                pass
            else:
                if event and hasattr(event, "type"):
                    if event.type.name in ("ButtonPress", "ButtonRelease", "KeyPress", "KeyRelease"):
                        self._hide_screensaver()
                else:
                    self._hide_screensaver()
        if self.idle_after_id:
            self.after_cancel(self.idle_after_id)
        self.idle_after_id = self.after(900000, self.show_screensaver)

    def _hide_screensaver(self):
        if self.screensaver_frame:
            self.screensaver_frame.destroy()
            self.screensaver_frame = None
        self.screensaver_active = False

    def show_screensaver(self):
        if self.screensaver_active:
            return
        # Não atrapalha se a janela estiver minimizada ou em segundo plano
        if self.state() == "iconic" or self.focus_displayof() is None:
            self.idle_after_id = self.after(900000, self.show_screensaver)
            return

        import random
        import tkinter as tk
        self.ss_start_time  = time.time()
        self.ss_last_time   = None
        self.screensaver_active = True

        self.screensaver_frame = ctk.CTkToplevel(self, fg_color="#0d1117")
        self.screensaver_frame.overrideredirect(True)

        x       = self.winfo_x()
        y       = self.winfo_y()
        root_x  = self.winfo_rootx()
        root_y  = self.winfo_rooty()
        border_w = root_x - x
        title_h  = root_y - y
        total_w  = self.winfo_width()  + 2 * border_w
        total_h  = self.winfo_height() + title_h + border_w
        self.screensaver_frame.geometry(f"{total_w}x{total_h}+{x}+{y}")
        self.screensaver_frame.attributes("-topmost", True)

        self.ss_canvas = tk.Canvas(self.screensaver_frame, bg="#0d1117", highlightthickness=0)
        self.ss_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.screensaver_frame.bind("<Any-Key>",    self._reset_idle)
        self.screensaver_frame.bind("<Any-Button>", self._reset_idle)
        self.ss_canvas.bind("<Any-Key>",    self._reset_idle)
        self.ss_canvas.bind("<Any-Button>", self._reset_idle)

        self.gh_colors = ["#161b22", "#21262d", "#30363d", "#010409"]
        self.nodes = []

        for _ in range(60):
            w     = random.randint(40, 150)
            h     = random.randint(30, 80)
            px    = random.randint(0, 2000)
            py    = random.randint(0, 1200)
            color = random.choice(self.gh_colors)
            rect  = self.ss_canvas.create_rectangle(px, py, px + w, py + h,
                                                    fill=color, outline="#30363d", width=1)
            self.nodes.append({"id": rect, "speed": random.uniform(0.3, 1.2)})

        self.lines = []
        for _ in range(25):
            x1, y1 = random.randint(0, 2000), random.randint(0, 1200)
            x2, y2 = x1 + random.randint(-200, 200), y1 + random.randint(-200, 200)
            line   = self.ss_canvas.create_line(x1, y1, x2, y2, fill="#21262d", width=1)
            self.lines.append({"id": line, "speed": random.uniform(0.3, 0.8)})

        self.logo_bg_id = self.ss_canvas.create_rectangle(
            -1000, -1000, -1000, -1000, fill="#0d1117", outline="#30363d", width=1, tags="logo")

        try:
            from PIL import ImageOps, ImageTk
            img_path = os.path.join(DATA_DIR, "octocat.png")
            if os.path.exists(img_path):
                pil_img = Image.open(img_path).convert("RGBA").resize((130, 130))
                r, g, b, a = pil_img.split()
                inverted  = ImageOps.invert(Image.merge("RGB", (r, g, b)))
                pil_img   = Image.merge("RGBA", inverted.split() + (a,))
                mask = Image.new("L", pil_img.size, 0)
                ImageDraw.Draw(mask).ellipse((0, 0, 130, 130), fill=255)
                pil_img.putalpha(mask)
                self.octo_img_tk = ImageTk.PhotoImage(pil_img)
            else:
                self.octo_img_tk = None
        except Exception:
            self.octo_img_tk = None

        self.logo_circle_id = self.ss_canvas.create_oval(
            -1000, -1000, -1000, -1000, fill="#ffffff", outline="", tags="logo")

        if self.octo_img_tk:
            self.logo_img_id  = self.ss_canvas.create_image(
                -1000, -1000, image=self.octo_img_tk, anchor="center", tags="logo")
            self.logo_text_id = None
        else:
            self.logo_img_id  = None
            self.logo_text_id = self.ss_canvas.create_text(
                -1000, -1000, text="⬡", font=("Segoe UI", 70),
                fill="#000000", anchor="center", tags="logo")

        self.logo_label_id = self.ss_canvas.create_text(
            -1000, -1000, text="G I T   A U T O",
            font=("Segoe UI", 24, "bold"), fill="#ffffff", anchor="center", tags="logo")
        self.logo_time_id = self.ss_canvas.create_text(
            -1000, -1000, text="", font=("Segoe UI", 16),
            fill="#8b949e", anchor="center", tags="logo")

        self._animate_screensaver()

    def _animate_screensaver(self):
        if not self.screensaver_active or not self.screensaver_frame or \
                not self.screensaver_frame.winfo_exists():
            return

        import random
        sw = self.screensaver_frame.winfo_width()
        sh = self.screensaver_frame.winfo_height()

        if sw > 0 and sh > 0:
            cx, cy = sw / 2, sh / 2
            bw, bh = 320, 280
            self.ss_canvas.coords(self.logo_bg_id,
                                  cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
            cw, ch = 130, 130
            self.ss_canvas.coords(self.logo_circle_id,
                                  cx - cw / 2, cy - ch / 2 - 30,
                                  cx + cw / 2, cy + ch / 2 - 30)

            if self.logo_img_id:
                self.ss_canvas.coords(self.logo_img_id, cx, cy - 30)
            if self.logo_text_id:
                self.ss_canvas.coords(self.logo_text_id, cx, cy - 35)

            self.ss_canvas.coords(self.logo_label_id, cx, cy + 80)
            self.ss_canvas.coords(self.logo_time_id,  cx, cy + 115)

            now = time.strftime("%H:%M")
            if not hasattr(self, "ss_last_time") or self.ss_last_time != now:
                self.ss_last_time = now
                self.ss_canvas.itemconfig(self.logo_time_id, text=now)

            self.ss_canvas.tag_raise("logo")
            for item in self.nodes + self.lines:
                self.ss_canvas.move(item["id"], -item["speed"], -item["speed"] * 0.7)
                coords = self.ss_canvas.coords(item["id"])
                if coords and len(coords) == 4:
                    x1, y1, x2, y2 = coords
                    if x2 < 0 or y2 < 0:
                        w = x2 - x1
                        h = y2 - y1
                        nx = sw + random.randint(0, 300)
                        ny = sh + random.randint(0, 300)
                        self.ss_canvas.coords(item["id"], nx, ny, nx + w, ny + h)

        self.after(30, self._animate_screensaver)

    # ── Theme ─────────────────────────────────────────────────────────────────
    def apply_theme(self):
        current_path = self.workspace_var.get()

        for attr in ("sidebar", "main_frame", "top_line"):
            if hasattr(self, attr):
                getattr(self, attr).destroy()

        self.workspace_var = ctk.StringVar(value=current_path)
        self.configure(fg_color=C["bg"])
        set_title_bar_color(self, C["bg"], C["text"])

        self._build_sidebar()
        self._build_main()

        self.top_line = ctk.CTkFrame(self, height=3, fg_color=C["blue"], corner_radius=0)
        self.top_line.place(relx=0, rely=0, relwidth=1)

        self.entry_folder.delete(0, "end")
        self.entry_folder.insert(0, current_path)
        self.load_history_ui()
        self.update_branch_status()

    def prompt_first_setup(self):
        messagebox.showinfo(
            "Bem-vindo ao Git Auto",
            "Parece que é a sua primeira vez aqui (ou faltam credenciais)!\n\n"
            "Por favor, insira o seu Username, Token do GitHub e Chave do Gemini "
            "para habilitar todas as funções.")
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
        logo_lbl = ctk.CTkLabel(logo_frame, text="⬡ Git Auto",
                                font=ctk.CTkFont("Segoe UI", 22, "bold"),
                                text_color=C["text"], cursor="hand2")
        logo_lbl.pack(anchor="w")
        logo_lbl.bind("<Button-1>", lambda e: self.restart_app())
        ctk.CTkLabel(logo_frame, text="AI-Powered Repository Manager",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=C["text_dim"]).pack(anchor="w")

        self.btn_sidebar_dash = ctk.CTkButton(
            self.sidebar, text="Meu Perfil", height=38,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=C["card"], hover_color=C["card_border"],
            text_color=C["blue"], border_width=1, border_color=C["card_border"],
            command=lambda: self.switch_main_view("dashboard"))
        self.btn_sidebar_dash.grid(row=1, column=0, sticky="ew", padx=20, pady=(20, 0))

        ctk.CTkFrame(self.sidebar, height=1, fg_color=C["card_border"]).grid(
            row=2, column=0, sticky="ew", padx=0, pady=16)

        self.status_pill = ctk.CTkFrame(self.sidebar, fg_color=C["card"], corner_radius=20, height=36)
        self.status_pill.grid(row=3, column=0, padx=20, sticky="ew")
        self.status_pill.pack_propagate(False)
        self.status_dot = ctk.CTkLabel(self.status_pill, text="●",
                                       font=ctk.CTkFont(size=12), text_color=C["muted"])
        self.status_dot.pack(side="left", padx=(14, 4))
        self.status_label = ctk.CTkLabel(self.status_pill, text="Aguardando",
                                         font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                         text_color=C["text_dim"])
        self.status_label.pack(side="left")

        self.progressbar = ctk.CTkProgressBar(self.sidebar, mode="indeterminate",
                                              height=3, corner_radius=0,
                                              progress_color=C["blue"],
                                              fg_color=C["card_border"])
        self.progressbar.grid(row=4, column=0, sticky="ew", padx=0, pady=(12, 0))
        self.progressbar.set(0)

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
            fg_color="transparent", border_width=1, border_color=C["card_border"],
            text_color=C["text_dim"], hover_color=C["red_dark"],
            command=self.clear_all_history)
        self.btn_clear_history.grid(row=0, column=2, sticky="e")

        self.history_frame = ctk.CTkScrollableFrame(
            self.sidebar, fg_color="transparent",
            scrollbar_button_color=C["muted"],
            scrollbar_button_hover_color=C["text_dim"])
        self.history_frame.grid(row=6, column=0, sticky="nsew", padx=10, pady=(0, 10))

        bottom_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_frame.grid(row=7, column=0, sticky="ew", padx=20, pady=(10, 5))
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

        import base64
        _c_txt = base64.b64decode(b"RGVzZW52b2x2aWRvIHBvciBDb3JzaW5p").decode("utf-8")
        self.lbl_credits = ctk.CTkLabel(
            self.sidebar, text=_c_txt, font=ctk.CTkFont("Segoe UI", 10),
            text_color=C["muted"], cursor="hand2")
        self.lbl_credits.grid(row=8, column=0, sticky="s", pady=(0, 20))
        
        def _open_creator(e):
            import webbrowser
            _u = base64.b64decode(b"aHR0cHM6Ly9naXRodWIuY29tL0NvcnMxbjE=").decode("utf-8")
            webbrowser.open(_u)
        self.lbl_credits.bind("<Button-1>", _open_creator)

    def shutdown_app(self):
        self.quit()
        self.destroy()
        os._exit(0)

    def restart_app(self):
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

    # ── MAIN FRAME ────────────────────────────────────────────────────────────
    def _build_main(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=28, pady=28)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Nav bar
        self.nav_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.nav_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))

        def _nav_btn(text, cmd):
            return ctk.CTkButton(self.nav_frame, text=text,
                                 font=ctk.CTkFont("Segoe UI", 14, "bold"), height=42,
                                 fg_color=C["card"], hover_color=C["card_border"],
                                 text_color=C["text_dim"], corner_radius=10, command=cmd)

        self.btn_nav_push  = _nav_btn("Repositórios", lambda: self.switch_main_view("push"))
        self.btn_nav_push.configure(fg_color=C["blue"], text_color="#ffffff")
        self.btn_nav_push.pack(side="left", padx=(0, 10))

        self.btn_nav_clone = _nav_btn("Clonagem", lambda: self.switch_main_view("clone"))
        self.btn_nav_clone.pack(side="left", padx=(0, 10))

        self.btn_branch = _nav_btn("Branch: --", lambda: self.switch_main_view("branch"))
        self.btn_branch.pack(side="left", padx=(0, 10))

        self.btn_nav_pull  = _nav_btn("Sincronizar", lambda: self.switch_main_view("pull"))
        self.btn_nav_pull.pack(side="left", padx=(0, 10))

        self.btn_nav_issues = _nav_btn("Tarefas", lambda: self.switch_main_view("issues"))
        self.btn_nav_issues.pack(side="left", padx=(0, 10))

        # Content container
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.grid(row=2, column=0, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # ── Tabs ──────────────────────────────────────────────────────────────
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

        # ── Workspace card ────────────────────────────────────────────────────
        ws = ctk.CTkFrame(self.tab_push, fg_color=C["card"], corner_radius=16,
                          border_width=1, border_color=C["card_border"])
        ws.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        ws.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(ws, text="DIRETÓRIO DO PROJETO",
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=C["muted"]).grid(row=0, column=0, columnspan=3,
                                                 sticky="w", padx=20, pady=(16, 6))

        self.entry_folder = ctk.CTkEntry(
            ws, height=42, font=ctk.CTkFont("Consolas", 12),
            fg_color=C["input_bg"], border_color=C["card_border"],
            text_color=C["text"], textvariable=self.workspace_var,
            placeholder_text="Selecione o caminho do projeto...")
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

        self.btn_release = ctk.CTkButton(
            ws_actions, text="Lançar Versão", height=28, width=110,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color="transparent", hover_color=C["card"], text_color=C["orange"],
            border_width=1, border_color=C["card_border"],
            command=self.open_release_manager)
        self.btn_release.pack(side="right", padx=(10, 0))

        self.btn_time_machine = ctk.CTkButton(
            ws_actions, text="Máquina do Tempo", height=28, width=120,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color="transparent", hover_color=C["warn_bg"], text_color=C["red"],
            border_width=1, border_color=C["card_border"],
            command=self.discard_changes)
        self.btn_time_machine.pack(side="right", padx=(10, 0))

        self.btn_vscode = ctk.CTkButton(
            ws_actions, text="Abrir VSCode", height=28, width=110,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color="transparent", hover_color=C["card"], text_color=C["blue"],
            border_width=1, border_color=C["card_border"],
            command=self.open_vscode)
        self.btn_vscode.pack(side="right", padx=(10, 0))

        self.btn_gitignore = ctk.CTkButton(
            ws_actions, text="Gerar .gitignore", height=28, width=110,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color="transparent", hover_color=C["card"], text_color=C["text_dim"],
            border_width=1, border_color=C["card_border"],
            command=self.open_gitignore_generator)
        self.btn_gitignore.pack(side="right")

        # ── Action cards ──────────────────────────────────────────────────────
        self.actions_frame = ctk.CTkFrame(self.tab_push, fg_color="transparent")
        self.actions_frame.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        self.actions_frame.grid_columnconfigure((0, 1), weight=1)

        # Card Atualizar
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

        # Card Novo Projeto
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
        ctk.CTkFrame(cn, fg_color="transparent", height=32).grid(
            row=1, column=0, sticky="ew", padx=24, pady=(0, 10))
        self.btn_new = ctk.CTkButton(
            cn, text="Criar e Enviar", height=36,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color=C["green"], hover_color=C["green_dark"], text_color="#1a1b26",
            corner_radius=6, command=self.start_new_project_thread)
        self.btn_new.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 24))

        # ── Console + Push History tabs ───────────────────────────────────────
        self.tabs = ctk.CTkTabview(
            self.tab_push, fg_color=C["card"], corner_radius=16,
            border_width=1, border_color=C["card_border"],
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
            fg_color="transparent", border_width=1, border_color=C["card_border"],
            text_color=C["text_dim"], hover_color=C["muted"],
            command=self.clear_log)
        self.btn_clear_log.grid(row=0, column=1, sticky="e")

        self.console = ctk.CTkTextbox(
            tab_log, font=ctk.CTkFont("Consolas", 12),
            fg_color=C["console_bg"], text_color=C["console_fg"],
            wrap="word", corner_radius=0)
        self.console.grid(row=1, column=0, sticky="nsew", padx=10, pady=(4, 10))

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
        if hasattr(self, "tray_icon"):
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
            if isinstance(entry, str):
                entry = {"path": entry, "date": "", "branch": "", "status": "ok"}
            path   = entry.get("path", "")
            date   = entry.get("date", "")
            status = entry.get("status", "ok")

            folder_name = os.path.basename(path)
            exists      = os.path.isdir(path)
            icon_color  = C["green"] if status == "ok" else C["red"]

            card = ctk.CTkFrame(self.history_frame, fg_color=C["card"],
                                corner_radius=10, border_width=1, border_color=C["card_border"])
            card.pack(fill="x", pady=6, padx=4)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(12, 0))
            ctk.CTkLabel(top_row, text="●",
                         font=ctk.CTkFont(size=14), text_color=icon_color).pack(side="left", padx=(0, 8))
            ctk.CTkButton(top_row, text=folder_name,
                          font=ctk.CTkFont("Segoe UI", 14, "bold"),
                          text_color=C["text"], fg_color="transparent", hover_color=C["card_border"],
                          anchor="w",
                          command=lambda p=path: self.set_folder_from_history(p)).pack(
                side="left", fill="x", expand=True)
            ctk.CTkButton(top_row, text="✕", width=24, height=24,
                          font=ctk.CTkFont("Segoe UI", 12, "bold"),
                          fg_color="transparent", hover_color=C["card_border"],
                          text_color=C["text_dim"], corner_radius=4,
                          command=lambda p=path: self.remove_from_history(p)).pack(side="right")

            mid_row = ctk.CTkFrame(card, fg_color="transparent")
            mid_row.pack(fill="x", padx=12, pady=(0, 12))
            status_text = "Sincronizado" if status == "ok" else "Falhou"
            ctk.CTkLabel(mid_row, text=f"🕐 {date}   •   {status_text}",
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=icon_color if status != "ok" else C["text_dim"]).pack(
                side="left", padx=(20, 0))

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
            ctk.CTkLabel(self.project_history_scroll,
                         text="Repositório Git não inicializado.",
                         text_color=C["muted"]).pack(pady=40)
            return

        cmd = (f'git -C "{path}" log --remotes --format="%H|%ad|%an|%s" '
               '--date=format:"%d/%m/%Y %H:%M"')
        try:
            res   = subprocess.run(cmd, shell=True, capture_output=True,
                                   text=True, encoding="utf-8", errors="replace")
            lines = [l for l in res.stdout.strip().splitlines() if l.strip()]
        except Exception:
            lines = []

        if not lines:
            ctk.CTkLabel(self.project_history_scroll,
                         text="Nenhum push efetuado neste repositório ainda.",
                         text_color=C["muted"]).pack(pady=40)
            return

        folder_name = os.path.basename(path)
        for line in lines:
            parts = line.split("|", 3)
            if len(parts) < 4:
                continue
            c_hash, date, author, msg = parts

            container = ctk.CTkFrame(self.project_history_scroll, fg_color=C["card"],
                                     corner_radius=6, border_width=1, border_color=C["card_border"])
            container.pack(fill="x", pady=4)

            details_frame = ctk.CTkFrame(container, fg_color="transparent")

            def toggle_details(df=details_frame, h=c_hash, p=path, a=author):
                if df.winfo_ismapped():
                    df.pack_forget()
                else:
                    if not df.winfo_children():
                        ctk.CTkLabel(df, text=f"Hash: {h[:7]}   |   Autor: {a}",
                                     font=ctk.CTkFont("Consolas", 10),
                                     text_color=C["text_dim"]).pack(anchor="w", padx=14, pady=(8, 6))
                        cmd_stat = (f'git -C "{p}" show --name-status '
                                    f'--format="%B|||SPLIT|||" {h}')
                        try:
                            stat_res = subprocess.run(
                                cmd_stat, shell=True, capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
                            out = stat_res.stdout.strip()
                            if "|||SPLIT|||" in out:
                                msg_part, files_part = out.split("|||SPLIT|||", 1)
                            else:
                                msg_part, files_part = out, ""
                            msg_part   = msg_part.strip()
                            files_part = files_part.strip()
                            if msg_part:
                                mb = ctk.CTkTextbox(df, height=80, font=ctk.CTkFont("Segoe UI", 13),
                                                    fg_color="transparent", text_color=C["text"],
                                                    border_width=0)
                                mb.pack(fill="x", padx=10, pady=(0, 4))
                                mb.insert("1.0", msg_part)
                                mb.configure(state="disabled")
                            if files_part:
                                ctk.CTkLabel(df, text="Arquivos Alterados:",
                                             font=ctk.CTkFont("Segoe UI", 11, "bold"),
                                             text_color=C["text_dim"]).pack(anchor="w", padx=14, pady=(2, 2))
                                box = ctk.CTkTextbox(df, height=70, font=ctk.CTkFont("Consolas", 11),
                                                     fg_color=C["console_bg"], text_color=C["text_dim"],
                                                     border_width=1, border_color=C["card_border"],
                                                     corner_radius=6)
                                box.pack(fill="x", padx=14, pady=(0, 14))
                                box.insert("1.0", files_part)
                                box.configure(state="disabled")
                        except Exception:
                            pass
                    df.pack(fill="x", expand=True)

            btn = ctk.CTkButton(container,
                                text=f"✓   {folder_name}   •   {date}   (Clique para expandir)",
                                anchor="w", height=38,
                                fg_color="transparent", hover_color=C["input_bg"],
                                text_color=C["green"], font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                command=toggle_details)
            btn.pack(side="top", fill="x")

    def save_to_history(self, current_path, branch="master", status="ok"):
        history = load_history()
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
                               "Remover todos os projetos do histórico?\n"
                               "(Os arquivos locais não serão apagados.)"):
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
        for btn in (self.btn_update, self.btn_new, self.btn_browse, self.btn_clear_history):
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
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        prefix_map = {
            "info":    ("▸", C["console_fg"]),
            "warn":    ("⚠", C["orange"]),
            "error":   ("✖", C["red"]),
            "success": ("✔", C["green"]),
            "debug":   ("·", C["muted"]),
        }
        sym, _ = prefix_map.get(level, ("▸", C["console_fg"]))
        self.console.insert("end", f"[{ts}] {sym}  {text}\n")
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
        if cfg.VERBOSE_LOGGING:
            self.log(f"Executando: {command}", "debug")
        try:
            result = subprocess.run(
                command, shell=True, check=check,
                capture_output=True, text=True, encoding="utf-8", errors="replace")
            if cfg.VERBOSE_LOGGING:
                self.log(f"  [OK] Comando concluído.", "success")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            if cfg.VERBOSE_LOGGING:
                self.log(f"  [FALHA] Código de erro: {e.returncode}", "error")
            if check:
                self.log(f"[ERRO] {command}\n{e.stderr.strip()}", "error")
            return ""

    def _show_error(self, msg):
        messagebox.showerror("Erro", msg)

    def ensure_gitignore(self):
        all_templates = ["Python", "Node.js", "Java", "C++", "React/Next.js", "Godot", "Unity", "Generico"]
        self.generate_specific_gitignore(all_templates, silent=True, append_missing=True)

    def open_gitignore_generator(self):
        dialog = GitignoreDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self.generate_specific_gitignore(dialog.result)

    def open_vscode(self):
        repo = self.entry_folder.get().strip()
        if not repo or not os.path.exists(repo):
            self._show_error("Selecione uma pasta válida primeiro.")
            return
        try:
            subprocess.Popen(["code", "."], cwd=repo, shell=True)
            if cfg.VERBOSE_LOGGING:
                self.log(f"[SYS] VSCode aberto na pasta: {repo}", "success")
        except Exception as e:
            self._show_error(f"Erro ao abrir VSCode: {e}\nCertifique-se de que o comando 'code' está no PATH.")

    def discard_changes(self):
        repo = self.entry_folder.get().strip()
        if not repo or not os.path.exists(os.path.join(repo, ".git")):
            self._show_error("Esta pasta não é um repositório Git válido.")
            return
        repo_name = os.path.basename(os.path.abspath(repo))
        commit_info_text = "Nenhum commit encontrado (Estado Inicial)"
        try:
            info_meta = self.run_command(
                f'git -C "{repo}" log -1 --format="%h | %cd" '
                '--date=format:"%d/%m/%Y às %H:%M"', check=False)
            info_msg = self.run_command(
                f'git -C "{repo}" log -1 --format="%s"', check=False)
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
                self.log("[SYS] ⏪ Máquina do Tempo ativada! Todas as mudanças não salvas foram apagadas.", "success")
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
            self.run_command("git add -N .", check=False)
            diff_output = self.run_command("git diff", check=False)
        except Exception as e:
            diff_output = f"Erro ao gerar diff: {str(e)}"
        finally:
            os.chdir(original_cwd)
        DiffViewerDialog(self, diff_output)

    def open_release_manager(self):
        repo = self.entry_folder.get().strip()
        if not repo or not os.path.exists(os.path.join(repo, ".git")):
            self._show_error("Selecione um repositório Git válido primeiro.")
            return
        dialog = ReleaseManagerDialog(self, repo)
        self.wait_window(dialog)

    def generate_specific_gitignore(self, template_names, silent=False, append_missing=False):
        base_ignores = ("# Ambiente / SO\n.env\n.env.*\n.flaskenv*\n.flasken\n!.env.example\n.DS_Store\n"
                        "Thumbs.db\ndesktop.ini\n\n# IDEs\n.vscode/\n.idea/\n\n")
        templates = {
            "Python":      "# Python\n__pycache__/\n*.py[cod]\n*$py.class\nvenv/\n.venv/\nenv/\n.env/\nbuild/\ndist/\n*.egg-info/\n*.log\n",
            "Node.js":     "# Node\nnode_modules/\nnpm-debug.log\nyarn-error.log\nbuild/\ndist/\ncoverage/\n",
            "Java":        "# Java\n*.class\n*.log\n*.jar\n*.war\n*.nar\n*.ear\n*.zip\n*.tar.gz\n*.rar\ntarget/\nbuild/\n.gradle/\n",
            "C++":         "# C++\n*.o\n*.obj\n*.exe\n*.dll\n*.so\n*.dylib\n*.out\n*.app\nCMakeCache.txt\nCMakeFiles/\ncmake_install.cmake\nMakefile\nbin/\nbuild/\n",
            "React/Next.js": "# React / Next.js\nnode_modules/\n.pnp\n.pnp.js\ncoverage/\nbuild/\n.next/\nout/\n.env.local\n.env.development.local\n.env.test.local\n.env.production.local\n",
            "Godot":       "# Godot\n.godot/\n*.translation\nexport_presets.cfg\n",
            "Unity":       "# Unity\n[Ll]ibrary/\n[Tt]emp/\n[Oo]bj/\n[Bb]uild/\n[Bb]uilds/\n[Ll]ogs/\n[Uu]ser[Ss]ettings/\n*.csproj\n*.unityproj\n*.sln\n*.suo\n*.tmp\n*.user\n*.userprefs\n",
            "Generico":    "# Generic\nbuild/\ndist/\n*.log\ntmp/\n",
        }
        selected = "\n".join(templates.get(t, "") for t in template_names)
        content  = base_ignores + (selected if selected.strip() else templates["Generico"])
        path = self.entry_folder.get()
        
        if not path or not os.path.exists(path):
            if not silent:
                self.log("[ERRO] Diretório inválido para gerar .gitignore.", "error")
            return
            
        filepath = os.path.join(path, ".gitignore")
        
        try:
            if append_missing and os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    existing_content = f.read()
                
                existing_rules = set(line.strip() for line in existing_content.split("\n") 
                                     if line.strip() and not line.startswith("#"))
                
                to_append = ""
                added_any = False
                for line in content.split("\n"):
                    clean = line.strip()
                    if clean and not clean.startswith("#"):
                        if clean not in existing_rules:
                            to_append += clean + "\n"
                            added_any = True
                            existing_rules.add(clean)
                
                if added_any:
                    to_append = "\n\n# --- Regras Automáticas Adicionais (Git Auto) ---\n" + to_append
                    with open(filepath, "a", encoding="utf-8") as f:
                        f.write(to_append)
                    if not silent:
                        self.log("[SYS] .gitignore existente atualizado com regras de segurança.", "success")
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                if not silent:
                    self.log(f"[SYS] .gitignore gerado com sucesso.", "success")
        except Exception as e:
            if not silent:
                self.log(f"[ERRO] Falha ao criar/atualizar .gitignore: {e}", "error")

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

        def build_tree(dir_path, prefix="", depth=0):
            if depth > 2:
                return ""
            ignored = {".git", "__pycache__", "node_modules", ".venv", "venv", "env", "dist", "build"}
            try:
                entries = [e for e in os.listdir(dir_path) if e not in ignored]
            except Exception:
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
            except Exception:
                pass
        elif os.path.exists("package.json"):
            try:
                with open("package.json", "r", encoding="utf-8") as f:
                    pkg  = json.load(f)
                    deps = pkg.get("dependencies", {})
                    deps_content = "\n--- DEPENDÊNCIAS ATUAIS (package.json) ---\n" + json.dumps(deps, indent=2)
            except Exception:
                pass

        auto_setup_rule = (
            "\nIMPORTANTE: Verifique se o código possui mecanismos de auto-instalação ou "
            "auto-configuração. Se sim, documente que a instalação/configuração é AUTOMÁTICA.\n"
        )

        # Prevenção contra Payload Too Large / Limites de Token
        safe_diff = diff[:8000] + "\n... [diff truncado]" if len(diff) > 8000 else diff
        safe_tree = tree[:4000] + "\n... [árvore truncada]" if len(tree) > 4000 else tree
        safe_readme = current_readme[:4000] + "\n... [readme truncado]" if len(current_readme) > 4000 else current_readme

        if not current_readme.strip():
            prompt = (
                f"Você é um desenvolvedor sênior. Crie um README.md curto e objetivo para este "
                f"novo projeto, baseado no git diff inicial, na estrutura de arquivos e nas dependências abaixo.\n"
                f"Retorne APENAS o markdown final, sem blocos de código (```markdown).\n{auto_setup_rule}\n"
                f"--- ESTRUTURA DE ARQUIVOS ---\n{safe_tree}{deps_content}\n--- GIT DIFF ---\n{safe_diff}\n"
            )
        else:
            prompt = (
                f"Você é um desenvolvedor sênior mantenedor deste projeto.\n{auto_setup_rule}\n"
                f"SUA TAREFA É RETORNAR O README COMPLETO ATUALIZADO:\n"
                f"1. Mantenha todo o histórico de atualizações antigas intacto.\n"
                f"2. Atualize a seção 'Estrutura do Projeto'.\n"
                f"3. Atualize a seção 'Dependências' se existir.\n"
                f"4. Crie a tag '## 📋 Histórico de Atualizações' se não existir.\n"
                f"5. Adicione:\n\n### 🔄 Atualização ({today})\n- [Resumo da ação]\n\n"
                f"Retorne APENAS o markdown final.\n"
                f"--- NOVA ESTRUTURA ---\n{safe_tree}{deps_content}\n"
                f"--- GIT DIFF ---\n{safe_diff}\n--- README ATUAL ---\n{safe_readme}\n"
            )

        retry_delays = [15, 30, 60, 120]
        for attempt in range(4):
            try:
                response = cfg.model.generate_content(prompt)
                content  = response.text.strip()
                for marker in ("```markdown", "```"):
                    if content.startswith(marker):
                        content = content[len(marker):]
                if content.endswith("```"):
                    content = content[:-3]

                ai_summary = "Atualização documentada via Git Auto"
                if "### 🔄 Atualização" in content:
                    parts = content.split("### 🔄 Atualização")
                    if len(parts) > 1:
                        lines = [l.strip("- *").strip() for l in parts[-1].split("\n")
                                 if l.strip().startswith("-")]
                        if lines:
                            ai_summary = lines[0]
                return content.strip(), ai_summary

            except google_exceptions.ResourceExhausted as e:
                err = str(e)
                if "PerDay" in err or "per_day" in err.lower():
                    self.log("⚠ Cota diária de IA esgotada. Usando fallback local…", "warn")
                    return None, None
                wait = retry_delays[attempt] if attempt < len(retry_delays) else 120
                self.log(f"[IA] Rate-limit. Tentativa {attempt + 1}/4 — aguardando {wait}s…", "warn")
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
        ignored_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "env", "dist", "build"}

        for root, dirs, files in os.walk(cwd):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for fname in files:
                rel = os.path.relpath(os.path.join(root, fname), cwd)
                all_files.append(rel)
                ext = os.path.splitext(fname)[1].lower()
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1

        lang_map = {".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
                    ".java": "Java", ".cs": "C#", ".cpp": "C++", ".c": "C",
                    ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
                    ".swift": "Swift", ".kt": "Kotlin", ".html": "HTML/CSS"}
        detected_lang = "Não identificada"
        if extensions:
            top_ext       = max(extensions, key=extensions.get)
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

        bad_exts  = {".pyc", ".pyo", ".pyd", ".log", ".lock", ".png", ".jpg", ".ico", ".gif", ".woff", ".ttf"}
        key_files = [f for f in all_files
                     if not any(f.endswith(e) for e in bad_exts)
                     and len(f.split(os.sep)) <= 3]
        files_section = ("\n## Estrutura do Projeto\n\n```\n" +
                         "\n".join(sorted(key_files)[:30]) + "\n```\n") if key_files else ""

        readme = (
            f"# {project_name}\n\n"
            f"> Documentação gerada automaticamente pelo Git Auto.\n\n"
            f"## Sobre o Projeto\n\nRepositório **{project_name}**.\n\n"
            f"- **Linguagem principal:** {detected_lang}\n"
            f"- **Total de arquivos:** {len(all_files)}\n"
            f"{deps_section}{files_section}"
            f"## Como Usar\n\n```bash\n"
            f"git clone https://github.com/{os.getenv('GITHUB_USERNAME', 'seu-usuario')}/{project_name}.git\n"
            f"cd {project_name}\n```\n\n## Contribuição\n\n"
            f"Contribuições são bem-vindas! Abra uma *issue* ou envie um *pull request*.\n\n"
            f"## Licença\n\nDistribuído sob a licença MIT.\n"
        )
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
        self.run_command('git commit -F ".git/AUTO_MSG"', check=False)
        if os.path.exists(msg_file):
            os.remove(msg_file)
        branch = self.run_command("git branch --show-current") or "master"
        self.log(f"[GIT] Push → branch '{branch}'…", "info")
        try:
            subprocess.run(f"git push -u origin {branch}", shell=True, check=True,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.log("✔  Processo finalizado com sucesso! 🎉", "success")
            self.save_to_history(project_path, branch=branch, status="ok")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Push falhou: {e.stderr.strip()}", "error")
            self.log("Verifique o remote: git remote -v", "warn")
            self.save_to_history(project_path, branch=branch, status="erro")
            return False

    # ── INLINE CONFIRMATIONS ──────────────────────────────────────────────────
    def ask_inline_confirmation(self, title, message):
        self._confirm_result = None
        self._confirm_event  = threading.Event()
        self.after(0, self._show_inline_confirmation, title, message)
        self._confirm_event.wait()
        return self._confirm_result

    def _show_inline_confirmation(self, title, message):
        self.actions_frame.grid_forget()
        self.confirm_frame = ctk.CTkFrame(self.main_frame, fg_color=C["warn_bg"],
                                          corner_radius=12, border_width=1,
                                          border_color=C["orange"])
        self.confirm_frame.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        self.confirm_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.confirm_frame, text=title,
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=C["orange"]).pack(pady=(15, 5))
        ctk.CTkLabel(self.confirm_frame, text=message,
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=C["text"]).pack(pady=(0, 20))
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
        self.actions_frame.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        self._confirm_result = result
        self._confirm_event.set()

    def ask_inline_commit_preview(self, suggested_commit, title="📝 Revisão do Commit"):
        self._preview_result = None
        self._preview_event  = threading.Event()
        self.after(0, self._show_inline_commit_preview, title, suggested_commit)
        self._preview_event.wait()
        return self._preview_result

    def _show_inline_commit_preview(self, title, suggested_commit):
        self.actions_frame.grid_forget()
        self.preview_frame = ctk.CTkFrame(self.main_frame, fg_color=C["card"],
                                          corner_radius=12, border_width=1,
                                          border_color=C["blue"])
        self.preview_frame.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        self.preview_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.preview_frame, text=title,
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=C["blue"]).pack(pady=(15, 5))
        ctk.CTkLabel(self.preview_frame,
                     text="A IA sugeriu a mensagem abaixo. Edite se desejar antes de enviar:",
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=C["text"]).pack(pady=(0, 10))
        self.commit_textbox = ctk.CTkTextbox(
            self.preview_frame, height=80, font=ctk.CTkFont("Consolas", 13),
            fg_color=C["input_bg"], border_color=C["card_border"], border_width=1,
            text_color=C["text"])
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
                      command=lambda: self._resolve_preview(
                          self.commit_textbox.get("0.0", "end").strip())).pack(side="left", padx=10)

    def _resolve_preview(self, result):
        self.preview_frame.destroy()
        self.actions_frame.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        self._preview_result = result
        self._preview_event.set()

    # ── THREADS ───────────────────────────────────────────────────────────────
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
        url  = opts["url"]
        dest = opts["dest"]
        try:
            repo_name = url.rstrip("/").split("/")[-1]
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
            self.log(f"[SYS] Iniciando clonagem de {repo_name}...", "info")
            os.makedirs(dest, exist_ok=True)
            os.chdir(dest)
            proc = subprocess.run(f'git clone "{url}"', shell=True, capture_output=True, text=True)
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
            ProjectReadmeDialog(self, path)

    # ── PULL TAB ──────────────────────────────────────────────────────────────
    def _build_pull_tab(self):
        container = ctk.CTkFrame(self.tab_pull, fg_color="transparent")
        container.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(container, text="Atualizar Projeto Local",
                     font=ctk.CTkFont("Segoe UI", 28, "bold"),
                     text_color=C["text"]).pack(pady=(0, 10))
        ctk.CTkLabel(container,
                     text="Puxe as últimas atualizações do GitHub para a sua máquina.\nO Auto-save irá proteger seus arquivos locais antes de baixar.",
                     font=ctk.CTkFont("Segoe UI", 14),
                     text_color=C["text_dim"], justify="center").pack(pady=(0, 20))

        ws = ctk.CTkFrame(container, fg_color=C["card"], corner_radius=16,
                          border_width=1, border_color=C["card_border"])
        ws.pack(fill="x", pady=(0, 20))
        ws.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(ws, text="DIRETÓRIO DO PROJETO",
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=C["muted"]).grid(row=0, column=0, columnspan=3,
                                                 sticky="w", padx=20, pady=(16, 6))
        self.entry_folder_pull = ctk.CTkEntry(
            ws, height=42, font=ctk.CTkFont("Consolas", 12),
            fg_color=C["input_bg"], border_color=C["card_border"],
            text_color=C["text"], textvariable=self.workspace_var)
        self.entry_folder_pull.grid(row=1, column=0, columnspan=2,
                                    sticky="ew", padx=20, pady=(0, 18))
        ctk.CTkButton(ws, text="Procurar", width=130, height=42,
                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      fg_color=C["muted"], hover_color=C["blue"],
                      command=self.browse_folder).grid(row=1, column=2,
                                                       padx=(0, 20), pady=(0, 18))

        self.btn_action_pull = ctk.CTkButton(
            container, text="Puxar Alterações", width=300, height=50,
            font=ctk.CTkFont("Segoe UI", 16, "bold"),
            fg_color=C["blue"], hover_color=C["blue_dark"], text_color="#ffffff",
            command=self._pull_code)
        self.btn_action_pull.pack(pady=(0, 30))

        self.pull_console = ctk.CTkTextbox(
            container, width=600, height=200, font=ctk.CTkFont("Consolas", 12),
            fg_color=C["console_bg"], text_color=C["console_fg"],
            border_width=1, border_color=C["card_border"])
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
                self._log_pull("> [1/2] Salvando alterações locais...")
                subprocess.run("git add .", cwd=path, shell=True, capture_output=True)
                diff = subprocess.run("git diff --staged", cwd=path, shell=True,
                                      capture_output=True, text=True,
                                      encoding="utf-8", errors="replace").stdout
                if diff.strip():
                    self._log_pull("> Alterações detectadas. Criando Auto-save...")
                    subprocess.run(
                        ["git", "commit", "-m",
                         f"Auto-save antes de Pull ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})"],
                        cwd=path, capture_output=True, encoding="utf-8", errors="replace")
                else:
                    self._log_pull("> Nada local pendente de salvamento.")
                self._log_pull("> [2/2] Baixando da nuvem (git pull origin HEAD)...")
                proc = subprocess.run("git pull origin HEAD", cwd=path, shell=True,
                                      capture_output=True, text=True,
                                      encoding="utf-8", errors="replace")
                if proc.returncode == 0:
                    self._log_pull("> ✅ Sucesso! Projeto atualizado.\n" + proc.stdout)
                else:
                    self._log_pull("> Falha no Pull:\n" + proc.stderr)
            except Exception as e:
                self._log_pull(f"> [ERRO] {str(e)}")
            finally:
                self.after(0, lambda: self.btn_action_pull.configure(
                    state="normal", text="Puxar Alterações"))

        threading.Thread(target=task, daemon=True).start()

    def _log_pull(self, msg):
        self.after(0, self._insert_pull_log, msg)

    def _insert_pull_log(self, msg):
        self.pull_console.configure(state="normal")
        self.pull_console.insert("end", msg + "\n")
        self.pull_console.see("end")
        self.pull_console.configure(state="disabled")

    # ── VIEW SWITCHER ─────────────────────────────────────────────────────────
    def switch_main_view(self, view):
        # Reset all nav buttons
        inactive = {"fg_color": C["card"], "hover_color": C["card_border"], "text_color": C["text_dim"]}
        active   = {"fg_color": C["blue"], "hover_color": C["blue_dark"], "text_color": "#ffffff"}

        for btn in (self.btn_nav_push, self.btn_nav_clone,
                    self.btn_branch, self.btn_nav_pull, self.btn_nav_issues):
            if hasattr(self, btn.winfo_name() if hasattr(btn, "winfo_name") else ""):
                pass
            btn.configure(**inactive)

        # Hide all tabs
        for tab in ("tab_push", "tab_clone", "tab_pull", "tab_dash", "tab_branch", "tab_issues"):
            if hasattr(self, tab):
                getattr(self, tab).grid_forget()

        mapping = {
            "push":      (self.btn_nav_push,   self.tab_push),
            "clone":     (self.btn_nav_clone,  self.tab_clone),
            "pull":      (self.btn_nav_pull,   self.tab_pull),
            "branch":    (self.btn_branch,     self.tab_branch),
            "dashboard": (None,                self.tab_dash),
            "issues":    (self.btn_nav_issues, self.tab_issues),
        }
        btn_ref, tab_ref = mapping.get(view, (None, None))
        if btn_ref:
            btn_ref.configure(**active)
        if tab_ref:
            tab_ref.grid(row=0, column=0, sticky="nsew")

        # Post-show hooks
        if view == "branch":
            self.branch_manager_view.load_branches()
        elif view == "dashboard":
            self.dashboard_view.load_profile()
        elif view == "issues":
            self.issues_view.load_repos()

    # ── NEW PROJECT ───────────────────────────────────────────────────────────
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

            diff = self.get_code_changes()
            new_readme, ai_summary = self.generate_readme(diff)
            if not new_readme:
                new_readme, ai_summary = self.generate_readme_fallback()
            if not new_readme:
                self.log("[ERRO] Não foi possível gerar README. Abortando.", "error")
                return

            final_commit_msg = self.ask_inline_commit_preview(ai_summary, title="🚀 Finalizar Setup")
            if not final_commit_msg:
                self.log("[SYS] Setup cancelado pelo usuário. Repositório no GitHub não foi criado.", "warn")
                return

            headers = {"Authorization": f"Bearer {cfg.GITHUB_TOKEN}",
                       "Accept": "application/vnd.github.v3+json"}
            payload = {"name":        repo_name,
                       "private":     opts["private"],
                       "description": opts.get("description", "")}
            resp = requests.post("https://api.github.com/user/repos",
                                 json=payload, headers=headers)
            if resp.status_code == 201:
                remote_url = resp.json()["clone_url"]
                if cfg.GITHUB_USERNAME and cfg.GITHUB_TOKEN:
                    remote_url = remote_url.replace(
                        "https://github.com",
                        f"https://{cfg.GITHUB_USERNAME}:{cfg.GITHUB_TOKEN}@github.com")
                self.log(f"[GITHUB] Repositório criado: {resp.json()['clone_url']}", "success")
                existing = self.run_command("git remote", check=False)
                if "origin" in existing.split():
                    self.run_command("git remote remove origin", check=False)
                self.run_command(f"git remote add origin {remote_url}")
                time.sleep(3)
            else:
                msg = resp.json().get("message", "Erro desconhecido")
                err = resp.json().get("errors", "")
                self.log(f"[GITHUB] Erro ao criar repo: {msg} | {err}", "error")
                return

            with open("README.md", "w", encoding="utf-8") as f:
                f.write(new_readme + "\n")
            self.execute_workflow(path, commit_message=final_commit_msg)
        finally:
            self.set_processing_state(False)
