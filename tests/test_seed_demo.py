"""
Dados de demonstração (tools/seed_demo.py): a apresentação do TCC depende
deles, então eles precisam continuar válidos a cada mudança do esquema.
"""

import pytest

from backend import db
from conftest import logar
from tools import seed_demo


def test_seed_cria_conta_demo_que_consegue_entrar_e_ver_as_conversas(cliente):
    assert seed_demo.seed() is True

    assert logar(cliente, email=seed_demo.DEMO_EMAIL, senha=seed_demo.DEMO_PASSWORD).status_code == 200
    painel = cliente.get("/api/dashboard").get_json()
    assert [c["title"] for c in painel["chats"]] == ["A semana no curso", "Puxar assunto no intervalo"]
    assert painel["needsConsent"] is False

    semana = cliente.get(f"/api/chats/{painel['chats'][0]['id']}").get_json()["messages"]
    assert [(m["role"], m["personality"]) for m in semana] == [
        ("user", None), ("assistant", "mathias"), ("assistant", "trashtalker"),
    ]
    assert len(semana[0]["content"]) > 800  # o textão que dispara a "preguiça" do MathIAs


def test_seed_nao_duplica_nem_altera_conta_existente(cliente):
    assert seed_demo.seed() is True
    assert seed_demo.seed() is False
    assert db.query_one("SELECT count(*) AS total FROM chats")["total"] == 2


def test_seed_recusa_rodar_em_producao(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    with pytest.raises(SystemExit):
        seed_demo.main()
    assert db.query("SELECT id FROM users") == []
