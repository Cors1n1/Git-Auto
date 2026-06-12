"""
views/security_view.py
Ferramenta visual intuitiva para limpeza de segurança e máquina do tempo.
"""
import os
import subprocess
import threading
import customtkinter as ctk
from tkinter import messagebox
from app.config import C

class SecurityView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.files_cache = []
        self.commits_cache = []

        # Custom Toggle Buttons
        self.toggle_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.toggle_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.btn_tab_files = ctk.CTkButton(self.toggle_frame, text="📄 Vazamentos (Arquivos)", font=ctk.CTkFont("Segoe UI", 14, "bold"), height=40, corner_radius=10, fg_color=C["blue"], hover_color=C["blue_dark"], command=lambda: self.switch_view("files"))
        self.btn_tab_files.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.btn_tab_commits = ctk.CTkButton(self.toggle_frame, text="⏱️ Linha do Tempo (Commits)", font=ctk.CTkFont("Segoe UI", 14, "bold"), height=40, corner_radius=10, fg_color="transparent", hover_color=C["card_border"], text_color=C["text_dim"], command=lambda: self.switch_view("commits"))
        self.btn_tab_commits.pack(side="left", expand=True, fill="x", padx=(5, 0))

        # Containers
        self.tab_files_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tab_commits_container = ctk.CTkFrame(self, fg_color="transparent")
        
        self.switch_view("files")

        self._build_files_tab()
        self._build_commits_tab()

        self.after(500, self.refresh_data)
        self.bind("<Map>", lambda e: self.refresh_data())
        self.app.workspace_var.trace_add("write", lambda *args: self.refresh_data())

    def switch_view(self, view):
        if hasattr(self, "tab_commit_details"):
            self.tab_commit_details.pack_forget()
            
        if view == "files":
            self.btn_tab_files.configure(fg_color=C["blue"], text_color="#fff")
            self.btn_tab_commits.configure(fg_color="transparent", text_color=C["text_dim"])
            self.tab_commits_container.pack_forget()
            self.tab_files_container.pack(fill="both", expand=True, padx=20, pady=5)
        elif view == "commits":
            self.btn_tab_commits.configure(fg_color=C["blue"], text_color="#fff")
            self.btn_tab_files.configure(fg_color="transparent", text_color=C["text_dim"])
            self.tab_files_container.pack_forget()
            self.tab_commits_container.pack(fill="both", expand=True, padx=20, pady=5)
        elif view == "details":
            self.btn_tab_commits.configure(fg_color="transparent", text_color=C["text_dim"])
            self.btn_tab_files.configure(fg_color="transparent", text_color=C["text_dim"])
            self.tab_commits_container.pack_forget()
            self.tab_files_container.pack_forget()
            self.tab_commit_details.pack(fill="both", expand=True, padx=20, pady=5)

    def _build_files_tab(self):
        # Search bar
        search_frame = ctk.CTkFrame(self.tab_files_container, fg_color="transparent")
        search_frame.pack(fill="x", pady=(5, 10))
        
        ctk.CTkLabel(search_frame, text="🔍 Buscar:", font=ctk.CTkFont("Segoe UI", 13, "bold"), text_color=C["text"]).pack(side="left", padx=(0, 10))
        self.entry_search = ctk.CTkEntry(search_frame, placeholder_text="Digite para filtrar... (ex: .env)", height=34)
        self.entry_search.pack(side="left", fill="x", expand=True)
        self.entry_search.bind("<KeyRelease>", self._filter_files)

        self.files_frame = ctk.CTkScrollableFrame(self.tab_files_container, fg_color=C["bg"], corner_radius=8, border_width=1, border_color=C["card_border"])
        self.files_frame.pack(fill="both", expand=True)

    def _build_commits_tab(self):
        # Search bar for commits
        search_frame = ctk.CTkFrame(self.tab_commits_container, fg_color="transparent")
        search_frame.pack(fill="x", pady=(5, 10))
        
        ctk.CTkLabel(search_frame, text="🔍 Buscar:", font=ctk.CTkFont("Segoe UI", 13, "bold"), text_color=C["text"]).pack(side="left", padx=(0, 10))
        self.entry_search_commits = ctk.CTkEntry(search_frame, placeholder_text="Filtrar por mensagem ou hash...", height=34)
        self.entry_search_commits.pack(side="left", fill="x", expand=True)
        self.entry_search_commits.bind("<KeyRelease>", self._filter_commits)

        self.commits_frame = ctk.CTkScrollableFrame(self.tab_commits_container, fg_color=C["bg"], corner_radius=8, border_width=1, border_color=C["card_border"])
        self.commits_frame.pack(fill="both", expand=True, pady=5)

    def get_repo(self):
        repo = self.app.entry_folder.get().strip()
        if not repo or not os.path.exists(os.path.join(repo, ".git")):
            return None
        return repo

    def refresh_data(self):
        repo = self.get_repo()
        if not repo:
            self._render_files([])
            self._render_commits([])
            return

        for widget in self.files_frame.winfo_children(): widget.destroy()
        for widget in self.commits_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.files_frame, text="Carregando repositório e escaneando vazamentos... ⏳", text_color=C["text_dim"]).pack(pady=20)
        ctk.CTkLabel(self.commits_frame, text="Carregando linha do tempo... ⏳", text_color=C["text_dim"]).pack(pady=20)

        def task():
            try:
                # Obter todos os arquivos do repositório (rastreados e não rastreados, mas respeitando o .gitignore)
                cmd_files = ['git', 'ls-files', '--cached', '--others', '--exclude-standard']
                proc = subprocess.run(cmd_files, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
                files = []
                if proc.returncode == 0:
                    raw_files = proc.stdout.split("\n")
                    files = [f.strip().replace("\\", "/") for f in raw_files if f.strip()]
                
                # Padrões Regex para detectar segredos reais no conteúdo
                import re
                secret_patterns = {
                    "Chave AWS": re.compile(r"AKIA[0-9A-Z]{16}"),
                    "Chave Google Cloud": re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
                    "Token GitHub": re.compile(r"(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36}"),
                    "Token NPM": re.compile(r"npm_[a-zA-Z0-9]{36}"),
                    "Chave Stripe": re.compile(r"(sk_live|rk_live|sk_test|rk_test)_[a-zA-Z0-9]+"),
                    "Senha em URL": re.compile(r"(?i)(postgres|mysql|redis|mongodb)(\+srv)?:\/\/[^:\/]+:[^@\/]+@"),
                    "Chave Genérica": re.compile(r"(?i)(api_key|apikey|secret|token|password|passwd|bearer|credentials)['\"]?\s*[:=]\s*['\"][A-Za-z0-9\-\_\.=]{8,}['\"]")
                }
                binary_exts = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.exe', '.dll', '.so', '.dylib', '.zip', '.tar', '.gz', '.mp4', '.mp3', '.wav', '.ttf', '.woff', '.woff2', '.eot', '.pyc'}
                
                # Scanner de Arquivos Suspeitos
                suspicious_exts = {
                    ".env": "Extensão de configuração (.env)",
                    ".pem": "Certificado/Chave (.pem)",
                    ".key": "Chave privada (.key)",
                    ".p12": "Certificado (.p12)",
                    ".pfx": "Certificado (.pfx)",
                    "id_rsa": "Chave SSH (id_rsa)",
                    ".sql": "Banco de dados (.sql)",
                    ".sqlite": "Banco de dados (.sqlite)"
                }
                suspicious_names = {
                    "credentials": "Nome de credenciais",
                    "secret": "Nome de segredo",
                    "passwd": "Nome de senhas",
                    "shadow": "Nome de senhas (shadow)",
                    "htpasswd": "Nome de senhas (htpasswd)"
                }
                
                risky_files_dict = {}
                normal_files = []
                for f in files:
                    fname = f.lower()
                    basename = fname.split("/")[-1]
                    reason = None
                    for ext, msg in suspicious_exts.items():
                        if fname.endswith(ext):
                            reason = msg
                            break
                    if not reason:
                        for name, msg in suspicious_names.items():
                            if name in basename:
                                reason = msg
                                break
                    # Busca profunda no conteúdo do arquivo
                    if not reason:
                        ext = os.path.splitext(f)[1].lower()
                        if ext not in binary_exts:
                            full_path = os.path.join(repo, f)
                            try:
                                if os.path.getsize(full_path) < 1024 * 1024:  # Ignora arquivos > 1MB
                                    with open(full_path, "r", encoding="utf-8") as file_obj:
                                        content = file_obj.read()
                                        for msg, pat in secret_patterns.items():
                                            if pat.search(content):
                                                reason = f"Segredo detectado ({msg})"
                                                break
                            except Exception:
                                pass
                    
                    if reason:
                        risky_files_dict[f] = reason
                    else:
                        normal_files.append(f)
                        
                # Para ordenar por pastas, vamos usar a lista em ordem alfabética normal para que a árvore fique perfeita
                # Arquivos de risco serão visualmente destacados pela cor e etiqueta
                files = list(risky_files_dict.keys()) + normal_files
                files.sort()
                self.risky_files_dict = risky_files_dict
                
                # Obter commits
                cmd_commits = ['git', 'log', '--oneline', '-n', '25', '--pretty=format:%h|%s|%ar|%an']
                proc_c = subprocess.run(cmd_commits, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
                commits = []
                if proc_c.returncode == 0:
                    raw_commits = proc_c.stdout.split("\n")
                    commits = [c.strip() for c in raw_commits if c.strip()]
                    
                # Scanner Profundo de Commits (Busca por segredos no código)
                cmd_scan = ['git', 'log', '-G', '(password|secret|api_key|apikey|token|bearer|sk_live|credentials)', '-i', '--format=%h']
                proc_scan = subprocess.run(cmd_scan, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
                strict_hashes = set()
                if proc_scan.returncode == 0:
                    raw_hashes = [h.strip() for h in proc_scan.stdout.split("\n") if h.strip()]
                    # Filtragem Fina (Autópsia)
                    # Apenas mantém os hashes que a nossa Regex Rigorosa confirmar como vazamento real.
                    for h in raw_hashes:
                        proc_p = subprocess.run(['git', 'show', h, '--oneline'], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
                        if proc_p.returncode == 0:
                            has_real_leak = False
                            for msg, pat in secret_patterns.items():
                                if pat.search(proc_p.stdout):
                                    has_real_leak = True
                                    break
                            if has_real_leak:
                                strict_hashes.add(h)
                                
                self.leaked_hashes_set = strict_hashes
                
                self.files_cache = files
                self.commits_cache = commits
                
                self.after(0, lambda: self._update_ui())
            except Exception as e:
                import traceback
                try:
                    with open(os.path.join(repo, "git_auto_debug.log"), "w", encoding="utf-8") as f:
                        f.write(traceback.format_exc())
                except:
                    pass
                print(f"[ERRO] Falha ao atualizar: {e}")
                
        threading.Thread(target=task, daemon=True).start()

    def _update_ui(self):
        self.entry_search.delete(0, "end")
        self.entry_search_commits.delete(0, "end")
        self._render_files(self.files_cache)
        self._render_commits(self.commits_cache)

    def _filter_files(self, event=None):
        query = self.entry_search.get().strip().lower()
        if not query:
            self._render_files(self.files_cache)
        else:
            filtered = [f for f in self.files_cache if query in f.lower()]
            self._render_files(filtered)

    def _filter_commits(self, event=None):
        query = self.entry_search_commits.get().strip().lower()
        if not query:
            self._render_commits(self.commits_cache)
        else:
            filtered = [c for c in self.commits_cache if query in c.lower()]
            self._render_commits(filtered)

    def _render_files(self, files_list):
        # Limpar
        for widget in self.files_frame.winfo_children():
            widget.destroy()

        if not files_list:
            ctk.CTkLabel(self.files_frame, text="Nenhum arquivo encontrado.", text_color=C["text_dim"]).pack(pady=20)
            return

        # Para não travar a UI caso a lista seja absurdamente gigante, limitamos a renderização a 200 itens.
        # A pesquisa filtrará os que o usuário quer.
        limit = min(200, len(files_list))
        
        import os
        from collections import defaultdict
        
        # Agrupar por pasta
        grouped = defaultdict(list)
        # Limite elevado para suportar mais arquivos
        limit = min(500, len(files_list))
        
        for f in files_list[:limit]:
            folder = os.path.dirname(f)
            if not folder: folder = "/"
            grouped[folder].append(f)
            
        # Identificar pastas que possuem arquivos de risco
        risky_folders = set()
        for f in getattr(self, "risky_files_dict", {}):
            folder = os.path.dirname(f)
            if not folder: folder = "/"
            risky_folders.add(folder)
            
        # Função para ordenar pastas: pastas com risco primeiro
        def folder_sort_key(folder):
            return (0 if folder in risky_folders else 1, folder.lower())
            
        for folder in sorted(grouped.keys(), key=folder_sort_key):
            # Header da pasta
            f_row = ctk.CTkFrame(self.files_frame, fg_color="transparent")
            f_row.pack(fill="x", padx=5, pady=(15, 5))
            
            # Se a pasta tiver arquivos de risco, podemos botar um ícone de alerta
            folder_icon = "🚨 📁" if folder in risky_folders else "📁"
            ctk.CTkLabel(f_row, text=f"{folder_icon} {folder}", font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color=C["text"]).pack(side="left")
            
            # Função para ordenar arquivos: risco primeiro
            def file_sort_key(f):
                return (0 if f in getattr(self, "risky_files_dict", {}) else 1, f.lower())
                
            for f in sorted(grouped[folder], key=file_sort_key):
                is_risky = f in getattr(self, "risky_files_dict", {})
                reason = getattr(self, "risky_files_dict", {}).get(f, "")
                
                border_col = C["red"] if is_risky else C["card"]
                row = ctk.CTkFrame(self.files_frame, fg_color=C["card"], corner_radius=6, border_width=1 if is_risky else 0, border_color=border_col)
                row.pack(fill="x", padx=(25, 5), pady=3)
                
                content = ctk.CTkFrame(row, fg_color="transparent")
                content.pack(fill="both", expand=True, padx=10, pady=8)
                
                # Botões - pack right FIRST so they are not pushed out
                btn_actions = ctk.CTkFrame(content, fg_color="transparent")
                btn_actions.pack(side="right")
                
                btn_view = ctk.CTkButton(btn_actions, text="👁️ Ver", width=50, height=26, fg_color="transparent", hover_color=C["card_border"], text_color=C["blue"], font=ctk.CTkFont("Segoe UI", 12, "bold"), command=lambda f=f: self.view_file_content(f))
                btn_view.pack(side="left", padx=5)
                
                btn_del = ctk.CTkButton(btn_actions, text="🗑️ Purgar", width=60, height=26, fg_color="transparent", hover_color=C["red_dark"], text_color=C["red"], font=ctk.CTkFont("Segoe UI", 12, "bold"), command=lambda f=f: self.ask_purge(f))
                btn_del.pack(side="left")
                
                # Nomes e Avisos - expand to fill remaining space
                left_col = ctk.CTkFrame(content, fg_color="transparent")
                left_col.pack(side="left", fill="both", expand=True)
                
                top_line = ctk.CTkFrame(left_col, fg_color="transparent")
                top_line.pack(fill="x")
                
                if is_risky:
                    ctk.CTkLabel(top_line, text="🚨 RISCO", font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color=C["red"], fg_color=C["red_dark"], corner_radius=4).pack(side="left", padx=(0, 5))
                    
                basename = os.path.basename(f)
                ctk.CTkLabel(top_line, text=basename, font=ctk.CTkFont("Consolas", 12), text_color=C["text"]).pack(side="left")
                
                if is_risky:
                    ctk.CTkLabel(left_col, text=f"⚠️ Motivo: {reason}", font=ctk.CTkFont("Segoe UI", 11, slant="italic"), text_color=C["orange"]).pack(anchor="w", pady=(2, 0))

        if len(files_list) > limit:
            ctk.CTkLabel(self.files_frame, text=f"... e mais {len(files_list) - limit} arquivos escondidos. Use a barra de pesquisa.", text_color=C["text_dim"], font=ctk.CTkFont("Segoe UI", 11, slant="italic")).pack(pady=10)

    def view_file_content(self, target_file, commit_hash=None):
        repo = self.get_repo()
        if not repo: return
        
        if commit_hash:
            # Mostra o patch (diff) exato deste arquivo neste commit para evidenciar o vazamento
            cmd = f'git show {commit_hash} -- "{target_file}"'
            win_title = f"Patch de {target_file} em {commit_hash}"
        else:
            # Obter o conteúdo do arquivo via Git
            cmd = f'git show HEAD:"{target_file}"'
            win_title = f"Visualizando: {target_file}"
            
        proc = subprocess.run(cmd, shell=True, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
        content = proc.stdout if proc.returncode == 0 else f"[Erro ao ler conteúdo: {proc.stderr}]"
        
        import os
        filepath = os.path.join(repo, target_file)
        if not commit_hash and proc.returncode != 0 and os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception as e:
                content = f"[Erro ao ler arquivo fisicamente: {e}]"
                
        import re
        
        named_patterns = {
            "Chave AWS": r"AKIA[0-9A-Z]{16}",
            "Chave Google Cloud": r"AIza[0-9A-Za-z\-_]{35}",
            "Token GitHub": r"(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36}",
            "Token NPM": r"npm_[a-zA-Z0-9]{36}",
            "Chave Stripe": r"(sk_live|rk_live|sk_test|rk_test)_[a-zA-Z0-9]+",
            "Senha em URL": r"(?i)(postgres|mysql|redis|mongodb)(\+srv)?:\/\/[^:\/]+:[^@\/]+@",
            "Chave Genérica": r"(?i)(api_key|apikey|secret|token|password|passwd|bearer|credentials)\s*[:=]"
        }
        
        dynamic_reason = None
        for msg, pat in named_patterns.items():
            if re.search(pat, content):
                dynamic_reason = f"Vazamento Critíco Detectado ({msg})"
                break
                
        if not dynamic_reason:
            dynamic_reason = getattr(self, "risky_files_dict", {}).get(target_file, "")
            
        win = ctk.CTkToplevel(self)
        win.title(win_title)
        win.geometry("700x500")
        win.transient(self.winfo_toplevel())
        win.grab_set()
        
        hdr = ctk.CTkFrame(win, fg_color=C["bg"])
        hdr.pack(fill="x", padx=15, pady=15)
        ctk.CTkLabel(hdr, text=target_file, font=ctk.CTkFont("Consolas", 14, "bold"), text_color=C["text"]).pack(side="left")
        
        if dynamic_reason:
            ctk.CTkLabel(hdr, text=f"🚨 {dynamic_reason}", font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=C["red"]).pack(side="left", padx=15)
        
        textbox = ctk.CTkTextbox(win, fg_color=C["card"], text_color=C["text"], font=ctk.CTkFont("Consolas", 12))
        textbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        textbox.insert("0.0", content)
        
        # CTkTextbox não expõe tag_config nativamente, temos que acessar o widget interno do Tkinter
        try:
            textbox._textbox.tag_config("danger", background=C["red_dark"], foreground="white")
            for line_num, line in enumerate(content.split("\n"), 1):
                if any(re.search(pat, line) for pat in named_patterns.values()):
                    textbox._textbox.tag_add("danger", f"{line_num}.0", f"{line_num}.end")
        except Exception:
            pass
            
        textbox.configure(state="disabled")
        
        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))
        ctk.CTkButton(btn_frame, text="Fechar", width=100, height=32, fg_color=C["card"], hover_color=C["card_border"], text_color=C["text"], font=ctk.CTkFont("Segoe UI", 12, "bold"), command=win.destroy).pack(side="right")
        ctk.CTkButton(btn_frame, text="🗑️ Purgar Definitivamente", width=180, height=32, fg_color=C["red_dark"], hover_color="#991b1b", font=ctk.CTkFont("Segoe UI", 12, "bold"), command=lambda: [win.destroy(), self.ask_purge(target_file)]).pack(side="left")

    def _render_commits(self, commits_list):
        for widget in self.commits_frame.winfo_children():
            widget.destroy()

        if not commits_list:
            ctk.CTkLabel(self.commits_frame, text="Nenhum commit encontrado.", text_color=C["text_dim"]).pack(pady=20)
            return

        for c_str in commits_list:
            parts = c_str.split("|")
            if len(parts) < 4: continue
            chash, cmsg, cdate, cauthor = parts[0], parts[1], parts[2], parts[3]
            is_leaked = chash in getattr(self, "leaked_hashes_set", set())

            row = ctk.CTkFrame(self.commits_frame, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=0)
            
            # Node (Timeline visual) - fix height to 10 so it doesn't default to 200px and ruin the layout
            dot_color = C["red"] if is_leaked else C["orange"]
            line_color = C["red"] if is_leaked else C["card_border"]
            
            node_frame = ctk.CTkFrame(row, fg_color="transparent", width=40, height=10)
            node_frame.pack(side="left", fill="y")
            node_frame.pack_propagate(False)
            
            line = ctk.CTkFrame(node_frame, width=2, fg_color=line_color)
            line.place(relx=0.5, rely=0, relheight=1, anchor="n")
            
            dot = ctk.CTkFrame(node_frame, width=12, height=12, corner_radius=6, fg_color=dot_color)
            dot.place(relx=0.5, rely=0.5, anchor="center")

            # Content card
            card_bw = 1 if is_leaked else 0
            card_border = C["red"] if is_leaked else C["card_border"]
            card = ctk.CTkFrame(row, fg_color=C["card"], corner_radius=8, border_width=card_bw, border_color=card_border)
            card.pack(side="left", fill="both", expand=True, pady=8, padx=(0, 5))
            
            # Pack buttons first so they are pinned to the right
            btn_actions = ctk.CTkFrame(card, fg_color="transparent")
            btn_actions.pack(side="right", padx=15)

            btn_gh = ctk.CTkButton(btn_actions, text="📄 Detalhes", width=70, height=28, fg_color="transparent", hover_color=C["card_border"], text_color=C["blue"], font=ctk.CTkFont("Segoe UI", 11, "bold"), command=lambda h=chash, m=cmsg, d=cdate: self.show_commit_details(h, m, d))
            btn_gh.pack(side="left", padx=(0, 10))

            btn_revert = ctk.CTkButton(btn_actions, text="⏪ Voltar", width=80, height=28, fg_color=C["muted"], hover_color=C["orange"], text_color=C["text"], font=ctk.CTkFont("Segoe UI", 11, "bold"), command=lambda h=chash, m=cmsg: self.ask_revert(h, m))
            btn_revert.pack(side="left")

            # Then pack info_frame which will expand to fill remaining space
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=10)
            
            if is_leaked:
                ctk.CTkLabel(info_frame, text="🚨 Possível Vazamento de Chave/Senha", font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color=C["red"]).pack(anchor="w", pady=(0, 2))
                
            # Truncate text to avoid pushing the UI limits horizontally
            display_msg = cmsg if len(cmsg) < 65 else cmsg[:62] + "..."
            
            ctk.CTkLabel(info_frame, text=display_msg, font=ctk.CTkFont("Segoe UI", 13, "bold"), text_color=C["text"], anchor="w").pack(fill="x")
            ctk.CTkLabel(info_frame, text=f"{cdate}", font=ctk.CTkFont("Consolas", 11), text_color=C["text_dim"], anchor="w").pack(fill="x")

    def show_commit_details(self, chash, cmsg, cdate):
        if not hasattr(self, "tab_commit_details"):
            self.tab_commit_details = ctk.CTkFrame(self, fg_color="transparent")
        else:
            for w in self.tab_commit_details.winfo_children():
                w.destroy()

        self.switch_view("details")

        hdr = ctk.CTkFrame(self.tab_commit_details, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 10))
        btn_back = ctk.CTkButton(hdr, text="⬅ Voltar", width=80, height=32, fg_color=C["card"], hover_color=C["card_border"], text_color=C["text"], font=ctk.CTkFont("Segoe UI", 12, "bold"), command=lambda: self.switch_view("commits"))
        btn_back.pack(side="left")
        ctk.CTkLabel(hdr, text="Detalhes do Commit", font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=C["text"]).pack(side="left", padx=15)

        info = ctk.CTkFrame(self.tab_commit_details, fg_color=C["card"], corner_radius=8)
        info.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(info, text=cmsg, font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color=C["text"], wraplength=500, justify="left").pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(info, text=f"Hash: {chash} • {cdate}", font=ctk.CTkFont("Consolas", 12), text_color=C["text_dim"]).pack(anchor="w", padx=15, pady=(0, 15))

        files_frame = ctk.CTkScrollableFrame(self.tab_commit_details, fg_color=C["bg"], border_width=1, border_color=C["card_border"], corner_radius=8)
        files_frame.pack(fill="both", expand=True)

        repo = self.get_repo()
        if not repo: return

        def load_details():
            cmd = ['git', 'show', '--name-status', '--pretty=format:', chash]
            proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
            
            # Descobrir quais arquivos vazaram neste commit
            cmd_scan = ['git', 'log', '-G', '(password|secret|api_key|apikey|token|bearer|sk_live|credentials)', '-i', '-1', '--name-only', '--format=', chash]
            proc_scan = subprocess.run(cmd_scan, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
            leaked_files = set()
            if proc_scan.returncode == 0:
                leaked_files = set([f.strip() for f in proc_scan.stdout.split("\n") if f.strip()])
                
            if proc.returncode == 0:
                lines = [line.strip() for line in proc.stdout.split("\n") if line.strip()]
                self.after(0, lambda: self._render_commit_files(files_frame, lines, leaked_files, chash))

        threading.Thread(target=load_details, daemon=True).start()

    def _render_commit_files(self, parent, lines, leaked_files, chash):
        if not lines:
            ctk.CTkLabel(parent, text="Nenhuma modificação de arquivo identificada.", text_color=C["text_dim"]).pack(pady=20)
            return

        for line in lines:
            parts = line.split(maxsplit=1)
            if len(parts) < 2: continue
            status, fname = parts[0], parts[1]

            is_leaked = fname in leaked_files

            icon = "📝 Modificado"
            color = C["blue"]
            if status.startswith("A"):
                icon = "✨ Adicionado"
                color = C["green"]
            elif status.startswith("D"):
                icon = "🗑️ Deletado"
                color = C["red"]

            border_col = C["red"] if is_leaked else C["card"]
            bw = 1 if is_leaked else 0
            
            row = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=6, height=35, border_width=bw, border_color=border_col)
            row.pack(fill="x", padx=5, pady=3)
            row.pack_propagate(False)

            if is_leaked:
                ctk.CTkLabel(row, text="🚨 VAZOU AQUI", font=ctk.CTkFont("Segoe UI", 11, "bold"), text_color=C["red"], fg_color=C["red_dark"], corner_radius=4).pack(side="left", padx=(10, 5))

            ctk.CTkLabel(row, text=icon, font=ctk.CTkFont("Segoe UI", 12, "bold"), text_color=color).pack(side="left", padx=(15 if not is_leaked else 5, 15))
            ctk.CTkLabel(row, text=fname, font=ctk.CTkFont("Consolas", 12), text_color=C["text"]).pack(side="left", padx=5)
            
            btn_actions = ctk.CTkFrame(row, fg_color="transparent")
            btn_actions.pack(side="right", padx=10)
            btn_view = ctk.CTkButton(btn_actions, text="🔍 Ver O que Mudou", width=50, height=26, fg_color="transparent", hover_color=C["card_border"], text_color=C["blue"], font=ctk.CTkFont("Segoe UI", 12, "bold"), command=lambda f=fname, h=chash: self.view_file_content(f, commit_hash=h))
            btn_view.pack(side="left")

    def show_alert(self, title, message, type="info", callback=None):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("450x220")
        win.resizable(False, False)
        win.transient(self.winfo_toplevel())
        win.grab_set()
        
        win.update_idletasks()
        x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() - 450) // 2
        y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() - 220) // 2
        win.geometry(f"+{x}+{y}")
        
        color = C.get("blue", "#0078D7")
        if type == "error": color = C.get("red", "#FF0000")
        elif type in ["warning", "ask"]: color = C.get("orange", "#FFA500")
        
        ctk.CTkLabel(win, text=title, font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=color).pack(pady=(20, 10))
        
        lbl = ctk.CTkLabel(win, text=message, font=ctk.CTkFont("Segoe UI", 12), text_color=C.get("text", "#FFFFFF"), wraplength=400, justify="center")
        lbl.pack(fill="both", expand=True, padx=20, pady=5)
        
        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=(10, 20))
        
        def on_yes():
            win.destroy()
            if callback: callback(True)
            
        def on_no():
            win.destroy()
            if callback: callback(False)
            
        if type == "ask":
            btn_yes = ctk.CTkButton(btn_frame, text="Sim", width=100, fg_color=color, hover_color=C.get("card_border", "#444"), text_color="#FFF", font=ctk.CTkFont("Segoe UI", 12, "bold"), command=on_yes)
            btn_yes.pack(side="left", padx=10)
            btn_no = ctk.CTkButton(btn_frame, text="Não", width=100, fg_color=C.get("card", "#333"), hover_color=C.get("card_border", "#444"), text_color=C.get("text", "#FFF"), font=ctk.CTkFont("Segoe UI", 12, "bold"), command=on_no)
            btn_no.pack(side="right", padx=10)
        else:
            btn_ok = ctk.CTkButton(btn_frame, text="OK", width=100, fg_color=color, hover_color=C.get("card_border", "#444"), text_color="#FFF", font=ctk.CTkFont("Segoe UI", 12, "bold"), command=on_yes)
            btn_ok.pack()

    def ask_purge(self, target_file):
        repo = self.get_repo()
        if not repo:
            return
            
        def on_confirm(confirm):
            if confirm:
                cmd = f'git filter-branch --force --index-filter "git rm --cached --ignore-unmatch \'{target_file}\'" --prune-empty --tag-name-filter cat -- --all'
                self.run_cmd(cmd, f"Arquivo '{target_file}' deletado do histórico local.", repo)
                
        self.show_alert("Confirmar Exclusão", f"Deseja purgar '{target_file}' permanentemente de todo o histórico do Git?\n\nIsso apagará o arquivo completamente.", "ask", on_confirm)

    def ask_revert(self, chash, cmsg):
        repo = self.get_repo()
        if not repo:
            return

        def on_keep(keep):
            if keep:
                self.run_cmd(f"git reset --soft {chash}", f"Voltou suavemente para {chash}. Arquivos mantidos.", repo)
            else:
                def on_sure(sure):
                    if sure:
                        self.run_cmd(f"git reset --hard {chash}", f"Voltou forçadamente para {chash}. Alterações destruídas.", repo)
                self.show_alert("DESTRUIR ARQUIVOS?", "Isso irá apagar FISICAMENTE todas as modificações nos seus arquivos feitas depois deste commit. Tem absoluta certeza?", "ask", on_sure)

        self.show_alert("Máquina do Tempo", f"Você escolheu voltar para o commit:\n'{cmsg}'\n\nDeseja MANTER seus arquivos atuais e apenas voltar o status do Git?\n\n(Clique SIM para manter os arquivos intactos na sua pasta. Clique NÃO para DESTRUIR as modificações e voltar os arquivos exatamente como eram nesta data.)", "ask", on_keep)

    def run_cmd(self, cmd, success_msg, repo):
        print(f"> {cmd}")
        
        loading = ctk.CTkToplevel(self)
        loading.title("Aguarde")
        loading.geometry("400x180")
        loading.resizable(False, False)
        loading.transient(self.winfo_toplevel())
        loading.grab_set()
        
        loading.update_idletasks()
        x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() - 400) // 2
        y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() - 180) // 2
        loading.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(loading, text="Processando...", font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color=C.get("text", "#FFFFFF")).pack(pady=(20, 5))
        ctk.CTkLabel(loading, text="Executando operação no histórico do Git.\nIsso pode levar alguns minutos dependendo do tamanho\ndo repositório. Não feche o aplicativo.", font=ctk.CTkFont("Segoe UI", 12), text_color=C.get("text_dim", "#AAAAAA")).pack(pady=(0, 15))
        
        progress = ctk.CTkProgressBar(loading, mode="indeterminate", width=300)
        progress.pack(pady=10)
        progress.start()
        
        lbl_status = ctk.CTkLabel(loading, text="Reescrevendo histórico local...", font=ctk.CTkFont("Segoe UI", 11, slant="italic"), text_color=C.get("orange", "#FFA500"))
        lbl_status.pack(pady=(5, 0))
        
        def task():
            try:
                proc = subprocess.run(cmd, shell=True, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
                
                # Executa a limpeza / fechamento do loader IMEDIATAMENTE após terminar, e chama o refresh_data para a tela atualizar
                self.after(0, lambda: progress.stop())
                self.after(0, lambda: loading.destroy())
                self.after(0, self.refresh_data)
                
                if proc.returncode == 0:
                    if "filter-branch" in cmd or "reset" in cmd:
                        print("> Sincronizando com remote...")
                        self.after(0, lambda: lbl_status.configure(text="Sincronizando com o GitHub (Push Forçado)..."))
                        push_args = "--force --all" if "filter-branch" in cmd else "--force"
                        push_proc = subprocess.run(f"git push origin {push_args}", shell=True, cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
                        if push_proc.returncode == 0:
                            self.after(100, lambda: self.show_alert("Sincronizado", "Ação concluída e sincronizada com o GitHub (Push Forçado) com sucesso!", "info"))
                        else:
                            self.after(100, lambda: self.show_alert("Aviso de Sincronização", f"O comando local deu certo, mas a sincronização falhou:\n\n{push_proc.stderr}", "warning"))
                    else:
                        self.after(100, lambda: self.show_alert("Sucesso", success_msg, "info"))
                else:
                    self.after(100, lambda: self.show_alert("Erro", f"Falha no comando Git:\n\n{proc.stderr}", "error"))
            except Exception as e:
                self.after(0, lambda: progress.stop())
                self.after(0, lambda: loading.destroy())
                self.after(0, self.refresh_data)
                self.after(100, lambda: self.show_alert("Erro Crítico", f"Exceção ao rodar comando:\n\n{e}", "error"))

        threading.Thread(target=task, daemon=True).start()
