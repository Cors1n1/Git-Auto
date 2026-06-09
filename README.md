# git_auto
> Automação inteligente para versionamento e gerenciamento de releases Git.

## Sobre o Projeto

O **git_auto** é uma ferramenta de automação desenvolvida em Python que integra a API do Google Gemini para auxiliar no gerenciamento de fluxos de trabalho Git. A ferramenta simplifica a criação de repositórios, geração de documentação (README.md) via IA e monitoramento de histórico através de uma interface gráfica intuitiva.

- **Linguagem principal:** Python
- **IA Generativa:** Utiliza o modelo `gemini-3.1-flash-lite` para processamento de contexto e geração de documentação.
- **Interface:** Desenvolvida com `CustomTkinter` para uma experiência moderna e temática em modo escuro.

## Funcionalidades

- **Criação Assistida:** Criação de novos repositórios locais e remotos (GitHub) com um clique.
- **Documentação Automática:** Gera ou atualiza o `README.md` baseando-se nas mudanças reais do código, suportando criação inicial ou adição incremental de logs de atualização.
- **Interface de Abas:** Navegação integrada entre console de logs e histórico de pushes locais.
- **Rastreabilidade:** Histórico persistente e visualização de logs de commits remotos.
- **Workflow Integrado:** Automação de `add`, `commit` (com mensagens sugeridas) e `push` com confirmações in-line na UI.
- **System Tray:** Suporte para minimização na bandeja do sistema para monitoramento contínuo.

## Estrutura do Projeto

```
.
├── .env              # Variáveis de ambiente (API keys e tokens)
├── .gitignore        # Definição de arquivos ignorados pelo Git
├── history.json      # Registro de logs de execução e status dos repositórios
├── release.py        # Script principal com a lógica da GUI, threads e integração Git/IA
└── requirements.txt  # Dependências do projeto
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

2. **Configuração:**
   Crie um arquivo `.env` na raiz do projeto com as seguintes chaves:
   - `GEMINI_API_KEY`: Sua chave da API do Google Gemini.
   - `GITHUB_TOKEN`: Seu Personal Access Token do GitHub.
   - `GITHUB_USERNAME`: Seu nome de usuário no GitHub.

3. **Execução:**
   ```bash
   pip install -r requirements.txt
   python release.py
   ```

## 📋 Histórico de Atualizações

### 🔄 Atualização (22/05/2024)
- Refatoração do design dos cards de histórico: mudança para layout vertical com separação clara de blocos (Header, Status e Ação).
- Inclusão de botão de remoção rápida na interface de histórico.
- Otimização do fluxo da IA para documentação: o sistema agora diferencia a criação de um README do zero da adição de logs de alterações (*Changelog*), evitando redundância e processamento desnecessário ao atualizar a documentação.

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma *issue* ou enviar um *pull request*.

## Licença

Distribuído sob a licença MIT.

### 🔄 Atualização (08/06/2026)
- Implementado sistema de visualização expandível no histórico de projetos, exibindo metadados do commit (hash, autor, mensagem) e um log detalhado de arquivos alterados (`git show --name-status`).
- Refatorado o fluxo de commit para utilizar mensagens dinâmicas geradas pela IA, eliminando mensagens estáticas em favor de resumos contextuais das mudanças realizadas.
- Ajustada a persistência de mensagens de commit através de arquivo temporário (`.git/AUTO_MSG`) para garantir a integridade dos caracteres especiais durante a execução dos comandos git.
- Otimizada a integração entre os métodos de geração de README e o workflow de deploy, garantindo que o resumo da IA seja devidamente propagado para a mensagem do commit.

### 🔄 Atualização (08/06/2026)
- Refatorada exibição de detalhes dos commits para separar mensagem e lista de arquivos.
- Implementado CTkTextbox dinâmico para melhor legibilidade das mensagens de commit.
- Otimizado o parsing dos comandos Git via delimitador customizado.

### 🔄 Atualização (08/06/2026)
- Implementada interface para gerenciamento de credenciais (.env) dentro da aplicação.
- Adicionada janela de configurações com suporte a edição e salvamento de chaves via UI.
- Otimizada a integração com o GitHub para inclusão automática de autenticação nas URLs remotas.

### 🔄 Atualização (08/06/2026)
- Removida interrupção forçada na inicialização por falta de credenciais.
- Implementado prompt automático de configuração inicial via interface.
- Otimizada a inicialização da API do Gemini.

### 🔄 Atualização (08/06/2026)
- Implementado sistema de temas personalizados (Dracula, Nord, Matrix, Cyberpunk e Light/Dark).
- Adicionada seletor de tema e cor de destaque no menu de configurações com persistência via .env.
- Refinado processamento de nomes de projetos com sanitização de caracteres especiais e acentos.

### 🔄 Atualização (08/06/2026)
- Implementado auto-instalador de dependências em `release.py`.
- Removido arquivo `requirements.txt` em favor da instalação dinâmica.
- Atualizado `.gitignore` para remover rastreio de arquivos JSON.

### 🔄 Atualização (08/06/2026)
- Adicionados temas "Tokyo Night" e "Catppuccin" com suporte a personalização da barra de título.
- Implementado sistema de ajuda com tutoriais integrados para configurações de API e GitHub.
- Refinamento visual da interface com novos cantos arredondados e linha de destaque superior.

### 🔄 Atualização (08/06/2026)
- Implementada interface "Central de Clonagem" com suporte a via URL e API do GitHub.
- Adicionada funcionalidade de leitura automática de README ou sugestão de setup após o clone.
- Adicionado sistema de navegação por abas (Gerenciar Repositório vs. Clonagem) na interface principal.

### 🔄 Atualização (08/06/2026)
- Ajustado o grid layout do main_frame para corrigir o posicionamento do container.
- Atualizado o registro de histórico com o timestamp da última execução.

### 🔄 Atualização (08/06/2026)
- Implementada sanitização de URL para remover âncoras e parâmetros de consulta.
- Atualizado registro de histórico de execução no arquivo de logs.

### 🔄 Atualização (08/06/2026)
- Implementada interface visual para revisão e edição manual de mensagens de commit via IA.
- Adicionada integração de confirmação de commit com pré-visualização no fluxo de automação.

### 🔄 Atualização (08/06/2026)
- Implementado gerador visual de `.gitignore` com suporte a múltiplos templates tecnológicos.
- Adicionada integração na interface para seleção e criação personalizada de arquivos de exclusão.
- Atualizada a estrutura de ignorados padrão para maior abrangência de ambientes e SOs.

### 🔄 Atualização (08/06/2026)
- Implementada nova Dashboard com visualização de perfil GitHub e estatísticas de repositório.
- Adicionada listagem dinâmica dos últimos projetos atualizados com atalho para clonagem.
- Refatorado sistema de navegação da interface para suporte a múltiplas views (Push, Clone, Dashboard).

### 🔄 Atualização (08/06/2026)
- Implementado o novo módulo `BranchManagerView` para criação, exclusão e troca de branches.
- Adicionado sistema de "Auto-Save" preventivo ao alternar entre branches via commit automático.
- Integrada visualização do status da branch atual na barra de navegação principal da aplicação.

### 🔄 Atualização (08/06/2026)
- Implementada a feature "Máquina do Tempo" para resetar repositórios ao último commit.
- Adicionada interface de aviso crítico para confirmação segura de descarte de alterações.
- Migrada a branch principal de "master" para "main" no histórico de registros.

### 🔄 Atualização (08/06/2026)
- Refatorada exibição das informações de commit no dashboard.
- Adicionada separação visual entre metadados e mensagem do commit.

### 🔄 Atualização (08/06/2026)
- Implementada classe `DiffViewerDialog` para visualização comparativa de alterações (side-by-side).
- Adicionada funcionalidade de inspeção de diff via interface gráfica com scroll sincronizado.

### 🔄 Atualização (08/06/2026)
- Implementado o ReleaseManagerDialog para automação de tags e lançamentos via GitHub.
- Integrada IA (Gemini) para geração automática de notas de versão baseadas no histórico de commits.
- Adicionado botão de atalho "Lançar Versão" na interface principal para acesso rápido ao gerenciador.

### 🔄 Atualização (08/06/2026)
- Atualizado motor de IA para gemini-3.5-flash.
- Refatorada estrutura de prompt e automação de títulos para Release Notes.

### 🔄 Atualização (08/06/2026)
- Adicionada barra de progresso indeterminada na interface de geração de notas.
- Atualizado feedback visual e estados do botão durante o processamento da IA.

### 🔄 Atualização (09/06/2026)
- Implementada nova aba de sincronização com funcionalidade de Auto-save pré-Pull.
- Adicionado seletor de arquivos na interface de visualização de diferenças (Diff Viewer).
- Adicionada opção de encerramento da aplicação no menu lateral.
Isso é um teste de Sincronização!

