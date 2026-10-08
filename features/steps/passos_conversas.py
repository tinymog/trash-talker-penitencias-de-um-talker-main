# language: pt
"""Passos das conversas: criar, enviar mensagem, renomear, apagar e isolamento."""

from backend import db
import backend.routes.chats_api as chats_api
from behave import given, then, when
from passos_comuns import cadastrar, logar


# --------------------------------------------------------------------------
# Contexto
# --------------------------------------------------------------------------


@given("que eu tenho uma conversa aberta")
def passo_tenho_conversa(context):
    resposta = context.cliente.post("/api/chats")
    assert resposta.status_code == 201, resposta.get_json()
    context.conversa_id = resposta.get_json()["id"]


@given('que eu já enviei a mensagem "{texto}"')
def passo_ja_enviei(context, texto):
    resposta = context.cliente.post(
        f"/api/chats/{context.conversa_id}/messages", json={"content": texto}
    )
    assert resposta.status_code == 200, resposta.get_json()


@given("que a IA está indisponível")
def passo_ia_indisponivel(context):
    chats_api.generate_reply = context.ia_que_falha


@given("que outra pessoa tem uma conversa")
def passo_conversa_alheia(context):
    outro = context.aplicacao.test_client()
    cadastrar(outro, "outro@exemplo.com", "Senha-Forte-123", nome="Outro")
    assert logar(outro, "outro@exemplo.com", "Senha-Forte-123").status_code == 200
    context.conversa_alheia_id = outro.post("/api/chats").get_json()["id"]


# --------------------------------------------------------------------------
# Ações
# --------------------------------------------------------------------------


@when('eu envio a mensagem "{texto}"')
def passo_envio_mensagem(context, texto):
    context.resposta = context.cliente.post(
        f"/api/chats/{context.conversa_id}/messages", json={"content": texto}
    )


@when('eu renomeio a conversa para "{titulo}"')
def passo_renomeio(context, titulo):
    context.resposta = context.cliente.post(
        f"/api/chats/{context.conversa_id}/title", json={"title": titulo}
    )


@when("eu apago a conversa")
def passo_apago_conversa(context):
    context.resposta = context.cliente.post(f"/api/chats/{context.conversa_id}/delete")


@when("eu abro meu painel")
def passo_abro_painel(context):
    context.resposta = context.cliente.get("/api/dashboard")


@when("eu tento abrir meu painel sem estar logado")
def passo_painel_sem_login(context):
    context.resposta = context.cliente.get("/api/dashboard")


@when("eu tento abrir a conversa da outra pessoa")
def passo_abrir_conversa_alheia(context):
    context.resposta = context.cliente.get(f"/api/chats/{context.conversa_alheia_id}")


@when("eu tento apagar a conversa da outra pessoa")
def passo_apagar_conversa_alheia(context):
    context.resposta = context.cliente.post(
        f"/api/chats/{context.conversa_alheia_id}/delete"
    )


# --------------------------------------------------------------------------
# Verificações
# --------------------------------------------------------------------------


@then("eu devo receber uma resposta do TrashTalker")
def passo_recebi_resposta(context):
    assert context.resposta.status_code == 200, context.resposta.get_json()
    corpo = context.resposta.get_json()
    assert corpo["assistantMessage"]["content"].strip() != ""


@then("a conversa deve ter {quantidade:d} mensagens guardadas")
def passo_quantidade_mensagens(context, quantidade):
    linhas = db.query(
        "SELECT * FROM messages WHERE chat_id = %s", (context.conversa_id,)
    )
    assert len(linhas) == quantidade, f"esperava {quantidade}, encontrei {len(linhas)}"


@then('o título da conversa deve ser "{titulo}"')
def passo_titulo(context, titulo):
    linha = db.query_one("SELECT title FROM chats WHERE id = %s", (context.conversa_id,))
    assert linha["title"] == titulo, f"título é {linha['title']!r}"


@then("eu não devo ter nenhuma conversa")
def passo_sem_conversas(context):
    corpo = context.cliente.get("/api/dashboard").get_json()
    assert corpo["chats"] == [], corpo["chats"]


@then("a conversa da outra pessoa deve continuar existindo")
def passo_conversa_alheia_intacta(context):
    linha = db.query_one(
        "SELECT id FROM chats WHERE id = %s", (context.conversa_alheia_id,)
    )
    assert linha is not None


# --------------------------------------------------------------------------
# Personalidades, autoria, parar resposta e aceite dos termos
# --------------------------------------------------------------------------


@given("que eu tenho uma conversa aberta com o MathIAs")
def passo_conversa_mathias(context):
    resposta = context.cliente.post("/api/chats", json={"personality": "mathias"})
    assert resposta.status_code == 201, resposta.get_json()
    context.conversa_id = resposta.get_json()["id"]


@given('que eu vou apertar "parar" enquanto a IA pensa')
def passo_vou_parar(context):
    def _ia_interrompida(history, user, personality=None, effort=None):
        # Outra aba do mesmo navegador (mesmo cookie) aperta "parar".
        with context.aplicacao.test_client() as aba:
            aba.set_cookie("session_token", context.cliente.get_cookie("session_token").value)
            assert aba.post(f"/api/chats/{context.conversa_id}/cancel").status_code == 200
        return "resposta que chegou tarde demais"

    chats_api.generate_reply = _ia_interrompida


@given("que os termos mudaram depois do meu aceite")
def passo_termos_mudaram(context):
    db.execute("UPDATE users SET consent_version = 'versao-anterior'")


@when("eu envio uma mensagem com {quantidade:d} caracteres")
def passo_mensagem_tamanho(context, quantidade):
    context.resposta = context.cliente.post(
        f"/api/chats/{context.conversa_id}/messages", json={"content": "a" * quantidade}
    )


@when("eu abro a conversa")
def passo_abro_conversa(context):
    context.resposta = context.cliente.get(f"/api/chats/{context.conversa_id}")


@when('eu tento renomear a conversa da outra pessoa para "{titulo}"')
def passo_renomear_alheia(context, titulo):
    context.resposta = context.cliente.post(
        f"/api/chats/{context.conversa_alheia_id}/title", json={"title": titulo}
    )


@then("a conversa deve passar a ser do TrashTalker")
def passo_conversa_virou_trashtalker(context):
    assert context.resposta.status_code == 200, context.resposta.get_json()
    linha = db.query_one("SELECT personality FROM chats WHERE id = %s", (context.conversa_id,))
    assert linha["personality"] == "trashtalker", linha


@then("a última resposta deve ter sido escrita pelo {nome}")
def passo_autor_ultima_resposta(context, nome):
    esperado = {"TrashTalker": "trashtalker", "MathIAs": "mathias"}[nome]
    mensagens = context.cliente.get(f"/api/chats/{context.conversa_id}").get_json()["messages"]
    ultima = [m for m in mensagens if m["role"] == "assistant"][-1]
    assert ultima["personality"] == esperado, ultima


@then("o envio deve ter sido descartado")
def passo_envio_descartado(context):
    assert context.resposta.get_json() == {"cancelled": True}, context.resposta.get_json()
