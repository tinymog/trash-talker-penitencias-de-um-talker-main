# Estrutura da apresentação

Duração total: **[PREENCHER: tempo dado pela banca]**. Os tempos abaixo são
proporções para **20 minutos**; ajuste mantendo a demonstração como o maior bloco.

| # | Bloco | Tempo | O que mostrar | Base |
|---|---|---|---|---|
| 1 | Abertura | 0:30 | Nome, equipe, orientador, frase "jogue o silêncio fora" | [PREENCHER] |
| 2 | Problema | 1:30 | O problema em uma frase + **1 dado com fonte** | `projeto.md` §1 |
| 3 | Objetivo e escopo | 1:00 | Objetivo geral; quadro FAZ / NÃO FAZ (deixa claro que não é terapia) | `projeto.md` §4, §6 |
| 4 | A solução | 1:30 | As duas personas e as regras que as limitam (sem romance, CVV, mundo real) | `requisitos.md` RN15, RN23-25 |
| 5 | **Demonstração** | 6:00 | Roteiro de `demonstracao.md` | `demonstracao.md` |
| 6 | Arquitetura | 1:00 | Um diagrama: navegador → API → banco; Gemini/SMTP só pelo servidor | `manual-tecnico.md` §1 |
| 7 | Banco de dados | 1:00 | DER simplificado (users, chats, messages + "dados de segurança") e uma decisão defendida (ex.: CASCADE para a LGPD) | `banco-de-dados.md` |
| 8 | Segurança e privacidade | 1:30 | 4 proteções com o defeito que motivou cada uma (XSS, link reutilizável, força bruta, tokens em hash) | `seguranca.md`, `resultados.md` §1.2 |
| 9 | Testes | 2:00 | Os números; um cenário Gherkin em português na tela; a matriz de rastreabilidade (uma linha como exemplo); antes → depois | `rastreabilidade.md`, `evidencias/` |
| 10 | Resultados | 1:00 | O que foi comprovado e, se feitos, os resultados da avaliação da IA e do SUS | `resultados.md` |
| 11 | Limitações e futuro | 1:00 | Eficácia não medida, dependência do Gemini; próximos passos | `projeto.md` §6-7 |
| 12 | Conclusão | 0:30 | Objetivos atingidos (tabela OE1-OE8 com ✅/🔶) | `projeto.md` §4 |

## O que **não** merece slide
- Lista completa de requisitos, rotas da API ou tabelas (fica no documento;
  mostrar se perguntarem).
- Código-fonte (no máximo um trecho curto, se ilustrar uma decisão de segurança).
- Explicação genérica de Python, Flask ou PostgreSQL - a banca quer saber
  **por que** foram escolhidos, não o que são.
- Prints de todas as telas - a demonstração já mostra.

## Materiais de apoio (deixar abertos em abas)
- `docs/rastreabilidade.md`, `docs/requisitos.md`, `docs/banco-de-dados.md`
  (DER), `docs/tcc/banca.md` para consulta rápida durante as perguntas.
- `docs/evidencias/` com as saídas dos testes.
- Vídeo da demonstração gravado (plano B).
