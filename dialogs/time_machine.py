"""
dialogs/time_machine.py
Diálogo de confirmação para reverter o repositório ao último commit.
"""
import customtkinter as ctk
from app.config import C
from app.theme import set_title_bar_color


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

        ctk.CTkLabel(self, text="MÁQUINA DO TEMPO",
                     font=ctk.CTkFont("Segoe UI", 20, "bold"),
                     text_color=C["red"]).pack(pady=(25, 5))

        msg_frame = ctk.CTkFrame(self, fg_color="transparent")
        msg_frame.pack(fill="x", padx=30, pady=10)

        warn_txt = ("Isso vai APAGAR todas as alterações não salvas e arquivos recém-criados.\n\n"
                    "O projeto retornará EXATAMENTE ao estado do seguinte commit:")
        ctk.CTkLabel(msg_frame, text=warn_txt, font=ctk.CTkFont("Segoe UI", 13),
                     text_color=C["text"], justify="center", wraplength=380).pack()

        pill = ctk.CTkFrame(self, fg_color=C["input_bg"], corner_radius=8,
                            border_width=1, border_color=C["card_border"])
        pill.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(pill, text=f"📌 {commit_info}",
                     font=ctk.CTkFont("Consolas", 11),
                     text_color=C["blue"], wraplength=360).pack(padx=15, pady=15)

        ctk.CTkLabel(self, text="Essa ação NÃO pode ser desfeita.",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=C["red"]).pack(pady=(0, 10))

        val_frame = ctk.CTkFrame(self, fg_color="transparent")
        val_frame.pack(fill="x", padx=30, pady=(5, 10))
        ctk.CTkLabel(val_frame, text=f"Digite o nome da pasta para confirmar:\n( {repo_name} )",
                     font=ctk.CTkFont("Segoe UI", 12),
                     text_color=C["text_dim"]).pack(pady=(0, 5))

        self.entry_var = ctk.StringVar()
        self.entry_var.trace_add("write", self._check_validation)
        self.entry_val = ctk.CTkEntry(val_frame, textvariable=self.entry_var,
                                      font=ctk.CTkFont("Consolas", 12),
                                      fg_color=C["input_bg"],
                                      border_color=C["card_border"],
                                      justify="center")
        self.entry_val.pack(fill="x", padx=20)

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=(10, 20))

        ctk.CTkButton(btns, text="Cancelar", width=120, height=36,
                      font=ctk.CTkFont("Segoe UI", 12),
                      fg_color=C["card_border"], hover_color=C["muted"],
                      text_color=C["text"], command=self.destroy).pack(side="left", padx=10)
        self.btn_confirm = ctk.CTkButton(btns, text="💥 SIM, DESCARTAR TUDO",
                                         width=200, height=36,
                                         font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                         fg_color=C["red_dark"], hover_color=C["red"],
                                         state="disabled", command=self._confirm)
        self.btn_confirm.pack(side="left", padx=10)

    def _check_validation(self, *args):
        if self.entry_var.get().strip() == self.repo_name:
            self.btn_confirm.configure(state="normal")
        else:
            self.btn_confirm.configure(state="disabled")

    def _confirm(self):
        self.result = True
        self.destroy()
