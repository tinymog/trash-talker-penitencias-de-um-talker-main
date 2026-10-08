"""
Regressões da revisão de segurança e robustez (docs/processo.md, D-07 a
D-13; requisitos RNF em docs/requisitos.md).

Cada bloco abaixo foi escrito ANTES da correção correspondente e falhava
no código anterior - é o que garante que a correção não volte a quebrar.
"""

import logging
from concurrent.futures import ThreadPoolExecutor

import pytest

from backend import db
from conftest import cadastrar, logar, ultimo_token_de_redefinicao

# --------------------------------------------------------------------------
# Entrada malformada nunca derruba o servidor (antes: 500)
# --------------------------------------------------------------------------

CORPOS_MALFORMADOS = [
    [],
    "texto solto",
    123,
    {"email": 1, "password": 2, "name": 3, "token": 4, "newPassword": 5},
    {"email": ["a@b.com"], "password": {"x": 1}, "name": None},
]


@pytest.mark.parametrize("rota", ["/api/signup", "/api/login", "/api/forgot-password", "/api/reset-password"])
@pytest.mark.parametrize("corpo", CORPOS_MALFORMADOS)
def test_rotas_publicas_nao_quebram_com_corpo_malformado(cliente, rota, corpo):
    resposta = cliente.post(rota, json=corpo)
    assert resposta.status_code < 500, resposta.get_data(as_text=True)[:200]
    assert resposta.is_json


@pytest.mark.parametrize(
    "caminho, corpo",
    [
        ("/api/chats/{c}/messages", {"content": 123}),
        ("/api/chats/{c}/messages", {"content": ["oi"]}),
        ("/api/chats/{c}/title", {"title": {"x": 1}}),
        ("/api/chats/{c}/personality", []),
        ("/api/chats/{c}/effort", "talker"),
        ("/api/account", {"name": 12345}),
        ("/api/account", {"name": "Igor", "displayName": {}}),
        ("/api/account", {"name": "Igor", "pronoun": 7}),
        ("/api/account/password", {"currentPassword": 1, "newPassword": 2}),
        ("/api/account/delete", {"password": 1, "confirmation": "eu quero excluir essa conta"}),
        ("/api/tts", {"text": 42}),
    ],
)
def test_rotas_autenticadas_recusam_tipos_invalidos_com_400(cliente, conversa, ia_falsa, caminho, corpo):
    resposta = cliente.post(caminho.format(c=conversa), json=corpo)
    assert resposta.status_code == 400, resposta.get_data(as_text=True)[:200]
    assert "error" in resposta.get_json()


def test_criar_conversa_com_corpo_que_nao_e_objeto_usa_os_padroes(cliente, usuario_logado):
    resposta = cliente.post("/api/chats", json=["mathias"])
    assert resposta.status_code == 201
    linha = db.query_one("SELECT personality, effort FROM chats")
    assert (linha["personality"], linha["effort"]) == ("trashtalker", "trash")


# --------------------------------------------------------------------------
# Limites de tamanho
# --------------------------------------------------------------------------


def test_mensagem_acima_do_limite_e_recusada_sem_chamar_a_ia(cliente, conversa, ia_falsa):
    resposta = cliente.post(f"/api/chats/{conversa}/messages", json={"content": "a" * 8001})
    assert resposta.status_code == 400
    assert db.query("SELECT * FROM messages") == []
    assert ia_falsa["chamadas"] == []


def test_mensagem_no_limite_e_aceita(cliente, conversa, ia_falsa):
    resposta = cliente.post(f"/api/chats/{conversa}/messages", json={"content": "a" * 8000})
    assert resposta.status_code == 200


def test_titulo_longo_demais_e_recusado(cliente, conversa):
    assert cliente.post(f"/api/chats/{conversa}/title", json={"title": "t" * 101}).status_code == 400
    assert cliente.post(f"/api/chats/{conversa}/title", json={"title": "t" * 100}).status_code == 200


@pytest.mark.parametrize(
    "campo, tamanho", [("name", 101), ("displayName", 51), ("pronoun", 31)]
)
def test_campos_do_perfil_tem_limite(cliente, usuario_logado, campo, tamanho):
    corpo = {"name": "Igor", campo: "x" * tamanho}
    assert cliente.post("/api/account", json=corpo).status_code == 400
    assert db.query_one("SELECT name FROM users")["name"] == "Pessoa"


def test_senha_gigante_e_recusada_antes_de_calcular_hash(cliente):
    assert cadastrar(cliente, senha="Aa1!" + "x" * 2000).status_code == 400
    assert db.query("SELECT id FROM users") == []


def test_corpo_maior_que_o_limite_devolve_413_em_json(cliente, usuario_logado):
    resposta = cliente.post("/api/account", json={"name": "Igor", "image": "a" * 1_100_000})
    assert resposta.status_code == 413
    assert "error" in resposta.get_json()


# --------------------------------------------------------------------------
# Avatar: só formatos conhecidos (antes: XSS armazenado no atributo src/alt)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "imagem",
    [
        "avatar:avatar_robot",
        "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
        "data:image/png;base64,iVBORw0KGgo=",
        "",
        None,
    ],
)
def test_avatar_em_formato_valido_e_aceito(cliente, usuario_logado, imagem):
    assert cliente.post("/api/account", json={"name": "Igor", "image": imagem}).status_code == 200


@pytest.mark.parametrize(
    "imagem",
    [
        'avatar:x" onerror="alert(1)',
        "avatar:avatar_que_nao_existe",
        "javascript:alert(1)",
        "https://rastreador.example/pixel.png",
        "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=",
        'data:image/png;base64,AAAA" onerror="alert(1)',
        123,
    ],
)
def test_avatar_em_formato_desconhecido_e_recusado(cliente, usuario_logado, imagem):
    resposta = cliente.post("/api/account", json={"name": "Igor", "image": imagem})
    assert resposta.status_code == 400
    assert db.query_one("SELECT image FROM users")["image"] is None


# --------------------------------------------------------------------------
# Origem da requisição (defesa contra CSRF em todas as rotas que alteram dados)
# --------------------------------------------------------------------------


def test_post_de_outra_origem_e_bloqueado(cliente, usuario_logado):
    resposta = cliente.post("/api/chats", headers={"Origin": "https://invasor.example"})
    assert resposta.status_code == 403
    assert db.query("SELECT * FROM chats") == []


def test_post_marcado_como_cross_site_e_bloqueado(cliente, usuario_logado):
    resposta = cliente.post("/api/logout", headers={"Sec-Fetch-Site": "cross-site"})
    assert resposta.status_code == 403
    assert cliente.get("/api/me").status_code == 200


def test_post_da_propria_origem_e_aceito(cliente, usuario_logado):
    resposta = cliente.post(
        "/api/chats", headers={"Origin": "http://localhost", "Sec-Fetch-Site": "same-origin"}
    )
    assert resposta.status_code == 201


def test_leitura_nao_depende_da_origem(cliente, usuario_logado):
    assert cliente.get("/api/me", headers={"Origin": "https://invasor.example"}).status_code == 200


# --------------------------------------------------------------------------
# Cabeçalhos de segurança e erros em JSON
# --------------------------------------------------------------------------


@pytest.mark.parametrize("caminho", ["/", "/login", "/api/me"])
def test_cabecalhos_de_seguranca_presentes(cliente, caminho):
    cabecalhos = cliente.get(caminho).headers
    assert "script-src 'self'" in cabecalhos["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in cabecalhos["Content-Security-Policy"]
    assert cabecalhos["X-Frame-Options"] == "DENY"
    assert cabecalhos["X-Content-Type-Options"] == "nosniff"
    assert cabecalhos["Referrer-Policy"] == "same-origin"


def test_rota_de_api_inexistente_devolve_404_em_json(cliente):
    resposta = cliente.get("/api/nao-existe")
    assert resposta.status_code == 404
    assert "error" in resposta.get_json()


def test_metodo_errado_na_api_devolve_405_em_json(cliente):
    # PUT e não GET: com static_url_path="" um GET em qualquer caminho também
    # casa com a rota de arquivos estáticos e vira 404 (igualmente em JSON).
    resposta = cliente.put("/api/login", json={})
    assert resposta.status_code == 405
    assert "error" in resposta.get_json()


def test_erro_inesperado_devolve_500_generico_sem_detalhes(cliente, aplicacao, usuario_logado, monkeypatch):
    monkeypatch.setitem(aplicacao.config, "PROPAGATE_EXCEPTIONS", False)

    def _explode(*_args, **_kwargs):
        raise RuntimeError("detalhe interno que não pode vazar")

    monkeypatch.setattr("backend.routes.chats_api.query", _explode)
    resposta = cliente.get("/api/dashboard")
    assert resposta.status_code == 500
    assert "detalhe interno" not in resposta.get_data(as_text=True)
    assert "error" in resposta.get_json()


def test_banco_desatualizado_avisa_no_log_o_que_fazer(cliente, usuario_logado, monkeypatch, caplog):
    """
    Código novo num banco que não recebeu o schema.sql da versão: antes o
    sintoma era um 500 genérico no login ("relation auth_rate_limits does
    not exist"), sem pista do que fazer.
    """
    from psycopg2 import errors

    def _tabela_que_falta(*_args, **_kwargs):
        raise errors.UndefinedTable('relation "tabela_nova" does not exist')

    monkeypatch.setattr("backend.routes.chats_api.query", _tabela_que_falta)
    with caplog.at_level(logging.ERROR):
        resposta = cliente.get("/api/dashboard")

    assert resposta.status_code == 503
    assert "tabela_nova" not in resposta.get_data(as_text=True)
    assert "schema.sql" in caplog.text and "tabela_nova" in caplog.text


def test_pagina_inexistente_mostra_404_amigavel(cliente):
    resposta = cliente.get("/pagina-que-nao-existe")
    assert resposta.status_code == 404
    assert "text/html" in resposta.content_type
    assert "Página não encontrada" in resposta.get_data(as_text=True)


# --------------------------------------------------------------------------
# Força bruta no login e abuso do "esqueci a senha"
# --------------------------------------------------------------------------


def _falhas_de_login(cliente, quantidade, email="pessoa@exemplo.com"):
    return [logar(cliente, email=email, senha="Senha-Errada-1!").status_code for _ in range(quantidade)]


def test_login_bloqueia_apos_dez_falhas_mesmo_com_a_senha_certa(cliente):
    cadastrar(cliente)
    assert _falhas_de_login(cliente, 10) == [401] * 10

    resposta = logar(cliente)
    assert resposta.status_code == 429
    assert int(resposta.headers["Retry-After"]) > 0
    assert db.query("SELECT * FROM sessions") == []


def test_bloqueio_de_login_e_por_conta(cliente):
    cadastrar(cliente)
    cadastrar(cliente, email="outra@exemplo.com")
    _falhas_de_login(cliente, 10)
    assert logar(cliente, email="outra@exemplo.com").status_code == 200


def test_login_certo_zera_o_contador_de_falhas(cliente):
    cadastrar(cliente)
    _falhas_de_login(cliente, 9)
    assert logar(cliente).status_code == 200
    assert _falhas_de_login(cliente, 9) == [401] * 9
    assert logar(cliente).status_code == 200


def test_bloqueio_de_login_expira_com_a_janela(cliente):
    cadastrar(cliente)
    _falhas_de_login(cliente, 10)
    db.execute("UPDATE auth_rate_limits SET window_started_at = now() - interval '16 minutes'")
    assert logar(cliente).status_code == 200


def test_login_de_conta_inexistente_tambem_calcula_hash(cliente, monkeypatch):
    """Sem isso, responder mais rápido para e-mail sem conta revelava quem tem conta."""
    from backend import two_factor

    verificacoes = []
    original = two_factor.verify_password
    monkeypatch.setattr(
        two_factor, "verify_password", lambda senha, hash_: verificacoes.append(hash_) or original(senha, hash_)
    )
    assert logar(cliente, email="ninguem@exemplo.com").status_code == 401
    assert len(verificacoes) == 1


def test_esqueci_a_senha_limita_envios_por_email_sem_revelar(cliente, monkeypatch):
    enviados = []
    monkeypatch.setattr(
        "backend.routes.auth_api.send_password_reset_email", lambda para, url: enviados.append(para)
    )
    cadastrar(cliente)
    respostas = [
        cliente.post("/api/forgot-password", json={"email": "pessoa@exemplo.com"}) for _ in range(5)
    ]
    assert all(r.status_code == 200 and r.get_json() == {"ok": True} for r in respostas)
    assert len(enviados) == 3


def test_link_de_redefinicao_nao_vai_para_o_log_em_producao(cliente, monkeypatch, caplog, capsys):
    def _smtp_fora(*_args):
        raise RuntimeError("SMTP indisponível")

    monkeypatch.setattr("backend.routes.auth_api.send_password_reset_email", _smtp_fora)
    monkeypatch.setenv("FLASK_ENV", "production")
    cadastrar(cliente)
    with caplog.at_level(logging.DEBUG):
        assert cliente.post("/api/forgot-password", json={"email": "pessoa@exemplo.com"}).status_code == 200

    saida = caplog.text + capsys.readouterr().out
    assert "reset-password?token=" not in saida


def test_banco_guarda_so_o_hash_dos_tokens(cliente, usuario_logado):
    """Quem ler o banco (backup, vazamento) não consegue usar sessões nem links."""
    cookie = cliente.get_cookie("session_token").value
    assert cookie not in [s["id"] for s in db.query("SELECT id FROM sessions")]

    cliente.post("/api/forgot-password", json={"email": "pessoa@exemplo.com"})
    link = ultimo_token_de_redefinicao()
    assert db.query_one("SELECT token FROM password_reset_tokens")["token"] != link
    # E mesmo assim tudo continua funcionando com o token de verdade.
    assert cliente.get("/api/me").status_code == 200
    assert cliente.post(
        "/api/reset-password", json={"token": link, "newPassword": "Nova-Senha-999"}
    ).status_code == 200


def test_novo_pedido_de_redefinicao_invalida_o_link_anterior(cliente):
    cadastrar(cliente)
    cliente.post("/api/forgot-password", json={"email": "pessoa@exemplo.com"})
    primeiro = ultimo_token_de_redefinicao()
    cliente.post("/api/forgot-password", json={"email": "pessoa@exemplo.com"})

    resposta = cliente.post("/api/reset-password", json={"token": primeiro, "newPassword": "Nova-Senha-999"})
    assert resposta.status_code == 400


# --------------------------------------------------------------------------
# Corridas (duas requisições ao mesmo tempo)
# --------------------------------------------------------------------------


def test_cadastros_simultaneos_do_mesmo_email_criam_uma_conta(aplicacao):
    def _tentar(_):
        with aplicacao.test_client() as outro:
            return cadastrar(outro).status_code

    with ThreadPoolExecutor(max_workers=4) as execucao:
        status = sorted(execucao.map(_tentar, range(4)))
    assert status == [201, 409, 409, 409]
    assert db.query_one("SELECT count(*) AS total FROM users")["total"] == 1


def test_token_de_redefinicao_usado_ao_mesmo_tempo_vale_uma_vez(cliente, aplicacao):
    cadastrar(cliente)
    cliente.post("/api/forgot-password", json={"email": "pessoa@exemplo.com"})
    token = ultimo_token_de_redefinicao()

    def _usar(senha):
        with aplicacao.test_client() as outro:
            return outro.post("/api/reset-password", json={"token": token, "newPassword": senha}).status_code

    with ThreadPoolExecutor(max_workers=4) as execucao:
        status = sorted(execucao.map(_usar, ["Nova-Senha-1!", "Nova-Senha-2!", "Nova-Senha-3!", "Nova-Senha-4!"]))
    assert status == [200, 400, 400, 400]


# --------------------------------------------------------------------------
# Conversa alheia ou inexistente: toda alteração devolve 404 (antes: 200 "ok")
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sufixo, corpo",
    [
        ("title", {"title": "invadido"}),
        ("personality", {"personality": "mathias"}),
        ("effort", {"effort": "talker"}),
        ("delete", None),
        ("cancel", None),
    ],
)
def test_alterar_conversa_alheia_devolve_404_e_nao_altera(cliente, aplicacao, usuario_logado, sufixo, corpo):
    outro = aplicacao.test_client()
    cadastrar(outro, email="outro@exemplo.com", nome="Outro")
    logar(outro, email="outro@exemplo.com")
    alheia = outro.post("/api/chats").get_json()["id"]
    antes = db.query_one("SELECT * FROM chats WHERE id = %s", (alheia,))

    resposta = cliente.post(f"/api/chats/{alheia}/{sufixo}", json=corpo)
    assert resposta.status_code == 404
    assert db.query_one("SELECT * FROM chats WHERE id = %s", (alheia,)) == antes
