# Definição do projeto

Base para os capítulos 1 a 5 da monografia. Tudo aqui foi derivado do
sistema implementado e da proposta original (`../proposta-do-site.md`).
Formulações marcadas **[VALIDAR]** são propostas de redação que o grupo e o
orientador precisam aprovar; trechos **[PENDENTE DE FONTE]** precisam de
referência bibliográfica real antes de entrar no texto.

## 1. Problema

**Formulação proposta [VALIDAR]:**
Pessoas jovens e adultas com dificuldade de socialização - timidez,
ansiedade em situações sociais, medo de julgamento ou de rejeição -
muitas vezes não têm um espaço de baixa pressão para organizar o que
sentem, ensaiar o que vão dizer e receber orientação prática antes de
enfrentar uma interação real.

O texto acadêmico precisa sustentar com fontes:
- que essa dificuldade é comum e afeta a vida das pessoas **[PENDENTE DE FONTE]**;
- que ensaiar/praticar situações sociais ajuda **[PENDENTE DE FONTE]**;
- que assistentes conversacionais têm sido usados nesse tipo de apoio, e com
  quais cuidados **[PENDENTE DE FONTE]**.

**Problema de pesquisa (para TCC técnico) [VALIDAR]:**
> Como desenvolver uma aplicação web que ofereça, com segurança e proteção
> de dados, um interlocutor baseado em inteligência artificial para que
> pessoas com dificuldade de socialização pratiquem e recebam orientação
> sobre interações do dia a dia, sem substituir relações humanas nem apoio
> profissional?

**Hipótese:** em TCC técnico ela costuma ser dispensável. Se a instituição
exigir, uma formulação compatível com o sistema seria: *"Personas de IA com
regras explícitas (limite romântico, encaminhamento em situação de risco,
incentivo ao mundo real) produzem orientação percebida como útil e segura
por pessoas com dificuldade de socialização."* - **ela só pode ser afirmada
depois do teste com usuários e da avaliação da IA** (ambos A REALIZAR, ver
`metodologia-e-avaliacao.md`). Sem eles, **não incluir hipótese**.

## 2. Proposta de solução
Uma aplicação web gratuita, para maiores de 18 anos, em que a pessoa
conversa por texto (ou voz) com duas personas de IA:
- **TrashTalker** - amigo empático e direto: acolhe, dá um passo prático por
  vez, ensaia falas e incentiva a socialização real;
- **MathIAs** - amigo bem-humorado para aliviar a tensão; passa conversas
  longas (desabafos) para o TrashTalker.

Diferenciais implementados (e verificáveis): regras de comportamento no
prompt (limite romântico, seção de segurança com o CVV, admitir que é IA),
histórico salvo e privado, personalização pelo perfil, consentimento
específico para o envio à IA, exportação e exclusão dos dados, 2FA opcional.

## 3. Público-alvo
Jovens e adultos (18+) que sentem dificuldade para iniciar ou manter
conversas, têm medo de falar algo errado, querem ensaiar uma situação
social ou só conversar de forma leve. Comunicação em português do Brasil,
linguagem informal. **Não** é público-alvo: menores de 18 anos; pessoas em
crise que precisam de atendimento (o sistema só encaminha ao CVV/emergência).

[PREENCHER: se o grupo entrevistou ou consultou pessoas do público-alvo,
descrever quem, quantos e como - ou deixar claro que não houve levantamento.]

## 4. Objetivos

**Objetivo geral [VALIDAR]:** desenvolver e verificar uma aplicação web de
conversa com inteligência artificial voltada a pessoas com dificuldade de
socialização, que permita desabafar, ensaiar interações e receber
orientação prática, com proteção dos dados pessoais e limites claros de uso.

| Objetivo específico | Requisitos | Situação |
|---|---|---|
| OE1 Especificar requisitos, regras de negócio e casos de uso | `../requisitos.md`, `../casos-de-uso.md` | ✅ |
| OE2 Implementar cadastro e autenticação seguros (senha forte, sessão, recuperação, 2FA) | RF01-RF04, RF10 | ✅ testado |
| OE3 Implementar conversas persistentes com duas personas de IA e regras de comportamento | RF05-RF08, RN23-RN25 | ✅ sistema testado · 🔶 comportamento da IA A REALIZAR |
| OE4 Implementar personalização do perfil e recursos de voz | RF09, RF12 | ✅ (voz real: verificar manualmente) |
| OE5 Atender aos direitos do titular de dados (LGPD) | RF11, RNF11 | ✅ testado |
| OE6 Modelar banco de dados relacional com integridade referencial | `../banco-de-dados.md` | ✅ |
| OE7 Verificar o sistema com testes automatizados (API, BDD, interface) e auditoria de acessibilidade | RNF13, RNF15 | ✅ (`../rastreabilidade.md`) |
| OE8 Avaliar o comportamento da IA e a usabilidade com pessoas | — | 🔶 **A REALIZAR** |

## 5. Justificativa
Três eixos que o texto pode desenvolver - todos dependem de fonte:
1. **Relevância social:** dificuldade de socialização e seus efeitos **[PENDENTE DE FONTE]**.
2. **Oportunidade técnica:** modelos de linguagem permitem conversa natural
   em português a custo baixo (o projeto usa a API do Google Gemini).
3. **Responsabilidade:** a maioria das soluções de "IA companheira"
   **[PENDENTE DE FONTE: exemplos e críticas reais]** levanta riscos de
   dependência emocional, vínculo romântico e conduta em crise. O Trash
   Talker trata isso como requisito (RN23, RN24) - argumento forte, **desde
   que a avaliação da IA seja feita** e mostre o resultado.

## 6. Escopo

### O Trash Talker FAZ
- Cadastro, login, recuperação de senha por e-mail, 2FA opcional.
- Conversas por texto com TrashTalker ou MathIAs, dois níveis de esforço,
  passagem automática de textão do MathIAs ao TrashTalker, parar resposta.
- Histórico salvo, título automático, renomear e excluir conversas.
- Ditado por voz (recurso do navegador) e leitura das respostas em voz.
- Perfil (avatar, apelido, pronome, interesses) usado pela IA.
- Tema claro/escuro; uso em computador e celular (navegador).
- LGPD: aceite versionado, exportação em JSON, exclusão da conta;
  Termos, Política de Privacidade e de Cookies.

### O Trash Talker NÃO FAZ (fora do escopo, de propósito)
- **Não é terapia nem atendimento de crise**: não diagnostica, não acompanha
  tratamento; em risco, indica o CVV (188) e serviços de emergência.
- Não mede "evolução" nem progresso social da pessoa - guarda só o histórico.
- Não conecta usuários entre si (não é rede social nem tem chat entre pessoas).
- Não tem aplicativo nativo (é web) nem funciona sem internet.
- Não tem painel de administração, moderação ou denúncia.
- Não grava áudio; não treina nem hospeda um modelo próprio de IA.
- Não atende menores de 18 anos; não tem plano pago nem anúncios.

### PODERÁ FAZER FUTURAMENTE (trabalhos futuros)
- Respostas em *streaming* (aparecendo enquanto são geradas).
- Avaliação contínua das respostas da IA (rodar `tools/avaliar_ia.py` a cada mudança de prompt/modelo).
- Exercícios guiados de ensaio (o projeto já teve ferramentas "Ensaiar
  conversa" e "Levar para a vida real", removidas - ver `public/js/ui.js`).
- Plano pago da API (o Google deixaria de usar o conteúdo para melhorar produtos).
- Limite de cadastro por IP, testes de interface na integração contínua.
- Aplicativo instalável (PWA) e mais idiomas.

## 7. Limitações
- **A eficácia para a socialização não foi medida** - o projeto não pode
  afirmar que ajuda as pessoas, só que o sistema funciona como especificado.
- O comportamento da IA depende de um modelo de terceiros (Google Gemini):
  pode errar, mudar de versão, ficar indisponível ou sem cota. As regras no
  prompt não garantem obediência - por isso a avaliação RN23-RN25.
- No plano gratuito da API, o Google pode usar o conteúdo enviado.
- Idade mínima (18+) é autodeclarada.
- Ditado por voz depende do navegador (ausente no Firefox).
- Projeto acadêmico: sem SLA, sem equipe de suporte.

## 8. Cadeia de coerência

| Elo | Situação | O que falta |
|---|---|---|
| Problema | 🟡 claro no produto, sem fontes | Referências reais (§1) |
| Objetivos | 🟡 propostos (§4) | Validação do grupo/orientador |
| Requisitos | ✅ RF/RNF/RN derivados do código | — |
| Funcionalidades | ✅ todas implementadas | — |
| Testes | ✅ sistema · 🔶 IA e usuários | Rodar a avaliação da IA e o teste de usabilidade |
| Resultados | 🟡 só técnicos | Resultados da avaliação da IA e do SUS (`resultados.md`) |
| Conclusão | ❌ | Escrever depois dos resultados |

**Ponto mais frágil diante de uma banca:** o problema é humano (socialização),
mas toda a evidência hoje é técnica. A ponte entre os dois é a avaliação da
IA (as respostas seguem as regras?) e o teste com pessoas (é útil e fácil de
usar?). Sem ao menos a avaliação da IA, o trabalho deve se apresentar como
**desenvolvimento e verificação de um sistema**, não como solução comprovada
para o problema.
