# Esqueleto da monografia

Estrutura sugerida para o texto do TCC, com o que cada seção deve conter, o
material do repositório que a sustenta e o que ainda falta. **Este arquivo
não é o texto final** - é o mapa para escrevê-lo sem inventar nada.

Marcadores: **[PREENCHER]** só o grupo sabe · **[PENDENTE DE FONTE]** precisa
de referência real · **[A REALIZAR]** depende de uma atividade ainda não feita.

Elementos pré-textuais (capa, folha de rosto, resumo, abstract, listas,
sumário) seguem o modelo da instituição **[PREENCHER: norma - ABNT NBR
14724 ou modelo próprio]**. O resumo deve ser o último texto escrito.

---

## 1. Introdução
- Contexto: dificuldade de socialização e o uso crescente de assistentes
  conversacionais **[PENDENTE DE FONTE]**.
- Apresentação do Trash Talker em um parágrafo (`projeto.md` §2).
- Organização do trabalho (o que vem em cada capítulo).

## 2. Problema
- Formulação e problema de pesquisa: `projeto.md` §1 **[VALIDAR]**.
- Hipótese: só se exigida - ver `projeto.md` §1.

## 3. Justificativa
- Três eixos (relevância social, oportunidade técnica, responsabilidade no
  uso de IA): `projeto.md` §5 **[PENDENTE DE FONTE]**.

## 4. Objetivo geral
- `projeto.md` §4 **[VALIDAR]**.

## 5. Objetivos específicos
- OE1-OE8 com o requisito que cada um cobre: `projeto.md` §4.

## 6. Fundamentação teórica
- Roteiro de conceitos e referências: `fundamentacao-teorica.md`.
- Incluir "trabalhos relacionados" **[PENDENTE DE FONTE]**.

## 7. Metodologia
- Natureza da pesquisa, processo de desenvolvimento, verificação em camadas:
  `metodologia-e-avaliacao.md` §1.
- Gestão, papéis, cronograma, ferramentas, declaração do uso de IA
  **[PREENCHER]**.
- Protocolos de avaliação A (IA) e B (usabilidade): mesmo arquivo, §2-3.

## 8. Tecnologias utilizadas
Quadro "tecnologia - versão - uso no projeto - por que foi escolhida":
| Tecnologia | Versão (requirements/ambiente) | Uso |
|---|---|---|
| Python | 3.10+ (testado em 3.14) | Servidor |
| Flask | 3.0.3 | API e páginas |
| PostgreSQL | testado em 17.7; produção Neon | Banco |
| psycopg2 | 2.9.12 | Acesso ao banco (SQL parametrizado) |
| Google Gemini (google-genai) | 2.18.1 | Respostas e voz |
| pyotp, qrcode, cryptography | 2.10.0 / 8.2 / 50.0.1 | 2FA |
| HTML, CSS, JavaScript | sem framework | Interface |
| pytest, Behave, Playwright | 9.1.1 / 1.3.3 / 1.63.0 | Testes |
| Vercel | — | Hospedagem |
Coluna "por que" **[PREENCHER com os critérios reais do grupo]** (ver `banca.md`).

## 9. Desenvolvimento
- Requisitos e regras de negócio: `../requisitos.md`.
- Casos de uso (+ diagrama PlantUML): `../casos-de-uso.md`.
- Telas e fluxos (com capturas): `../manual-do-usuario.md`.
- Decisões técnicas relevantes: `../processo.md` §4 (escolher 4-6, não todas).
- Personas e regras de comportamento: `backend/personalities.py` (citar trechos curtos).

## 10. Banco de dados
- Modelo conceitual, DER, modelo lógico, dicionário, decisões, integridade:
  `../banco-de-dados.md`.

## 11. Arquitetura
- Diagramas de componentes e de sequência, módulos, API: `../manual-tecnico.md`.
- Segurança: `../seguranca.md` (pode ser seção própria).

## 12. Testes
- Estratégia (níveis, ferramentas, banco real, IA simulada e por quê):
  `../testes.md`.
- Exemplo de cenário Gherkin e de teste de API (um de cada, curtos).
- Matriz de rastreabilidade: `../rastreabilidade.md`.
- Acessibilidade e qualidade: `../qualidade.md`.

## 13. Resultados
- Só o que está em `resultados.md` §1 (comprovado).
- Avaliação da IA e teste de usabilidade **[A REALIZAR]** - quando feitos,
  entram aqui com tabelas, sem arredondar a favor.

## 14. Limitações
- `projeto.md` §7.

## 15. Trabalhos futuros
- `projeto.md` §6 ("poderá fazer futuramente").

## 16. Conclusão
- Retomar cada objetivo específico e dizer, com a evidência, se foi atingido
  (`projeto.md` §4, coluna Situação).
- Responder ao problema de pesquisa nos limites do que foi comprovado.
- **Escrever depois dos resultados [A REALIZAR].**

## 17. Referências
- Só obras efetivamente consultadas. Ponto de partida:
  `fundamentacao-teorica.md` §2-4. **[PENDENTE DE FONTE]**

## Apêndices sugeridos
- A: Especificação de requisitos (`../requisitos.md`).
- B: Casos de uso (`../casos-de-uso.md`).
- C: Dicionário de dados (`../banco-de-dados.md` §4).
- D: Matriz de rastreabilidade (`../rastreabilidade.md`).
- E: Relatórios de execução dos testes (`../evidencias/`).
- Figuras: DER, arquitetura, sequências e navegação já exportados em `../img/diagramas/`; telas em `../img/`.
- F: Questionário SUS e roteiro de tarefas (`metodologia-e-avaliacao.md` §3).
- G: Manual do usuário (`../manual-do-usuario.md`).

Anexos: Termos de Uso e Política de Privacidade (`public/terms.html`,
`public/privacy.html`).
