# Trash Talker como TCC - diagnóstico, checklist e plano

Auditoria de 2026-10-08: o projeto avaliado como TCC técnico de
Desenvolvimento de Sistemas. Regra usada: só conta como ✅ o que foi
verificado no conteúdo (não basta o arquivo existir).

## Diagnóstico

**Existe um TCC de verdade por trás do sistema - do lado técnico, ele já é
defensável; do lado acadêmico, ainda não.**

- **Forte:** sistema completo e coerente com a proposta; requisitos, casos de
  uso, banco e arquitetura documentados a partir do código; verificação em
  várias camadas com resultados reais (207 testes de API, 53 cenários Gherkin
  em português, 8 testes de navegador, auditoria de acessibilidade sem
  violações); rastreabilidade completa; histórico de defeitos encontrados e
  corrigidos com prova (antes → depois); segurança e LGPD tratadas como requisito.
- **Fraco:** o problema é humano (socialização), mas toda a evidência é
  técnica. O comportamento das personas - o que mais diferencia o projeto -
  está só no prompt e **nunca foi avaliado com o modelo real**. Não há
  contato com usuários, fundamentação com referências, metodologia descrita
  pelo grupo nem texto acadêmico.
- **Consequência:** hoje o trabalho se sustenta como **"desenvolvimento e
  verificação de um sistema"**. Para afirmar algo sobre o problema, faltam o
  protocolo A (IA) e, idealmente, o B (usabilidade).

## Checklist

✅ completo · 🟡 parcial · ❌ ausente · ⚠️ precisa ser revisado/decidido

### Projeto
| Item | Status | Observação |
|---|---|---|
| Problema | 🟡 | Formulado em `projeto.md`; sem fontes |
| Proposta de solução | ✅ | `projeto.md` §2 |
| Público-alvo | 🟡 | Definido; sem contato com o público |
| Objetivo geral | ⚠️ | Proposto; validar com orientador |
| Objetivos específicos | ⚠️ | OE1-OE8 propostos e ligados a requisitos; validar |
| Justificativa | 🟡 | Eixos definidos; sem fontes |
| Escopo | ✅ | Faz / não faz / futuro, coerente com o código |
| Limitações | ✅ | `projeto.md` §7 |

### Requisitos
| Item | Status | Observação |
|---|---|---|
| Requisitos funcionais | ✅ | 12, com critérios de aceitação |
| Requisitos não funcionais | ✅ | 17, com critério verificável |
| Regras de negócio | ✅ | RN01-RN22 (código) + RN23-RN25 (IA) |
| Critérios de aceitação | ✅ | Em cada RF |
| Casos de uso | ✅ | 14 especificados; imagem do diagrama a gerar (PlantUML pronto) |
| Rastreabilidade | ✅ | `../rastreabilidade.md` |

### Desenvolvimento
| Item | Status | Observação |
|---|---|---|
| Arquitetura | ✅ | Diagramas de componentes, sequência e navegação (imagens em `../img/diagramas/`) |
| Tecnologias | 🟡 | Lista e versões prontas; falta o "por que" de cada escolha [grupo] |
| Estrutura do projeto | ✅ | README, manual técnico |
| Padrões utilizados | ✅ | Convenções em `processo.md` §2 |
| Decisões técnicas | ✅ | D-01 a D-17 |
| Organização do código | ✅ | Módulos com responsabilidade única; lint limpo |

### Banco de dados
| Item | Status | Observação |
|---|---|---|
| Modelo conceitual / lógico / DER | ✅ | `banco-de-dados.md` (DER em Mermaid) |
| Tabelas, relacionamentos, chaves | ✅ | Dicionário de dados completo |
| Constraints e integridade | ✅ | PK/FK/UNIQUE/CHECK/transações, com testes |
| Scripts | ✅ | `schema.sql` idempotente |
| Dados de teste | ✅ | Fixtures dos testes + `tools/seed_demo.py` |

### Interface
| Item | Status | Observação |
|---|---|---|
| Telas | ✅ | 16 capturas reais em `../img/` |
| Fluxo de navegação | ✅ | Diagrama em `manual-tecnico.md` |
| Responsividade | ✅ | Teste em 375 px |
| Acessibilidade | 🟡 | 0 violações automáticas + teclado; falta leitor de tela |
| Consistência visual | ✅ | Um CSS, temas claro/escuro |
| Usabilidade | ❌ | Sem teste com pessoas (protocolo B) |

### Testes
| Item | Status | Observação |
|---|---|---|
| Unitários | 🟡 | Poucos isolados (diagnóstico 2FA, protocolo da IA); a lógica é testada pela API - escolha explicada em `../testes.md` |
| Integração | ✅ | 207 testes HTTP + PostgreSQL real |
| Funcionais / aceitação / BDD | ✅ | 53 cenários Gherkin em português |
| Interface | ✅ | 8 testes no navegador |
| Positivos, negativos, extremos | ✅ | Limites, tipos inválidos, concorrência, falha da IA |
| Evidências e resultados | ✅ | `../evidencias/` |
| Comportamento da IA | ❌ | Protocolo pronto; **não executado** |

### Qualidade
| Item | Status | Observação |
|---|---|---|
| Revisão de código | ✅ | Revisões registradas (D-07 a D-17) |
| Segurança | ✅ | `../seguranca.md`; ⚠️ R-01 (rotacionar credencial) |
| Desempenho | 🟡 | Análise + medição local; benchmarks em produção a realizar |
| Tratamento de erros / validação | ✅ | Testados |
| Manutenção / riscos | ✅ | `../processo.md` |

### Documentação
| Item | Status | Observação |
|---|---|---|
| README / instalação | ✅ | |
| Manual do usuário | 🟡 | Pronto; falta a URL de produção |
| Documentação técnica / banco / requisitos / testes | ✅ | |
| Metodologia | 🟡 | Reconstituída; falta a do grupo |
| Referências | ❌ | Só roteiro e 5 referências já citadas no projeto |
| Limitações / trabalhos futuros | ✅ | |

### Texto do TCC
| Item | Status | Observação |
|---|---|---|
| Introdução | ❌ | Roteiro em `monografia.md` |
| Problema de pesquisa | 🟡 | Proposto |
| Hipótese | ⚠️ | Recomendado não ter, salvo exigência (`projeto.md` §1) |
| Justificativa, objetivos | 🟡 | Propostos |
| Metodologia | 🟡 | Parcial |
| Fundamentação teórica | ❌ | Roteiro de conceitos e fontes |
| Desenvolvimento, banco, arquitetura | 🟡 | Material pronto; texto não |
| Resultados | 🟡 | Só técnicos |
| Conclusão | ❌ | Depois dos resultados |
| Referências | ❌ | |
| Apêndices | ✅ | Material pronto (lista em `monografia.md`) |

## Prioridades

### Bloqueadores (sem isso o TCC não está pronto)
1. **Validar problema e objetivos** com o orientador e achar fontes para o problema.
2. **Executar o protocolo A** (avaliação da IA) - é a única evidência de que as regras das personas funcionam.
3. **Escrever o texto acadêmico**: introdução, fundamentação com referências reais, metodologia real, resultados, conclusão.
4. **R-01:** rotacionar a senha do banco que vazou no histórico público (se o repositório for/ficar público).
5. **Ambiente da apresentação definido e testado**: produção (aplicar `schema.sql`; todos precisarão entrar de novo por causa do D-15) **ou** local.

### Importantes
6. Protocolo B (tarefas + SUS) com alguns participantes.
7. Completar a metodologia (gestão, papéis, cronograma) e a declaração de uso de IA.
8. Ter o projeto num repositório Git com histórico (esta cópia não tem) - é evidência de processo.
9. Gravar o vídeo da demonstração (plano B).
10. Benchmarks B1 (no banco de produção), B2 e B3.

### Recomendados
11. Teste com leitor de tela (NVDA).
12. Verificar ditado e áudio manualmente (RF12).
13. Integração contínua rodando pytest e Behave a cada envio ao repositório.
14. Gerar a imagem do diagrama de casos de uso (colar o PlantUML de `../casos-de-uso.md` num renderizador) - os outros 5 diagramas já estão exportados em `../img/diagramas/`.

### Opcionais
15. Trabalhos futuros de `projeto.md` §6 (streaming, limite de cadastro por IP, PWA).

## Plano

**Estado atual → TCC pronto para entrega**
1. Reunião com o orientador levando `projeto.md` (problema, objetivos, escopo) e `banca.md`.
2. Pesquisa bibliográfica guiada por `fundamentacao-teorica.md`.
3. Protocolo A (1 dia com a chave do Gemini) → ajustar prompt se preciso → registrar.
4. Protocolo B, se o cronograma permitir (preparar termo, 5+ participantes, 1-2 dias).
5. Escrever os capítulos seguindo `monografia.md`; anexar os apêndices prontos.
6. Revisão final: cada afirmação do texto aponta para uma evidência em `docs/`.

**TCC entregue → pronto para apresentação**
7. Slides pela estrutura de `apresentacao.md`.
8. Ensaiar a demonstração (`demonstracao.md`) no ambiente real; gravar o vídeo.
9. Ensaiar as respostas de `banca.md`, completando os [PREENCHER].
10. Na véspera: rodar as suítes de teste e salvar a saída nova em `docs/evidencias/`.

## Índice deste material
| Arquivo | Conteúdo |
|---|---|
| [`projeto.md`](projeto.md) | Problema, objetivos, justificativa, escopo, limitações, cadeia de coerência |
| [`metodologia-e-avaliacao.md`](metodologia-e-avaliacao.md) | Metodologia; protocolos da IA e de usabilidade (SUS) |
| [`fundamentacao-teorica.md`](fundamentacao-teorica.md) | Conceitos e fontes a pesquisar |
| [`resultados.md`](resultados.md) | Comprovado × a obter |
| [`monografia.md`](monografia.md) | Esqueleto das 17 seções |
| [`banca.md`](banca.md) | Perguntas prováveis e evidências |
| [`apresentacao.md`](apresentacao.md) | Estrutura dos slides |
| [`demonstracao.md`](demonstracao.md) | Roteiro da demo e plano B |

Documentação técnica (em `docs/`): `requisitos.md`, `rastreabilidade.md`,
`casos-de-uso.md`, `banco-de-dados.md`, `manual-tecnico.md`, `seguranca.md`,
`qualidade.md`, `manual-do-usuario.md`, `testes.md`, `processo.md`, `evidencias/`.
