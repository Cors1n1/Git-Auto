"""
views/clone_view.py
Painel de clonagem de repositórios (via API GitHub ou URL direta).
"""
import os
import threading
import requests
import customtkinter as ctk
from tkinter import filedialog, messagebox
import app.config as cfg
from app.config import C


class CloneProjectView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=40, pady=(40, 20))
        ctk.CTkLabel(hdr, text="O que você deseja clonar?",
                     font=ctk.CTkFont("Segoe UI", 24, "bold"),
                     text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(hdr, text="Baixe projetos do GitHub diretamente para sua máquina local.",
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=C["text_dim"]).pack(anchor="w")

        self.mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.mode_frame.pack(fill="x", padx=40, pady=(0, 20))

        self.btn_mode_api = ctk.CTkButton(
            self.mode_frame, text="Meus Repositórios (API)", height=44,
            font=ctk.CTkFont("Segoe UI", 13, "bold"), corner_radius=8,
            command=lambda: self.set_mode("api"))
        self.btn_mode_api.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_mode_url = ctk.CTkButton(
            self.mode_frame, text="Via URL (HTTPS/SSH)", height=44,
            font=ctk.CTkFont("Segoe UI", 13, "bold"), corner_radius=8,
            command=lambda: self.set_mode("url"))
        self.btn_mode_url.pack(side="left", fill="x", expand=True, padx=(10, 0))

        self.container = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16,
                                      border_width=1, border_color=C["card_border"])
        self.container.pack(fill="both", expand=True, padx=40, pady=(0, 40))
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frame_api = ctk.CTkFrame(self.container, fg_color="transparent")
        self.frame_url = ctk.CTkFrame(self.container, fg_color="transparent")

        self.selected_repo_url = None
        self._build_api_tab(self.frame_api)
        self._build_url_tab(self.frame_url)

        self.set_mode("api")

    # ── mode switcher ─────────────────────────────────────────────────────────
    def set_mode(self, mode):
        if mode == "api":
            self.btn_mode_api.configure(fg_color=C["blue"], hover_color=C["blue_dark"],
                                        text_color="#ffffff")
            self.btn_mode_url.configure(fg_color=C["input_bg"], hover_color=C["card_border"],
                                        text_color=C["text_dim"])
            self.frame_url.grid_forget()
            self.frame_api.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        else:
            self.btn_mode_url.configure(fg_color=C["blue"], hover_color=C["blue_dark"],
                                        text_color="#ffffff")
            self.btn_mode_api.configure(fg_color=C["input_bg"], hover_color=C["card_border"],
                                        text_color=C["text_dim"])
            self.frame_api.grid_forget()
            self.frame_url.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)

    # ── URL tab ───────────────────────────────────────────────────────────────
    def _build_url_tab(self, frame):
        center_frame = ctk.CTkFrame(frame, fg_color="transparent")
        center_frame.pack(expand=True, fill="x", padx=10)

        ctk.CTkLabel(center_frame, text="URL do Repositório (HTTPS ou SSH):",
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=C["text_dim"]).pack(anchor="w", pady=(0, 5))
        self.entry_url = ctk.CTkEntry(center_frame, height=36,
                                      font=ctk.CTkFont("Consolas", 11),
                                      fg_color=C["input_bg"], border_color=C["card_border"],
                                      text_color=C["text"])
        self.entry_url.pack(fill="x", pady=(0, 20))

        self.entry_dest_url = self._build_destination_selector(center_frame)

        ctk.CTkButton(center_frame, text="Clonar Projeto", height=40,
                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      fg_color=C["blue"], hover_color=C["blue_dark"],
                      command=self._confirm_url).pack(fill="x", pady=(10, 0))

    # ── API tab ───────────────────────────────────────────────────────────────
    def _build_api_tab(self, frame):
        if not cfg.GITHUB_TOKEN:
            ctk.CTkLabel(
                frame,
                text="GitHub Token não configurado.\n\nConfigure nas Configurações para usar este recurso.",
                font=ctk.CTkFont("Segoe UI", 12),
                text_color=C["text_dim"], justify="center").pack(expand=True)
            return

        bottom_frame = ctk.CTkFrame(frame, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x")

        self.entry_dest_api = self._build_destination_selector(bottom_frame)
        self.btn_confirm_api = ctk.CTkButton(
            bottom_frame, text="Clonar Selecionado", height=40,
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            fg_color=C["blue"], hover_color=C["blue_dark"],
            command=self._confirm_api)
        self.btn_confirm_api.pack(fill="x", pady=10)

        ctk.CTkLabel(frame, text="Meus Repositórios:",
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=C["text_dim"]).pack(anchor="w", pady=(5, 5))

        self.repo_listbox = ctk.CTkScrollableFrame(frame, fg_color=C["input_bg"])
        self.repo_listbox.pack(fill="both", expand=True, pady=(0, 10))

        threading.Thread(target=self._load_repos, daemon=True).start()

    # ── helpers ───────────────────────────────────────────────────────────────
    def _build_destination_selector(self, parent):
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(container, text="Pasta de Destino Local:",
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=C["text_dim"]).pack(anchor="w", pady=(0, 5))

        dest_frame = ctk.CTkFrame(container, fg_color="transparent")
        dest_frame.pack(fill="x")

        entry_dest = ctk.CTkEntry(dest_frame, height=36, font=ctk.CTkFont("Consolas", 11),
                                  fg_color=C["input_bg"], border_color=C["card_border"],
                                  text_color=C["text"])
        entry_dest.pack(side="left", fill="x", expand=True, padx=(0, 10))
        entry_dest.insert(0, os.path.expanduser("~/Desktop"))

        ctk.CTkButton(dest_frame, text="...", width=40, height=36,
                      fg_color=C["card_border"], hover_color=C["blue"],
                      text_color=C["text"],
                      command=lambda e=entry_dest: self._browse(e)).pack(side="left")
        return entry_dest

    def _browse(self, entry):
        d = filedialog.askdirectory(title="Selecione a pasta destino")
        if d:
            entry.delete(0, "end")
            entry.insert(0, d)

    def _load_repos(self):
        headers = {"Authorization": f"token {cfg.GITHUB_TOKEN}",
                   "Accept": "application/vnd.github.v3+json"}
        try:
            resp = requests.get(
                "https://api.github.com/user/repos?sort=updated&per_page=100",
                headers=headers, timeout=5)
            if resp.status_code == 200:
                self.after(0, lambda: self._populate_repos(resp.json()))
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
            ctk.CTkLabel(self.repo_listbox, text="Nenhum repositório encontrado.",
                         text_color=C["muted"]).pack(pady=10)
            return
        self.repo_buttons = []
        for r in repos:
            btn = ctk.CTkButton(
                self.repo_listbox, text=f"📦 {r['full_name']}", anchor="w",
                fg_color="transparent", hover_color=C["card_border"], text_color=C["text"],
                command=lambda url=r["clone_url"]: self._select_repo(url))
            btn.pack(fill="x", pady=2)
            btn._my_url = r["clone_url"]
            self.repo_buttons.append(btn)

    def _select_repo(self, url):
        self.selected_repo_url = url
        for b in self.repo_buttons:
            if b._my_url == url:
                b.configure(fg_color=C["blue_dark"], text_color="#ffffff")
            else:
                b.configure(fg_color="transparent", text_color=C["text"])

    def _confirm_url(self):
        url = self.entry_url.get().strip()
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
