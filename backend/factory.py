"""
factory.py
==========
Monta a aplicação Flask ("application factory" - ver docs/processo.md, D-01).

Responsabilidades:
  1. Ligar o pool de conexões com o Postgres (db.init_pool()).
  2. Registrar as rotas da API (blueprints em routes/).
  3. Servir o frontend estático (pasta public/) nas URLs "bonitas"
     (/dashboard, /login, ...), sem extensão .html.
  4. Regras que valem para toda requisição: limite de tamanho do corpo,
     bloqueio de alterações vindas de outro site (CSRF), cabeçalhos de
     segurança e erros da API sempre em JSON.

Quem chama: app.py (servidor de desenvolvimento e Vercel) e os testes
(tests/conftest.py, features/environment.py), que passam o banco de teste.
"""

import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request, send_from_directory
from flask_cors import CORS
from psycopg2 import errors as pg_errors
from werkzeug.exceptions import HTTPException

from backend import db
from backend.routes.account_api import account_api
from backend.routes.auth_api import auth_api
from backend.routes.chats_api import chats_api
from backend.routes.two_factor_api import two_factor_api
from backend.validation import InvalidInput

# Carrega o .env antes de qualquer os.environ.get().
load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BACKEND_DIR, "..", "public")

# A maior coisa legítima que o frontend envia é a foto do avatar, já
# reduzida pelo navegador (MAX_IMAGE_CHARS em routes/account_api.py).
MAX_CONTENT_LENGTH = 1024 * 1024

# Na Vercel o HTML sai direto da CDN, sem passar pelo Flask: a mesma
# política está repetida em vercel.json. Mudou aqui, mude lá.
# Nenhum script ou estilo inline no projeto (o JS altera estilos só via
# element.style, que a CSP permite): tudo vem de /js e /css.
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; "
        "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    ),
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    # O link de redefinição de senha leva o token na URL: não vazar no Referer.
    "Referrer-Policy": "same-origin",
}

API_ERROR_MESSAGES = {
    400: "Solicitação inválida.",
    404: "Recurso não encontrado.",
    405: "Método não permitido.",
    413: "Solicitação muito grande.",
}

PAGE_ROUTES = {
    "/": "index.html",
    "/login": "login.html",
    "/signup": "signup.html",
    "/forgot-password": "forgot-password.html",
    "/reset-password": "reset-password.html",
    "/privacy": "privacy.html",
    "/terms": "terms.html",
    "/cookies": "cookies.html",
    "/dashboard": "dashboard.html",
    "/dashboard/account": "account.html",
    "/dashboard/settings": "settings.html",
}


def create_app(database_url=None):
    """
    Cria e configura a aplicação Flask.

    `database_url` é opcional: sem ele o banco vem de DATABASE_URL (.env).
    Os testes passam a URL do banco de teste aqui (ver tests/conftest.py).
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    # CORS só importa se o frontend for servido de outra origem (ex.: um
    # live-server em outra porta). Servido pelo Flask, é a mesma origem.
    frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5000")
    CORS(app, supports_credentials=True, origins=[frontend_origin])

    db.init_pool(database_url)

    for blueprint in (auth_api, chats_api, account_api, two_factor_api):
        app.register_blueprint(blueprint)

    _register_request_guards(app)
    _register_error_handlers(app)
    _register_pages(app)
    return app


def _register_request_guards(app):
    @app.before_request
    def block_cross_site_mutations():
        """
        Recusa POST/PUT/DELETE em /api/ vindos de outro site. O cookie de
        sessão já é SameSite=Lax, mas isso não cobre navegadores antigos nem
        subdomínios irmãos; o Origin (e o Sec-Fetch-Site dos navegadores
        atuais) diz de onde a requisição saiu. Sem nenhum dos dois (curl,
        testes) não há navegador a proteger, então passa.
        """
        if request.method in ("GET", "HEAD", "OPTIONS") or not request.path.startswith("/api/"):
            return None
        allowed = {request.host_url.rstrip("/"), os.environ.get("FRONTEND_ORIGIN", "").rstrip("/")}
        origin = request.headers.get("Origin")
        if (origin and origin not in allowed) or request.headers.get("Sec-Fetch-Site") == "cross-site":
            return jsonify({"error": "Origem da solicitação não permitida."}), 403
        return None

    @app.after_request
    def security_headers(response):
        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        # Respostas da API são dados pessoais: nada de guardar em cache.
        if request.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
        return response


def _register_error_handlers(app):
    @app.errorhandler(InvalidInput)
    def invalid_input(error):
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(pg_errors.UndefinedTable)
    @app.errorhandler(pg_errors.UndefinedColumn)
    def schema_outdated(error):
        """
        Código desta versão rodando num banco que não recebeu o schema.sql
        dela (aconteceu: todo login dava 500 com "relation auth_rate_limits
        does not exist"). O log diz exatamente o que fazer; quem usa vê só
        que o serviço está indisponível.
        """
        app.logger.error(
            "Banco desatualizado em relação ao código (%s). Rode backend/schema.sql "
            "no banco de DATABASE_URL - ver README, seção 'Banco de dados'.",
            str(error).splitlines()[0],
        )
        return jsonify({"error": "Serviço temporariamente indisponível. Tente mais tarde."}), 503

    @app.errorhandler(HTTPException)
    def http_error(error):
        """
        Erros HTTP da API viram JSON (o apiFetch do frontend lê `error`);
        páginas inexistentes mostram public/404.html. Inclui o 500: o Flask
        já registrou o traceback no log (app.logger) antes de chegar aqui, e
        a resposta nunca carrega detalhe interno.
        """
        if request.path.startswith("/api/"):
            message = API_ERROR_MESSAGES.get(error.code, "Algo deu errado. Tente novamente em instantes.")
            return jsonify({"error": message}), error.code
        if error.code == 404:
            return send_from_directory(FRONTEND_DIR, "404.html"), 404
        return error


def _register_pages(app):
    def make_page_view(filename):
        def view():
            return send_from_directory(FRONTEND_DIR, filename)

        return view

    for path, filename in PAGE_ROUTES.items():
        endpoint = "page_" + filename.replace(".html", "").replace("-", "_")
        app.add_url_rule(path, endpoint=endpoint, view_func=make_page_view(filename))

    @app.route("/dashboard/chat/<chat_id>")
    def chat_page(chat_id):
        # O id vai na URL; public/js/chat.js o lê de window.location.pathname.
        return send_from_directory(FRONTEND_DIR, "chat.html")

    @app.route("/dashboard/information")
    def information_redirect():
        # Página antiga incorporada à landing ("/"): mantém links/favoritos.
        return redirect("/", code=302)
