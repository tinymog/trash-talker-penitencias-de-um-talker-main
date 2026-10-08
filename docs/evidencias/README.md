# Evidências de execução

Saídas **reais** das verificações, gravadas sem edição (só os caminhos
locais da máquina foram trocados por `<projeto>`). Para gerar de novo:
`docs/testes.md`, seção "Gerar as evidências de execução".

**Execução de 2026-10-08.** Ambiente: Windows 10 Pro (10.0.19045),
Python 3.14.2, PostgreSQL 17.7 local, Microsoft Edge 154.0.4258.62 (headless,
via Playwright 1.63.0). A IA foi **simulada** nas suítes automáticas (ver
`docs/testes.md`, seção 5).

| Arquivo | Verificação | Resultado |
|---|---|---|
| [`pytest.txt`](pytest.txt) | Testes de API com banco real, um por linha | **207 passaram**, 0 falharam (70,50 s) |
| [`behave.txt`](behave.txt) | Cenários Gherkin em português, passo a passo | **53 cenários / 238 passos** passaram, 0 falharam |
| [`e2e.txt`](e2e.txt) | Testes de interface no navegador contra `python app.py` | **8 passaram** |
| [`unittest-diagnostico-2fa.txt`](unittest-diagnostico-2fa.txt) | Diagnóstico de permissão do 2FA sem banco | **3 passaram** |
| [`pyflakes.txt`](pyflakes.txt) | Análise estática de `backend`, `app.py`, `tests`, `features`, `tools`, `e2e` | Arquivo vazio = **nenhum aviso** |
| [`acessibilidade-axe.md`](acessibilidade-axe.md) (+ `.json` bruto) | axe-core 4.11, WCAG 2.1 A/AA, 14 páginas × 2 temas | **0 violações** |
| [`benchmark-local.md`](benchmark-local.md) | Tempo de 2 rotas, servidor e banco locais | ver arquivo (não representa produção) |

**Não há aqui** (não executado): avaliação real da IA (`tools/avaliar_ia.py`),
teste com usuários, verificação na Vercel, Lighthouse. Ver
`docs/tcc/resultados.md`, seção 2.

## Antes das correções (referência)
Na revisão de outubro de 2026, a suíte original foi rodada **antes** de
qualquer mudança: 138 testes passaram e os 58 testes novos, escritos para
reproduzir os defeitos encontrados, falharam (ex.: o mesmo link de
redefinição de senha aceito 4 vezes em paralelo; cadastro simultâneo
terminando em erro 500). Essa saída não foi guardada em arquivo - está
descrita em `docs/tcc/resultados.md` §1.2 e nas decisões D-07 a D-16 de
`docs/processo.md`.
