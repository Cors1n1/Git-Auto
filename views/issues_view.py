"""
views/issues_view.py
Painel de gerenciamento de issues/tarefas do GitHub.
"""
import os
import json
import threading
import requests
import customtkinter as ctk
from tkinter import messagebox
import app.config as cfg
from app.config import C, CACHE_REPOS
from app.theme import set_title_bar_color


class NewIssueDialog(ctk.CTkToplevel):
    def __init__(self, parent, repo_name, edit_mode=False,
                 initial_title="", initial_body=""):
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

        hdr = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        hdr_text = (f"Editar Tarefa em {repo_name}" if edit_mode
                    else f"Nova Tarefa em {repo_name}")
        ctk.CTkLabel(hdr, text=hdr_text, font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=C["text"]).pack(side="left", padx=20, pady=15)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Título:", font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=C["text_dim"]).pack(anchor="w")
        self.entry_title = ctk.CTkEntry(frame, height=36, font=ctk.CTkFont("Segoe UI", 12),
                                        fg_color=C["input_bg"], border_color=C["card_border"],
                                        text_color=C["text"])
        self.entry_title.pack(fill="x", pady=(5, 15))
        if initial_title:
            self.entry_title.insert(0, initial_title)

        ctk.CTkLabel(frame, text="Descrição:", font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=C["text_dim"]).pack(anchor="w")
        self.txt_body = ctk.CTkTextbox(frame, height=120, font=ctk.CTkFont("Segoe UI", 12),
                                       fg_color=C["input_bg"], border_color=C["card_border"],
                                       border_width=1, text_color=C["text"])
        self.txt_body.pack(fill="x", pady=(5, 20))
        if initial_body:
            self.txt_body.insert("1.0", initial_body)

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom")
        ctk.CTkButton(btn_frame, text="Cancelar", width=100, height=36,
                      fg_color="transparent", border_width=1, border_color=C["card_border"],
                      hover_color=C["card"], text_color=C["text"],
                      command=self.destroy).pack(side="left")
        btn_text = "Salvar" if edit_mode else "Criar Tarefa"
        ctk.CTkButton(btn_frame, text=btn_text, width=120, height=36,
                      fg_color=C["blue"], hover_color=C["blue_dark"],
                      command=self.confirm).pack(side="right")
        self.entry_title.focus()

    def confirm(self):
        title = self.entry_title.get().strip()
        body  = self.txt_body.get("1.0", "end").strip()
        if not title:
            messagebox.showwarning("Aviso", "O título não pode estar vazio.")
            return
        self.result = {"title": title, "body": body}
        self.destroy()


class IssueDetailsDialog(ctk.CTkToplevel):
    def __init__(self, parent, issue_data, issues_view):
        super().__init__(parent)
        self.issue_data  = issue_data
        self.issues_view = issues_view

        self.title(f"Issue #{issue_data['number']}")
        self.geometry("650x700")
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color=C["bg"])
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))

        # Comment input (bottom)
        add_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=80)
        add_frame.pack(fill="x", side="bottom")
        add_frame.pack_propagate(False)

        self.entry_comment = ctk.CTkEntry(
            add_frame, placeholder_text="Escreva um comentário...",
            font=ctk.CTkFont("Segoe UI", 12),
            fg_color=C["input_bg"], border_color=C["card_border"])
        self.entry_comment.pack(side="left", fill="x", expand=True,
                                padx=(20, 10), pady=20)

        ctk.CTkButton(add_frame, text="Comentar", width=100, height=36,
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      fg_color=C["blue"], hover_color=C["blue_dark"],
                      command=self.post_comment).pack(side="right", padx=(0, 20), pady=20)

        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=20, pady=10)

        self.build_ui()
        self.load_comments()

    def build_ui(self):
        for w in self.main_scroll.winfo_children():
            w.destroy()

        hdr = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 10))

        is_open    = self.issue_data["state"] == "open"
        state_color = C["green"] if is_open else C["red"]
        ctk.CTkLabel(hdr, text=self.issue_data["state"].upper(),
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=state_color).pack(side="left", padx=(0, 15))
        ctk.CTkLabel(hdr, text=self.issue_data["title"],
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=C["text"], wraplength=500, justify="left").pack(
            side="left", fill="x", expand=True)

        body_text = self.issue_data.get("body") or "*Sem descrição*"
        ctk.CTkLabel(self.main_scroll, text=body_text,
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=C["text_dim"], justify="left",
                     wraplength=550).pack(anchor="w", pady=(0, 20))

        actions = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        actions.pack(fill="x", pady=(0, 20))

        ctk.CTkButton(actions, text="Editar", width=80, height=30,
                      fg_color="transparent", border_width=1,
                      border_color=C["card_border"], hover_color=C["muted"],
                      text_color=C["text"], command=self.edit_issue).pack(side="left", padx=(0, 10))

        if is_open:
            ctk.CTkButton(actions, text="Concluir Tarefa", width=120, height=30,
                          fg_color=C["green"], hover_color="#207a3c",
                          command=lambda: self.toggle_state("closed")).pack(side="left", padx=(0, 10))
        else:
            ctk.CTkButton(actions, text="Reabrir Tarefa", width=120, height=30,
                          fg_color=C["orange"], hover_color="#cc6600",
                          command=lambda: self.toggle_state("open")).pack(side="left", padx=(0, 10))

        ctk.CTkButton(actions, text="Dica do Gemini", width=120, height=30,
                      fg_color=C["blue"], hover_color=C["blue_dark"],
                      command=self.ask_gemini).pack(side="left")

        self.ai_frame = ctk.CTkFrame(self.main_scroll, fg_color=C["card"], corner_radius=8,
                                     border_width=1, border_color=C["blue"])

        ctk.CTkFrame(self.main_scroll, height=1, fg_color=C["card_border"]).pack(fill="x", pady=20)
        ctk.CTkLabel(self.main_scroll, text="Comentários",
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(0, 10))

        self.comments_container = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.comments_container.pack(fill="x", pady=(0, 10))

    def ask_gemini(self):
        self.ai_frame.pack(fill="x", pady=10)
        for w in self.ai_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.ai_frame,
                     text="Analisando com Inteligência Artificial...",
                     font=ctk.CTkFont(slant="italic"),
                     text_color=C["blue"]).pack(pady=15)

        def task():
            try:
                prompt = (
                    f"Eu tenho uma tarefa no meu projeto chamada '{self.issue_data['title']}'. "
                    f"A descrição é: {self.issue_data.get('body', '')}. "
                    "Me dê uma dica rápida e direta de programador de como eu poderia resolver ou começar a resolver isso."
                )
                if not cfg.GEMINI_API_KEY:
                    self.winfo_exists() and self.after(
                        0, lambda: self.show_ai_result("Erro: Chave do Gemini não configurada."))
                    return
                resp = cfg.model.generate_content(prompt)
                self.winfo_exists() and self.after(0, lambda: self.show_ai_result(resp.text))
            except Exception:
                self.winfo_exists() and self.after(0, lambda: self.show_ai_result("Falha na IA."))

        threading.Thread(target=task, daemon=True).start()

    def show_ai_result(self, text):
        for w in self.ai_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.ai_frame, text="Dica do Gemini",
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=C["blue"]).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(self.ai_frame, text=text, font=ctk.CTkFont("Segoe UI", 12),
                     text_color=C["text"], justify="left",
                     wraplength=480).pack(anchor="w", padx=15, pady=(0, 15))

    def load_comments(self):
        for w in self.comments_container.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.comments_container, text="Carregando...",
                     text_color=C["text_dim"]).pack(pady=10)

        def task():
            token    = os.getenv("GITHUB_TOKEN")
            username = os.getenv("GITHUB_USERNAME")
            headers  = {"Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json"}
            url = (f"https://api.github.com/repos/{username}/"
                   f"{self.issues_view.current_repo}/issues/{self.issue_data['number']}/comments")
            try:
                r = requests.get(url, headers=headers)
                comments = r.json() if r.status_code == 200 else []
                self.winfo_exists() and self.after(0, lambda: self.render_comments(comments))
            except Exception:
                self.winfo_exists() and self.after(0, lambda: self.render_comments([]))

        threading.Thread(target=task, daemon=True).start()

    def render_comments(self, comments):
        for w in self.comments_container.winfo_children():
            w.destroy()
        if not comments:
            ctk.CTkLabel(self.comments_container,
                         text="Nenhum comentário ainda.",
                         text_color=C["muted"]).pack(pady=10)
            return
        for c in comments:
            c_frame = ctk.CTkFrame(self.comments_container, fg_color=C["card"],
                                   corner_radius=8, border_width=1,
                                   border_color=C["card_border"])
            c_frame.pack(fill="x", pady=5)
            hdr = ctk.CTkFrame(c_frame, fg_color="transparent")
            hdr.pack(fill="x", padx=15, pady=(10, 5))
            user = c.get("user", {}).get("login", "alguém")
            date = c.get("created_at", "").split("T")[0]
            ctk.CTkLabel(hdr, text=user, font=ctk.CTkFont("Segoe UI", 11, "bold"),
                         text_color=C["text"]).pack(side="left")
            ctk.CTkLabel(hdr, text=date, font=ctk.CTkFont("Segoe UI", 10),
                         text_color=C["muted"]).pack(side="right")
            body = c.get("body", "")
            ctk.CTkLabel(c_frame, text=body, font=ctk.CTkFont("Segoe UI", 12),
                         text_color=C["text_dim"], justify="left",
                         wraplength=500).pack(anchor="w", padx=15, pady=(0, 15))

    def post_comment(self):
        text = self.entry_comment.get().strip()
        if not text:
            return
        self.entry_comment.delete(0, "end")

        def task():
            token    = os.getenv("GITHUB_TOKEN")
            username = os.getenv("GITHUB_USERNAME")
            headers  = {"Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json"}
            url = (f"https://api.github.com/repos/{username}/"
                   f"{self.issues_view.current_repo}/issues/{self.issue_data['number']}/comments")
            requests.post(url, headers=headers, json={"body": text})
            self.winfo_exists() and self.after(0, self.load_comments)

        threading.Thread(target=task, daemon=True).start()

    def toggle_state(self, new_state):
        def task():
            token    = os.getenv("GITHUB_TOKEN")
            username = os.getenv("GITHUB_USERNAME")
            headers  = {"Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json"}
            url = (f"https://api.github.com/repos/{username}/"
                   f"{self.issues_view.current_repo}/issues/{self.issue_data['number']}")
            r = requests.patch(url, headers=headers, json={"state": new_state})
            if r.status_code == 200:
                self.issue_data["state"] = new_state
                self.winfo_exists() and self.after(0, self.build_ui)
                self.winfo_exists() and self.after(
                    0, lambda: self.issues_view.load_issues_for_repo(
                        self.issues_view.current_repo))

        threading.Thread(target=task, daemon=True).start()

    def edit_issue(self):
        dialog = NewIssueDialog(self, self.issues_view.current_repo,
                                edit_mode=True,
                                initial_title=self.issue_data["title"],
                                initial_body=self.issue_data.get("body", ""))
        self.wait_window(dialog)
        if dialog.result:
            title = dialog.result["title"]
            body  = dialog.result["body"]

            def task():
                token    = os.getenv("GITHUB_TOKEN")
                username = os.getenv("GITHUB_USERNAME")
                headers  = {"Authorization": f"Bearer {token}",
                            "Accept": "application/vnd.github+json"}
                url = (f"https://api.github.com/repos/{username}/"
                       f"{self.issues_view.current_repo}/issues/{self.issue_data['number']}")
                r = requests.patch(url, headers=headers, json={"title": title, "body": body})
                if r.status_code == 200:
                    self.issue_data["title"] = title
                    self.issue_data["body"]  = body
                    self.winfo_exists() and self.after(0, self.build_ui)
                    self.winfo_exists() and self.after(
                        0, lambda: self.issues_view.load_issues_for_repo(
                            self.issues_view.current_repo))

            threading.Thread(target=task, daemon=True).start()


class IssuesView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app          = app
        self.current_repo = None
        self.issues_data  = []

        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(hdr, text="Tarefas",
                     font=ctk.CTkFont("Segoe UI", 24, "bold"),
                     text_color=C["text"]).pack(side="left")
        self.btn_new = ctk.CTkButton(hdr, text="Nova Tarefa", height=32,
                                     fg_color=C["blue"], hover_color=C["blue_dark"],
                                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                     command=self.open_new_issue)
        self.btn_new.pack(side="right")

        repo_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=8, height=60)
        repo_frame.pack(fill="x", padx=20, pady=10)
        repo_frame.pack_propagate(False)

        ctk.CTkLabel(repo_frame, text="Projeto:",
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=C["text_dim"]).pack(side="left", padx=(15, 10))
        self.repo_combo = ctk.CTkOptionMenu(
            repo_frame, values=["Carregando..."], width=250,
            fg_color=C["input_bg"], button_color=C["card_border"],
            command=self.load_issues_for_repo)
        self.repo_combo.pack(side="left", pady=15)

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def load_repos(self):
        if os.path.exists(CACHE_REPOS):
            try:
                with open(CACHE_REPOS, "r", encoding="utf-8") as f:
                    data  = json.load(f)
                    names = [r["name"] for r in data[:15]]
                    if names:
                        self.repo_combo.configure(values=names)
                        if not self.current_repo:
                            self.repo_combo.set(names[0])
                            self.load_issues_for_repo(names[0])
                    else:
                        self.repo_combo.configure(values=["Nenhum repositório"])
            except Exception:
                pass

    def load_issues_for_repo(self, repo_name):
        self.current_repo = repo_name
        for w in self.list_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.list_frame, text="Carregando tarefas...",
                     text_color=C["text_dim"]).pack(pady=40)

        def task():
            token    = os.getenv("GITHUB_TOKEN")
            username = os.getenv("GITHUB_USERNAME")
            if not token or not username:
                self.app.after(0, lambda: self.show_error("Credenciais do GitHub ausentes."))
                return
            headers = {"Authorization": f"Bearer {token}",
                       "Accept": "application/vnd.github+json"}
            url = (f"https://api.github.com/repos/{username}/{repo_name}"
                   "/issues?state=all&per_page=20")
            try:
                r = requests.get(url, headers=headers)
                if r.status_code == 200:
                    issues = [i for i in r.json() if "pull_request" not in i]
                    self.app.after(0, lambda: self.render_issues(issues))
                else:
                    self.app.after(0, lambda: self.show_error(f"Erro da API: {r.status_code}"))
            except Exception:
                self.app.after(0, lambda: self.show_error("Erro de conexão."))

        threading.Thread(target=task, daemon=True).start()

    def render_issues(self, issues):
        self.issues_data = issues
        for w in self.list_frame.winfo_children():
            w.destroy()
        if not issues:
            ctk.CTkLabel(self.list_frame,
                         text="✨ Nenhuma tarefa aberta neste projeto. Tudo limpo!",
                         font=ctk.CTkFont("Segoe UI", 14),
                         text_color=C["muted"]).pack(pady=60)
            return
        for issue in issues:
            is_open = issue["state"] == "open"
            card = ctk.CTkFrame(self.list_frame, fg_color=C["card"], corner_radius=6,
                                border_width=1, border_color=C["card_border"], height=46)
            card.pack(fill="x", pady=4, padx=5)
            card.pack_propagate(False)

            status_icon = "🟢" if is_open else "🟣"
            ctk.CTkLabel(card, text=status_icon,
                         font=ctk.CTkFont("Segoe UI", 12)).pack(side="left", padx=(15, 10))

            title = issue["title"]
            if len(title) > 45:
                title = title[:42] + "..."
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont("Segoe UI", 13, "bold"),
                         text_color=C["text"]).pack(side="left")

            user = issue.get("user", {}).get("login", "alguém")
            meta_text = f"  #{issue['number']} aberto por {user}"
            ctk.CTkLabel(card, text=meta_text, font=ctk.CTkFont("Segoe UI", 11),
                         text_color=C["text_dim"]).pack(side="left", padx=(0, 10))

            ctk.CTkButton(card, text="Abrir  →", width=80, height=26,
                          font=ctk.CTkFont("Segoe UI", 11, "bold"),
                          fg_color=C["input_bg"], hover_color=C["blue"],
                          text_color=C["text"],
                          command=lambda i=issue: self.open_issue_details(i)).pack(
                side="right", padx=(10, 15))

            for lbl in reversed(issue.get("labels", [])[:2]):
                color_hex = f"#{lbl.get('color', '333333')}"
                ctk.CTkLabel(
                    card, text=f" {lbl.get('name')} ",
                    font=ctk.CTkFont("Segoe UI", 10, "bold"),
                    fg_color=color_hex,
                    text_color="#111111" if int(color_hex[1:], 16) > 0x888888 else "#ffffff",
                    corner_radius=4).pack(side="right", padx=2)

    def show_error(self, msg):
        for w in self.list_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.list_frame, text=msg, text_color=C["red"]).pack(pady=40)

    def open_new_issue(self):
        if not self.current_repo:
            return
        dialog = NewIssueDialog(self, self.current_repo)
        self.wait_window(dialog)
        if dialog.result:
            self.create_issue(dialog.result["title"], dialog.result["body"])

    def open_issue_details(self, issue):
        IssueDetailsDialog(self.app, issue, self)

    def create_issue(self, title, body):
        token    = os.getenv("GITHUB_TOKEN")
        username = os.getenv("GITHUB_USERNAME")

        def task():
            headers = {"Authorization": f"Bearer {token}",
                       "Accept": "application/vnd.github+json"}
            url = f"https://api.github.com/repos/{username}/{self.current_repo}/issues"
            try:
                r = requests.post(url, headers=headers, json={"title": title, "body": body})
                if r.status_code == 201:
                    self.app.after(0, lambda: self.app.log(
                        f"[SYS] Tarefa '{title}' criada com sucesso!", "success"))
                    self.app.after(2000, lambda: self.load_issues_for_repo(self.current_repo))
                else:
                    self.app.after(0, lambda: self.app.log(
                        f"[ERRO] Falha ao criar tarefa ({r.status_code})", "error"))
            except Exception:
                pass

        threading.Thread(target=task, daemon=True).start()
