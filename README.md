# git_auto
> Automação inteligente para versionamento e gerenciamento de releases Git.

## Sobre o Projeto

O **git_auto** é uma ferramenta de automação desenvolvida em Python que integra a API do Google Gemini para auxiliar no gerenciamento de fluxos de trabalho Git. A ferramenta simplifica a criação de repositórios, geração de documentação (README.md) via IA e monitoramento de histórico através de uma interface gráfica intuitiva.

- **Linguagem principal:** Python
- **IA Generativa:** Utiliza modelos do Google Gemini para processamento de contexto e geração de documentação.
- **Interface:** Desenvolvida com `CustomTkinter` para uma experiência moderna e temática em modo escuro.

## Funcionalidades

- **Criação Assistida:** Criação de novos repositórios locais e remotos (GitHub) com um clique.
- **Documentação Automática:** Gera ou atualiza o `README.md` baseando-se nas mudanças reais do código.
- **Interface de Abas:** Navegação integrada entre console de logs, histórico de pushes, dashboard e gerenciamento de issues.
- **Rastreabilidade:** Histórico persistente e visualização de logs de commits remotos.
- **Workflow Integrado:** Automação de `add`, `commit` e `push` com revisão via IA.
- **System Tray:** Suporte para minimização na bandeja do sistema para monitoramento contínuo.

## Estrutura do Projeto

```
.
├── data/             # Armazenamento de caches, logs e dados locais
├── .env              # Variáveis de ambiente e tokens de API
├── .gitignore        # Definição de arquivos ignorados pelo Git
├── README.md         # Documentação atualizada do projeto
├── emojis.txt        # Tabela de ícones e recursos visuais da GUI
└── release.py        # Script principal: lógica da GUI, threads e auto-configuração
```

## Dependências

```
google-generativeai==0.4.1
python-dotenv==1.0.1
requests==2.31.0
customtkinter==5.2.2
pystray==0.19.0
Pillow==9.4.0
```

## Como Usar

1. **Clonar o repositório:**
   ```bash
   git clone https://github.com/Cors1n1/git_auto.git
   cd git_auto
   ```

2. **Execução:**
   ```bash
   python release.py
   ```

**Configuração Automática:** O projeto possui mecanismos de auto-instalação e auto-configuração. Ao executar o script `release.py` pela primeira vez, o sistema instalará automaticamente as dependências necessárias e solicitará os tokens de API (como o `GEMINI_API_KEY`) via interface gráfica. Não é necessário instalar bibliotecas manualmente ou editar o arquivo `.env` de forma externa.

## 📋 Histórico de Atualizações

### 🔄 Atualização (22/05/2024)
- Refatoração do design dos cards de histórico: mudança para layout vertical com separação clara de blocos (Header, Status e Ação).
- Inclusão de botão de remoção rápida na interface de histórico.

### 🔄 Atualização (08/06/2026)
- Implementado sistema de visualização expandível no histórico de projetos e refatorado o fluxo de commit para utilizar mensagens dinâmicas via IA.
- Ajustada a persistência de mensagens através de `.git/AUTO_MSG`.

### 🔄 Atualização (08/06/2026)
- Implementada interface para gerenciamento de credenciais (.env) e configurações via UI.

### 🔄 Atualização (08/06/2026)
- Implementado sistema de temas (Dracula, Nord, Matrix, etc) com persistência via .env.

### 🔄 Atualização (08/06/2026)
- Implementado auto-instalador de dependências em `release.py`.

### 🔄 Atualização (08/06/2026)
- Implementada interface de "Central de Clonagem" e navegação por abas.

### 🔄 Atualização (08/06/2026)
- Implementado `BranchManagerView` para controle de branches e "Máquina do Tempo" para resetar estados.

### 🔄 Atualização (08/06/2026)
- Implementado `DiffViewerDialog` para visualização comparativa (side-by-side) de alterações.

### 🔄 Atualização (08/06/2026)
- Implementado `ReleaseManagerDialog` para automação de tags e lançamentos no GitHub.

### 🔄 Atualização (09/06/2026)
- Adicionado suporte a gerenciamento de colaboradores e gráfico de contribuições.
- Implementado módulo de gerenciamento de Tarefas (Issues) com sugestões do Gemini AI.

### 🔄 Atualização (09/06/2026)
- Limpeza de código, centralização de dados no diretório /data e suporte a tray icon.

### 🔄 Atualização (09/06/2026)
- Simplificação das labels da interface: remoção de emojis redundantes para um visual mais limpo e profissional.
- Otimização do sistema de bandeja (System Tray) para gerenciamento de estados da janela principal.
