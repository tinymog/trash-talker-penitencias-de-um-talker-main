# Resultados

Separação estrita entre o que **já foi comprovado** (com a evidência) e o
que **ainda precisa ser obtido**. No texto do TCC, só a primeira parte pode
aparecer como resultado.

## 1. Resultados já comprovados

### 1.1 O sistema cumpre os requisitos especificados
| Evidência | Resultado (2026-10-08) | Onde ver |
|---|---|---|
| Testes de API com banco PostgreSQL real | 207 passaram, 0 falharam | `../evidencias/pytest.txt` |
| Cenários de comportamento em Gherkin (pt-BR) | 53 cenários / 238 passos passaram | `../evidencias/behave.txt` |
| Testes de interface no navegador (Edge) | 8 passaram | `../evidencias/e2e.txt` |
| Rastreabilidade | RF01-RF12 e RNF01-RNF17 com prova (exceto itens ⏸️/🔶 da matriz) | `../rastreabilidade.md` |
| Telas reais | 16 capturas (desktop, celular, tema escuro) | `../img/`, `../manual-do-usuario.md` |

### 1.2 A verificação encontrou e corrigiu defeitos reais (antes → depois)
Na revisão de outubro de 2026, testes novos foram escritos **antes** das
correções. No código anterior, a suíte original passava inteira, mas **58
testes novos falharam**, expondo os problemas abaixo; depois das correções,
todos passam (`../processo.md`, D-07 a D-17).

| Defeito encontrado | Como foi demonstrado | Correção |
|---|---|---|
| `python app.py` não iniciava o servidor | inspeção + execução | D-07 |
| Dados malformados derrubavam rotas (erro 500) | 21 casos parametrizados falharam (11 em rotas públicas, 10 em autenticadas) | D-08 |
| XSS armazenado pelo nome/avatar | teste com `"` no atributo; confirmado no navegador | D-09 |
| Link de redefinição de senha usado 4 vezes em paralelo, com 4 sucessos | teste de concorrência | D-12 |
| Cadastro simultâneo do mesmo e-mail → erro 500 | teste de concorrência | D-12 |
| Sem limite de tentativas de login | teste (10 falhas não bloqueavam) | D-10 |
| Alterar conversa de outra pessoa respondia "ok" | 4 casos | D-06 |
| Aviso de erro do chat aparecia fora da tela | medição no navegador (topo em 808 px numa tela de 800 px) | `ui.js` |
| Aviso de cookies cobria o botão Sair, o campo de mensagem e o menu | teste no navegador (clique bloqueado) | CSS |
| Tokens de sessão/redefinição em texto puro no banco | teste comparando cookie × banco | D-15 |
| Exclusão da conta deixava o e-mail no registro de tentativas (contra a Política de Privacidade) | teste | D-16 |
| Foto do avatar lida do banco em toda requisição | teste | D-16 |
| Dados da demonstração não acionavam a regra que deveriam mostrar (737 < 800 caracteres) | teste do seed | `tools/seed_demo.py` |
| Código novo num banco sem o `schema.sql` da versão: todo login dava 500 sem pista da causa | ocorreu no uso, com o banco Neon; reproduzido e corrigido aplicando o esquema | D-17 (mensagem clara no log + 503) |

### 1.3 Acessibilidade verificável por ferramenta
axe-core 4.11 (WCAG 2.1 A/AA) em 14 páginas, temas claro e escuro:
**0 violações**; 8 itens inconclusivos (2 tipos) revisados manualmente -
contraste medido de 13,36:1 e 14,71:1, acima do mínimo de 4,5:1; login
completo só pelo teclado com foco visível (`../evidencias/acessibilidade-axe.md`).

### 1.4 Desempenho (medição local, não representa produção)
`/api/me` mediana 3,3 ms e `/api/dashboard` 3,8 ms, com servidor e banco na
mesma máquina (`../evidencias/benchmark-local.md`). Não é evidência de
desempenho em produção.

## 2. Resultados a obter

| # | Resultado | Por que importa | Como obter | Situação |
|---|---|---|---|---|
| A | As respostas reais da IA seguem as regras (limite romântico, CVV, formato) | Liga o sistema ao problema; é o que a banca mais vai questionar | Protocolo A (`metodologia-e-avaliacao.md`) | **A REALIZAR** (precisa de `GEMINI_API_KEY`) |
| B | Pessoas conseguem usar e acham fácil | Usabilidade além da ferramenta automática | Protocolo B (tarefas + SUS) | **A REALIZAR** |
| C | Sistema publicado funcionando | Mostra que roda fora da máquina do grupo | Deploy na Vercel + checklist do `DEPLOY_VERCEL.md` + captura dos cabeçalhos | **PENDENTE DE EVIDÊNCIA** |
| D | Tempos em produção | Eficiência real | B1 contra o Neon, B2 e B3 (`../qualidade.md`) | **BENCHMARK A REALIZAR** |
| E | Acessibilidade com leitor de tela | Complementa a ferramenta | NVDA (Windows) percorrendo cadastro, conversa e configurações | **A REALIZAR** |
| F | Ditado e "ouvir" funcionando | RF12 sem simulação | Chrome/Edge com microfone + chave do Gemini | **A REALIZAR** (manual) |

## 3. O que NÃO pode ser afirmado (por enquanto)
- Que o Trash Talker **ajuda** pessoas a socializar ou reduz ansiedade.
- Que a IA **sempre** respeita as regras (mesmo depois do protocolo A, a
  afirmação correta é "nas N rodadas testadas, X de Y respostas atenderam").
- Qualquer número de usuários, satisfação ou tempo em produção.
