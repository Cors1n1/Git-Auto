"""
dialogs/new_project.py
Diálogo para criação de um novo repositório GitHub.
"""
import re
import unicodedata
import customtkinter as ctk
from app.config import C
from app.theme import set_title_bar_color


class NewProjectDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        self.title("Novo Repositório")
        self.geometry("480x380")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()
        self.configure(fg_color=C["bg"])
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))

        hdr = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Criar Novo Repositório",
                     font=ctk.CTkFont("Segoe UI", 18, "bold"),
                     text_color=C["text"]).pack(side="left", padx=20, pady=15)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=20)

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

        opts = ctk.CTkFrame(body, fg_color="transparent")
        opts.pack(fill="x", pady=(0, 20))
        self.sw_private = ctk.CTkSwitch(opts, text="  Repositório Privado",
                                        font=ctk.CTkFont("Segoe UI", 12),
                                        progress_color=C["blue"],
                                        button_color=C["text"],
                                        text_color=C["text_dim"])
        self.sw_private.pack(side="left")

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
        name = unicodedata.normalize('NFKD', raw_name).encode('ASCII', 'ignore').decode('ASCII')
        name = re.sub(r'[^a-zA-Z0-9_\-\.]', '-', name)
        name = re.sub(r'-+', '-', name).strip('-').lower()
        self.result = {
            "name": name,
            "description": self.entry_desc.get().strip(),
            "private": self.sw_private.get() == 1,
        }
        self.destroy()
