"""
widgets/tooltip.py
Tooltip flutuante para uso no gráfico de contribuições.
"""
import customtkinter as ctk
from app.config import C


class HoverTooltip:
    def __init__(self, parent):
        self.tw = ctk.CTkToplevel(parent)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_attributes("-topmost", True)
        self.tw.withdraw()

        self.frame = ctk.CTkFrame(self.tw, fg_color=C["card_border"], corner_radius=6)
        self.frame.pack()
        self.lbl = ctk.CTkLabel(self.frame, text="", font=ctk.CTkFont("Segoe UI", 11),
                                text_color=C["text"])
        self.lbl.pack(padx=8, pady=4)

        self.is_visible = False

    def show(self, text, x, y):
        self.lbl.configure(text=text)
        self.tw.geometry(f"+{x + 15}+{y + 15}")
        if not self.is_visible:
            self.tw.deiconify()
            self.is_visible = True

    def hide(self):
        if self.is_visible:
            self.tw.withdraw()
            self.is_visible = False
