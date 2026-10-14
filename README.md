# Frontchat Empregos em Massa

Aplicativo desktop para **Windows 10/11** que localiza vagas reais, descobre
contatos públicos de recrutamento, valida e-mails e gerencia campanhas de
candidatura em massa com currículo — tudo com revisão e aprovação do usuário.

> **Funciona SEM chave de API.** Nenhuma fonte de vagas exige cadastro, token
> ou chave. Basta ter internet. Não há telas simuladas nem dados de exemplo
> apresentados como resultados reais.

---

## Índice

1. [O que o programa faz](#1-o-que-o-programa-faz)
2. [Funciona sem API (sem chave)](#2-funciona-sem-api-sem-chave)
3. [Requisitos](#3-requisitos)
4. [Instalar e usar (usuário final)](#4-instalar-e-usar-usuário-final)
5. [Rodar o programa a partir do código](#5-rodar-o-programa-a-partir-do-código)
6. [Editar o código-fonte](#6-editar-o-código-fonte)
7. [Rodar no VS Code](#7-rodar-no-vs-code)
8. [Empacotar (gerar .EXE e instalador)](#8-empacotar-gerar-exe-e-instalador)
9. [Configurar envio de e-mail (SMTP)](#9-configurar-envio-de-e-mail-smtp)
10. [Inteligência artificial (opcional)](#10-inteligência-artificial-opcional)
11. [Estrutura do projeto](#11-estrutura-do-projeto)
12. [Segurança e privacidade (LGPD)](#12-segurança-e-privacidade-lgpd)
13. [Limitações conhecidas](#13-limitações-conhecidas)

---

## 1. O que o programa faz

| Módulo | Situação |
|---|---|
| Pesquisa real de vagas | 7 fontes públicas gratuitas, **sem chave** (ver tabela na seção 2) |
| Extração de contatos | Varre páginas públicas de carreiras/contato; captura **e-mails**, **telefones** e **links reais de candidatura** (ATS: Gupy, Lever, Greenhouse…); decodifica ofuscação (`[at]`/`[dot]`, Cloudflare) |
| Validação de e-mails | Sintaxe, domínio, registros **MX** (com fallback de DNS público), deduplicação e classificação |
| Importação de currículo | PDF, DOCX e TXT |
| Personalização | Modelos com variáveis + IA opcional (nunca inventa qualificações) |
| Campanhas | Preparar em lote → **revisar** → enviar (SMTP autenticado, com confirmação real do provedor) |
| IA (opcional) | Compatível com OpenAI/Groq/OpenRouter/Ollama |
| Dashboard | Métricas reais calculadas do banco |
| Exportação | CSV e Excel (.xlsx) |
| Segurança | Senhas/tokens no **Windows Credential Manager** (keyring), nunca em texto puro |

---

## 2. Funciona sem API (sem chave)

Todas as fontes abaixo funcionam **automaticamente**, sem cadastro e sem chave.
O aplicativo **nunca** solicita API key.

| Fonte | Tipo | Foco |
|---|---|---|
| Remotive | API pública | Vagas remotas (internacional) |
| Arbeitnow | API pública | Vagas (foco Europa/remoto) |
| Jobicy | Endpoint público | Vagas remotas |
| Remote OK | Endpoint público | Vagas remotas |
| Himalayas | Endpoint público | Vagas remotas |
| Working Nomads | Endpoint público | Vagas remotas |
| We Work Remotely | Raspagem de RSS público | Vagas remotas |

Só é necessária **conexão com a internet**. A tela
**Configurações → Fontes de vagas** lista todas e confirma que nenhuma exige chave.

---

## 3. Requisitos

- Windows 10 ou 11 (64 bits)
- Para usar o `.EXE`/instalador: **nada precisa ser instalado**.
- Para compilar/rodar do código-fonte: **Python 3.10+** (testado no 3.12).

---

## 4. Instalar e usar (usuário final)

1. Execute `installer_output/FrontchatEmpregosEmMassa-Setup.exe`.
2. Siga o assistente (pode criar atalho na Área de Trabalho).
3. Abra pelo menu Iniciar ou pelo atalho criado.

Os dados ficam em:

```
%LOCALAPPDATA%\FrontchatEmpregosEmMassa\
```

(banco `jobhunter.db`, `logs\`, `curriculos\`, `exportacoes\`.)

---

## 5. Rodar o programa a partir do código

```bat
:: Cria o ambiente virtual, instala dependências e compila o EXE
build.bat

:: Rodar sem compilar
run.bat

:: Rodar os testes automatizados
run_tests.bat
```

Ou manualmente (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

---

## 6. Editar o código-fonte

O código fica em `jobhunter/`. Para alterar:

1. Abra a pasta do projeto no seu editor.
2. Edite os arquivos `.py` desejados (veja a seção 11 para o mapa).
3. Rode `run.bat` para testar (ou `.venv\Scripts\python.exe main.py`).
4. Antes de finalizar, rode `run_tests.bat` para garantir que nada quebrou.

Pontos de edição mais comuns:

| Quero mudar… | Arquivo |
|---|---|
| Cores / tema | `jobhunter/ui/theme.py` |
| Layout do menu lateral | `jobhunter/ui/main_window.py` |
| Uma tela específica | `jobhunter/ui/pages/<tela>.py` |
| Adicionar uma fonte de vagas | crie um arquivo em `jobhunter/search/` e registre em `jobhunter/search/manager.py` |
| Regras de validação de e-mail | `jobhunter/validation/` |
| Textos dos e-mails | `jobhunter/campaigns/templates.py` |
| Nome/versão do app | `jobhunter/__init__.py` |

---

## 7. Rodar no VS Code

1. Instale o [VS Code](https://code.visualstudio.com/).
2. Instale a extensão **Python** (Microsoft) — o VS Code sugere automaticamente
   ao abrir a pasta (há recomendações em `.vscode/extensions.json`).
3. Abra a pasta do projeto: **File → Open Folder…** → selecione a pasta do app.
4. Selecione o interpretador: **Ctrl+Shift+P → “Python: Select Interpreter”** →
   escolha o do ambiente virtual (`\.venv\Scripts\python.exe`).
   - Se o `.venv` ainda não existir, rode `build.bat` uma vez ou crie com
     `python -m venv .venv` e instale `requirements.txt`.
5. Pressione **F5** para executar/debugar. Já existem configurações prontas em
   `.vscode/launch.json`:
   - **“Frontchat (app)”** — abre o aplicativo.
   - **“Frontchat (testes)”** — roda a suíte de testes.
6. O terminal integrado já abre na pasta do projeto.

> Dica: no VS Code, use **Ctrl+`** para abrir o terminal e então
> `.venv\Scripts\python.exe main.py`.

---

## 8. Empacotar (gerar .EXE e instalador)

O empacotamento do Windows é feito em duas etapas:

**Etapa 1 — gerar o executável (PyInstaller):**

```bat
build.bat
```

Isso usa `jobhunter.spec` e gera `dist\FrontchatEmpregosEmMassa.exe`
(arquivo único, sem console).

Manualmente:

```powershell
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe -m PyInstaller jobhunter.spec --noconfirm --clean
```

**Etapa 2 — gerar o instalador (Inno Setup 6):**

1. Instale o Inno Setup 6.
2. Compile o script:

```powershell
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" "installer\FrontchatEmpregosEmMassa.iss"
```

Resultado: `installer_output\FrontchatEmpregosEmMassa-Setup.exe`.

O instalador cria atalhos no menu Iniciar e na Área de Trabalho e registra o
desinstalador.

---

## 9. Configurar envio de e-mail (SMTP)

O envio é **opcional** e só ocorre após você revisar e aprovar. Na tela
**Campanhas → Envio**:

- **Gmail**: usuário = seu e-mail; senha = **Senha de App** do Google.
- **Outlook/Office 365**: senha de app (ou SMTP AUTH habilitado).
- A senha é salva no **Windows Credential Manager**, nunca em texto puro.
- Há intervalo configurável entre envios, com **pausar / retomar / cancelar**.
- O status “Enviada” só é marcado após o servidor SMTP confirmar.

---

## 10. Inteligência artificial (opcional)

Na tela **Inteligência artificial** (totalmente opcional):

- OpenAI: `https://api.openai.com/v1`, modelo `gpt-4o-mini`, sua chave.
- Ollama local: `http://localhost:11434/v1`, modelo desejado, chave em branco.

A IA **não inventa** experiências, diplomas ou competências; ela só usa o que
está no currículo importado.

---

## 11. Estrutura do projeto

```
FrontchatEmpregosEmMassa/
├── jobhunter/               # código-fonte do aplicativo
│   ├── db/                  # banco SQLite, schema e repositórios
│   ├── search/              # fontes de vagas SEM chave (remotive, arbeitnow, feeds)
│   │   └── feeds.py         # Jobicy, Remote OK, Himalayas, Working Nomads, WWR
│   ├── contacts/            # descoberta de e-mails e formulários públicos
│   ├── validation/          # validação de e-mail (MX) e deduplicação
│   ├── resume/              # importação de currículo (PDF/DOCX)
│   ├── campaigns/           # modelos, provedores SMTP/OAuth e motor de campanha
│   ├── ai/                  # cliente de IA compatível com OpenAI (opcional)
│   ├── export/              # exportação CSV/Excel
│   ├── security/            # armazenamento seguro de credenciais
│   ├── ui/                  # interface (PySide6) com 10 telas
│   ├── stats.py             # métricas do dashboard
│   └── __main__.py          # ponto de entrada
├── tests/                   # testes automatizados
├── scripts/                 # geração de ícone e capturas
├── .vscode/                 # launch.json, settings.json, extensions.json
├── installer/               # script do Inno Setup
├── assets/icon.ico
├── main.py
├── jobhunter.spec           # especificação PyInstaller
├── build.bat / run.bat / run_tests.bat
└── requirements.txt
```

---

## 12. Segurança e privacidade (LGPD)

- Credenciais de envio guardadas no Windows Credential Manager.
- Coleta apenas de informações **públicas** (não acessa áreas privadas, não
  contorna login/CAPTCHA, não usa proxies para burlar bloqueios).
- Origem de cada contato coletado é registrada.
- Botão para **excluir permanentemente** todos os dados locais.
- O envio de currículos exige revisão e aprovação manual.

---

## 13. Limitações conhecidas

- As fontes gratuitas sem chave têm **foco em vagas remotas**; vagas
  presenciais brasileiras aparecem quando publicadas nessas fontes.
- A descoberta de contatos depende do que a empresa publica em seu site; se ela
  só aceita candidaturas por portal, o programa registra o **link do formulário
  real de candidatura** (ex.: `jobs.lever.co/...`, Gupy) em vez de inventar um e-mail.
- **Telefones** só aparecem quando publicados na página (ex.: `tel:` ou
  `(11) 91234-5678`). O programa nunca gera números.
- O filtro de **País** é tolerante: vagas remotas/globais não são descartadas só
  porque não citam o país — isso evita perder resultados válidos.
- “Encontrado e origem confirmada” significa que o endereço foi **publicado em
  fonte verificável** e o domínio possui MX — não que a caixa postal exista.
- Envio por OAuth2 (Gmail/Microsoft) exige que cada usuário crie seu próprio
  cliente OAuth (infraestrutura pronta em `campaigns/oauth.py`); o caminho padrão
  é a **senha de app** SMTP.

Detalhes completos de testes e limitações: veja `RELATORIO.md`.
