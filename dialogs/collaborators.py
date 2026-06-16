"""
dialogs/collaborators.py
Gerenciamento de colaboradores de um repositório GitHub.
"""
import os
import re
import subprocess
import threading
import requests
import customtkinter as ctk
from tkinter import filedialog
from app.config import C
from app.theme import set_title_bar_color
from app.history import load_history


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

        # Build history mapping
        self.history_map = {}
        for item in load_history():
            path = item.get("path", "") if isinstance(item, dict) else item
            if os.path.exists(path):
                name = os.path.basename(path)
                self.history_map[name] = path

        self.current_path = self.app.workspace_var.get()
        current_name = os.path.basename(self.current_path) if self.current_path else ""
        if current_name and current_name not in self.history_map:
            self.history_map[current_name] = self.current_path

        self.owner = None
        self.repo  = None

        # Header Card
        self.header_card = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16,
                                        border_width=1, border_color=C["card_border"])
        self.header_card.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(self.header_card, text="Gerenciar Colaboradores",
                     font=ctk.CTkFont("Segoe UI", 20, "bold"),
                     text_color=C["text"]).pack(pady=(15, 5))

        selector_frame = ctk.CTkFrame(self.header_card, fg_color="transparent")
        selector_frame.pack(pady=(5, 15))

        ctk.CTkLabel(selector_frame, text="Projeto:",
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=C["text_dim"]).pack(side="left", padx=(0, 10))

        self.opt_project = ctk.CTkOptionMenu(
            selector_frame, values=list(self.history_map.keys()), width=160,
            fg_color=C["input_bg"], text_color=C["text"],
            button_color=C["blue"], button_hover_color=C["blue_dark"],
            command=self._on_project_change)
        self.opt_project.pack(side="left")
        if current_name in self.history_map:
            self.opt_project.set(current_name)

        ctk.CTkButton(selector_frame, text="Procurar...", width=80,
                      fg_color=C["card_border"], text_color=C["text"],
                      hover_color=C["muted"],
                      command=self._browse_folder).pack(side="left", padx=(10, 0))

        self.lbl_repo_info = ctk.CTkLabel(self.header_card, text="",
                                          font=ctk.CTkFont("Segoe UI", 12),
                                          text_color=C["blue"])
        self.lbl_repo_info.pack(pady=(0, 15))

        # Invite section
        invite_frame = ctk.CTkFrame(self, fg_color="transparent")
        invite_frame.pack(fill="x", padx=20, pady=(10, 5))

        self.entry_username = ctk.CTkEntry(
            invite_frame, placeholder_text="Digite o @username", width=180,
            fg_color=C["input_bg"], text_color=C["text"], border_color=C["card_border"])
        self.entry_username.pack(side="left", padx=(0, 10))

        self.opt_perm = ctk.CTkOptionMenu(
            invite_frame,
            values=["Leitura (Pull)", "Escrita (Push)", "Triagem", "Manutenção", "Admin"],
            width=130, fg_color=C["input_bg"], button_color=C["card_border"],
            text_color=C["text"])
        self.opt_perm.pack(side="left", padx=(0, 10))
        self.opt_perm.set("Escrita (Push)")

        ctk.CTkButton(invite_frame, text="Convidar", width=90,
                      fg_color=C["blue"], hover_color=C["blue_dark"],
                      text_color="#ffffff", command=self._invite).pack(side="left", fill="x", expand=True)

        self.lbl_status = ctk.CTkLabel(self, text="", font=ctk.CTkFont("Segoe UI", 12))
        self.lbl_status.pack(pady=(0, 10))

        ctk.CTkLabel(self, text="Colaboradores Atuais:",
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=C["text"], anchor="w").pack(fill="x", padx=20, pady=(0, 10))

        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color=C["card"], corner_radius=12,
            border_width=1, border_color=C["card_border"])
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        if self.current_path:
            self._update_repo_context()

    # ── helpers ──────────────────────────────────────────────────────────────
    def _on_project_change(self, selected_name):
        self.current_path = self.history_map.get(selected_name)
        self._update_repo_context()

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Selecione a Pasta do Projeto")
        if folder:
            if not os.path.isdir(os.path.join(folder, ".git")):
                self.lbl_repo_info.configure(
                    text="Esta pasta não é um repositório Git (.git).", text_color=C["red"])
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
        self.repo  = None
        try:
            out = subprocess.run(
                "git config --get remote.origin.url",
                cwd=self.current_path, shell=True, capture_output=True, text=True).stdout.strip()
            m = re.search(r'github\.com[:/]([^/]+)/([^.]+)', out)
            if m:
                self.owner, self.repo = m.groups()
                if self.repo.endswith(".git"):
                    self.repo = self.repo[:-4]
        except Exception:
            pass

        if self.owner and self.repo:
            self.lbl_repo_info.configure(
                text=f"Conectado: {self.owner}/{self.repo}", text_color=C["blue"])
            self._load_collaborators()
        else:
            self.lbl_repo_info.configure(
                text="Repositório GitHub não detectado neste projeto.", text_color=C["red"])
            for widget in self.list_frame.winfo_children():
                widget.destroy()

    def _load_collaborators(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        lbl_loading = ctk.CTkLabel(self.list_frame, text="Carregando colaboradores...",
                                   text_color=C["text_dim"])
        lbl_loading.pack(pady=20)

        def task():
            token = os.getenv("GITHUB_TOKEN")
            if not token:
                self.app.after(0, lambda: lbl_loading.configure(
                    text="Erro: GITHUB_TOKEN não configurado."))
                return
            headers = {"Authorization": f"Bearer {token}",
                       "Accept": "application/vnd.github+json"}
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/collaborators"
            try:
                resp = requests.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    self.app.after(0, lambda d=data: self._populate_list(d))
                else:
                    self.app.after(0, lambda: lbl_loading.configure(
                        text=f"Erro ao carregar ({resp.status_code})"))
            except Exception:
                self.app.after(0, lambda: lbl_loading.configure(text="Erro de conexão"))

        threading.Thread(target=task, daemon=True).start()

    def _populate_list(self, data):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
        if not data:
            ctk.CTkLabel(self.list_frame, text="Nenhum colaborador encontrado.",
                         text_color=C["text_dim"]).pack(pady=20)
            return

        perm_reverse_map = {
            "read": "Leitura (Pull)", "write": "Escrita (Push)",
            "admin": "Admin", "maintain": "Manutenção", "triage": "Triagem"
        }
        for user in data:
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            row.pack(fill="x", pady=8)
            ctk.CTkLabel(row, text=user.get("login", ""),
                         font=ctk.CTkFont("Segoe UI", 15, "bold"),
                         text_color=C["text"]).pack(side="left", padx=10)
            role_name = user.get("role_name", "read").lower()
            current_ui_perm = perm_reverse_map.get(role_name, "Leitura (Pull)")
            opt = ctk.CTkOptionMenu(
                row,
                values=["Leitura (Pull)", "Escrita (Push)", "Triagem", "Manutenção", "Admin"],
                width=130, height=28, font=ctk.CTkFont("Segoe UI", 11, "bold"),
                fg_color=C["bg"], button_color=C["card_border"], text_color=C["blue"],
                command=lambda v, u=user.get("login", ""): self._update_permission(u, v))
            opt.set(current_ui_perm)
            opt.pack(side="right", padx=10)

    def _update_permission(self, username, new_ui_perm):
        perm_map = {"Leitura (Pull)": "pull", "Escrita (Push)": "push",
                    "Triagem": "triage", "Manutenção": "maintain", "Admin": "admin"}
        perm = perm_map.get(new_ui_perm, "push")
        self.lbl_status.configure(text=f"Atualizando permissão de {username}...",
                                  text_color=C["text_dim"])

        def task():
            token = os.getenv("GITHUB_TOKEN")
            headers = {"Authorization": f"Bearer {token}",
                       "Accept": "application/vnd.github+json"}
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/collaborators/{username}"
            try:
                resp = requests.put(url, headers=headers, json={"permission": perm})
                if resp.status_code in [201, 204]:
                    self.app.after(0, lambda: self.lbl_status.configure(
                        text=f"✅ Permissão de @{username} atualizada!", text_color=C["green"]))
                else:
                    self.app.after(0, lambda: self.lbl_status.configure(
                        text="❌ Erro ao atualizar permissão.", text_color=C["red"]))
            except Exception:
                self.app.after(0, lambda: self.lbl_status.configure(
                    text="❌ Falha de conexão.", text_color=C["red"]))

        threading.Thread(target=task, daemon=True).start()

    def _invite(self):
        username = self.entry_username.get().strip()
        if not username:
            return
        if username.startswith("@"):
            username = username[1:]
        perm_map = {"Leitura (Pull)": "pull", "Escrita (Push)": "push",
                    "Triagem": "triage", "Manutenção": "maintain", "Admin": "admin"}
        perm = perm_map.get(self.opt_perm.get(), "push")
        self.lbl_status.configure(text="Enviando convite...", text_color=C["text_dim"])

        def task():
            token = os.getenv("GITHUB_TOKEN")
            headers = {"Authorization": f"Bearer {token}",
                       "Accept": "application/vnd.github+json"}
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/collaborators/{username}"
            try:
                resp = requests.put(url, headers=headers, json={"permission": perm})
                if resp.status_code in [201, 204]:
                    self.app.after(0, lambda: self.lbl_status.configure(
                        text=f"✅ Convite enviado para @{username} com permissão: {perm}!",
                        text_color=C["green"]))
                    self.app.after(0, self._load_collaborators)
                    self.app.after(0, lambda: self.entry_username.delete(0, "end"))
                else:
                    err = resp.json().get("message", "Erro desconhecido")
                    self.app.after(0, lambda: self.lbl_status.configure(
                        text=f"❌ Erro: {err}", text_color=C["red"]))
            except Exception:
                self.app.after(0, lambda: self.lbl_status.configure(
                    text="❌ Falha de conexão.", text_color=C["red"]))

        threading.Thread(target=task, daemon=True).start()
