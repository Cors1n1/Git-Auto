# git_auto

> Automação inteligente para versionamento e gerenciamento de releases Git.

## Sobre o Projeto

O **git_auto** é uma ferramenta de automação desenvolvida em Python que integra a API do Google Gemini para auxiliar no gerenciamento de fluxos de trabalho Git. A ferramenta simplifica a criação de repositórios, geração de documentação (README.md) via IA e monitoramento de histórico através de uma interface gráfica intuitiva.

- **Linguagem principal:** Python
- **IA Generativa:** Utiliza o modelo `gemini-3.1-flash-lite` para processamento de contexto e geração de documentação.
- **Interface:** Desenvolvida com `CustomTkinter` para uma experiência moderna e temática em modo escuro.

## Funcionalidades

- **Criação Assistida:** Criação de novos repositórios locais e remotos (GitHub) com um clique.
- **Documentação Automática:** Gera ou atualiza o `README.md` baseando-se nas mudanças reais do código (*git diff*).
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
   Certifique-se de que todas as dependências estão instaladas e execute o script:
   ```bash
   pip install -r requirements.txt
   python release.py
   ```

## Funcionalidades Recentes (v1.2)

- **Abas de Navegação:** Substituição do console único por um sistema de abas (Logs vs. Histórico de Pushes).
- **Histórico de Pushes:** Nova funcionalidade de leitura e listagem automática de logs remotos (`git log --remotes`) integrada à interface.
- **Confirmadores In-line:** Substituição de janelas modais nativas por painéis de confirmação integrados à UI, melhorando a experiência de fluxo.
- **Otimização de UI:** Refatoração da estrutura de frames para maior responsividade e organização dinâmica de elementos.

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma *issue* ou enviar um *pull request*.

## Licença

Distribuído sob a licença MIT.
