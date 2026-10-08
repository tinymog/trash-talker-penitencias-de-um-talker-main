# Trash Talker

Companheiro de conversa com IA para quem tem dificuldade de socialização:
um espaço para desabafar, ensaiar o que dizer e ganhar confiança para
conversar com pessoas de verdade. Proposta completa em
[docs/proposta-do-site.md](docs/proposta-do-site.md).

**Stack:** Python 3.10+ (Flask, SQL cru com `psycopg2`, sem ORM) ·
PostgreSQL (local ou Neon) · HTML/CSS/JavaScript puro, sem etapa de build ·
Google Gemini (texto e voz) · testes com pytest e Behave (Gherkin pt-BR).

## Funcionalidades

- Cadastro com senha forte e confirmação de 18+ e do uso da IA; login por
  sessão (cookie `httponly`); recuperação de senha por e-mail.
- Autenticação em dois fatores opcional (Google Authenticator) com códigos
  de recuperação - [docs/2fa.md](docs/2fa.md).
- Conversas salvas com duas personalidades (TrashTalker e MathIAs) e dois
  níveis de esforço; o MathIAs passa textões para o TrashTalker; parar a
  resposta desfaz o envio; título automático; renomear e excluir.
- Ditado por voz (navegador) e "ouvir" as respostas (Gemini TTS, com a voz
  do navegador como reserva).
- Perfil (avatar, apelido, pronome, interesses) que a IA usa para
  personalizar a conversa.
- LGPD: aceite versionado dos termos, exportação dos dados em JSON e
  exclusão da conta.

## Documentação

| Para | Leia |
|---|---|
| Usar o sistema | [Manual do usuário](docs/manual-do-usuario.md) |
| Entender a arquitetura, a API e manter | [Manual técnico](docs/manual-tecnico.md) |
| Requisitos e regras de negócio | [docs/requisitos.md](docs/requisitos.md) · [casos de uso](docs/casos-de-uso.md) |
| Como cada requisito foi provado | [Matriz de rastreabilidade](docs/rastreabilidade.md) · [evidências](docs/evidencias/README.md) |
| Banco de dados (DER, dicionário) | [docs/banco-de-dados.md](docs/banco-de-dados.md) |
| Segurança e qualidade | [docs/seguranca.md](docs/seguranca.md) · [docs/qualidade.md](docs/qualidade.md) |
| Processo, decisões e riscos | [docs/processo.md](docs/processo.md) |
| Material do TCC (diagnóstico, checklist, banca, demo) | [docs/tcc/README.md](docs/tcc/README.md) |

## Estrutura

```
app.py                    # ponto de entrada (python app.py / Vercel)
backend/
  factory.py              # cria o app: rotas, páginas, CSP, origem, erros em JSON
  db.py                   # pool de conexões + query()/execute()
  auth.py                 # senha, sessão, tokens de reset, limite de tentativas
  two_factor.py           # regras do 2FA (TOTP + códigos de recuperação)
  validation.py           # leitura defensiva do corpo JSON
  ai.py                   # Gemini: resposta de texto e áudio
  personalities.py        # TrashTalker e MathIAs (prompts e regra de "preguiça")
  email_utils.py          # e-mail de redefinição (SMTP)
  avatars.py              # avatares ilustrados disponíveis
  routes/                 # auth_api, chats_api, account_api, two_factor_api
  schema.sql              # esquema do banco (idempotente)
public/                   # páginas HTML, css/app.css, js/*.js, imagens
tests/                    # testes de API (pytest)
features/                 # cenários de comportamento (Behave, pt-BR)
e2e/                      # testes de interface no navegador (Playwright)
tools/                    # conta demo, avaliação da IA, diagnósticos
docs/                     # manuais, requisitos, banco, segurança, testes, evidências
  tcc/                    # material do TCC (projeto, banca, apresentação, demo)
```

## Como rodar

### 1. Dependências

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
python -m pip install -r requirements.txt          # só a aplicação
python -m pip install -r requirements-dev.txt      # + pytest, behave, pyflakes
```

### 2. Configuração

```bash
cp .env.example .env               # Windows: copy .env.example .env
```

Preencha pelo menos `DATABASE_URL`. Cada variável está explicada no
próprio [.env.example](.env.example): `GEMINI_API_KEY` (respostas da IA),
`TOTP_ENCRYPTION_KEY` (2FA), `FRONTEND_ORIGIN`, `SMTP_*` (e-mail),
`FLASK_ENV`, `HOST`/`PORT`/`FLASK_DEBUG`.

> ⚠️ Nunca cole uma connection string real em arquivo versionado. O
> `.env` está no `.gitignore`.

### 3. Banco de dados

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/schema.sql
```

O arquivo é idempotente: rode de novo sempre que atualizar o projeto (é
assim que colunas e tabelas novas chegam a um banco existente). Ele nunca
apaga dados. Sem PostgreSQL instalado, veja a opção portátil em
[docs/testes.md](docs/testes.md#preparar-o-banco-uma-vez).

### 4. Servidor

```bash
python app.py
```

Abra <http://localhost:5000>. O Flask serve o frontend e a API na mesma
porta. Por segurança o servidor escuta só nesta máquina e sem o debugger;
use `HOST=0.0.0.0` e/ou `FLASK_DEBUG=1` no `.env` se precisar.

> Atualizando de uma versão anterior a 2026-10-08? Depois de rodar o
> `schema.sql`, todos precisam entrar de novo uma vez: as sessões passaram a
> ser guardadas como hash (`docs/processo.md`, D-15).

Sem `GEMINI_API_KEY` tudo funciona, menos as respostas da IA (o chat
mostra "Não foi possível falar com a IA agora" e mantém sua mensagem).
Sem SMTP, o link de redefinição de senha aparece no terminal (só fora de
produção).

### Problemas comuns

| Sintoma | Causa | Solução |
|---|---|---|
| Login ou envio de mensagem dá erro; no terminal aparece `relation "auth_rate_limits" does not exist`, `column "personality" does not exist` ou "Banco desatualizado em relação ao código" | O banco de `DATABASE_URL` não recebeu o `schema.sql` desta versão | Rode o passo 3 (`schema.sql`) **nesse** banco. É seguro repetir. |
| Todos foram deslogados depois de atualizar | Esperado: sessões passaram a ser guardadas como hash (D-15) | Entrar de novo |
| Enviar mensagem mostra "A resposta falhou…" | `GEMINI_API_KEY` ausente, inválida ou sem cota | Conferir a chave (`python tools/check_gemini_tier.py`) |
| "Autenticação em dois fatores temporariamente indisponível" | `TOTP_ENCRYPTION_KEY` ausente ou diferente da original | Definir a chave original no `.env` (`docs/2fa.md`) |
| Link de redefinição não chega por e-mail | `SMTP_*` ausente ou recusado | Em desenvolvimento o link aparece no terminal |

## Testes

```bash
export TEST_DATABASE_URL="postgresql://localhost/trashtalker_test"   # banco SEPARADO
python -m pytest        # testes de API
python -m behave        # cenários de comportamento (Gherkin pt-BR)
```

Os testes apagam as tabelas do banco de teste e recusam rodar sem
`TEST_DATABASE_URL` ou com ela igual a `DATABASE_URL`. Há também testes de
interface no navegador (`e2e/`, Playwright), que rodam contra o servidor no
ar. Detalhes, Windows e como escrever testes: [docs/testes.md](docs/testes.md).

**Conta de demonstração** (só em banco de desenvolvimento):
`python -m tools.seed_demo` cria `demo@trashtalker.example` /
`Demo-Banca-2026!` com duas conversas de exemplo.

## Segurança (resumo)

Senhas com hash (Werkzeug), SQL sempre parametrizado, cookie de sessão
`httponly`/`SameSite=Lax`/`Secure` em produção, verificação de origem em
toda alteração (anti-CSRF), CSP sem script inline, limite de tentativas
no login e na recuperação de senha, limites de tamanho em toda entrada,
2FA opcional. Decisões e riscos em aberto: [docs/processo.md](docs/processo.md).

## Publicação

Vercel: [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md). **Rode `backend/schema.sql`
no banco de produção antes de publicar uma versão nova.**

## Histórico

O projeto começou em TypeScript (Express + EJS + better-auth) e foi
reescrito em Python + HTML/JS puro. Consequência que ainda importa: contas
criadas na versão TypeScript não funcionam aqui (o formato do hash de
senha é outro) - precisam ser recriadas. Decisões técnicas e o registro
das mudanças de 2026-10: [docs/processo.md](docs/processo.md).
