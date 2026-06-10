"""
dialogs/release_manager.py
Diálogo para publicar releases/versões no GitHub.
"""
import os
import json
import threading
import subprocess
import requests
import customtkinter as ctk
import google.generativeai as genai
from app.config import C, HISTORY_FILE
from app.theme import set_title_bar_color


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

        ctk.CTkLabel(self, text="Lançar Versão",
                     font=ctk.CTkFont("Segoe UI", 20, "bold"),
                     text_color=C["orange"]).pack(pady=(20, 5))
        ctk.CTkLabel(self, text="Crie um 'Patch Note' oficial e publico no GitHub.",
                     font=ctk.CTkFont("Segoe UI", 12),
                     text_color=C["text_dim"]).pack(pady=(0, 20))

        inputs_frame = ctk.CTkFrame(self, fg_color="transparent")
        inputs_frame.pack(fill="x", padx=30)

        ctk.CTkLabel(inputs_frame, text="Tag da Versão (ex: v1.0.0):",
                     font=ctk.CTkFont("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        self.entry_tag = ctk.CTkEntry(inputs_frame, width=150,
                                      font=ctk.CTkFont("Consolas", 12),
                                      fg_color=C["input_bg"], border_color=C["card_border"])
        self.entry_tag.grid(row=1, column=0, sticky="w", pady=(5, 15), padx=(0, 20))
        self.entry_tag.insert(0, "v1.0.0")

        ctk.CTkLabel(inputs_frame, text="Título do Lançamento:",
                     font=ctk.CTkFont("Segoe UI", 12, "bold")).grid(row=0, column=1, sticky="w")
        self.entry_title = ctk.CTkEntry(inputs_frame, width=400,
                                        font=ctk.CTkFont("Segoe UI", 12),
                                        fg_color=C["input_bg"], border_color=C["card_border"])
        self.entry_title.grid(row=1, column=1, sticky="ew", pady=(5, 15))
        self.entry_title.insert(0, "Lançamento Oficial")

        self.btn_gen = ctk.CTkButton(self, text="Gerar Notas com IA", height=36,
                                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                     fg_color=C["blue"], hover_color=C["blue_dark"],
                                     command=self._generate_notes)
        self.btn_gen.pack(fill="x", padx=30, pady=(0, 5))

        self.progress_ai = ctk.CTkProgressBar(self, mode="indeterminate",
                                              fg_color=C["input_bg"],
                                              progress_color=C["orange"], height=4)
        self.progress_ai.set(0)
        ctk.CTkFrame(self, height=10, fg_color="transparent").pack()

        ctk.CTkLabel(self, text="Notas da Versão (Markdown):",
                     font=ctk.CTkFont("Segoe UI", 12, "bold")).pack(anchor="w", padx=30)
        self.tb_notes = ctk.CTkTextbox(self, font=ctk.CTkFont("Consolas", 12),
                                       fg_color=C["input_bg"], text_color=C["text"],
                                       border_width=1, border_color=C["card_border"])
        self.tb_notes.pack(fill="both", expand=True, padx=30, pady=(5, 20))

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=(0, 20))

        ctk.CTkButton(btns, text="Cancelar", width=120, height=36,
                      fg_color=C["card_border"], hover_color=C["muted"],
                      text_color=C["text"], command=self.destroy).pack(side="left", padx=10)
        ctk.CTkButton(btns, text="Publicar no GitHub", width=180, height=36,
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      fg_color=C["orange"], hover_color="#d68910",
                      text_color="#ffffff", command=self._publish).pack(side="left", padx=10)

    def _generate_notes(self):
        self.btn_gen.configure(text="Gerando...", state="disabled")
        self.progress_ai.pack(fill="x", padx=30, pady=(0, 10))
        self.progress_ai.start()
        self.update()

        def task():
            try:
                prev_tag = subprocess.run(
                    "git describe --tags --abbrev=0", shell=True, capture_output=True,
                    text=True, cwd=self.repo_path).stdout.strip()
                cmd = f"git log {prev_tag}..HEAD --oneline" if prev_tag else "git log --oneline"
                commits = subprocess.run(cmd, shell=True, capture_output=True,
                                         text=True, cwd=self.repo_path).stdout.strip()
                if not commits:
                    self.parent_app.after(
                        0, lambda: self._set_notes("Nenhum commit novo encontrado desde o último lançamento."))
                    return
                prompt = (
                    "Gere o 'Release Note' técnico em Markdown baseado nestes commits.\n"
                    "Proibido: usar introduções corporativas, saudações, conclusões, gírias ou emojis.\n"
                    "Estrutura EXIGIDA:\n"
                    "1. A PRIMEIRA LINHA deve ser um Título curto e profissional.\n"
                    "2. A SEGUNDA LINHA em diante deve ser um parágrafo direto.\n"
                    "3. O resto deve ser 'Resumo de Alterações' em bullet points.\n\n"
                    f"Commits:\n{commits}"
                )
                model_gen = genai.GenerativeModel("gemini-3.5-flash")
                resp = model_gen.generate_content(prompt)
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

        def task():
            try:
                self.parent_app.log(f"[SYS] Criando tag local {tag}...", "info")
                subprocess.run(f'git tag -a {tag} -m "{title}"', shell=True, check=True,
                               cwd=self.repo_path)
                self.parent_app.log(f"[SYS] Enviando tag {tag} para o repositório remoto...", "info")
                subprocess.run(f'git push origin {tag}', shell=True, check=True, cwd=self.repo_path)

                remote_url = subprocess.run(
                    "git config --get remote.origin.url", shell=True, capture_output=True,
                    text=True, cwd=self.repo_path).stdout.strip()
                if not remote_url:
                    self.parent_app.log("[ERRO] Repositório remoto não encontrado.", "error")
                    return
                if "github.com" not in remote_url:
                    self.parent_app.log("[SYS] O remote não é GitHub. Release local criado.", "warn")
                    return

                parts = remote_url.replace(".git", "").split("/")
                if remote_url.startswith("git@"):
                    parts = remote_url.split(":")[-1].replace(".git", "").split("/")
                owner, repo = parts[-2], parts[-1]

                token = os.environ.get("GITHUB_TOKEN", "")
                if not token:
                    try:
                        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                            token = json.load(f).get("github_token", "")
                    except Exception:
                        pass

                if not token:
                    self.parent_app.log("[ERRO] Token não encontrado. Tag enviada sem Release.", "error")
                    return

                self.parent_app.log("[SYS] Publicando release na aba Releases do GitHub...", "info")
                headers = {"Authorization": f"token {token}",
                           "Accept": "application/vnd.github.v3+json"}
                payload = {"tag_name": tag, "name": title, "body": body,
                           "draft": False, "prerelease": False}
                response = requests.post(
                    f"https://api.github.com/repos/{owner}/{repo}/releases",
                    json=payload, headers=headers)
                if response.status_code == 201:
                    url = response.json().get("html_url")
                    self.parent_app.log(f"🏆 Lançamento {tag} publicado! Link: {url}", "success")
                else:
                    self.parent_app.log(
                        f"[ERRO] Falha na API do GitHub: {response.status_code} - {response.text}", "error")
            except Exception as e:
                self.parent_app.log(f"[ERRO] Falha ao publicar: {str(e)}", "error")
            finally:
                self.parent_app.after(0, self.destroy)

        threading.Thread(target=task, daemon=True).start()
