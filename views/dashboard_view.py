"""
views/dashboard_view.py
Painel de perfil GitHub, gráfico de contribuições e repositórios recentes.
"""
import os
import io
import json
import threading
import datetime
import requests
import customtkinter as ctk
from PIL import Image, ImageDraw

import app.config as cfg
from app.config import C, CACHE_PROFILE, CACHE_REPOS, CACHE_AVATAR, CACHE_GRAPH
from app.theme import set_title_bar_color
from widgets.tooltip import HoverTooltip


class DashboardView(ctk.CTkScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app            = app
        self.loaded         = False
        self.graph_data_map = {}
        self.tooltip        = HoverTooltip(self)

        # ── Profile header ────────────────────────────────────────────────────
        self.header = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16,
                                   border_width=1, border_color=C["card_border"])
        self.header.pack(fill="x", pady=(0, 15))

        self.lbl_avatar = ctk.CTkLabel(self.header, text="", width=80, height=80)
        self.lbl_avatar.pack(side="left", padx=20, pady=20)

        info_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, pady=20)

        self.btn_collab = ctk.CTkButton(
            self.header, text="Colaboradores", width=140,
            fg_color=C["blue"], hover_color=C["blue_dark"],
            command=self.open_collab_dialog)
        self.btn_collab.pack(side="right", padx=20, pady=20)

        self.lbl_name = ctk.CTkLabel(info_frame, text="Carregando Perfil...",
                                     font=ctk.CTkFont("Segoe UI", 24, "bold"),
                                     text_color=C["text"])
        self.lbl_name.pack(anchor="w")
        self.lbl_username = ctk.CTkLabel(info_frame, text="@...",
                                         font=ctk.CTkFont("Segoe UI", 14),
                                         text_color=C["blue"])
        self.lbl_username.pack(anchor="w")
        self.lbl_bio = ctk.CTkLabel(info_frame, text="",
                                    font=ctk.CTkFont("Segoe UI", 12),
                                    text_color=C["text_dim"])
        self.lbl_bio.pack(anchor="w", pady=(5, 0))

        self.details_frame = ctk.CTkFrame(info_frame, fg_color="transparent", height=24)
        self.details_frame.pack(anchor="w", pady=(10, 0))

        # ── Stats ─────────────────────────────────────────────────────────────
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0, 15))
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.stat_repos_pub  = self._build_stat_card(self.stats_frame, 0, "Repositórios Públicos", "-")
        self.stat_repos_priv = self._build_stat_card(self.stats_frame, 1, "Repositórios Privados", "-")
        self.stat_followers  = self._build_stat_card(self.stats_frame, 2, "Seguidores", "-")
        self.stat_following  = self._build_stat_card(self.stats_frame, 3, "Seguindo", "-")

        # ── Contribution graph ────────────────────────────────────────────────
        self.graph_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16,
                                        border_width=1, border_color=C["card_border"])
        self.graph_frame.pack(fill="x", pady=(0, 15))

        graph_header = ctk.CTkFrame(self.graph_frame, fg_color="transparent")
        graph_header.pack(fill="x", padx=20, pady=(15, 5))
        self.lbl_contributions = ctk.CTkLabel(
            graph_header, text="Contribuições no Último Ano",
            font=ctk.CTkFont("Segoe UI", 14, "bold"), text_color=C["text"])
        self.lbl_contributions.pack(side="left")

        self.graph_canvas = ctk.CTkCanvas(self.graph_frame, bg=C["card"],
                                          highlightthickness=0, height=120)
        self.graph_canvas.pack(fill="x", padx=20, pady=(5, 15))

        # ── Recent repos ──────────────────────────────────────────────────────
        self.recent_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=16,
                                         border_width=1, border_color=C["card_border"])
        self.recent_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(self.recent_frame, text="Últimos Projetos Atualizados",
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color=C["text"]).pack(anchor="w", padx=20, pady=(15, 10))

        self.repos_container = ctk.CTkScrollableFrame(self.recent_frame, fg_color="transparent")
        self.repos_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ── public API ────────────────────────────────────────────────────────────
    def open_collab_dialog(self):
        if not self.app.workspace_var.get():
            return
        from dialogs.collaborators import CollaboratorManagerDialog
        CollaboratorManagerDialog(self, self.app)

    def load_profile(self):
        if self.loaded:
            return
        self.loaded = True
        # Show cached data immediately
        try:
            if os.path.exists(CACHE_PROFILE):
                with open(CACHE_PROFILE, "r", encoding="utf-8") as f:
                    self._update_ui_user(json.load(f))
            if os.path.exists(CACHE_REPOS):
                with open(CACHE_REPOS, "r", encoding="utf-8") as f:
                    self._update_ui_repos(json.load(f))
            if os.path.exists(CACHE_GRAPH):
                with open(CACHE_GRAPH, "r", encoding="utf-8") as f:
                    self._update_ui_graph(json.load(f))
            if os.path.exists(CACHE_AVATAR):
                with open(CACHE_AVATAR, "rb") as f:
                    self.lbl_avatar.configure(
                        image=self._create_circular_image(f.read()))
        except Exception:
            pass
        threading.Thread(target=self._fetch_data_thread, daemon=True).start()

    # ── private helpers ───────────────────────────────────────────────────────
    def _build_stat_card(self, parent, col, title, value):
        card = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=16,
                            border_width=1, border_color=C["card_border"])
        card.grid(row=0, column=col, sticky="nsew", padx=8)
        lbl_val = ctk.CTkLabel(card, text=value,
                               font=ctk.CTkFont("Segoe UI", 32, "bold"),
                               text_color=C["blue"])
        lbl_val.pack(pady=(20, 2))
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color=C["text_dim"]).pack(pady=(0, 20))
        return lbl_val

    def _create_circular_image(self, img_data):
        img  = Image.open(io.BytesIO(img_data)).convert("RGBA")
        img  = img.resize((80, 80), Image.Resampling.LANCZOS)
        mask = Image.new("L", (80, 80), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 80, 80), fill=255)
        result = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask)
        return ctk.CTkImage(light_image=result, dark_image=result, size=(80, 80))

    def _fetch_data_thread(self):
        headers = {"Authorization": f"Bearer {cfg.GITHUB_TOKEN}",
                   "Accept": "application/vnd.github.v3+json"}
        try:
            resp = requests.get("https://api.github.com/user", headers=headers, timeout=10)
            if resp.status_code != 200:
                return
            data = resp.json()

            all_repos = []
            page = 1
            while True:
                r = requests.get(
                    f"https://api.github.com/user/repos?sort=updated&per_page=100&page={page}",
                    headers=headers, timeout=10)
                if r.status_code == 200:
                    batch = r.json()
                    if not batch:
                        break
                    all_repos.extend(batch)
                    if len(batch) < 100:
                        break
                    page += 1
                else:
                    break

            data["total_private_repos"] = sum(1 for r in all_repos if r.get("private"))
            try:
                with open(CACHE_PROFILE, "w", encoding="utf-8") as f:
                    json.dump(data, f)
            except Exception:
                pass

            avatar_resp = requests.get(data.get("avatar_url", ""), timeout=10)
            if avatar_resp.status_code == 200:
                try:
                    with open(CACHE_AVATAR, "wb") as f:
                        f.write(avatar_resp.content)
                except Exception:
                    pass
                ctk_img = self._create_circular_image(avatar_resp.content)
                self.app.after(0, lambda: self.lbl_avatar.configure(image=ctk_img))

            self.app.after(0, lambda: self._update_ui_user(data))

            top_repos = all_repos[:5]
            try:
                with open(CACHE_REPOS, "w", encoding="utf-8") as f:
                    json.dump(top_repos, f)
            except Exception:
                pass
            self.app.after(0, lambda: self._update_ui_repos(top_repos))

            # GraphQL contribution graph
            query = """
            query {
              user(login: "%s") {
                contributionsCollection {
                  contributionCalendar {
                    totalContributions
                    weeks {
                      contributionDays {
                        contributionCount
                        date
                      }
                    }
                  }
                }
              }
            }
            """ % data.get("login")
            gql = requests.post("https://api.github.com/graphql",
                                json={"query": query}, headers=headers, timeout=10)
            if gql.status_code == 200:
                gql_data = gql.json()
                try:
                    with open(CACHE_GRAPH, "w", encoding="utf-8") as f:
                        json.dump(gql_data, f)
                except Exception:
                    pass
                self.app.after(0, lambda: self._update_ui_graph(gql_data))
        except Exception:
            pass

    def _update_ui_user(self, data):
        self.lbl_name.configure(text=data.get("name") or data.get("login") or "Usuário")
        self.lbl_username.configure(text=f"@{data.get('login', '')}")
        self.lbl_bio.configure(text=data.get("bio") or "")

        for child in self.details_frame.winfo_children():
            child.destroy()

        details = []
        if data.get("location"): details.append(f"📍 {data['location']}")
        if data.get("company"):  details.append(f"🏢 {data['company']}")
        if data.get("blog"):     details.append(f"🌐 {data['blog']}")
        if data.get("created_at"):
            try:
                dt = datetime.datetime.strptime(data["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                details.append(f"📅 Membro desde {dt.year}")
            except Exception:
                pass

        for text in details:
            ctk.CTkLabel(self.details_frame, text=f" {text} ",
                         font=ctk.CTkFont("Segoe UI", 11),
                         fg_color=C["card_border"], corner_radius=6,
                         text_color=C["text"]).pack(side="left", padx=(0, 10))

        self.stat_repos_pub.configure(text=str(data.get("public_repos", 0)))
        self.stat_repos_priv.configure(text=str(data.get("total_private_repos", 0)))
        self.stat_followers.configure(text=str(data.get("followers", 0)))
        self.stat_following.configure(text=str(data.get("following", 0)))

    def _update_ui_repos(self, repos):
        for child in self.repos_container.winfo_children():
            child.destroy()
        for repo in repos:
            item = ctk.CTkFrame(self.repos_container, fg_color="transparent")
            item.pack(fill="x", pady=5)
            ctk.CTkLabel(item, text=repo.get("name", ""),
                         font=ctk.CTkFont("Segoe UI", 13, "bold"),
                         text_color=C["text"]).pack(side="left", padx=10)
            pvt         = repo.get("private", False)
            badge_color = C["red_dark"] if pvt else C["green_dark"]
            badge_text  = "Privado" if pvt else "Público"
            ctk.CTkLabel(item, text=badge_text, font=ctk.CTkFont("Segoe UI", 10),
                         fg_color=badge_color, corner_radius=4,
                         text_color="#ffffff").pack(side="left", padx=5)
            url = repo.get("clone_url", "")
            ctk.CTkButton(item, text="Baixar / Selecionar", width=120, height=28,
                          font=ctk.CTkFont("Segoe UI", 11),
                          fg_color=C["muted"], hover_color=C["blue"],
                          command=lambda u=url: self._select_repo(u)).pack(side="right", padx=10)

    def _update_ui_graph(self, graph_data):
        self.graph_canvas.delete("all")
        self.graph_data_map.clear()
        try:
            cal   = graph_data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
            total = cal["totalContributions"]
            self.lbl_contributions.configure(text=f"{total} contribuições no último ano")
            weeks = cal["weeks"]

            sq_size  = 11
            gap      = 3
            canvas_w = self.graph_canvas.winfo_width()
            if canvas_w < 10:
                canvas_w = 750

            total_w = len(weeks) * (sq_size + gap)
            start_x = max((canvas_w - total_w) / 2, 10)
            start_y = 10

            is_dark = ctk.get_appearance_mode() == "Dark"
            c_empty = "#161b22" if is_dark else "#ebedf0"
            c1 = "#0e4429" if is_dark else "#9be9a8"
            c2 = "#006d32" if is_dark else "#40c463"
            c3 = "#26a641" if is_dark else "#30a14e"
            c4 = "#39d353" if is_dark else "#216e39"

            for col_idx, week in enumerate(weeks):
                x0 = start_x + col_idx * (sq_size + gap)
                x1 = x0 + sq_size
                for day in week["contributionDays"]:
                    dt      = datetime.datetime.strptime(day["date"], "%Y-%m-%d")
                    row_idx = (dt.weekday() + 1) % 7
                    y0      = start_y + row_idx * (sq_size + gap)
                    y1      = y0 + sq_size
                    count   = day["contributionCount"]
                    if count == 0:    color = c_empty
                    elif count <= 3:  color = c1
                    elif count <= 6:  color = c2
                    elif count <= 10: color = c3
                    else:             color = c4

                    rect_id = self.graph_canvas.create_rectangle(
                        x0, y0, x1, y1, fill=color, outline=color, width=0, tags="square")

                    txt_count = (f"{count} contribuições" if count != 1
                                 else "1 contribuição")
                    if count == 0:
                        txt_count = "Nenhuma contribuição"
                    br_date  = dt.strftime("%d/%m/%Y")
                    raw_date = dt.strftime("%Y-%m-%d")
                    self.graph_data_map[rect_id] = (f"{txt_count} em {br_date}", raw_date, count)

            self.graph_canvas.tag_bind("square", "<Enter>",   self._on_sq_enter)
            self.graph_canvas.tag_bind("square", "<Leave>",   self._on_sq_leave)
            self.graph_canvas.tag_bind("square", "<Motion>",  self._on_sq_motion)
            self.graph_canvas.tag_bind("square", "<Button-1>", self._on_sq_click)
        except Exception:
            pass

    def _on_sq_enter(self, event):
        item = self.graph_canvas.find_withtag("current")
        if item:
            data = self.graph_data_map.get(item[0])
            if data:
                self.tooltip.show(data[0], event.x_root, event.y_root)

    def _on_sq_leave(self, event):
        self.tooltip.hide()

    def _on_sq_motion(self, event):
        item = self.graph_canvas.find_withtag("current")
        if item:
            data = self.graph_data_map.get(item[0])
            if data and self.tooltip.tw:
                self.tooltip.tw.geometry(f"+{event.x_root + 15}+{event.y_root + 15}")

    def _on_sq_click(self, event):
        item = self.graph_canvas.find_withtag("current")
        if item:
            data = self.graph_data_map.get(item[0])
            if data and data[2] > 0:
                raw_date = data[1]
                br_date  = data[0].split(" em ")[1]
                login    = ""
                if os.path.exists(CACHE_PROFILE):
                    try:
                        with open(CACHE_PROFILE, "r", encoding="utf-8") as f:
                            login = json.load(f).get("login", "")
                    except Exception:
                        pass
                if login:
                    ContributionDetailsDialog(self.app, login, raw_date, br_date)

    def _select_repo(self, clone_url):
        self.app.switch_main_view("clone")
        self.app.clone_view.entry_url.delete(0, "end")
        self.app.clone_view.entry_url.insert(0, clone_url)


class ContributionDetailsDialog(ctk.CTkToplevel):
    def __init__(self, parent, login, raw_date, br_date):
        super().__init__(parent, fg_color=C["bg"])
        self.title(f"Detalhes - {br_date}")
        self.geometry("450x500")
        self.minsize(400, 400)
        self.transient(parent)
        self.grab_set()
        self.after(200, lambda: self.winfo_exists() and set_title_bar_color(self, C["bg"], C["text"]))

        self.login    = login
        self.raw_date = raw_date

        self.header_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0)
        self.header_frame.pack(fill="x")
        ctk.CTkLabel(self.header_frame, text=f"Atividade em {br_date}",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=C["text"]).pack(pady=15)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=15, pady=15)

        self.lbl_status = ctk.CTkLabel(self.scroll,
                                       text="Buscando detalhes na nuvem...",
                                       text_color=C["text_dim"])
        self.lbl_status.pack(pady=40)

        threading.Thread(target=self._fetch_details, daemon=True).start()

    def _fetch_details(self):
        from_dt = f"{self.raw_date}T00:00:00Z"
        to_dt   = f"{self.raw_date}T23:59:59Z"

        query = """
        query {
          user(login: "%s") {
            contributionsCollection(from: "%s", to: "%s") {
              commitContributionsByRepository {
                repository { nameWithOwner }
                contributions(first: 100) {
                  nodes { commitCount }
                }
              }
              issueContributions(first: 100) {
                nodes { issue { title, repository { nameWithOwner } } }
              }
              pullRequestContributions(first: 100) {
                nodes { pullRequest { title, repository { nameWithOwner } } }
              }
            }
          }
        }
        """ % (self.login, from_dt, to_dt)

        headers = {"Authorization": f"Bearer {cfg.GITHUB_TOKEN}",
                   "Accept": "application/vnd.github.v3+json"}
        try:
            resp = requests.post("https://api.github.com/graphql",
                                 json={"query": query}, headers=headers, timeout=15)
            if resp.status_code == 200:
                self.after(0, lambda: self._render_details(resp.json()))
            else:
                self.after(0, lambda: self.lbl_status.configure(text="❌ Erro ao buscar dados."))
        except Exception:
            self.after(0, lambda: self.lbl_status.configure(text="❌ Falha de conexão."))

    def _render_details(self, data):
        self.lbl_status.destroy()
        try:
            col             = data["data"]["user"]["contributionsCollection"]
            commits_by_repo = col["commitContributionsByRepository"]
            issues          = col["issueContributions"]["nodes"]
            prs             = col["pullRequestContributions"]["nodes"]
            has_data        = False

            if commits_by_repo:
                has_data = True
                ctk.CTkLabel(self.scroll, text="📝 Commits",
                             font=ctk.CTkFont("Segoe UI", 14, "bold"),
                             text_color=C["green"]).pack(anchor="w", pady=(0, 5), padx=5)
                for repo_group in commits_by_repo:
                    repo_name = repo_group["repository"]["nameWithOwner"]
                    count     = sum(n["commitCount"] for n in
                                    repo_group["contributions"]["nodes"])
                    txt  = f"{count} commit{'s' if count > 1 else ''} em {repo_name}"
                    card = ctk.CTkFrame(self.scroll, fg_color=C["card"], corner_radius=8,
                                        border_width=1, border_color=C["card_border"])
                    card.pack(fill="x", pady=4, padx=5)
                    ctk.CTkLabel(card, text=txt, font=ctk.CTkFont("Segoe UI", 12),
                                 text_color=C["text_dim"]).pack(anchor="w", padx=15, pady=10)
                ctk.CTkFrame(self.scroll, height=1, fg_color=C["card_border"]).pack(
                    fill="x", pady=15, padx=5)

            if issues:
                has_data = True
                ctk.CTkLabel(self.scroll, text="🐛 Issues Criadas",
                             font=ctk.CTkFont("Segoe UI", 14, "bold"),
                             text_color=C["red"]).pack(anchor="w", pady=(0, 5), padx=5)
                for issue in issues:
                    iss = issue["issue"]
                    txt = f"{iss['title']} ({iss['repository']['nameWithOwner']})"
                    card = ctk.CTkFrame(self.scroll, fg_color=C["card"], corner_radius=8,
                                        border_width=1, border_color=C["card_border"])
                    card.pack(fill="x", pady=4, padx=5)
                    ctk.CTkLabel(card, text=txt, font=ctk.CTkFont("Segoe UI", 12),
                                 text_color=C["text_dim"], wraplength=350,
                                 justify="left").pack(anchor="w", padx=15, pady=10)
                ctk.CTkFrame(self.scroll, height=1, fg_color=C["card_border"]).pack(
                    fill="x", pady=15, padx=5)

            if prs:
                has_data = True
                ctk.CTkLabel(self.scroll, text="🔄 Pull Requests",
                             font=ctk.CTkFont("Segoe UI", 14, "bold"),
                             text_color="#a371f7").pack(anchor="w", pady=(0, 5), padx=5)
                for pr in prs:
                    p   = pr["pullRequest"]
                    txt = f"{p['title']} ({p['repository']['nameWithOwner']})"
                    card = ctk.CTkFrame(self.scroll, fg_color=C["card"], corner_radius=8,
                                        border_width=1, border_color=C["card_border"])
                    card.pack(fill="x", pady=4, padx=5)
                    ctk.CTkLabel(card, text=txt, font=ctk.CTkFont("Segoe UI", 12),
                                 text_color=C["text_dim"], wraplength=350,
                                 justify="left").pack(anchor="w", padx=15, pady=10)
                ctk.CTkFrame(self.scroll, height=1, fg_color=C["card_border"]).pack(
                    fill="x", pady=15, padx=5)

            if not has_data:
                ctk.CTkLabel(self.scroll, text="Nenhum detalhe encontrado.",
                             text_color=C["text_dim"]).pack(pady=20)
        except Exception:
            ctk.CTkLabel(self.scroll, text="❌ Erro ao processar dados.",
                         text_color=C["red"]).pack(pady=20)
