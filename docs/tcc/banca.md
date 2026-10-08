# Preparação para a banca

Perguntas prováveis, resposta curta **baseada no sistema real** e onde está
a evidência. **Situação:** ✅ temos evidência · 🟡 parcial · ❌ ainda não temos
(o que fazer está na coluna). Respostas marcadas [PREENCHER] dependem do grupo.

## Problema e proposta
| Pergunta | Resposta curta | Evidência | Sit. |
|---|---|---|---|
| Qual problema o sistema resolve? | Falta de um espaço de baixa pressão para quem tem dificuldade de socialização desabafar, ensaiar e receber orientação prática. | `projeto.md` §1 | 🟡 faltam fontes |
| Por que esse problema? | [PREENCHER: motivação real do grupo] + dados com fonte. | — | ❌ |
| Quem é o usuário? | Jovens e adultos 18+ com dificuldade de socialização; não é para crise nem para menores. | `projeto.md` §3 | 🟡 sem contato com usuários |
| Como provam que ajuda as pessoas? | **Não provamos** - o trabalho comprova que o sistema funciona como especificado. A eficácia exigiria estudo com usuários (trabalho futuro). | `resultados.md` §3 | ✅ resposta honesta |
| Qual a diferença para usar o ChatGPT direto? | Personas com regras explícitas (sem romance, CVV em crise, incentivo ao mundo real, respostas curtas), histórico privado, consentimento específico, exclusão/exportação, sem anúncios. | `personalities.py`, `requisitos.md` RN23-25 | 🟡 as regras ainda não foram avaliadas com o modelo real |
| Por que uma persona humorística (MathIAs) num tema sério? | Parte do público só quer conversar leve; a seção de segurança vale acima do humor e textões vão para o TrashTalker. | RN15, RN24 | 🟡 avaliar IA-04 |

## Requisitos e metodologia
| Pergunta | Resposta curta | Evidência | Sit. |
|---|---|---|---|
| Quais são os requisitos? | 12 RF, 17 RNF, 22 regras de negócio + 3 regras de comportamento da IA. | `requisitos.md` | ✅ |
| Como os requisitos surgiram? | [PREENCHER] | — | ❌ |
| Qual foi a metodologia? | Iterativa, com testes antes da correção e especificação em Gherkin; [PREENCHER: gestão real]. | `metodologia-e-avaliacao.md` §1 | 🟡 |
| Como mostram que cada requisito foi implementado? | Matriz requisito → tela → código → cenário → teste → resultado. | `rastreabilidade.md` | ✅ |
| Usaram IA para desenvolver? | [PREENCHER conforme a regra da instituição] - a revisão de 2026-10 usou assistente de programação com IA, com revisão e testes. | `metodologia-e-avaliacao.md` §1 | 🟡 |

## Tecnologia e arquitetura
| Pergunta | Resposta curta | Evidência | Sit. |
|---|---|---|---|
| Por que Python/Flask? | Pequeno e explícito: uma API JSON com poucas rotas, sem a estrutura pesada de um framework maior. [PREENCHER: domínio do grupo] | `manual-tecnico.md` | 🟡 |
| Por que HTML/JS puro, sem React? | Sem etapa de build, cada página legível sozinha; o sistema é multipágina e pequeno. | `processo.md` §1 | ✅ |
| Por que PostgreSQL e não SQLite/MySQL? | Integridade (FK, CHECK, transações com `FOR UPDATE`, `ON CONFLICT`), arrays e datas com fuso; hospedagem gratuita serverless (Neon). Testes rodam no mesmo banco da produção. | `banco-de-dados.md`, `processo.md` D-04 | ✅ |
| Por que Gemini? | [PREENCHER: critério real - custo/cota gratuita, qualidade em português?]. A troca de modelo é uma constante em `ai.py`. | `ai.py` | 🟡 |
| Como funciona a arquitetura? | Navegador (HTML+JS) → API Flask JSON → PostgreSQL; Gemini e SMTP só pelo servidor. | diagramas em `manual-tecnico.md` | ✅ |
| E se o Gemini cair? | A mensagem fica salva, a pessoa vê um aviso, nada se perde; o áudio cai para a voz do navegador. | `test_falha_da_ia_*`, captura `img/11` | ✅ |
| Como escalaria? | Servidor sem estado (sessão no banco) → várias instâncias; gargalos seriam cota do Gemini e conexões ao banco (usar pool do Neon). Sem teste de carga. | `qualidade.md` §4 | 🟡 |

## Banco de dados
| Pergunta | Resposta curta | Evidência | Sit. |
|---|---|---|---|
| Como o banco foi modelado? | 9 tabelas; usuário no centro, conversas → mensagens, 2FA isolado, limite de tentativas sem FK (de propósito). | DER em `banco-de-dados.md` | ✅ |
| Por que ids aleatórios em texto? | Não revelam volume nem permitem adivinhar ids; ainda assim toda rota confere o dono. | `banco-de-dados.md` §5.1 | ✅ |
| `interests` como array fere a 1FN? | Sim, de forma consciente: lista pequena, lida/gravada inteira, nunca consultada por item. Normalizar se surgir essa consulta. | §5.3 | ✅ |
| Como garantem integridade? | PK/UNIQUE/FK com CASCADE/CHECK/NOT NULL, transações e operações atômicas contra corrida. | §5.8 + testes de concorrência | ✅ |
| Como apagam todos os dados de alguém? | Apagar o usuário apaga tudo por CASCADE; o registro de tentativas é apagado explicitamente. | `test_excluir_*` | ✅ |

## Segurança e privacidade
| Pergunta | Resposta curta | Evidência | Sit. |
|---|---|---|---|
| Como protegem as senhas? | Hash com sal (Werkzeug), política de senha forte, limite de tentativas, 2FA opcional. | `seguranca.md` §1 | ✅ |
| E SQL Injection? XSS? CSRF? | SQL sempre parametrizado; texto do usuário só como texto + CSP sem script inline; SameSite + checagem de origem. | `seguranca.md` §5-7 + testes | ✅ |
| E se o banco vazar? | Senhas, tokens e códigos estão em hash; segredo do 2FA cifrado com chave fora do banco. Conversas **não** são cifradas. | `seguranca.md` | 🟡 conversas em claro (limitação) |
| As conversas podem ter dado sensível. E a LGPD? | Consentimento específico no cadastro, aviso sobre o plano gratuito do Gemini, exportação e exclusão. | `privacy.html`, RF11 | ✅ |
| Como garantem 18+? | Autodeclaração no cadastro (limitação conhecida). | Termos §2 | ✅ (honesto) |
| E se alguém falar em suicídio? | O prompt manda levar a sério, sem piada, indicar CVV 188 e emergência. | RN24 | ❌ falta o protocolo A (IA-03/IA-04) |

## Testes e resultados
| Pergunta | Resposta curta | Evidência | Sit. |
|---|---|---|---|
| Como testaram o sistema? | 207 testes de API com banco real, 53 cenários Gherkin, 8 testes de navegador, auditoria de acessibilidade, análise estática. | `evidencias/` | ✅ |
| Testaram a IA? | Nos testes automáticos ela é simulada (de propósito: resultado determinístico e sem custo). O comportamento real tem protocolo próprio. | `tools/avaliar_ia.py` | ❌ rodar protocolo A |
| Quais bugs encontraram? | XSS no avatar, link de senha reutilizável em paralelo, erro 500 com dado malformado, aviso de erro fora da tela, entre outros. | `resultados.md` §1.2 | ✅ |
| Testaram com usuários? | Ainda não. | — | ❌ protocolo B |
| É acessível? | 0 violações WCAG 2.1 A/AA no axe-core, uso por teclado testado; falta leitor de tela e pessoas. | `qualidade.md` §3 | 🟡 |
| Como provam que funciona? | Demonstração ao vivo com roteiro fixo + testes rodando + matriz de rastreabilidade. | `demonstracao.md` | ✅ |

## Fechamento
| Pergunta | Resposta | Sit. |
|---|---|---|
| Quais as limitações? | Dependência do Gemini (custo, cota, privacidade no plano gratuito), eficácia não medida, idade autodeclarada, sem teste de carga. | ✅ `projeto.md` §7 |
| O que fariam diferente? | [PREENCHER] - sugestões reais do histórico: testar desde o início (os testes acharam defeitos tarde), começar pelo Gherkin dos requisitos, avaliar a IA antes de ampliar funcionalidades. | 🟡 |
| Maior dificuldade? | [PREENCHER] | ❌ |
| Trabalhos futuros? | Streaming, avaliação contínua da IA, exercícios guiados, plano pago da API, estudo com usuários. | ✅ `projeto.md` §6 |
