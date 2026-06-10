"""
dialogs/settings.py
Diálogos de ajuda e configurações de credenciais + tema.
"""
import os
import customtkinter as ctk
import google.generativeai as genai

import app.config as cfg
from app.config import C
from app.theme import set_title_bar_color, update_palette


class HelpDialog(ctk.CTkToplevel):
    def __init__(self, master, topic):
        super().__init__(master)
        self.title("Ajuda de Configuração")
        self.geometry("450x380")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color=C["bg"])
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        if topic == "github_token":
            title = "Como obter o GitHub Token?"
            text = (
                "1. Acesse o GitHub no navegador e faça login.\n"
                "2. Vá em Settings > Developer settings > Personal access tokens > Tokens (classic).\n"
                "3. Clique em 'Generate new token (classic)'.\n"
                "4. Dê um nome (ex: Git Auto) e defina a validade (Expiration).\n"
                "5. Marque a caixa 'repo' (Controle de código e tarefas).\n"
                "6. Marque a caixa 'admin:org' (Obrigatório para gerenciar permissões de colaboradores).\n"
                "7. Marque a caixa 'user' (Necessário para carregar seu avatar e perfil).\n"
                "8. Clique em 'Generate token' no fim da página.\n"
                "9. Copie o token gerado (começa com ghp_...) e cole aqui."
            )
        elif topic == "gemini_key":
            title = "Como obter a Gemini API Key?"
            text = (
                "1. Acesse https://aistudio.google.com/ e faça login com sua conta Google.\n"
                "2. No menu superior, clique em 'Get API key'.\n"
                "3. Clique no botão azul 'Create API key'.\n"
                "4. Copie a chave gerada e cole aqui.\n\n"
                "A chave é gratuita e permite que a Inteligência Artificial gere os nomes dos commits automaticamente para você."
            )
        else:
            title = "Ajuda"
            text = ""

        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(0, 15))

        textbox = ctk.CTkTextbox(frame, font=ctk.CTkFont("Segoe UI", 12),
                                  fg_color=C["input_bg"], text_color=C["text"], wrap="word")
        textbox.pack(fill="both", expand=True)
        textbox.insert("0.0", text)
        textbox.configure(state="disabled")

        ctk.CTkButton(frame, text="Entendi", height=32,
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      fg_color=C["blue"], hover_color=C["blue_dark"],
                      command=self.destroy).pack(fill="x", pady=(15, 0))


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Configurações do Git Auto")
        self.geometry("450x620")
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color=C["bg"])
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Credenciais (Salvas localmente no .env)",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(0, 15))

        def create_field_header(parent, label_text, help_topic=None):
            h_frame = ctk.CTkFrame(parent, fg_color="transparent")
            h_frame.pack(fill="x", pady=(0, 4))
            ctk.CTkLabel(h_frame, text=label_text,
                         font=ctk.CTkFont("Segoe UI", 12, "bold"),
                         text_color=C["text_dim"]).pack(side="left")
            if help_topic:
                ctk.CTkButton(h_frame, text="?", width=20, height=20, corner_radius=10,
                              fg_color=C["card_border"], hover_color=C["blue"],
                              text_color=C["text"],
                              command=lambda t=help_topic: HelpDialog(self, t)).pack(side="left", padx=10)

        create_field_header(frame, "GitHub Username")
        self.entry_user = ctk.CTkEntry(frame, height=36, font=ctk.CTkFont("Consolas", 11),
                                       fg_color=C["input_bg"], border_color=C["card_border"],
                                       text_color=C["text"])
        self.entry_user.pack(fill="x", pady=(0, 15))
        self.entry_user.insert(0, cfg.GITHUB_USERNAME)

        create_field_header(frame, "GitHub Token", "github_token")
        self.entry_github = ctk.CTkEntry(frame, height=36, font=ctk.CTkFont("Consolas", 11),
                                         fg_color=C["input_bg"], border_color=C["card_border"],
                                         text_color=C["text"], show="*")
        self.entry_github.pack(fill="x", pady=(0, 15))
        self.entry_github.insert(0, cfg.GITHUB_TOKEN)

        create_field_header(frame, "Gemini API Key", "gemini_key")
        self.entry_gemini = ctk.CTkEntry(frame, height=36, font=ctk.CTkFont("Consolas", 11),
                                         fg_color=C["input_bg"], border_color=C["card_border"],
                                         text_color=C["text"], show="*")
        self.entry_gemini.pack(fill="x", pady=(0, 20))
        self.entry_gemini.insert(0, cfg.GEMINI_API_KEY)

        ctk.CTkFrame(frame, height=1, fg_color=C["card_border"]).pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(frame, text="Aparência Visual",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(0, 10))

        theme_frame = ctk.CTkFrame(frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(theme_frame, text="Tema:", font=ctk.CTkFont("Segoe UI", 12),
                     text_color=C["text_dim"]).pack(side="left", padx=(0, 10))
        self.opt_theme = ctk.CTkOptionMenu(
            theme_frame,
            values=["GitHub Dark", "GitHub Light", "VSCode Modern", "Vercel Black",
                    "Dracula PRO", "Catppuccin Mocha", "One Dark Pro", "Monokai Pro"],
            fg_color=C["input_bg"], button_color=C["card_border"], text_color=C["text"])
        self.opt_theme.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.opt_theme.set(cfg.APP_THEME)

        ctk.CTkLabel(theme_frame, text="Destaque:", font=ctk.CTkFont("Segoe UI", 12),
                     text_color=C["text_dim"]).pack(side="left", padx=(0, 10))
        self.opt_color = ctk.CTkOptionMenu(
            theme_frame, values=["Azul", "Verde", "Laranja", "Roxo", "Vermelho"],
            fg_color=C["input_bg"], button_color=C["card_border"], text_color=C["text"])
        self.opt_color.pack(side="left", fill="x", expand=True)
        self.opt_color.set(cfg.APP_COLOR)

        ctk.CTkFrame(frame, height=1, fg_color=C["card_border"]).pack(fill="x", pady=(5, 15))

        ctk.CTkLabel(frame, text="Sistema",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=C["text"]).pack(anchor="w", pady=(0, 10))
        
        self.sw_verbose = ctk.CTkSwitch(frame, text="Logs Detalhados (Mostrar comandos no painel)",
                                        font=ctk.CTkFont("Segoe UI", 12),
                                        progress_color=C["blue"], button_color=C["text"],
                                        text_color=C["text_dim"])
        self.sw_verbose.pack(anchor="w", pady=(0, 20))
        if cfg.VERBOSE_LOGGING:
            self.sw_verbose.select()

        ctk.CTkButton(frame, text="Salvar Configurações  ✓", height=36,
                      font=ctk.CTkFont("Segoe UI", 12, "bold"),
                      fg_color=C["blue"], hover_color=C["blue_dark"],
                      command=self.save).pack(fill="x")

    def save(self):
        gh_user    = self.entry_user.get().strip()
        gh_tok     = self.entry_github.get().strip()
        gem_key    = self.entry_gemini.get().strip()
        app_theme  = self.opt_theme.get()
        app_color  = self.opt_color.get()
        is_verbose = self.sw_verbose.get() == 1

        env_path = os.path.join(cfg.PROJECT_ROOT, ".env")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(f'APP_THEME="{app_theme}"\n')
            f.write(f'APP_COLOR="{app_color}"\n')
            f.write(f'GITHUB_TOKEN="{gh_tok}"\n')
            f.write(f'GITHUB_USERNAME="{gh_user}"\n')
            f.write(f'GEMINI_API_KEY="{gem_key}"\n')
            f.write(f'VERBOSE_LOGGING="{is_verbose}"\n')

        # Update os.environ so subprocesses inherit new values
        os.environ["GITHUB_TOKEN"]    = gh_tok
        os.environ["GITHUB_USERNAME"] = gh_user
        os.environ["GEMINI_API_KEY"]  = gem_key
        os.environ["APP_THEME"]       = app_theme
        os.environ["APP_COLOR"]       = app_color
        os.environ["VERBOSE_LOGGING"] = str(is_verbose)

        # Update the shared config module globals
        cfg.GITHUB_TOKEN    = gh_tok
        cfg.GITHUB_USERNAME = gh_user
        cfg.GEMINI_API_KEY  = gem_key
        cfg.VERBOSE_LOGGING = is_verbose

        if gem_key:
            genai.configure(api_key=gem_key)
            cfg.model = genai.GenerativeModel('gemini-3.1-flash-lite')

        if hasattr(self.master, "log"):
            self.master.log("[SYS] Configurações salvas e aplicadas.", "success")

        old_theme = cfg.APP_THEME
        old_color = cfg.APP_COLOR
        app_ref   = self.master
        self.destroy()

        if app_theme != old_theme or app_color != old_color:
            cfg.APP_THEME = app_theme
            cfg.APP_COLOR = app_color
            update_palette(app_theme, app_color)
            if hasattr(app_ref, "apply_theme"):
                app_ref.after(10, app_ref.apply_theme)
