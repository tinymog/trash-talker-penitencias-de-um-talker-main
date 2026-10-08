# language: pt
"""Passos de segurança: força bruta, origem, avatar, limites e entrada malformada."""

from behave import then, when


@when('alguém erra a senha de "{email}" {vezes:d} vezes')
def passo_erra_senha(context, email, vezes):
    for _ in range(vezes):
        resposta = context.cliente.post(
            "/api/login", json={"email": email, "password": "Senha-Errada-1!"}
        )
        assert resposta.status_code == 401, resposta.get_json()


@when('eu peço a redefinição de senha do e-mail "{email}" {vezes:d} vezes')
def passo_pede_redefinicao_varias(context, email, vezes):
    for _ in range(vezes):
        context.resposta = context.cliente.post("/api/forgot-password", json={"email": email})


@then("no máximo {quantidade:d} e-mails de redefinição devem ter sido enviados")
def passo_emails_enviados(context, quantidade):
    assert 0 < len(context.emails) <= quantidade, context.emails


@when("um site de outra origem tenta criar uma conversa em meu nome")
def passo_outra_origem(context):
    context.resposta = context.cliente.post(
        "/api/chats", headers={"Origin": "https://site-malicioso.example"}
    )


@when("eu tento salvar como avatar o texto '{texto}'")
def passo_avatar_malicioso(context, texto):
    context.resposta = context.cliente.post("/api/account", json={"name": "Pessoa", "image": texto})


@when('eu envio para "{rota}" o campo "{campo}" com um número no lugar de texto')
def passo_campo_numerico(context, rota, campo):
    corpo = {"name": "Pessoa", "currentPassword": "x", campo: 12345}
    context.resposta = context.cliente.post(rota.replace("{c}", context.conversa_id), json=corpo)
