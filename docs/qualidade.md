# Qualidade de software

Avaliação do Trash Talker pelas características de qualidade de produto da
norma ISO/IEC 25010 (usada aqui como roteiro; a referência precisa ser
conferida e formatada - ver `tcc/fundamentacao-teorica.md`). Cada afirmação
aponta para uma evidência; o que ainda não tem evidência está marcado.

Medidas de 2026-10-08: backend 2.807 linhas (Python + SQL, 14 arquivos),
frontend 2.988 linhas de JavaScript + 3.682 de HTML/CSS, testes 3.100 linhas
(207 casos pytest, 53 cenários Behave, 8 testes de navegador).

## 1. Adequação funcional
**Evidência:** todos os requisitos RF01-RF12 têm cenário e/ou teste
automatizado passando (`rastreabilidade.md`).
**Lacuna:** o comportamento da IA (RN23-RN25) - a parte que responde
diretamente ao problema - ainda não foi verificado com o modelo real
(protocolo pronto, **A REALIZAR**).

## 2. Confiabilidade
| Aspecto | Evidência |
|---|---|
| Falha da IA não perde dados | `test_falha_da_ia_devolve_502_sem_perder_a_mensagem_do_usuario`; cenário Behave |
| Erro inesperado não derruba nem vaza | handler 500 (`test_erro_inesperado_*`); rollback (`test_erro_interno_reverte_consumo_do_codigo`) |
| Concorrência | 3 testes com requisições simultâneas reais (`rastreabilidade.md`, RNF09) |
| Conexão derrubada pelo banco serverless | descarte + nova tentativa (`db._with_retry`) - **sem teste** (exigiria derrubar conexões do servidor) |
| Disponibilidade em produção | **NÃO MEDIDA** (depende da Vercel/Neon/Gemini; plano gratuito) |

## 3. Usabilidade e acessibilidade
| Aspecto | Evidência | Resultado |
|---|---|---|
| Conformidade WCAG 2.1 A/AA verificável por ferramenta | axe-core 4.11 em 14 páginas × tema claro/escuro (`evidencias/acessibilidade-axe.md`) | **0 violações**; 588 aprovações de regra (soma das 28 execuções); 8 itens inconclusivos (2 tipos) revisados à mão, com contraste medido de 13,36:1 e 14,71:1 |
| Uso só pelo teclado, foco visível | e2e `test_login_usando_so_o_teclado_com_foco_visivel`; foco visível global no CSS (`:focus-visible`) | ✅ |
| Celular | e2e em 375 px: sem rolagem horizontal, menu e campo de mensagem alcançáveis | ✅ |
| Feedback de ações | avisos de sucesso/erro em todos os formulários; estado "Preparando resposta…"; estado vazio da lista | ✅ (capturas em `img/`) |
| Movimento reduzido | `@media (prefers-reduced-motion)` no CSS | presente, não testado |
| Leitor de tela (NVDA/VoiceOver) | — | **A REALIZAR** (manual) |
| Satisfação/facilidade percebida por usuários | — | **A REALIZAR**: teste de usabilidade com SUS (`tcc/metodologia-e-avaliacao.md`) |

Limite da ferramenta: verificação automática encontra só parte dos
problemas de acessibilidade; não substitui teste com pessoas e com leitor de tela.

## 4. Eficiência de desempenho
Única medição feita: **B1 local** (servidor e banco na mesma máquina, não
representa produção) - `/api/me` mediana 3,3 ms e `/api/dashboard` 3,8 ms
(`evidencias/benchmark-local.md`). Nenhum outro tempo é afirmado. Análise do código:

| Observação | Situação |
|---|---|
| Foto do avatar (até ~350 mil caracteres) era lida do banco em **toda** requisição autenticada | **Corrigido** (só painel e `/api/me`; `test_avatar_volta_no_painel_e_no_me_mas_nao_em_toda_requisicao`) |
| Conversa inteira ia para a IA a cada mensagem | **Corrigido**: últimas 40 (RN16) |
| Sessão validada com uma consulta (JOIN) por requisição | adequado |
| Enviar mensagem faz de 8 a 11 idas ao banco em sequência, cada uma numa transação curta | aceitável: o tempo do Gemini (segundos) domina; agrupar em uma transação é melhoria possível - quantificar no B1/B2 |
| Lista de conversas sem paginação | adequado ao porte; paginar se uma conta passar de centenas de conversas |
| Páginas do painel carregam 9-10 arquivos JS sem minificação (~220 KB de JS+CSS no total do site) | escolha consciente (sem build); cache de 1 h na Vercel |
| SDK do Gemini importado só quando usado | reduz o *cold start* da função serverless |
| `getDashboard()` compartilhado entre scripts da página; áudio do TTS reaproveitado na mesma bolha | evita requisições repetidas |

### BENCHMARK A REALIZAR
| ID | O que medir | Como | Registrar |
|---|---|---|---|
| B1 | Tempo das rotas sem IA | Servidor local com o banco que será usado na apresentação (Neon ou local), conta demo (`python -m tools.seed_demo`). Rodar o script abaixo 2 vezes (descartar a 1ª, que aquece o pool). **Feito só com banco local** (`evidencias/benchmark-local.md`); falta com o Neon. | mediana e p95 por rota; banco usado; máquina |
| B2 | Tempo de resposta da IA por nível de esforço | Com `GEMINI_API_KEY`: 20 mensagens iguais em conversas novas, 10 em "Mais rápida" e 10 em "Mais elaborada"; medir do envio à resposta (aba Rede do navegador, coluna Tempo). | mediana e máximo por nível; data e modelo |
| B3 | Carregamento das páginas | Lighthouse (DevTools do Chrome/Edge > Lighthouse > Mobile) em `/`, `/login`, `/dashboard`, numa janela anônima, no site publicado. | pontuação de Desempenho e LCP de cada página |

```python
# B1 - salve como medir.py e rode: python medir.py  (servidor no ar, conta demo criada)
import json, statistics, time, urllib.request
from http.cookiejar import CookieJar
BASE = "http://127.0.0.1:5000"
abrir = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar())).open
login = urllib.request.Request(BASE + "/api/login", method="POST", headers={"Content-Type": "application/json"},
    data=json.dumps({"email": "demo@trashtalker.example", "password": "Demo-Banca-2026!"}).encode())
abrir(login).read()
for rota in ["/api/me", "/api/dashboard"]:
    tempos = []
    for _ in range(100):
        inicio = time.perf_counter(); abrir(BASE + rota).read(); tempos.append((time.perf_counter() - inicio) * 1000)
    tempos.sort()
    print(rota, "mediana %.1f ms" % statistics.median(tempos), "p95 %.1f ms" % tempos[94])
```

## 5. Compatibilidade e portabilidade
| Ambiente | Situação |
|---|---|
| Windows 10 + Python 3.14 + PostgreSQL 17.7 | ✅ testado (todas as suítes) |
| Microsoft Edge (Chromium), desktop e 375 px | ✅ testado (e2e e capturas) |
| Python 3.10-3.13, Linux/macOS | não testado (sem recurso específico de versão no código - **INFERÊNCIA**) |
| Chrome, Firefox, Safari | não testado; o Firefox não tem ditado por voz (o botão some, por desenho) |
| Vercel + Neon | configuração presente (`vercel.json`, `DEPLOY_VERCEL.md`); **não verificado** neste ambiente |

## 6. Segurança
Ver [`seguranca.md`](seguranca.md): cada proteção com o teste que a prova.
**Não executado:** varredura automatizada e teste de invasão. Procedimento
sugerido: OWASP ZAP *baseline scan* contra uma cópia publicada (nunca
contra a produção com dados reais), registrando alertas e o que foi feito
com cada um.

## 7. Manutenibilidade
| Aspecto | Evidência |
|---|---|
| Módulos com uma responsabilidade cada | `manual-tecnico.md`, seção 2; maior arquivo do backend: 375 linhas |
| Regras e limites em constantes nomeadas | RN01-RN22 apontam para a constante (`requisitos.md`) |
| Testes como rede de proteção | 207 + 53 + 8; rodam em ~1 min |
| Análise estática | `pyflakes` sem avisos |
| Decisões registradas | `processo.md` (D-01 a D-17), divergências e riscos |
| Banco evolui sem perder dados | `schema.sql` idempotente, testado |
| Ausências | sem integração contínua (CI) configurada; sem histórico Git nesta cópia |
