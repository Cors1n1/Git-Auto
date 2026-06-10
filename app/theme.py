"""
app/theme.py
Funções de tema: paleta de cores e customização da barra de título do Windows.
"""
import os
import ctypes
import customtkinter as ctk
from app.config import C


def set_title_bar_color(window, bg_hex, text_hex=None):
    if os.name != 'nt':
        return
    try:
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        bg_hex = bg_hex.lstrip('#')
        r, g, b = int(bg_hex[0:2], 16), int(bg_hex[2:4], 16), int(bg_hex[4:6], 16)
        bg_colorref = (b << 16) | (g << 8) | r
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 35, ctypes.byref(ctypes.c_int(bg_colorref)), ctypes.sizeof(ctypes.c_int))
        if text_hex:
            text_hex = text_hex.lstrip('#')
            tr, tg, tb = int(text_hex[0:2], 16), int(text_hex[2:4], 16), int(text_hex[4:6], 16)
            text_colorref = (tb << 16) | (tg << 8) | tr
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 36, ctypes.byref(ctypes.c_int(text_colorref)), ctypes.sizeof(ctypes.c_int))
    except Exception:
        pass


def update_palette(app_theme, app_color):
    if app_theme == "GitHub Light":
        ctk.set_appearance_mode("light")
    else:
        ctk.set_appearance_mode("dark")

    if app_theme == "GitHub Light":
        C.update({
            "bg": "#ffffff", "sidebar": "#f6f8fa", "card": "#ffffff",
            "card_border": "#d0d7de", "input_bg": "#f6f8fa",
            "green": "#2da44e", "green_dark": "#1a7f37",
            "blue": "#0969da", "blue_dark": "#0550ae",
            "orange": "#bf8700", "red": "#cf222e", "red_dark": "#a40e26",
            "muted": "#57606a", "text": "#24292f", "text_dim": "#57606a",
            "success_bg": "#dafbe1", "warn_bg": "#fff8c5",
            "console_bg": "#f6f8fa", "console_fg": "#24292f",
        })
    elif app_theme == "VSCode Modern":
        C.update({
            "bg": "#181818", "sidebar": "#1f1f1f", "card": "#1f1f1f",
            "card_border": "#333333", "input_bg": "#2b2b2b",
            "green": "#4eb071", "green_dark": "#3c8656",
            "blue": "#007acc", "blue_dark": "#005a9e",
            "orange": "#d18616", "red": "#f14c4c", "red_dark": "#d13b3b",
            "muted": "#858585", "text": "#cccccc", "text_dim": "#a0a0a0",
            "success_bg": "#1e2e23", "warn_bg": "#3b2e1b",
            "console_bg": "#1e1e1e", "console_fg": "#d4d4d4",
        })
    elif app_theme == "Vercel Black":
        C.update({
            "bg": "#000000", "sidebar": "#000000", "card": "#0a0a0a",
            "card_border": "#333333", "input_bg": "#000000",
            "green": "#0070f3", "green_dark": "#0051a2",
            "blue": "#ededed", "blue_dark": "#a1a1a1",
            "orange": "#f5a623", "red": "#e00000", "red_dark": "#cc0000",
            "muted": "#666666", "text": "#ededed", "text_dim": "#a1a1a1",
            "success_bg": "#001a00", "warn_bg": "#1a1000",
            "console_bg": "#000000", "console_fg": "#ededed",
        })
    elif app_theme == "Dracula PRO":
        C.update({
            "bg": "#22212C", "sidebar": "#1E1E28", "card": "#2D2B3B",
            "card_border": "#454158", "input_bg": "#1E1E28",
            "green": "#80FFEA", "green_dark": "#5CCCBA",
            "blue": "#8AFF80", "blue_dark": "#6BCC63",
            "orange": "#FFCA80", "red": "#FF9580", "red_dark": "#CC7766",
            "muted": "#7970A9", "text": "#F8F8F2", "text_dim": "#B8B4D1",
            "success_bg": "#2A3D39", "warn_bg": "#3D3126",
            "console_bg": "#22212C", "console_fg": "#80FFEA",
        })
    elif app_theme == "Catppuccin Mocha":
        C.update({
            "bg": "#1e1e2e", "sidebar": "#181825", "card": "#313244",
            "card_border": "#45475a", "input_bg": "#11111b",
            "green": "#a6e3a1", "green_dark": "#94e2d5",
            "blue": "#89b4fa", "blue_dark": "#89dceb",
            "orange": "#fab387", "red": "#f38ba8", "red_dark": "#eba0ac",
            "muted": "#585b70", "text": "#cdd6f4", "text_dim": "#bac2de",
            "success_bg": "#1f292e", "warn_bg": "#2e222a",
            "console_bg": "#1e1e2e", "console_fg": "#f5c2e7",
        })
    elif app_theme == "One Dark Pro":
        C.update({
            "bg": "#282c34", "sidebar": "#21252b", "card": "#2c313a",
            "card_border": "#3e4451", "input_bg": "#1e2227",
            "green": "#98c379", "green_dark": "#7a9c61",
            "blue": "#61afef", "blue_dark": "#4e8cbf",
            "orange": "#d19a66", "red": "#e06c75", "red_dark": "#b3565e",
            "muted": "#5c6370", "text": "#abb2bf", "text_dim": "#828997",
            "success_bg": "#2a3328", "warn_bg": "#332b21",
            "console_bg": "#282c34", "console_fg": "#98c379",
        })
    elif app_theme == "Monokai Pro":
        C.update({
            "bg": "#2d2a2e", "sidebar": "#221f22", "card": "#3a363b",
            "card_border": "#5b595c", "input_bg": "#19181a",
            "green": "#a9dc76", "green_dark": "#87b05e",
            "blue": "#78dce8", "blue_dark": "#60b0ba",
            "orange": "#fc9867", "red": "#ff6188", "red_dark": "#cc4d6c",
            "muted": "#727072", "text": "#fcfcfa", "text_dim": "#c1c0c0",
            "success_bg": "#364528", "warn_bg": "#452b1f",
            "console_bg": "#2d2a2e", "console_fg": "#a9dc76",
        })
    else:  # GitHub Dark (Default)
        C.update({
            "bg": "#0d1117", "sidebar": "#010409", "card": "#161b22",
            "card_border": "#30363d", "input_bg": "#0d1117",
            "green": "#238636", "green_dark": "#2ea043",
            "blue": "#58a6ff", "blue_dark": "#3182ce",
            "orange": "#d29922", "red": "#f85149", "red_dark": "#da3633",
            "muted": "#8b949e", "text": "#c9d1d9", "text_dim": "#b1bac4",
            "success_bg": "#12241b", "warn_bg": "#292000",
            "console_bg": "#0d1117", "console_fg": "#58a6ff",
        })

    # Cor de destaque manual (só funciona nos temas flexíveis)
    if app_theme in ["GitHub Dark", "GitHub Light", "VSCode Modern", "Vercel Black"]:
        if app_color == "Verde":
            C["blue"], C["blue_dark"] = C["green"], C["green_dark"]
        elif app_color == "Laranja":
            C["blue"], C["blue_dark"] = C["orange"], "#d68910"
        elif app_color == "Vermelho":
            C["blue"], C["blue_dark"] = C["red"], C["red_dark"]
        elif app_color == "Roxo":
            C["blue"], C["blue_dark"] = "#8b5cf6", "#7c3aed"
