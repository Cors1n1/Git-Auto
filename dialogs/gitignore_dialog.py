"""
dialogs/gitignore_dialog.py
Gerador de .gitignore por tecnologia.
"""
import customtkinter as ctk
from app.config import C


class GitignoreDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Gerador de .gitignore")
        self.geometry("400x450")
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=C["bg"])

        ctk.CTkLabel(self, text="Gerar .gitignore",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=C["text"]).pack(pady=(20, 5))
        ctk.CTkLabel(self, text="Selecione as tecnologias do seu projeto:",
                     font=ctk.CTkFont("Segoe UI", 12),
                     text_color=C["text_dim"]).pack(pady=(0, 10))

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=C["input_bg"],
                                             border_width=1, border_color=C["card_border"])
        self.scroll.pack(fill="both", expand=True, padx=30, pady=10)

        templates = ["Python", "Node.js", "React/Next.js", "Java", "C++", "Godot", "Unity", "Generico"]
        self.checkboxes = {}

        for t in templates:
            var = ctk.IntVar(value=1 if t == "Python" else 0)
            cb = ctk.CTkCheckBox(self.scroll, text=t, variable=var,
                                 font=ctk.CTkFont("Segoe UI", 13),
                                 text_color=C["text"],
                                 fg_color=C["blue"],
                                 hover_color=C["blue_dark"])
            cb.pack(anchor="w", padx=10, pady=8)
            self.checkboxes[t] = var

        self.result = None

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=20)

        ctk.CTkButton(btns, text="Cancelar", width=100,
                      fg_color=C["card_border"], hover_color=C["red_dark"],
                      command=self.destroy).pack(side="left", padx=10)
        ctk.CTkButton(btns, text="Gerar Arquivo", width=120,
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      fg_color=C["blue"], hover_color=C["blue_dark"],
                      command=self._confirm).pack(side="left", padx=10)

    def _confirm(self):
        self.result = [t for t, var in self.checkboxes.items() if var.get() == 1]
        self.destroy()
