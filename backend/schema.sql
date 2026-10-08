-- schema.sql
-- ===========
-- Esquema do banco de dados PostgreSQL para o Trash Talker (versão Python).
--
-- Substitui as tabelas que o `better-auth` gerava automaticamente
-- (user, session, account, verification) por um esquema mais simples,
-- pensado para a autenticação própria implementada em backend/auth.py.
-- Os nomes das tabelas de conversa/mensagem foram mantidos no mesmo
-- espírito do original (chat -> chats, message -> messages).
--
-- Como usar: rode este arquivo uma vez no seu banco Postgres (local ou
-- no Neon), por exemplo:
--   psql "$DATABASE_URL" -f schema.sql

CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    image         TEXT,
    display_name  TEXT,
    pronoun       TEXT,
    interests     TEXT[] NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Migração idempotente: cobre bancos onde `users` já existia antes destas
-- colunas (o CREATE TABLE IF NOT EXISTS acima é um no-op nesse caso). Não
-- há ferramenta de migração neste projeto - este arquivo é rodado à mão,
-- e continua sendo a referência única de "como deixar o banco no formato
-- atual".
ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS pronoun TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS interests TEXT[] NOT NULL DEFAULT '{}';

-- Registro do aceite (LGPD art. 8º §2º: quem trata o dado precisa provar o
-- consentimento). consent_version diz QUAL versão dos termos foi aceita
-- (ver CONSENT_VERSION em auth.py); NULL = conta anterior ao registro, que
-- precisa aceitar de novo no próximo acesso.
ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_accepted_at TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_version TEXT;

CREATE TABLE IF NOT EXISTS sessions (
    id         TEXT PRIMARY KEY,            -- SHA-256 do token do cookie (auth.hash_token)
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token      TEXT PRIMARY KEY,                -- SHA-256 do token do link (auth.hash_token)
    user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    used       BOOLEAN NOT NULL DEFAULT false,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chats (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL DEFAULT 'New Chat',
    personality TEXT NOT NULL DEFAULT 'trashtalker',
    effort      TEXT NOT NULL DEFAULT 'trash',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Migração idempotente (mesmo padrão das colunas de users acima).
ALTER TABLE chats ADD COLUMN IF NOT EXISTS personality TEXT NOT NULL DEFAULT 'trashtalker';
ALTER TABLE chats ADD COLUMN IF NOT EXISTS effort TEXT NOT NULL DEFAULT 'trash';

CREATE TABLE IF NOT EXISTS messages (
    id         TEXT PRIMARY KEY,
    chat_id    TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role       TEXT NOT NULL,             -- "user" ou "assistant"
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);

-- 2FA opcional. Segredos ativos e pendentes são criptografados com uma
-- chave externa ao banco. Ausência de secret_encrypted significa desativado.
CREATE TABLE IF NOT EXISTS user_two_factor (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    secret_encrypted TEXT,
    pending_secret_encrypted TEXT,
    pending_expires_at TIMESTAMPTZ,
    pending_session_hash TEXT,
    pending_password_version TEXT,
    last_used_step BIGINT NOT NULL DEFAULT -1,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    failure_window_at TIMESTAMPTZ,
    blocked_until TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS two_factor_login_challenges (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    password_version TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS two_factor_recovery_codes (
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code_hash TEXT NOT NULL,
    PRIMARY KEY (user_id, code_hash)
);

-- --------------------------------------------------------------------------
-- Revisão 2026-10 (ver docs/processo.md, D-07 a D-13). Tudo idempotente e
-- sem apagar dado: pode rodar quantas vezes quiser.
-- --------------------------------------------------------------------------

-- Qual personalidade escreveu cada resposta. Sem isso, ao reabrir uma
-- conversa toda resposta aparecia só como "IA" (e o "ouvir" usava a voz
-- padrão). NULL = mensagem do usuário ou resposta anterior a esta coluna.
ALTER TABLE messages ADD COLUMN IF NOT EXISTS personality TEXT;

-- Só existem dois papéis. NOT VALID: vale para toda linha nova sem
-- precisar varrer (nem travar) a tabela inteira na migração.
DO $$
BEGIN
    ALTER TABLE messages ADD CONSTRAINT messages_role_check
        CHECK (role IN ('user', 'assistant')) NOT VALID;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Contador de tentativas (força bruta no login, abuso do "esqueci a
-- senha") - ver rate_limit_* em backend/auth.py. Guardado no banco porque
-- na Vercel cada requisição pode cair numa instância diferente.
CREATE TABLE IF NOT EXISTS auth_rate_limits (
    bucket            TEXT PRIMARY KEY,
    attempts          INTEGER NOT NULL CHECK (attempts > 0),
    window_started_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índices para as consultas que o app realmente faz:
--   mensagens de uma conversa em ordem (GET /api/chats/<id>, histórico da IA);
--   barra lateral ordenada pela conversa mais recente;
--   faxina de sessões vencidas a cada login (auth.create_session);
--   invalidação dos links de redefinição anteriores da conta.
CREATE INDEX IF NOT EXISTS idx_messages_chat_created ON messages(chat_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chats_user_updated ON chats(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
