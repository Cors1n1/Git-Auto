"""
dialogs/history_dialog.py
Exibe o histórico completo de commits de um repositório local.
"""
import os
import subprocess
import customtkinter as ctk
from app.config import C
from app.theme import set_title_bar_color


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

        hdr = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=f"⏳  Histórico de Commits — {folder_name}",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=C["text"]).pack(side="left", padx=20, pady=14)

        info = ctk.CTkFrame(self, fg_color=C["input_bg"], corner_radius=0, height=30)
        info.pack(fill="x")
        info.pack_propagate(False)
        ctk.CTkLabel(info, text=path,
                     font=ctk.CTkFont("Consolas", 10),
                     text_color=C["muted"]).pack(side="left", padx=14, pady=6)

        col_hdr = ctk.CTkFrame(self, fg_color=C["card_border"], corner_radius=0, height=28)
        col_hdr.pack(fill="x")
        col_hdr.pack_propagate(False)
        for txt, w in [("Hash", 70), ("Data", 140), ("Autor", 140), ("Mensagem", 0)]:
            ctk.CTkLabel(col_hdr, text=txt,
                         font=ctk.CTkFont("Segoe UI", 10, "bold"),
                         text_color=C["text_dim"],
                         width=w if w else 1).pack(side="left", padx=(10, 0), pady=5)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                        scrollbar_button_color=C["muted"])
        scroll.pack(fill="both", expand=True, padx=0, pady=0)

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
            ctk.CTkLabel(container, text=f"Erro ao ler o log: {e}",
                         text_color=C["red"]).pack(pady=20)
            return

        if not lines:
            ctk.CTkLabel(container, text="Nenhum commit encontrado neste repositório.",
                         font=ctk.CTkFont("Segoe UI", 12),
                         text_color=C["muted"]).pack(pady=40)
            self.count_label.configure(text="0 commits")
            return

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

            ctk.CTkLabel(row, text=date, width=140,
                         font=ctk.CTkFont("Consolas", 11),
                         text_color=C["text_dim"]).pack(side="left", padx=(10, 0))
            ctk.CTkLabel(row, text=author[:18], width=130,
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=C["text_dim"]).pack(side="left", padx=(10, 0))
            ctk.CTkLabel(row, text=msg[:80] + ("…" if len(msg) > 80 else ""),
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=C["text"],
                         anchor="w").pack(side="left", padx=(10, 6), fill="x", expand=True)

        pushed_count = sum(1 for l in lines if l.split("|")[0] in pushed_hashes)
        self.count_label.configure(
            text=f"{len(lines)} commits  │  {pushed_count} enviados ao remote")
