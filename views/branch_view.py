"""
views/branch_view.py
Gerenciador visual de branches Git.
"""
import os
import customtkinter as ctk
from tkinter import messagebox
from app.config import C


class BranchManagerView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Folder indicator
        self.info_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16,
                                       border_width=1, border_color=C["blue"])
        self.info_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))

        self.lbl_current_repo = ctk.CTkLabel(
            self.info_frame, text="Nenhum diretório selecionado",
            font=ctk.CTkFont("Consolas", 14, "bold"), text_color=C["text"])
        self.lbl_current_repo.pack(side="left", padx=20, pady=15, fill="x", expand=True, anchor="w")

        ctk.CTkButton(self.info_frame, text="Trocar Pasta", width=120, height=36,
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      fg_color=C["blue"], hover_color=C["blue_dark"],
                      command=self.change_folder).pack(side="right", padx=20, pady=15)

        # New branch input
        new_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16,
                                 border_width=1, border_color=C["card_border"])
        new_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=20)

        ctk.CTkLabel(new_frame, text="Nova Branch",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=C["text"]).pack(anchor="w", padx=20, pady=(20, 10))

        input_container = ctk.CTkFrame(new_frame, fg_color="transparent")
        input_container.pack(fill="x", padx=20, pady=(0, 20))

        self.entry_new = ctk.CTkEntry(input_container,
                                      placeholder_text="Nome da nova branch...", height=40)
        self.entry_new.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(input_container, text="Criar Branch", height=40,
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      command=self.create_branch).pack(side="left")

        # Branches list
        list_container = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16,
                                      border_width=1, border_color=C["card_border"])
        list_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))

        ctk.CTkLabel(list_container, text="Branches Disponíveis",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=C["text"]).pack(anchor="w", padx=20, pady=(20, 10))

        self.list_frame = ctk.CTkScrollableFrame(list_container, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ── helpers ───────────────────────────────────────────────────────────────
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
                ctk.CTkLabel(self.list_frame,
                             text="Não é um repositório git válido.").pack(pady=20)
                return

            for b in branches_str.split("\n"):
                if not b.strip():
                    continue
                is_current = b.startswith("*")
                b_name = b.replace("*", "").strip()

                item = ctk.CTkFrame(self.list_frame,
                                    fg_color=C["card_border"] if is_current else "transparent")
                item.pack(fill="x", pady=2)

                ctk.CTkLabel(item, text=b_name,
                             font=ctk.CTkFont("Segoe UI", 14,
                                              "bold" if is_current else "normal"),
                             text_color=C["text"] if is_current else C["text_dim"]).pack(
                    side="left", padx=10, pady=12)

                if not is_current:
                    ctk.CTkButton(item, text="Excluir", width=30, height=30,
                                  fg_color="transparent", hover_color=C["red_dark"],
                                  command=lambda name=b_name: self.delete_branch(name)).pack(
                        side="right", padx=5)
                    ctk.CTkButton(item, text="Mudar para Branch", height=30,
                                  fg_color=C["muted"], hover_color=C["blue"],
                                  command=lambda name=b_name: self.checkout_branch(name)).pack(
                        side="right", padx=15)
                else:
                    ctk.CTkLabel(item, text="(Você está aqui)",
                                 font=ctk.CTkFont("Segoe UI", 12),
                                 text_color=C["blue"]).pack(side="right", padx=15)
        finally:
            os.chdir(original_cwd)
            self.app.update_branch_status()

    def create_branch(self):
        name = self.entry_new.get().strip()
        if not name:
            return
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
            # Auto-save before switching
            self.app.run_command("git add .", check=False)
            status = self.app.run_command("git status --porcelain", check=False)
            if status.strip():
                current_branch = self.app.run_command("git branch --show-current", check=False)
                self.app.run_command(
                    f'git commit -m "Auto-save: Mudança de branch saindo da {current_branch}"',
                    check=False)
            self.app.run_command(f"git checkout {name}", check=False)
            self.load_branches()
        finally:
            os.chdir(original_cwd)

    def delete_branch(self, name):
        if messagebox.askyesno("Confirmar Exclusão",
                               f"Tem certeza que deseja apagar a branch '{name}'?\nIsso não pode ser desfeito."):
            repo = self.get_repo_path()
            original_cwd = os.getcwd()
            try:
                os.chdir(repo)
                self.app.run_command(f"git branch -D {name}", check=False)
                self.load_branches()
            finally:
                os.chdir(original_cwd)
