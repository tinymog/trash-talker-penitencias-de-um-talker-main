# Publicação na Vercel

Ao importar o repositório na Vercel, use como **Root Directory** a pasta
que contém `app.py` e `vercel.json` (a raiz deste projeto; se ele estiver
dentro de uma subpasta do repositório, aponte para ela) e mantenha as
configurações de build em branco. A Vercel detecta `app.py` como aplicação
Flask e publica `public/` como arquivos estáticos na CDN.

## Rotas publicadas

| URL | Arquivo servido |
| --- | --- |
| `/` | `public/index.html` |
| `/login` | `public/login.html` |
| `/signup` | `public/signup.html` |
| `/forgot-password` | `public/forgot-password.html` |
| `/reset-password` | `public/reset-password.html` |
| `/privacy` | `public/privacy.html` |
| `/terms` | `public/terms.html` |
| `/dashboard` | `public/dashboard.html` |
| `/dashboard/account` | `public/account.html` |
| `/dashboard/settings` | `public/settings.html` |
| `/dashboard/chat/:chatId` | `public/chat.html` |
| `/cookies` | `public/cookies.html` |
| qualquer outro endereço | `public/404.html` (status 404) |

`/dashboard/information` é uma rota legada e redireciona para `/`.
As rotas acima são *rewrites*: a aba continua exibindo a URL limpa, sem
`.html`. As chamadas `/api/*` são atendidas pela aplicação Flask.

## Cabeçalhos de segurança

O HTML sai direto da CDN, sem passar pelo Flask; por isso a CSP e os
demais cabeçalhos de segurança estão em `vercel.json` (bloco `headers`,
`"source": "/(.*)"`), idênticos a `SECURITY_HEADERS` em
`backend/factory.py`. Mudou num, mude no outro. Depois do deploy, confira:

```bash
curl -sI https://seu-dominio/login | grep -iE "content-security|x-frame|referrer"
```

## Variáveis de ambiente

Cadastre em **Settings > Environment Variables** para Preview e Production:

- `DATABASE_URL` — obrigatório; URL de conexão do PostgreSQL.
- `GEMINI_API_KEY` — necessário para o envio de mensagens à IA.
- `TOTP_ENCRYPTION_KEY` — chave Fernet persistente para o Google Authenticator.
  Gere e guarde conforme [docs/2fa.md](docs/2fa.md); todas as instâncias
  ligadas ao mesmo banco precisam da mesma chave.
- `FLASK_ENV=production` — habilita o cookie de sessão seguro.
- `FRONTEND_ORIGIN=https://seu-dominio.vercel.app` — origem pública da
  aplicação; substitua pelo domínio final.

Se a recuperação de senha for usada em produção, inclua também `SMTP_HOST`,
`SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` e `SMTP_FROM`.

Nunca envie um arquivo `.env` ao repositório ou à Vercel. Depois de cadastrar
as variáveis, faça um deploy de Preview e valide as URLs da tabela antes de
promover para Production.

**Antes de publicar esta versão, rode o `backend/schema.sql` no banco de
produção:**

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/schema.sql
```

A versão de 2026-10 depende da coluna `messages.personality` e da tabela
`auth_rate_limits`: sem elas, **todo login e todo envio de mensagem falham**.
O arquivo é idempotente e não apaga dados - pode rodar quantas vezes
quiser (versões anteriores também dependiam dele para
`users.terms_accepted_at`/`consent_version` e as tabelas de 2FA).

**Efeito esperado ao publicar a versão de 2026-10-08:** sessões e links de
redefinição passaram a ser guardados como hash (`docs/processo.md`, D-15).
Os que já estavam abertos deixam de valer, então **todo mundo precisa entrar
de novo uma vez** - não é falha. Avise os usuários, se houver.

Nunca rode `python -m tools.seed_demo` no banco de produção: a conta de
demonstração tem senha pública (o script recusa quando `VERCEL=1` ou
`FLASK_ENV=production`, mas a proteção depende dessas variáveis).

Para disponibilizar o 2FA, aplique o `backend/schema.sql` atualizado antes
de publicar o backend e as telas. Contas existentes continuam sem 2FA até
a ativação individual nas Configurações. Nunca faça rollback para um login
sem verificação 2FA depois que houver contas protegidas.
