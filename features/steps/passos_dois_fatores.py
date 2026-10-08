# language: pt
"""Passos do 2FA (Google Authenticator), pela mesma API que a tela de Configurações usa."""

from datetime import datetime, timedelta, timezone

import pyotp
from behave import given, then, when

from passos_comuns import EMAIL_PADRAO, SENHA_PADRAO, logar


def _codigo_novo(context):
    # Cada intervalo de 30 s só vale uma vez; o próximo intervalo também é
    # aceito (tolerância de relógio), então ele nunca colide com o já usado.
    agora = datetime.now(timezone.utc) + timedelta(seconds=30 * context.codigos_usados)
    context.codigos_usados += 1
    return pyotp.TOTP(context.segredo_2fa).at(agora)


@when("eu inicio a ativação do 2FA com a minha senha")
def passo_inicia_ativacao(context):
    resposta = context.cliente.post("/api/2fa/setup", json={"password": SENHA_PADRAO})
    assert resposta.status_code == 200, resposta.get_json()
    context.segredo_2fa = resposta.get_json()["manualKey"]
    context.codigos_usados = 0


@when("eu confirmo a ativação com um código válido do aplicativo")
def passo_confirma_ativacao(context):
    context.resposta = context.cliente.post("/api/2fa/confirm", json={"code": _codigo_novo(context)})
    assert context.resposta.status_code == 200, context.resposta.get_json()
    context.codigos_recuperacao = context.resposta.get_json()["recoveryCodes"]


@given("que a proteção em dois fatores está ativa na minha conta")
def passo_2fa_ativo(context):
    passo_inicia_ativacao(context)
    passo_confirma_ativacao(context)


@then("a proteção em dois fatores deve estar ativa")
def passo_2fa_esta_ativo(context):
    assert context.cliente.get("/api/2fa/status").get_json()["enabled"] is True


@then("eu devo ter recebido {quantidade:d} códigos de recuperação")
def passo_codigos_recebidos(context, quantidade):
    assert len(set(context.codigos_recuperacao)) == quantidade


@given("que eu saí e informei minha senha de novo")
def passo_sai_e_informa_senha(context):
    context.cliente.post("/api/logout")
    resposta = logar(context.cliente, EMAIL_PADRAO, SENHA_PADRAO)
    assert resposta.status_code == 202, resposta.get_json()
    context.desafio_2fa = resposta.get_json()["challengeToken"]


def _informa(context, codigo):
    context.resposta = context.cliente.post(
        "/api/login/2fa", json={"challengeToken": context.desafio_2fa, "code": codigo}
    )


@when("eu informo um código válido do aplicativo")
def passo_informa_codigo_valido(context):
    _informa(context, _codigo_novo(context))


@when('eu informo o código "{codigo}"')
def passo_informa_codigo(context, codigo):
    _informa(context, codigo)


@given("que eu entrei com um código de recuperação")
def passo_entrei_com_recuperacao(context):
    context.codigo_recuperacao_usado = context.codigos_recuperacao[0]
    _informa(context, context.codigo_recuperacao_usado)
    assert context.resposta.status_code == 200, context.resposta.get_json()


@when("eu informo o mesmo código de recuperação")
def passo_informa_mesmo_recuperacao(context):
    _informa(context, context.codigo_recuperacao_usado)
