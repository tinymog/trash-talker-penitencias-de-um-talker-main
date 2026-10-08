"""
auth.py
=======
Substitui a biblioteca "better-auth" (usada no projeto TypeScript original)
por uma implementação própria, simples e explícita, de autenticação por
sessão com cookie.

O que este módulo faz:
  1. Hash e verificação de senha (via werkzeug, que já vem com o Flask).
  2. Criação/leitura/destruição de sessões (tabela `sessions`), com um
     cookie httponly guardando o token da sessão.
  3. Geração e validação de tokens de "esqueci minha senha"
     (tabela `password_reset_tokens`, equivalente à tabela `verification`
     do better-auth).
  4. Um decorator `require_auth` para proteger rotas que só usuários
     logados podem acessar (equivalente a src/require-auth.ts).

Aviso de migração (leia isto!):
  O better-auth usa seu próprio algoritmo de hash de senha (scrypt com um
  formato específico) e sua própria tabela `account` para guardar esse
  hash. Não é possível reaproduzir esse formato de forma simples em Python
  sem reimplementar a biblioteca inteira. Por isso este projeto usa um
  esquema de banco de dados NOVO (ver schema.sql) com hash via
  werkzeug.security (PBKDF2-SHA256). Isso significa que contas criadas
  pela versão antiga (TypeScript) não vão funcionar aqui - é preciso
  recriar as contas depois de rodar schema.sql em um banco novo (ou
  limpo). Para um projeto de TCC ainda em desenvolvimento, isso é o
  caminho mais simples e seguro.
"""

import hashlib
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from backend.db import execute, query_one

SESSION_COOKIE_NAME = "session_token"
SESSION_DURATION = timedelta(days=30)
RESET_TOKEN_DURATION = timedelta(hours=1)

PASSWORD_MIN_LENGTH = 8
# Tetos de entrada usados no cadastro, login e conta. Senha tem teto porque
# o hash (PBKDF2) de um texto de vários MB custa CPU de verdade; o nome
# aparece no prompt da IA.
MAX_EMAIL_LENGTH = 320
MAX_PASSWORD_LENGTH = 1024
MAX_NAME_LENGTH = 100
_SPECIAL_CHAR_RE = re.compile(r"[^A-Za-z0-9]")

# Versão dos termos/consentimento em vigor. Trocar este valor quando a
# Política ou os Termos mudarem de forma relevante faz todo mundo ver de
# novo a janela de aceite (ver needs_consent e public/js/layout.js).
CONSENT_VERSION = "2026-10-06"


def has_required_consents(body):
    """
    As duas confirmações obrigatórias, usadas no cadastro e no novo aceite:
    18+ com Termos/Política, e o envio das mensagens à IA (consentimento
    específico - as conversas podem ter dado sensível, LGPD art. 11).
    Só vale True de verdade, não string/número "truthy".
    """
    return body.get("acceptTerms") is True and body.get("acceptAi") is True


def needs_consent(user):
    """True se a conta ainda não aceitou a versão atual dos termos."""
    return (user or {}).get("consent_version") != CONSENT_VERSION


def hash_password(password):
    """Gera o hash de uma senha para salvar no banco."""
    return generate_password_hash(password)


def verify_password(password, password_hash):
    """Confere se `password` corresponde ao hash salvo no banco."""
    return check_password_hash(password_hash, password)


def get_password_requirement_failures(password):
    """
    Confere `password` contra a política de senha forte do app e devolve
    a lista de mensagens (uma por regra não cumprida, em pt-BR) - lista
    vazia significa senha válida. Único lugar onde a regra é definida no
    backend, usado no cadastro, na redefinição por e-mail e na troca de
    senha estando logado (routes/auth_api.py e routes/account_api.py), para
    não divergir entre os três. Espelha PASSWORD_RULES em public/js/auth.js.
    """
    password = password or ""
    failures = []
    if len(password) < PASSWORD_MIN_LENGTH:
        failures.append(
            f"A senha deve ter no mínimo {PASSWORD_MIN_LENGTH} caracteres"
        )
    if not re.search(r"[A-Z]", password):
        failures.append("A senha deve conter pelo menos 1 letra maiúscula")
    if not re.search(r"[a-z]", password):
        failures.append("A senha deve conter pelo menos 1 letra minúscula")
    if not re.search(r"[0-9]", password):
        failures.append("A senha deve conter pelo menos 1 número")
    if not _SPECIAL_CHAR_RE.search(password):
        failures.append(
            "A senha deve conter pelo menos 1 caractere especial (ex.: !@#$%^&*)"
        )
    return failures


def hash_token(token):
    """
    SHA-256 de um token de sessão ou de redefinição. O banco guarda só isto:
    quem ler o banco (backup, vazamento, acesso indevido) não consegue usar
    o valor para entrar na conta - só quem tem o cookie ou o link de verdade.
    Um hash simples basta (sem sal/PBKDF2) porque o token já é aleatório,
    com 256 bits: não há como adivinhá-lo por força bruta.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(user_id, cursor=None):
    """
    Cria uma nova sessão para o usuário e devolve o token (que vai para o
    cookie; o banco guarda só o hash - ver hash_token).
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + SESSION_DURATION
    run = cursor.execute if cursor is not None else execute
    # Faxina das sessões vencidas a cada login, sem precisar de cron
    # (usa o índice idx_sessions_expires_at).
    run("DELETE FROM sessions WHERE expires_at < now()")
    run("INSERT INTO sessions (id, user_id, expires_at) VALUES (%s, %s, %s)",
        (hash_token(token), user_id, expires_at))
    return token, expires_at


def destroy_session(token):
    """Remove a sessão do banco (usado no logout)."""
    if token:
        execute("DELETE FROM sessions WHERE id = %s", (hash_token(token),))


def destroy_all_sessions(user_id, exceto=None):
    """
    Apaga todas as sessões do usuário, opcionalmente preservando uma
    (`exceto` = token da sessão atual).

    Motivo: quando a senha de uma conta muda, qualquer sessão aberta em
    outro dispositivo/navegador continuava valendo, porque a sessão é
    validada só pelo token na tabela `sessions` - ela não consulta o
    hash da senha. Ou seja: uma pessoa que tivesse acesso indevido à
    conta continuava dentro mesmo depois da vítima trocar a senha, o que
    esvazia o propósito da troca. Ver docs/processo.md (decisão D-02).
    """
    if exceto:
        execute(
            "DELETE FROM sessions WHERE user_id = %s AND id <> %s",
            (user_id, hash_token(exceto)),
        )
    else:
        execute("DELETE FROM sessions WHERE user_id = %s", (user_id,))


def get_session_user(req):
    """
    Lê o cookie de sessão da requisição e devolve o usuário correspondente
    (ou None se não houver sessão válida). Equivalente a getSessionUser()
    em src/require-auth.ts.
    """
    token = req.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None

    # Uma consulta só (JOIN) em vez de sessão + usuário separados: isto roda
    # em toda rota autenticada, e cada ida ao Neon é uma viagem de rede.
    # Sem a coluna image: a foto pode ter centenas de KB e só o painel e o
    # /api/me precisam dela (eles a buscam à parte).
    return query_one(
        "SELECT u.id, u.name, u.email, u.display_name, u.pronoun, u.interests, "
        "u.consent_version "
        "FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.id = %s AND s.expires_at > now()",
        (hash_token(token),),
    )


def is_production():
    """Produção = FLASK_ENV=production ou rodando na Vercel."""
    return os.environ.get("FLASK_ENV") == "production" or os.environ.get("VERCEL") == "1"


def set_session_cookie(response, token, expires_at):
    """Anexa o cookie de sessão em uma resposta Flask."""
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        samesite="Lax",
        secure=is_production(),
        expires=expires_at,
        path="/",
    )
    return response


def clear_session_cookie(response):
    """Remove o cookie de sessão (usado no logout)."""
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return response


def require_auth(view_func):
    """
    Decorator usado em toda rota que exige usuário logado (equivalente ao
    middleware requireAuth do Express). Diferente da versão original (que
    redirecionava para /login), aqui devolvemos um JSON 401, já que estas
    rotas agora são uma API consumida via fetch() pelo JavaScript do
    frontend - é o próprio frontend que decide redirecionar para /login
    quando recebe esse 401 (ver public/js/layout.js).
    """

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user = get_session_user(request)
        if not user:
            return jsonify({"error": "Não autenticado"}), 401
        g.user = user
        return view_func(*args, **kwargs)

    return wrapper


def create_password_reset_token(user_id):
    """
    Gera um token de redefinição de senha válido por 1 hora. Pedir um link
    novo invalida os anteriores da mesma conta: só o e-mail mais recente
    funciona (e a faxina dos vencidos de todo mundo vai junto).
    """
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + RESET_TOKEN_DURATION
    execute(
        "DELETE FROM password_reset_tokens WHERE user_id = %s OR expires_at < now()",
        (user_id,),
    )
    execute(
        "INSERT INTO password_reset_tokens (token, user_id, expires_at) "
        "VALUES (%s, %s, %s)",
        (hash_token(token), user_id, expires_at),
    )
    return token


def consume_password_reset_token(token):
    """
    Valida um token de redefinição de senha e já marca como usado.
    Devolve o user_id se válido, ou None se inválido/expirado/já usado.

    Um único UPDATE condicional: antes era SELECT e depois UPDATE, e duas
    requisições simultâneas com o mesmo link passavam as duas pelo SELECT
    (o link valia mais de uma vez).
    """
    row = query_one(
        "UPDATE password_reset_tokens SET used = true "
        "WHERE token = %s AND used = false AND expires_at > now() "
        "RETURNING user_id",
        (hash_token(token),),
    )
    return row["user_id"] if row else None


# --------------------------------------------------------------------------
# Limite de tentativas (força bruta no login, abuso do "esqueci a senha")
# --------------------------------------------------------------------------
# Guardado no banco, e não em memória, porque na Vercel cada requisição
# pode cair numa instância diferente. O "bucket" identifica o que está
# sendo contado, ex.: "login:pessoa@exemplo.com". A contagem é por conta
# (e-mail), não por IP: trocar de IP não ajuda o atacante. O custo é que
# alguém pode travar o login de outra pessoa por LOGIN_WINDOW errando a
# senha dela de propósito - aceito para o porte deste projeto.

LOGIN_MAX_FAILURES = 10
LOGIN_WINDOW = timedelta(minutes=15)
RESET_MAX_REQUESTS = 3
RESET_WINDOW = timedelta(hours=1)


def rate_limit_hit(bucket, window):
    """
    Soma uma ocorrência em `bucket` e devolve o total na janela atual (que
    recomeça quando a anterior venceu). Um único upsert, então duas
    requisições simultâneas nunca leem o mesmo valor.
    """
    # ponytail: faxina a cada ocorrência; mover para um job se a tabela crescer.
    execute("DELETE FROM auth_rate_limits WHERE window_started_at < now() - interval '1 day'")
    row = query_one(
        "INSERT INTO auth_rate_limits (bucket, attempts, window_started_at) "
        "VALUES (%s, 1, now()) ON CONFLICT (bucket) DO UPDATE SET "
        "attempts = CASE WHEN auth_rate_limits.window_started_at <= now() - %s "
        "THEN 1 ELSE auth_rate_limits.attempts + 1 END, "
        "window_started_at = CASE WHEN auth_rate_limits.window_started_at <= now() - %s "
        "THEN now() ELSE auth_rate_limits.window_started_at END "
        "RETURNING attempts",
        (bucket, window, window),
    )
    return row["attempts"]


def rate_limit_retry_after(bucket, limit, window):
    """Segundos até `bucket` liberar, ou 0 se ainda não chegou a `limit` na janela."""
    row = query_one(
        "SELECT GREATEST(1, CEIL(EXTRACT(EPOCH FROM window_started_at + %s - now())))::int AS seconds "
        "FROM auth_rate_limits "
        "WHERE bucket = %s AND attempts >= %s AND window_started_at > now() - %s",
        (window, bucket, limit, window),
    )
    return row["seconds"] if row else 0


def rate_limit_clear(bucket):
    """Zera a contagem (ex.: login certo depois de algumas tentativas erradas)."""
    execute("DELETE FROM auth_rate_limits WHERE bucket = %s", (bucket,))


def login_bucket(email):
    return "login:" + email


def reset_bucket(email):
    return "reset:" + email


def forget_rate_limits(email):
    """
    Apaga os contadores ligados a um e-mail. Usado na exclusão da conta: o
    bucket contém o e-mail, e a Política de Privacidade promete apagar os
    dados da pessoa na hora.
    """
    execute(
        "DELETE FROM auth_rate_limits WHERE bucket IN (%s, %s)",
        (login_bucket(email), reset_bucket(email)),
    )
