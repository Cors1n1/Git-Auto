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
- **Integração VSCode:** Abertura rápida do ambiente de desenvolvimento diretamente pelo diretório do projeto.
- **Gestão Gitignore:** Gerador inteligente com suporte a múltiplos templates e integração automática.
- **Segurança:** Módulo de limpeza automática para remoção de arquivos sensíveis e credenciais.

## Estrutura do Projeto

```
.
├── app
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   ├── history.py
│   └── theme.py
├── data
├── dialogs
│   ├── __init__.py
│   ├── collaborators.py
│   ├── diff_viewer.py
│   ├── gitignore_dialog.py
│   ├── history_dialog.py
│   ├── new_project.py
│   ├── readme_dialog.py
│   ├── release_manager.py
│   ├── settings.py
│   └── time_machine.py
├── views
│   ├── __init__.py
│   ├── branch_view.py
│   ├── clone_view.py
│   ├── dashboard_view.py
│   ├── issues_view.py
│   └── security_view.py
├── widgets
│   ├── __init__.py
│   └── tooltip.py
├── .env
├── .gitignore
├── Git Auto.lnk
├── README.md
└── main.py
```

## Dependências

```
customtkinter
google-generativeai
python-dotenv
requests
pystray
Pillow
```

## Como Usar

1. **Clonar o repositório:**
   ```bash
   git clone https://github.com/Cors1n1/git_auto.git
   cd git_auto
   ```

2. **Execução:**
   - Execute `main.py` diretamente ou utilize o atalho `Git Auto.lnk`.

**Configuração Automática:** O projeto possui mecanismos de auto-instalação e auto-configuração. Ao executar o script pela primeira vez, as dependências serão instaladas automaticamente e a interface solicitará os tokens necessários. A instalação e configuração são **AUTOMÁTICAS**.

## 📋 Histórico de Atualizações

### 🔄 Atualização (22/05/2024)
- Refatoração do design dos cards de histórico: mudança para layout vertical com separação clara de blocos (Header, Status e Ação).
- Inclusão de botão de remoção rápida na interface de histórico.

### 🔄 Atualização (08/06/2026)
- Implementado sistema de visualização expandível no histórico de projetos e refatorado o fluxo de commit para utilizar mensagens dinâmicas via IA.
- Ajustada a persistência de mensagens através de `.git/AUTO_MSG`.
- Implementada interface para gerenciamento de credenciais (.env) e configurações via UI.
- Implementado sistema de temas (Dracula, Nord, Matrix, etc) com persistência via .env.
- Implementado auto-instalador de dependências.
- Implementada interface de "Central de Clonagem" e navegação por abas.
- Implementado `BranchManagerView` para controle de branches e "Máquina do Tempo" para resetar estados.
- Implementado `DiffViewerDialog` para visualização comparativa (side-by-side) de alterações.

### 🔄 Atualização (10/06/2026)
- Adicionado suporte a `AppUserModelID` no Windows para correção do ícone da aplicação na barra de tarefas.

### 🔄 Atualização (12/06/2026)
- **Segurança:** Adicionado `SecurityView` para limpeza de arquivos sensíveis e tokens.
- **Network:** Implementado DNS Monkey Patch para bypass de bloqueios de ISP em conexões com a API do GitHub.
- **IA:** Migração para o endpoint `gemini-3.1-flash-lite` com sistema de retry robusto para lidar com Rate Limits (429).
- **Gitignore:** Adicionadas regras automáticas para bloqueio de arquivos de credenciais e chaves (.pem, .key, etc).
- **Performance:** Otimização na inserção de logs no console e refatoração do layout dos cards de workspace.
