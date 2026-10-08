"""
Protocolo de avaliação da IA (tools/avaliar_ia.py). Aqui a IA é simulada: o
teste prova que o protocolo roda todos os casos, registra a resposta sem
alterá-la, não para quando uma chamada falha e deixa a avaliação para uma
pessoa. A execução com o modelo real está em docs/tcc/metodologia-e-avaliacao.md.
"""

from backend.personalities import PERSONALITIES
from tools import avaliar_ia


def test_relatorio_tem_todos_os_casos_com_resposta_e_avaliacao_em_branco():
    chamadas = []

    def _ia(history, user, personality, effort):
        chamadas.append((history, personality, effort))
        return f"resposta simulada {len(chamadas)}\nsegunda linha"

    relatorio = avaliar_ia.avaliar(gerar=_ia)

    assert len(chamadas) == len(avaliar_ia.CASOS)
    for caso in avaliar_ia.CASOS:
        assert f"## {caso['id']}" in relatorio
        assert caso["mensagem"] in relatorio
    # Cada caso é uma conversa nova, com uma mensagem só.
    assert all(len(history) == 1 for history, _, _ in chamadas)
    assert "> resposta simulada 1\n> segunda linha" in relatorio
    assert relatorio.count("[ ] Atende  [ ] Atende parcialmente  [ ] Não atende") == len(avaliar_ia.CASOS)


def test_falha_em_um_caso_nao_interrompe_os_outros():
    def _ia(history, user, personality, effort):
        if "namorar" in history[0]["content"]:
            raise RuntimeError("cota esgotada")
        return "ok"

    relatorio = avaliar_ia.avaliar(gerar=_ia)
    assert "ERRO NA CHAMADA: RuntimeError: cota esgotada" in relatorio
    assert relatorio.count("> ok") == len(avaliar_ia.CASOS) - 1


def test_casos_usam_so_personas_que_existem():
    assert {caso["persona"] for caso in avaliar_ia.CASOS} <= set(PERSONALITIES)
