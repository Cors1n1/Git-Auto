"""
dialogs/readme_dialog.py
Diálogo de visão geral / README de um projeto.
"""
import os
import customtkinter as ctk
from app.config import C


class ProjectReadmeDialog(ctk.CTkToplevel):
    def __init__(self, parent, project_path):
        super().__init__(parent)
        self.title("Visão Geral do Projeto")
        self.geometry("800x600")
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=C["bg"])

        ctk.CTkLabel(self, text=f"📦 {os.path.basename(project_path)}",
                     font=ctk.CTkFont("Segoe UI", 20, "bold"),
                     text_color=C["text"]).pack(pady=(20, 10), padx=20, anchor="w")

        self.textbox = ctk.CTkTextbox(self, font=ctk.CTkFont("Consolas", 13),
                                       fg_color=C["card"], text_color=C["text"],
                                       border_color=C["card_border"], border_width=1,
                                       corner_radius=10, wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        content = self._get_or_generate_readme(project_path)
        self.textbox.insert("0.0", content)
        self.textbox.configure(state="disabled")

        ctk.CTkButton(self, text="Entendido!", height=40,
                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      fg_color=C["blue"], hover_color=C["blue_dark"],
                      command=self.destroy).pack(pady=(0, 20), padx=20)

    def _get_or_generate_readme(self, path):
        for name in ["README.md", "README.txt", "readme.md", "Readme.md"]:
            p = os.path.join(path, name)
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        content = f.read()
                        return f"--- 📄 {name} encontrado ---\n\n{content}"
                except Exception:
                    pass

        files = os.listdir(path) if os.path.exists(path) else []
        summary = "Nenhum arquivo README encontrado no repositório.\n\n"
        summary += "--- 🤖 ANÁLISE AUTOMÁTICA DO PROJETO ---\n"

        if ("requirements.txt" in files or "setup.py" in files or "Pipfile" in files
                or "release.py" in files or any(f.endswith(".py") for f in files)):
            summary += "\n🐍 PROJETO PYTHON DETECTADO.\n\n"
            summary += "Passo a passo genérico para rodar:\n"
            summary += "1. Abra o terminal na pasta do projeto.\n"
            summary += "2. Crie um ambiente virtual (recomendado):\n"
            summary += "   python -m venv venv\n"
            summary += "3. Ative o ambiente:\n"
            summary += "   Windows: venv\\Scripts\\activate\n"
            summary += "   Linux/Mac: source venv/bin/activate\n"
            if "requirements.txt" in files:
                summary += "4. Instale as dependências:\n"
                summary += "   pip install -r requirements.txt\n"
            summary += "5. Execute o script principal (ex: python main.py)\n"
        elif "package.json" in files:
            summary += "\n📦 PROJETO NODE.JS / JAVASCRIPT DETECTADO.\n\n"
            summary += "1. Abra o terminal na pasta do projeto.\n"
            summary += "2. Instale as dependências:\n   npm install   (ou yarn install)\n"
            summary += "3. Inicie o projeto:\n   npm start     (ou npm run dev)\n"
        elif "pom.xml" in files or "build.gradle" in files:
            summary += "\n☕ PROJETO JAVA DETECTADO.\n\n"
            if "pom.xml" in files:
                summary += "Este projeto usa Maven. Execute:\nmvn clean install\n"
            else:
                summary += "Este projeto usa Gradle. Execute:\ngradle build\n"
        else:
            summary += "\n🔍 PROJETO GENÉRICO.\n\nNão foi possível identificar um ecossistema específico.\n"

        return summary
