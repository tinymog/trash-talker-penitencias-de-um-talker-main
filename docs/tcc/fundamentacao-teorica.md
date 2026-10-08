# Fundamentação teórica - roteiro

Este arquivo **não** é o capítulo pronto: é a lista do que precisa ser
explicado, por que entra no trabalho e onde aparece no sistema. Nenhuma
referência abaixo foi lida ou resumida para você - todas precisam ser
consultadas, conferidas e formatadas (ABNT ou norma da instituição) antes
de entrar no texto.

## 1. Conceitos a explicar

| Conceito | Por que entra no TCC | Onde aparece no projeto |
|---|---|---|
| Dificuldade de socialização / ansiedade social | Sustenta o problema. **Cuidado:** usar fontes da área da saúde/psicologia e não afirmar diagnóstico. | `projeto.md` §1 |
| Agentes conversacionais e modelos de linguagem (LLM) | O núcleo da solução: o que são, limitações (erros, "alucinação", não determinismo). | `backend/ai.py` |
| Engenharia de prompt e *system prompt* | As regras das personas existem só no prompt. | `backend/personalities.py` |
| Riscos de IA "companheira": dependência emocional, vínculo romântico, conduta em crise | Justifica RN23/RN24 e a avaliação da IA. | `personalities.py`, `metodologia-e-avaliacao.md` |
| Aplicações web cliente-servidor e HTTP | Arquitetura do sistema. | `manual-tecnico.md` §1 |
| API REST/JSON | Comunicação entre página e servidor. | `manual-tecnico.md` §3 |
| Banco de dados relacional, modelagem ER, normalização, integridade referencial | Capítulo de banco. | `banco-de-dados.md` |
| PostgreSQL (tipos `TIMESTAMPTZ`, arrays, `ON CONFLICT`, transações) | Recursos realmente usados. | `schema.sql`, `auth.py` |
| Autenticação: hash de senha com sal, sessões com cookie, tokens | Segurança da conta. | `auth.py` |
| Autenticação em dois fatores com TOTP | RF04. | `two_factor.py` |
| Segurança de aplicações web: injeção de SQL, XSS, CSRF, força bruta, CSP | Capítulo de segurança. | `seguranca.md` |
| LGPD: bases legais, consentimento, dado sensível, direitos do titular | RF11; o conteúdo das conversas pode ser dado sensível. | `public/privacy.html` |
| Qualidade de software (ISO/IEC 25010) | Estrutura da avaliação de qualidade. | `qualidade.md` |
| Testes de software: níveis (unidade, integração, sistema, aceitação), casos positivos/negativos | Capítulo de testes. | `testes.md` |
| BDD e Gherkin | Especificação executável em português. | `features/` |
| Usabilidade e escala SUS | Protocolo B. | `metodologia-e-avaliacao.md` |
| Acessibilidade web (WCAG 2.1) | RNF13 e auditoria axe-core. | `qualidade.md` §3 |
| Métodos de desenvolvimento (o que o grupo realmente usou) | Capítulo de metodologia. | `metodologia-e-avaliacao.md` §1 |

## 2. Referências reais já presentes no projeto
| Referência | Onde é citada | Uso |
|---|---|---|
| BRASIL. Lei nº 13.709, de 14 de agosto de 2018 (Lei Geral de Proteção de Dados Pessoais) | `public/privacy.html` | Capítulo de privacidade/LGPD |
| OWASP. *Multifactor Authentication Cheat Sheet*. https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html | `docs/2fa.md` | 2FA |
| PyOTP (documentação). https://pyauth.github.io/pyotp/ | `docs/2fa.md` | Implementação TOTP |
| Cryptography - Fernet (documentação). https://cryptography.io/en/stable/fernet/ | `docs/2fa.md` | Cifra do segredo TOTP |
| CVV - Centro de Valorização da Vida (telefone 188, cvv.org.br) | prompts, Termos | Encaminhamento em situação de risco |

## 3. Documentos técnicos a consultar (existem; conferir versão e data de acesso)
- RFC 6238 - TOTP: Time-Based One-Time Password Algorithm (IETF).
- OWASP Top 10 e OWASP Cheat Sheet Series (Password Storage, Session
  Management, Cross-Site Request Forgery Prevention, Content Security Policy).
- W3C - Web Content Accessibility Guidelines (WCAG) 2.1.
- ISO/IEC 25010 - modelo de qualidade de produto de software.
- Documentação oficial: Flask (flask.palletsprojects.com), PostgreSQL
  (postgresql.org/docs), psycopg2 (psycopg.org/docs), Google Gemini API
  (ai.google.dev), MDN Web Docs (developer.mozilla.org), Behave
  (behave.readthedocs.io), Gherkin (cucumber.io/docs/gherkin), Playwright
  (playwright.dev/python), axe-core (github.com/dequelabs/axe-core).
- North, Dan. *Introducing BDD* (artigo que apresentou o termo) - localizar a
  publicação original.
- Brooke, John. *SUS: a "quick and dirty" usability scale* - capítulo de
  livro de 1996; conferir dados completos.
- Termos de uso da API do Gemini (uso de dados no plano gratuito) - página
  oficial do Google, com data de acesso.

## 4. Livros-texto sugeridos para os conceitos gerais
Sugestões de títulos clássicos da área, **ainda não consultados** - usar a
edição disponível na biblioteca e citar só o que for efetivamente lido:
engenharia de software (Sommerville; Pressman), banco de dados (Elmasri e
Navathe; Heuser), redes/web (Kurose e Ross).

## 5. O que pesquisar (e ainda não existe no projeto)
1. Dados sobre dificuldade de socialização/ansiedade social em jovens e
   adultos no Brasil **[fontes de saúde]**.
2. Estudos sobre uso de chatbots para apoio emocional ou treino de
   habilidades sociais - benefícios **e** riscos.
3. Trabalhos ou produtos semelhantes (para a seção de trabalhos
   relacionados) e o que o Trash Talker faz diferente.
4. Diretrizes de comunicação responsável sobre suicídio (para justificar
   RN24) **[fonte oficial: CVV, Ministério da Saúde ou OMS]**.
