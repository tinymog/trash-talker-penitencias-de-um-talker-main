"""
features/environment.py
=======================
Preparação do ambiente para os testes de comportamento (Behave).

Segue as mesmas decisões do tests/conftest.py (pytest):

  - banco PostgreSQL separado, apontado por `TEST_DATABASE_URL`, com
    trava para não rodar por engano contra o banco real;
  - tabelas zeradas antes de cada cenário, para que um cenário nunca
    dependa do anterior;
  - a chamada ao Gemini é substituída por uma resposta fixa - o que
    está sob teste é o comportamento da aplicação, não o texto que o
    modelo devolve.
"""

import os
import sys

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(APP_DIR, "backend")
sys.path.insert(0, APP_DIR)

from cryptography.fernet import Fernet  # noqa: E402

import backend.routes.auth_api as auth_api  # noqa: E402
import backend.routes.chats_api as chats_api  # noqa: E402
from backend import db  # noqa: E402
from backend.factory import create_app  # noqa: E402

SCHEMA_PATH = os.path.join(BACKEND_DIR, "schema.sql")
# TRUNCATE ... CASCADE em users já limparia as tabelas dependentes; listar
# todas deixa explícito o que cada cenário zera.
TABELAS = ["messages", "chats", "password_reset_tokens", "sessions", "auth_rate_limits",
           "two_factor_recovery_codes", "two_factor_login_challenges", "user_two_factor", "users"]

RESPOSTA_SIMULADA = "Resposta simulada do TrashTalker."


def _ia_simulada(history, user, personality=None, effort=None):
    """Substitui generate_reply(): nenhuma chamada de rede nos testes."""
    return RESPOSTA_SIMULADA


def _ia_que_falha(history, user, personality=None, effort=None):
    raise RuntimeError("Falha simulada da IA")


def before_all(context):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        raise RuntimeError(
            "TEST_DATABASE_URL não definida. Os cenários zeram tabelas e por "
            "isso exigem um banco separado. Ver docs/testes.md."
        )
    if url == os.environ.get("DATABASE_URL"):
        raise RuntimeError(
            "TEST_DATABASE_URL é igual a DATABASE_URL. Recusando rodar: os "
            "cenários apagariam os dados do banco de desenvolvimento."
        )

    # Chave temporária do 2FA: nunca a do ambiente de quem roda os testes.
    os.environ["TOTP_ENCRYPTION_KEY"] = Fernet.generate_key().decode()

    context.aplicacao = create_app(database_url=url)
    context.aplicacao.config.update(TESTING=True)

    with open(SCHEMA_PATH, encoding="utf-8") as arquivo:
        db.execute(arquivo.read())


def before_scenario(context, scenario):
    db.execute("TRUNCATE " + ", ".join(TABELAS) + " RESTART IDENTITY CASCADE")

    # Por padrão a IA responde; cenários que testam falha trocam isso
    # via o passo "Dado que a IA está indisponível".
    chats_api.generate_reply = _ia_simulada
    context.ia_que_falha = _ia_que_falha

    # Nenhum e-mail de verdade sai dos testes, mesmo com SMTP configurado
    # no .env de quem roda. Os links "enviados" ficam em context.emails.
    context.emails = []
    auth_api.send_password_reset_email = lambda para, url: context.emails.append((para, url))

    context.cliente = context.aplicacao.test_client()
    context.outro_cliente = None
    context.resposta = None
    context.conversa_id = None


def after_all(context):
    db.close_pool()
