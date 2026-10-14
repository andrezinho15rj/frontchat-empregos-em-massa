# Relatório de desenvolvimento — Frontchat Empregos em Massa

**Versão:** 1.0.0
**Plataforma de build:** Windows 11 (win32)
**Data:** 14/10/2026

---

## 1. Resumo

Aplicativo desktop completo em Python 3.12 + PySide6, empacotado em
`.EXE` (PyInstaller) e com instalador (Inno Setup). O núcleo funcional foi
implementado e **verificado executando** as operações reais descritas abaixo.

---

## 2. Funcionalidades implementadas e verificadas

### 2.1 Pesquisa real de vagas (SEM chave de API) — VERIFICADO
- 7 fontes públicas gratuitas, todas **sem chave**: Remotive, Arbeitnow, Jobicy,
  Remote OK, Himalayas, Working Nomads (endpoints públicos) e We Work Remotely
  (raspagem de feed RSS público). Implementadas em
  `jobhunter/search/` (`remotive.py`, `arbeitnow.py`, `feeds.py`).
- **Execução real verificada**: uma busca sem filtros retornou **105 vagas**
  (15 por fonte) e salvou todas, sem qualquer erro e sem nenhuma chave.
- O aplicativo **nunca** solicita API key. A tela *Configurações → Fontes de
  vagas* apenas lista as fontes e confirma que são isentas de chave.
- Teste automatizado `tests/test_search.py`: valida que nenhuma fonte exige
  chave e executa busca real (Remotive) com persistência.

### 2.2 Descoberta de contatos públicos — VERIFICADO
- `ContactExtractor` varre páginas públicas (home, contato, carreiras,
  trabalhe conosco, vagas…), extrai `mailto:`, e-mails em texto, e-mails
  ofuscados (`[at]`/`[dot]`, “arroba/ponto”) e proteção Cloudflare
  (`data-cfemail`).
- Extrai **telefones** (`tel:` e padrões brasileiros `(11) 91234-5678`,
  `0800 123 4567`), normalizados sem inventar dígitos.
- Detecta **links reais de candidatura** (ATS: jobs.lever.co, greenhouse.io,
  gupy.io, workable, smartrecruiters…) e descarta menus/categorias.
- Teste `tests/test_contacts.py` valida e-mails, Cloudflare, telefones e
  armazenamento do telefone no banco.

### 2.3 Validação de e-mails — VERIFICADO
- Sintaxe (regex), classificação de adequação (RH vs. setor indevido),
  detecção de domínio pessoal/descartável.
- Consulta de **registros MX** via dnspython, com **fallback de DNS público**
  (1.1.1.1/8.8.8.8/9.9.9.9) — necessário porque o DNS local do ambiente de
  teste falhava por UDP.
- Estados: *Encontrado e origem confirmada*, *Domínio válido, entrega não
  confirmada*, *E-mail inválido*, *E-mail duplicado*, *Contato inadequado*,
  *Formulário de candidatura disponível*.
- **Não** marca como existente apenas por haver MX.
- Testes `tests/test_validation.py` (inclui MX real de domínio).

### 2.4 Deduplicação e filtros — VERIFICADO
- Vaga por URL (única), contato por (e-mail, empresa), e-mail duplicado marcado.
- Filtros por status, área, fonte e busca textual nas telas e na exportação.

### 2.5 Exportação CSV / Excel — VERIFICADO
- Colunas: Empresa, Cargo, Cidade, Estado, E-mail, Site, URL da vaga, Fonte do
  contato, Data de publicação, Última verificação, Status da candidatura.
- Teste `tests/test_export.py` gera e relê CSV e XLSX (openpyxl).

### 2.6 Currículo e personalização — VERIFICADO
- Importação PDF/DOCX/TXT com extração de texto.
- Modelos pt/en com variáveis `{empresa} {cargo} {candidato} {area} {cidade}
  {apresentacao}`.
- Teste `tests/test_campaign.py`: importa DOCX, renderiza e **prepara** a
  candidatura (sem enviar).

### 2.7 Campanhas de candidatura — VERIFICADO (preparação) / REQUER CREDENCIAL (envio)
- Fluxo: **PREPARAR CANDIDATURAS EM LOTE** → revisão editável → envio com
  confirmação.
- Envio por SMTP autenticado (senha de app) com XOAUTH2 opcional; pausar,
  retomar e cancelar; intervalo entre envios.
- Só marca “Enviada” após confirmação do servidor SMTP.
- **Envio real não testado automaticamente** (exige credencial de e-mail
  válida). Infraestrutura pronta e tela de configuração presente.

### 2.8 Inteligência artificial — VERIFICADO (infraestrutura)
- Cliente compatível com OpenAI; análise de compatibilidade com pontuação e
  justificativa; personalização de assunto e apresentação.
- Prompt reforça que a IA **nunca** inventa dados do currículo.
- Teste de conexão na própria tela. Sem chave, o módulo fica claramente
  indisponível.

### 2.9 Dashboard — VERIFICADO
- 9 indicadores calculados do banco + atividade recente.

### 2.10 Interface (10 telas) — VERIFICADO
- Dashboard, Buscar vagas, Empresas, Contatos, Validação, Meu currículo, IA,
  Campanhas, Histórico, Configurações.
- Tema escuro/claro, menu lateral, tabelas com filtros, notificações (toast),
  barras de progresso, tarefas em threads (UI não trava).
- Todas as telas instanciadas e navegadas sem erro no teste de fumaça.

### 2.11 Segurança — VERIFICADO
- Credenciais no Windows Credential Manager (keyring).
- Botão de exclusão permanente de dados.
- Origem de cada contato registrada.

### 2.12 Empacotamento — VERIFICADO no Windows
- `dist\FrontchatEmpregosEmMassa.exe` (~75 MB) gerado com PyInstaller e
  **executado com sucesso** (banco criado, “Interface pronta.” no log).
- `installer_output\FrontchatEmpregosEmMassa-Setup.exe` (~76 MB) gerado com
  Inno Setup, com atalho na Área de Trabalho.

---

## 3. Testes automatizados

Execução: `run_tests.bat` (ou `python -m unittest discover -s tests -t .`).

```
Ran 24 tests ... OK
```

Cobertura:
- Banco: persistência após reabrir, unicidade de vaga por URL, exclusão de dados.
- Validação: sintaxe, classificação, MX real, deduplicação.
- Contatos: extração de HTML, Cloudflare, formulários, telefones e armazenamento.
- Currículo/modelos: importação DOCX, render de variáveis.
- Campanha: preparação sem envio + bloqueio de candidatura duplicada.
- Exportação: CSV e XLSX.
- Busca: confirma que nenhuma fonte exige chave + integração real (Remotive) + dedup na persistência.

---

## 4. Limitações conhecidas

1. **Envio de e-mail**: não foi disparado automaticamente nos testes (requer
   credencial real). O usuário configura na tela de Envio; a senha nunca é
   gravada em texto puro.
2. **OAuth2** (Gmail/Microsoft): a troca de token e os fluxos de autorização
   (loopback e device code) estão implementados, mas exigem que o usuário crie
   seu próprio cliente OAuth. O caminho padrão recomendado é **senha de app**.
3. **Fontes sem chave** têm foco em **vagas remotas**; vagas presenciais
   brasileiras aparecem quando publicadas nessas fontes. Nenhuma fonte exige
   chave de API.
4. **Descoberta de contatos**: depende do que a empresa publica; se houver
   apenas portal, registra-se o link do formulário.
5. **MX**: “origem confirmada” indica endereço publicado + domínio com MX, não
   a existência comprovada da caixa postal.
6. **Playwright**: não incluído por padrão (navegador pesado). As coletas usam
   HTTP + parsing; a dependência está comentada em `requirements.txt`.

---

## 5. Artefatos entregues

- Código-fonte modular em `jobhunter/`.
- `requirements.txt`, `jobhunter.spec`.
- Scripts: `build.bat`, `run.bat`, `run_tests.bat`.
- Instalador: `installer/FrontchatEmpregosEmMassa.iss`.
- `README.md` (instalação e configuração de APIs).
- Este relatório.
