"""
Teste de interface no navegador (Playwright): o que os testes de API não
enxergam - a página monta, os avisos aparecem na tela, nada fica coberto,
a CSP não bloqueia nenhum recurso do próprio site e o layout cabe no celular.

Fica fora da suíte normal (pytest.ini só coleta tests/): precisa do
servidor no ar e cria contas no banco que ele usa (o de desenvolvimento).

    python app.py                                   # outro terminal
    python -m playwright install chromium           # uma vez
    E2E_BASE_URL=http://127.0.0.1:5000 python -m pytest e2e

No Windows dá para usar o Edge instalado, sem baixar o Chromium:
E2E_BROWSER_CHANNEL=msedge. Sem E2E_BASE_URL, os testes são ignorados.
"""

import os
import re
import time

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect, sync_playwright  # noqa: E402

BASE = (os.environ.get("E2E_BASE_URL") or "").rstrip("/")
pytestmark = pytest.mark.skipif(not BASE, reason="defina E2E_BASE_URL com o servidor no ar")

SENHA = "Senha-Forte-123!"
# Erros de rede esperados no console: 401 (visitante na landing, senha
# errada), 404 (página inexistente) e 502 (servidor sem GEMINI_API_KEY).
ESPERADOS = re.compile(r"Failed to load resource: .* (401|404|502)")


def _email_novo(prefixo):
    return f"{prefixo}{time.time_ns()}@exemplo.com"


def _esperar_js(page, expressao, timeout=10):
    # page.evaluate roda fora da CSP; wait_for_function usaria eval na página,
    # que a própria CSP do site (corretamente) bloqueia.
    fim = time.time() + timeout
    while time.time() < fim:
        if page.evaluate(expressao):
            return
        time.sleep(0.2)
    raise AssertionError("tempo esgotado esperando: " + expressao)


@pytest.fixture(scope="module")
def playwright_rodando():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="module")
def navegador(playwright_rodando):
    canal = os.environ.get("E2E_BROWSER_CHANNEL") or None
    browser = playwright_rodando.chromium.launch(channel=canal, headless=True)
    yield browser
    browser.close()


@pytest.fixture(scope="module")
def conta(playwright_rodando):
    """Conta criada pela API (o cadastro pela tela tem teste próprio)."""
    email = _email_novo("e2e")
    api = playwright_rodando.request.new_context(base_url=BASE)
    resposta = api.post("/api/signup", data={
        "email": email, "password": SENHA, "name": "Pessoa E2E", "acceptTerms": True, "acceptAi": True,
    })
    assert resposta.status == 201, resposta.text()
    api.dispose()
    return email


@pytest.fixture
def abrir(navegador):
    """Abre uma aba nova; no fim do teste, falha se houve erro de JS ou CSP."""
    problemas, contextos = [], []

    def _abrir(largura=1280, altura=800):
        contexto = navegador.new_context(viewport={"width": largura, "height": altura})
        contextos.append(contexto)
        page = contexto.new_page()
        page.on("console", lambda m: m.type == "error" and not ESPERADOS.search(m.text)
                and problemas.append(m.text))
        page.on("pageerror", lambda erro: problemas.append(str(erro)))
        return page

    yield _abrir
    for contexto in contextos:
        contexto.close()
    assert problemas == [], problemas


def _entrar(page, email):
    page.goto(BASE + "/login")
    page.fill("#email", email)
    page.fill("#password", SENHA)
    page.click("#login-form button[type=submit]")
    page.wait_for_url("**/dashboard")


def test_cadastro_pela_tela_leva_ao_login_com_aviso(abrir):
    page = abrir()
    page.goto(BASE + "/signup")
    page.fill("#email", _email_novo("cadastro"))
    page.fill("#name", "Pessoa Cadastro")
    page.fill("#password", SENHA)
    page.fill("#confirm-password", SENHA)
    page.check("#consent-terms")
    page.check("#consent-ai")
    page.click("button[type=submit]")
    page.wait_for_url("**/login?cadastro=ok")
    expect(page.locator("#login-notice")).to_contain_text("Conta criada")


def test_senha_errada_mostra_erro_e_a_certa_abre_o_painel(abrir, conta):
    page = abrir()
    page.goto(BASE + "/login")
    page.fill("#email", conta)
    page.fill("#password", "Senha-Errada-1!")
    page.click("#login-form button[type=submit]")
    expect(page.locator("#login-error")).to_be_visible()

    page.fill("#password", SENHA)
    page.click("#login-form button[type=submit]")
    page.wait_for_url("**/dashboard")
    expect(page.locator(".user-name")).to_have_text("Pessoa E2E")


def test_nome_com_aspas_aparece_como_texto_e_nao_executa(abrir, conta):
    page = abrir()
    _entrar(page, conta)
    page.goto(BASE + "/dashboard/account")
    page.click('.illustrated-avatar-btn[data-avatar-id="avatar_robot"]')
    page.fill("#name", 'Pessoa" onerror="window.__xss=1')
    page.click("#account-form button[type=submit]")
    expect(page.locator("#account-success")).to_be_visible()
    time.sleep(1.2)  # account.js recarrega a página depois de salvar
    page.goto(BASE + "/dashboard/account")
    avatar = page.locator(".avatar-slot img.avatar")
    expect(avatar).to_have_attribute("src", "/avatars/avatar_robot.svg")
    expect(avatar).to_have_attribute("alt", 'Pessoa" onerror="window.__xss=1')
    assert page.evaluate("window.__xss") is None


def test_mensagem_enviada_continua_na_tela_e_o_resultado_e_visivel(abrir, conta):
    page = abrir()
    _entrar(page, conta)
    page.fill("#welcome-input", "oi, tudo bem?")
    page.locator("#welcome-input").press("Enter")
    page.wait_for_url(re.compile(r".*/dashboard/chat/.+"), timeout=60000)
    expect(page.locator(".msg-user .msg-content").first).to_have_text("oi, tudo bem?")
    # Com GEMINI_API_KEY chega a resposta; sem, o aviso de falha. Os dois
    # precisam ficar visíveis dentro da tela.
    resultado = page.locator(".msg-assistant .msg-content, .ui-message").first
    expect(resultado).to_be_visible(timeout=60000)
    caixa = resultado.bounding_box()
    assert caixa and caixa["y"] + caixa["height"] <= 800


def test_configuracoes_mostram_a_conta_e_o_2fa(abrir, conta):
    page = abrir()
    _entrar(page, conta)
    page.goto(BASE + "/dashboard/settings")
    expect(page.locator("#account-info-email")).to_have_text(conta)
    expect(page.locator("#two-factor-status")).not_to_have_text("Consultando proteção da conta...")
    if page.locator("#two-factor-start").is_visible():  # servidor com TOTP_ENCRYPTION_KEY
        page.click("#two-factor-start")
        page.fill("#two-factor-password", SENHA)
        page.click("#two-factor-action-submit")
        _esperar_js(page, "document.getElementById('two-factor-qr').naturalWidth > 0")
        page.locator("#two-factor-enrollment [data-two-factor-cancel]").click()


def test_pagina_inexistente_e_sair_da_conta(abrir, conta):
    page = abrir()
    page.goto(BASE + "/pagina-que-nao-existe")
    expect(page.locator("h1")).to_have_text("Página não encontrada")
    _entrar(page, conta)
    page.click(".logout-btn")
    page.wait_for_url("**/login")


def test_login_usando_so_o_teclado_com_foco_visivel(abrir, conta):
    page = abrir()
    page.goto(BASE + "/login")
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.className") == "skip-link"
    for campo, texto in (("email", conta), ("password", SENHA)):
        for _ in range(6):  # avança pelo Tab até o campo, como uma pessoa faria
            if page.evaluate("document.activeElement.id") == campo:
                break
            page.keyboard.press("Tab")
        assert page.evaluate("document.activeElement.id") == campo
        # Foco visível (WCAG 2.4.7): o elemento focado tem contorno ou sombra.
        assert page.evaluate("""() => { const s = getComputedStyle(document.activeElement);
            return s.outlineStyle !== 'none' || s.boxShadow !== 'none'; }""")
        page.keyboard.type(texto)
    page.keyboard.press("Enter")
    page.wait_for_url("**/dashboard")


def test_celular_menu_alcancavel_e_sem_rolagem_horizontal(abrir, conta):
    page = abrir(375, 812)
    _entrar(page, conta)
    assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    page.locator(".topbar .sidebar-toggle").click()
    _esperar_js(page, "document.querySelector('.app-shell').classList.contains('sidebar-open')")
    page.goto(BASE + "/dashboard/account")
    assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
