"""
dialogs/diff_viewer.py
Visualizador de diferenças Git lado a lado.
"""
import customtkinter as ctk
from app.config import C
from app.theme import set_title_bar_color


class DiffViewerDialog(ctk.CTkToplevel):
    def __init__(self, parent, diff_text):
        super().__init__(parent)
        self.title("Diff Lado a Lado")
        self.geometry("1200x700")
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=C["bg"])
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(header_frame, text="Visualizador de Diferenças",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=C["text"]).pack(side="left")

        self.parse_diff_text(diff_text)
        files = list(self.diffs_by_file.keys())

        if files:
            self.file_selector = ctk.CTkOptionMenu(
                header_frame, values=files, command=self._on_file_select,
                width=350, font=ctk.CTkFont("Segoe UI", 12),
                fg_color=C["card"], button_color=C["card_border"])
            self.file_selector.pack(side="right")
        else:
            self.file_selector = ctk.CTkOptionMenu(
                header_frame, values=["Nenhum arquivo alterado"], width=350, state="disabled")
            self.file_selector.pack(side="right")

        titles = ctk.CTkFrame(self, fg_color="transparent")
        titles.pack(fill="x", padx=20, pady=(10, 0))
        titles.grid_columnconfigure(0, weight=1)
        titles.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(titles, text="Original", font=ctk.CTkFont("Segoe UI", 12),
                     text_color=C["text_dim"]).grid(row=0, column=0, sticky="w", padx=10)
        ctk.CTkLabel(titles, text="Modificado", font=ctk.CTkFont("Segoe UI", 12),
                     text_color=C["text_dim"]).grid(row=0, column=1, sticky="w", padx=10)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=(5, 10))
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(2, weight=1)
        container.grid_rowconfigure(0, weight=1)

        font_code = ctk.CTkFont("Consolas", 13)

        self.tb_left = ctk.CTkTextbox(container, font=font_code, fg_color=C["console_bg"],
                                       text_color=C["text"], border_width=0, wrap="none")
        self.tb_left.grid(row=0, column=0, sticky="nsew", padx=(0, 2))

        divisor = ctk.CTkFrame(container, width=1, fg_color=C["card_border"])
        divisor.grid(row=0, column=1, sticky="ns")

        self.tb_right = ctk.CTkTextbox(container, font=font_code, fg_color=C["console_bg"],
                                        text_color=C["text"], border_width=0, wrap="none")
        self.tb_right.grid(row=0, column=2, sticky="nsew", padx=(2, 0))

        for tb in [self.tb_left, self.tb_right]:
            tb.tag_config("deletion", background="#511d1d", foreground="#f48771")
            tb.tag_config("addition", background="#1d3b26", foreground="#61cc86")
            tb.tag_config("header", foreground="#569cd6")
            tb.tag_config("info", foreground="#858585")
            tb.tag_config("blank", foreground=C["console_bg"], background=C["console_bg"])
            tb.bind("<MouseWheel>", self.sync_scroll)

        if files:
            self._on_file_select(files[0])
        else:
            self.insert_diff_side_by_side("")
            self.tb_left.configure(state="disabled")
            self.tb_right.configure(state="disabled")

        ctk.CTkButton(self, text="Fechar Lente", width=120, height=36,
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      fg_color=C["card_border"], hover_color=C["muted"],
                      text_color=C["text"], command=self.destroy).pack(pady=(10, 20))

    def sync_scroll(self, event):
        delta = int(-1 * (event.delta / 120))
        self.tb_left._textbox.yview_scroll(delta, "units")
        self.tb_right._textbox.yview_scroll(delta, "units")
        return "break"

    def parse_diff_text(self, text):
        self.diffs_by_file = {}
        if not text.strip():
            return
        current_file = None
        current_lines = []
        for line in text.split('\n'):
            if line.startswith('diff --git '):
                if current_file:
                    self.diffs_by_file[current_file] = '\n'.join(current_lines)
                parts = line.split(' ')
                if len(parts) >= 4:
                    current_file = parts[-1][2:] if parts[-1].startswith('b/') else parts[-1]
                else:
                    current_file = "Desconhecido"
                current_lines = [line]
            else:
                if current_file:
                    current_lines.append(line)
        if current_file:
            self.diffs_by_file[current_file] = '\n'.join(current_lines)

    def _on_file_select(self, filename):
        self.tb_left.configure(state="normal")
        self.tb_right.configure(state="normal")
        self.tb_left.delete("1.0", "end")
        self.tb_right.delete("1.0", "end")
        diff_text = self.diffs_by_file.get(filename, "")
        self.insert_diff_side_by_side(diff_text)
        self.tb_left.configure(state="disabled")
        self.tb_right.configure(state="disabled")

    def insert_diff_side_by_side(self, diff_text):
        if not diff_text.strip():
            self.tb_left.insert("end", " Nenhuma diferença encontrada.", "info")
            self.tb_right.insert("end", " Nenhuma diferença encontrada.", "info")
            return

        del_buf = []
        add_buf = []

        def flush_buffers():
            n = max(len(del_buf), len(add_buf))
            for i in range(n):
                dl = del_buf[i] if i < len(del_buf) else ""
                al = add_buf[i] if i < len(add_buf) else ""
                if dl:
                    self.tb_left.insert("end", dl + "\n", "deletion")
                else:
                    self.tb_left.insert("end", "\n", "blank")
                if al:
                    self.tb_right.insert("end", al + "\n", "addition")
                else:
                    self.tb_right.insert("end", "\n", "blank")
            del_buf.clear()
            add_buf.clear()

        for line in diff_text.split('\n'):
            if line.startswith('diff --git') or line.startswith('+++') or line.startswith('---'):
                flush_buffers()
                self.tb_left.insert("end", "\n" + line + "\n", "header")
                self.tb_right.insert("end", "\n" + line + "\n", "header")
            elif line.startswith('@@'):
                flush_buffers()
                self.tb_left.insert("end", "\n" + line + "\n", "info")
                self.tb_right.insert("end", "\n" + line + "\n", "info")
            elif line.startswith('-'):
                del_buf.append(line)
            elif line.startswith('+'):
                add_buf.append(line)
            else:
                flush_buffers()
                self.tb_left.insert("end", line + "\n")
                self.tb_right.insert("end", line + "\n")
        flush_buffers()
