"""
routes/auth_api.py
===================
Endpoints de autenticação: login, cadastro, logout, sessão atual,
"esqueci minha senha" e redefinição de senha.

Equivalente a:
  - src/routes/auth-forms.ts (login, signup, logout)
  - as rotas /api/auth/forget-password e /api/auth/reset-password que o
    better-auth expunha automaticamente e que o JS do frontend chamava
    direto (public/js/auth.js)

Diferença de arquitetura importante: no projeto original, /login e /signup
eram rotas que RENDERIZAVAM uma página EJS de novo em caso de erro (ou
redirecionavam em caso de sucesso). Aqui, como o frontend é HTML estático
puro, essas rotas passam a devolver sempre JSON - é o JavaScript do
frontend (public/js/login.js, signup.js, etc.) que decide o que mostrar
na tela ou para onde navegar.
"""

import logging
import os
import re

from flask import Blueprint, jsonify, request

from backend.email_utils import send_password_reset_email
from backend.auth import (
    CONSENT_VERSION,
    LOGIN_MAX_FAILURES,
    LOGIN_WINDOW,
    MAX_EMAIL_LENGTH,
    MAX_NAME_LENGTH,
    MAX_PASSWORD_LENGTH,
    RESET_MAX_REQUESTS,
    RESET_WINDOW,
    SESSION_COOKIE_NAME,
    clear_session_cookie,
    consume_password_reset_token,
    create_password_reset_token,
    destroy_all_sessions,
    destroy_session,
    get_password_requirement_failures,
    get_session_user,
    has_required_consents,
    hash_password,
    is_production,
    login_bucket,
    rate_limit_clear,
    rate_limit_hit,
    rate_limit_retry_after,
    reset_bucket,
    set_session_cookie,
)
from backend.db import execute, new_id, query_one
from backend.two_factor import TwoFactorError, password_login
from backend.validation import json_body, text_field

auth_api = Blueprint("auth_api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _too_many_attempts(retry_after):
    response = jsonify({"error": "Muitas tentativas. Aguarde alguns minutos e tente de novo."})
    response.status_code = 429
    response.headers["Retry-After"] = str(retry_after)
    return response


@auth_api.after_request
def no_store_auth(response):
    response.headers["Cache-Control"] = "no-store"
    return response


def _public_user(user):
    """Remove campos internos antes de devolver o usuário para o frontend."""
    if not user:
        return None
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "image": user.get("image"),
        "display_name": user.get("display_name"),
        "pronoun": user.get("pronoun"),
        "interests": user.get("interests") or [],
    }


@auth_api.route("/me", methods=["GET"])
def me():
    """Devolve o usuário logado atualmente (ou 401 se não houver sessão)."""
    user = get_session_user(request)
    if not user:
        return jsonify({"error": "Não autenticado"}), 401
    # A foto não vem com a sessão (ver get_session_user): busca só aqui.
    foto = query_one("SELECT image FROM users WHERE id = %s", (user["id"],))
    return jsonify({"user": _public_user({**user, "image": foto["image"] if foto else None})})


@auth_api.route("/login", methods=["POST"])
def login():
    body = json_body()
    email = text_field(body, "email", MAX_EMAIL_LENGTH).strip().lower()
    password = text_field(body, "password", MAX_PASSWORD_LENGTH)

    # Validação equivalente ao loginSchema (zod) do original.
    if not EMAIL_RE.match(email) or len(password) < 8:
        return jsonify({"error": "Email ou senha inválidos"}), 400

    # Força bruta: depois de LOGIN_MAX_FAILURES senhas erradas na janela, a
    # conta para de aceitar tentativas - inclusive a certa, senão o bloqueio
    # ainda revelaria quando o atacante acertou.
    bucket = login_bucket(email)
    retry_after = rate_limit_retry_after(bucket, LOGIN_MAX_FAILURES, LOGIN_WINDOW)
    if retry_after:
        return _too_many_attempts(retry_after)
    try:
        result = password_login(email, password)
    except TwoFactorError as error:
        if error.code == "invalid_credentials":
            rate_limit_hit(bucket, LOGIN_WINDOW)
        raise
    rate_limit_clear(bucket)

    if result.get("twoFactorRequired"):
        destroy_session(request.cookies.get(SESSION_COOKIE_NAME))
        response = jsonify(result)
        response.status_code = 202
        return clear_session_cookie(response)
    response = jsonify({"user": _public_user(result["user"])})
    return set_session_cookie(response, *result["session"])


@auth_api.route("/signup", methods=["POST"])
def signup():
    body = json_body()
    email = text_field(body, "email", MAX_EMAIL_LENGTH, "Email inválido").strip().lower()
    password = text_field(body, "password", MAX_PASSWORD_LENGTH, "Senha longa demais")
    name = text_field(
        body, "name", MAX_NAME_LENGTH, f"Nome longo demais (máximo de {MAX_NAME_LENGTH} caracteres)"
    ).strip()

    # Validação equivalente ao signupSchema (zod) do original, com a
    # política de senha forte descrita em get_password_requirement_failures.
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Email inválido"}), 400
    password_errors = get_password_requirement_failures(password)
    if password_errors:
        return jsonify({"error": "\n".join(password_errors)}), 400
    if len(name) < 1:
        return jsonify({"error": "Nome é obrigatório"}), 400
    # Confirmações explícitas (caixas desmarcadas no formulário): 18+ com
    # Termos/Política, e o envio das mensagens à IA. Ver auth.py.
    if not has_required_consents(body):
        return jsonify({
            "error": "Para criar a conta, confirme que tem 18 anos ou mais "
            "e aceite os termos e o uso da IA."
        }), 400

    # ON CONFLICT em vez de "SELECT e depois INSERT": dois cadastros
    # simultâneos do mesmo e-mail passavam os dois pelo SELECT e o segundo
    # estourava a constraint UNIQUE com um 500.
    created = query_one(
        "INSERT INTO users (id, name, email, password_hash, terms_accepted_at, consent_version) "
        "VALUES (%s, %s, %s, %s, now(), %s) ON CONFLICT (email) DO NOTHING RETURNING id",
        (new_id(), name, email, hash_password(password), CONSENT_VERSION),
    )
    if not created:
        return jsonify({"error": "Este email já está cadastrado"}), 409

    # Igual ao original: signup NÃO loga o usuário automaticamente, ele
    # é redirecionado para a tela de login (ver public/js/signup.js).
    return jsonify({"ok": True}), 201


@auth_api.route("/logout", methods=["POST"])
def logout():
    token = request.cookies.get(SESSION_COOKIE_NAME)
    destroy_session(token)
    response = jsonify({"ok": True})
    return clear_session_cookie(response)


@auth_api.route("/forgot-password", methods=["POST"])
def forgot_password():
    email = text_field(json_body(), "email", MAX_EMAIL_LENGTH).strip().lower()

    user = query_one("SELECT id, email FROM users WHERE email = %s", (email,)) if email else None
    # Limite por conta: sem ele, qualquer um podia lotar a caixa de entrada
    # de alguém com e-mails de redefinição. Acima do limite a resposta é a
    # mesma de sempre - nada muda para quem está do outro lado.
    if user and rate_limit_hit(reset_bucket(email), RESET_WINDOW) <= RESET_MAX_REQUESTS:
        token = create_password_reset_token(user["id"])
        frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5000")
        reset_url = f"{frontend_origin}/reset-password?token={token}"
        try:
            send_password_reset_email(user["email"], reset_url)
        except Exception as e:
            # SMTP não configurado, credenciais erradas, etc.: a resposta
            # não quebra. Em desenvolvimento o link vai para o terminal; em
            # produção NUNCA - o log é lido por mais gente que o dono da
            # conta, e o link dá acesso a ela.
            logger.warning("Falha ao enviar e-mail de redefinição: %s", e)
            if not is_production():
                print(f"\n[LINK DE REDEFINIÇÃO DE SENHA] Para: {user['email']}\n{reset_url}\n", flush=True)

    # Sempre devolvemos sucesso, exista ou não o email - isso evita que
    # alguém descubra quais emails estão cadastrados testando um por um.
    return jsonify({"ok": True})


@auth_api.route("/reset-password", methods=["POST"])
def reset_password():
    body = json_body()
    token = text_field(body, "token", 128)
    new_password = text_field(body, "newPassword", MAX_PASSWORD_LENGTH, "Senha longa demais")

    password_errors = get_password_requirement_failures(new_password)
    if password_errors:
        return jsonify({"error": "\n".join(password_errors)}), 400

    user_id = consume_password_reset_token(token)
    if not user_id:
        return jsonify({"error": "Link inválido ou expirado"}), 400

    execute(
        "UPDATE users SET password_hash = %s, updated_at = now() WHERE id = %s",
        (hash_password(new_password), user_id),
    )
    # Quem redefine a senha por e-mail normalmente é alguém que perdeu o
    # acesso - possivelmente porque outra pessoa entrou na conta. Derrubar
    # todas as sessões abertas é o que faz a troca de senha realmente
    # expulsar quem não deveria estar lá.
    destroy_all_sessions(user_id)
    return jsonify({"ok": True})
