"""
app/config.py
Variáveis globais, constantes de ambiente e paleta de cores centralizada.
"""
import os
import json
import customtkinter as ctk
import google.generativeai as genai
from dotenv import load_dotenv

# ── Raiz do projeto (pai da pasta app/) ───────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=True)

# ── Credenciais e tema ─────────────────────────────────────────────────────────
APP_THEME       = os.getenv("APP_THEME", "Dark")
APP_COLOR       = os.getenv("APP_COLOR", "Azul")
GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")

# ── Caminhos de dados ──────────────────────────────────────────────────────────
DATA_DIR      = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

HISTORY_FILE  = os.path.join(DATA_DIR, "history.json")
CACHE_PROFILE = os.path.join(DATA_DIR, "profile_cache.json")
CACHE_REPOS   = os.path.join(DATA_DIR, "repos_cache.json")
CACHE_AVATAR  = os.path.join(DATA_DIR, "avatar_cache.png")
CACHE_EVENTS  = os.path.join(DATA_DIR, "events_cache.json")
CACHE_GRAPH   = os.path.join(DATA_DIR, "graph_cache.json")

# ── Modelo de IA ───────────────────────────────────────────────────────────────
model = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-3.1-flash-lite')

ctk.set_default_color_theme("blue")

# ── Paleta de cores (preenchida por app/theme.py ao chamar update_palette) ────
C: dict = {}
