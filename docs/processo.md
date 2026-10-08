# Processo de desenvolvimento

Como o Trash Talker é desenvolvido, quais decisões técnicas foram
tomadas e por quê, e quais riscos continuam abertos.

- Requisitos e regras de negócio: `requisitos.md` · prova de cada um: `rastreabilidade.md`
- Arquitetura e API: `manual-tecnico.md` · banco: `banco-de-dados.md` · segurança: `seguranca.md`
- Como rodar e escrever testes: `testes.md` · qualidade: `qualidade.md`
- Material do TCC: `tcc/README.md`
- 2FA: `2fa.md` · Publicação: `../DEPLOY_VERCEL.md`

---

## 1. Estrutura do projeto

```
app.py            # ponto de entrada (python app.py / Vercel)
backend/          # API Flask + acesso ao banco + IA + schema.sql
public/           # HTML/CSS/JS estático (sem build), servido pelo Flask/Vercel
tests/            # testes de API (pytest)
features/         # especificações de comportamento (Behave, Gherkin pt-BR)
tools/            # utilitários avulsos (diagnósticos)
docs/             # este arquivo, requisitos, testes, 2FA
```

O backend não tem ORM nem framework de frontend. É uma escolha, não uma
omissão: o projeto é pequeno, é base de um TCC, e SQL cru + JavaScript
puro tornam cada camada legível sem conhecimento prévio de biblioteca.

---

## 2. Convenções

**Python**
- SQL sempre parametrizado (`%s` + tupla). Nunca concatenar valor em
  string de query - é o que protege contra SQL Injection.
- Corpo da requisição lido só por `json_body()`/`text_field()`
  (`backend/validation.py`): tipo errado vira 400, nunca 500. Todo campo
  de texto tem tamanho máximo.
- Toda rota que exige login usa `@require_auth`; dentro dela, `g.user`
  está garantidamente preenchido.
- Toda rota que toca uma conversa só age sobre a do usuário logado
  (`get_owned_chat` ou `WHERE … AND user_id = %s RETURNING id`) e devolve
  **404** (não 403) quando não pertence a ele - 403 confirmaria que o id
  existe.
- Erros inesperados vão para o log (`logging`), nunca para a resposta.
- Comentário explica *por quê*, não *o quê*. O código já diz o quê.

**Frontend**
- Dado vindo do usuário entra no DOM só por `textContent`/propriedades,
  nunca por `innerHTML` com string montada. A CSP (`factory.py`) proíbe
  script e estilo inline - não adicione `<script>` inline, `onclick=` nem
  atributo `style=`.

**Banco**
- Mudança de esquema só em `backend/schema.sql`, sempre idempotente
  (`IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`, bloco `DO` para
  constraint) e sem apagar dado.

**Testes**
- Nomes em português, descrevendo o comportamento:
  `test_falha_da_ia_devolve_502_sem_perder_a_mensagem_do_usuario`.
- Um comportamento por teste. Gherkin em português, com `# language: pt`.
- Bug corrigido = teste que falhava antes da correção.

**Repositório**
- Nunca commitar `.env`, credencial, token ou chave de API.
- Mensagem de commit deve dizer o que mudou (ver R-11).

---

## 3. Fluxo de trabalho

Para qualquer alteração de comportamento:

1. Entender o comportamento atual (ler o código, rodar o que existe).
2. Escrever ou ajustar o teste que descreve o comportamento desejado - e
   ver ele falhar.
3. Implementar.
4. Rodar **as duas** suítes: `python -m pytest` e `python -m behave`.
5. Se algo quebrou, achar a causa raiz antes de mexer no teste.
6. Atualizar `requisitos.md` (e a documentação) se o comportamento
   externo mudou.

### Definição de pronto

- [ ] `python -m pytest` passa inteiro
- [ ] `python -m behave` passa inteiro
- [ ] `python -m pyflakes backend app.py tests features tools e2e` sem avisos
- [ ] mudança de interface: `python -m pytest e2e` com o servidor no ar (ver `testes.md`)
- [ ] a aplicação sobe com `python app.py` e as páginas respondem
- [ ] comportamento novo ou alterado tem teste e linha em `requisitos.md` e `rastreabilidade.md`
- [ ] mudança de banco está em `schema.sql` e é idempotente
- [ ] nenhuma credencial entrou no repositório
- [ ] documentação afetada foi atualizada

---

## 4. Decisões técnicas

Registro das decisões cujo motivo não é óbvio pelo código.

### D-01 — `create_app()` como application factory

**Situação:** importar o módulo da aplicação já abria conexão com o
Postgres, o que impedia rodar testes ou ler as rotas sem banco.

**Decisão:** `backend/factory.py` expõe `create_app()`; os testes passam o
banco de teste a ela. `app.py` (raiz) cria a instância que a Vercel
importa e, como script, sobe o servidor local (ver D-07).

### D-02 — Trocar a senha derruba as sessões

**Situação:** a sessão é validada apenas pelo token na tabela
`sessions`; quem já estivesse logado continuava logado depois da troca
de senha - inclusive alguém com acesso indevido.

**Decisão:** `auth.destroy_all_sessions(user_id, exceto=None)`:
redefinição por e-mail derruba **todas**; troca estando logado derruba
as outras e **mantém a atual**. Coberta nas duas suítes.

### D-03 — Banco de teste separado, com trava

Os testes truncam tabelas; rodar isso no banco errado apagaria dados
reais. As travas recusam rodar sem `TEST_DATABASE_URL` ou quando ela é
igual a `DATABASE_URL`. Ver `testes.md`, seção 3.

### D-04 — PostgreSQL nos testes, não SQLite

`db.py` depende de recursos exclusivos do Postgres. Testar em SQLite
validaria um código diferente do que roda em produção.

### D-05 — Raciocínio do Gemini por `thinking_level`

Os modelos Gemini 3 não deixam desligar o raciocínio (o antigo
`thinking_budget=0`), e os tokens dele saem do mesmo orçamento de
`max_output_tokens`. Por isso: `thinking_level` por nível de esforço
("medium" no Trash, "high" no Talker), `MAX_OUTPUT_TOKENS` alto como teto
e o tamanho da resposta controlado pelo prompt. Ver `backend/ai.py`.

### D-06 — 404 em vez de 403 para recurso de outro usuário

Um 403 confirmaria que aquele id existe. Desde D-12 isso vale também para
renomear, apagar e trocar personalidade/esforço (antes respondiam 200).

### D-07 — Servidor local seguro por padrão (2026-10)

`python app.py` não subia servidor nenhum: o `if __name__ == "__main__"`
tinha ficado em `backend/factory.py`. Movido para `app.py`, agora
escutando em `127.0.0.1` e sem o debugger do Werkzeug (antes: `0.0.0.0` e
`debug=True` por padrão, ou seja, console interativo exposto na rede
local). `HOST`, `PORT` e `FLASK_DEBUG=1` mudam isso conscientemente.

### D-08 — Validação centralizada e limites de tamanho (2026-10)

Rotas faziam `(body.get("x") or "").strip()`, que estoura com 500 quando
o campo é número ou o corpo é lista. `backend/validation.py` padroniza a
leitura (400 com mensagem). Limites: corpo 1 MB, mensagem 8000, título
100, nome 100, apelido 50, pronome 30, senha 1024 (hash de texto enorme
custa CPU). Apelido e pronome entram no prompt da IA a cada mensagem.

### D-09 — Avatar só em formatos conhecidos + frontend sem HTML em string (2026-10)

**Situação (XSS armazenado):** o backend aceitava qualquer texto como
imagem, e `renderAvatarHTML` interpolava imagem e nome em atributos com
um escape que não tratava aspas. Um nome como `x" onerror="…` virava
código na página.

**Decisão:** defesa nas duas pontas. Backend: `avatar:<id conhecido>` ou
foto JPEG/PNG/WebP/GIF em base64 (SVG fora - pode conter script).
Frontend: `renderAvatar` monta o elemento e preenche por propriedade.
Mais a CSP estrita (D-11), que barraria script inline mesmo que outro
ponto escapasse.

### D-10 — Limite de tentativas no banco (2026-10)

Login sem limite permitia força bruta; "esqueci a senha" sem limite
permitia lotar a caixa de entrada de alguém. Tabela `auth_rate_limits`
(no banco porque na Vercel cada requisição pode cair numa instância
diferente) com upsert atômico. **Por conta (e-mail), não por IP**: trocar
de IP não ajuda o atacante, e não é preciso confiar em cabeçalho de
proxy. Custo aceito: alguém pode travar o login de outra pessoa por 15
minutos errando a senha dela (R-13).

### D-11 — Origem verificada em toda a API + cabeçalhos de segurança (2026-10)

A checagem de `Origin`/`Sec-Fetch-Site` existia só nas rotas de 2FA; foi
para `factory.py` e vale para todo POST em `/api/`. Cabeçalhos em toda
resposta: CSP sem `unsafe-inline`, `X-Frame-Options: DENY` (clickjacking
na exclusão de conta), `nosniff`, `Referrer-Policy: same-origin` (o token
de redefinição vai na URL). Na Vercel o HTML sai da CDN: os mesmos
cabeçalhos estão em `vercel.json`.

### D-12 — Corridas resolvidas no próprio SQL (2026-10)

Cadastro fazia SELECT e depois INSERT (dois cadastros simultâneos → 500);
o link de redefinição fazia SELECT e depois UPDATE (o mesmo link valia
várias vezes - reproduzido: 4 usos simultâneos, 4 sucessos). Agora:
`INSERT … ON CONFLICT DO NOTHING RETURNING` e `UPDATE … WHERE used = false
RETURNING`. Pedir um link novo invalida os anteriores.

### D-13 — Autoria das respostas e histórico limitado (2026-10)

Coluna `messages.personality`: ao reabrir uma conversa, cada resposta
mostra quem a escreveu (antes tudo aparecia como "IA" e o "ouvir" usava
a voz errada). Respostas antigas ficam `NULL` e continuam como "IA". A IA
recebe as últimas 40 mensagens (antes, a conversa inteira a cada envio).

### D-14 — Rotas de conta separadas (2026-10)

`/api/account*` (perfil, senha, aceite, exportação, exclusão) saiu de
`chats_api.py` para `routes/account_api.py`. URLs e contratos iguais.

### D-15 — Tokens guardados só como hash (2026-10)

**Situação:** o id da sessão **era** o próprio token do cookie, e o link de
redefinição guardava o token em claro. Quem lesse o banco (backup,
vazamento) podia entrar em qualquer conta com sessão aberta.

**Decisão:** o banco guarda só o SHA-256 (`auth.hash_token`); o valor real
fica só no cookie/link. SHA-256 simples basta porque o token tem 256 bits
aleatórios (não há o que adivinhar), diferente de uma senha.

**Impacto (deliberado):** ao publicar esta versão, as sessões e links
abertos deixam de valer - **todo mundo precisa entrar de novo uma vez**.
Os testes passaram a pegar o token do link "enviado" por e-mail, como a
pessoa faria (`ultimo_token_de_redefinicao` no conftest).

### D-16 — Coerência com a Política de Privacidade e dados pesados fora da sessão (2026-10)

1. A Política promete apagar tudo "na hora" ao excluir a conta, mas o limite
   de tentativas (D-10) guardava o e-mail sem ligação com `users`. Agora a
   exclusão chama `auth.forget_rate_limits`, e a Política declara esse
   registro e quanto tempo ele dura.
2. A foto do avatar (até ~350 mil caracteres) era lida do banco em toda
   requisição autenticada, inclusive a cada mensagem. A sessão deixou de
   carregá-la; só o painel e `/api/me` a buscam.

### D-17 — Banco desatualizado vira mensagem clara (2026-10)

**Situação (ocorreu):** o código desta versão foi executado contra o banco
Neon sem o `schema.sql` novo. Todo login devolvia 500 e o log só dizia
`relation "auth_rate_limits" does not exist`.

**Correção do caso:** `schema.sql` aplicado no Neon numa única transação
(só acréscimos; contagens de usuários, conversas, mensagens e sessões
conferidas antes e depois).

**Decisão:** `UndefinedTable`/`UndefinedColumn` do PostgreSQL agora viram
503 "temporariamente indisponível" para quem usa e, no log, "Banco
desatualizado em relação ao código… rode backend/schema.sql"
(`factory.schema_outdated`; teste
`test_banco_desatualizado_avisa_no_log_o_que_fazer`). Não há verificação ao
subir o servidor: custaria uma consulta a cada *cold start* na Vercel, e o
tratamento no erro cobre qualquer migração esquecida, não só esta.

---

## 5. Divergências

Quando o requisito, a implementação e o teste discordarem, **não escolha
em silêncio**. Registre aqui, decida com base em evidência, e só então
altere o código ou o teste.

| ID | Divergência | Decisão |
|---|---|---|
| DV-01 | `test_atualizar_perfil_salva_todos_os_campos` enviava `"image": "avatar_robot"`, formato que o frontend nunca produz (ele envia `"avatar:avatar_robot"`). Com D-09 o backend passou a recusar o formato inválido. | O teste estava errado, não o código: passou a usar o formato real e a conferir que ele é salvo. |
| DV-02 | Ao escrever o teste de "método errado → 405", `GET /api/login` devolveu 404: com `static_url_path=""`, qualquer GET também casa com a rota de arquivos estáticos. | Comportamento aceito (o 404 já sai em JSON). O teste usa `PUT`, que não colide. |
| DV-03 | A narrativa de `conversas.feature` prometia "acompanhar minha evolução", mas o sistema não mede progresso - só guarda o histórico. | O texto estava errado (fora do escopo): passou a "retomar de onde parei quando quiser". |

Nenhuma divergência aberta no momento.

---

## 6. Riscos e dívida técnica

| ID | Risco | Severidade | Situação |
|---|---|---|---|
| R-01 | Connection string do Neon commitada em texto puro no README, no histórico do Git desde o commit inicial, em repositório público | **Crítica** | Removida do arquivo. **Continua no histórico.** Exige rotação da senha no painel do Neon - ação fora do código |
| R-02 | Nomes de modelo em `ai.py` (`gemini-3.8-flash`, `gemini-3.8-flash-tts`) não confirmados neste ambiente | Alta | Em aberto: sem `GEMINI_API_KEY` aqui. Se estiverem errados, todo envio devolve 502. Conferir com `tools/check_gemini_tier.py` |
| R-03 | Sem limite de tentativas em login/esqueci-senha | Alta | **Mitigado** (D-10). Cadastro continua sem limite (R-14) |
| R-04 | Sem proteção CSRF formal | Média | **Mitigado** (D-11): `SameSite=Lax` + verificação de origem em toda a API |
| R-05 | Avatar sem limite/formato | Média | **Resolvido** (D-09) |
| R-06 | Sem limite de tamanho de requisição | Média | **Resolvido** (D-08) |
| R-07 | Histórico inteiro vai para o Gemini | Média | **Resolvido** (D-13): últimas 40 mensagens |
| R-08 | `traceback.print_exc()`/`print` em vez de logging | Baixa | **Resolvido**: `logging` em todo o backend |
| R-09 | Sem ferramenta de migração - `schema.sql` rodado à mão | Baixa | Aceito. O arquivo é idempotente e testado (`test_schema_idempotente_*`) |
| R-10 | Frontend sem teste automatizado | Média | **Mitigado**: `e2e/` (8 testes no navegador, Playwright) - roda só com o servidor no ar, fora da suíte padrão e sem CI |
| R-11 | Mensagens de commit pouco descritivas | Baixa | Em aberto (a cópia de trabalho revisada em 2026-10 não era um repositório Git) |
| R-12 | Tokens de sessão e de redefinição guardados em texto puro no banco: quem ler o banco assume sessões | Média | **Resolvido** (D-15) |
| R-13 | Bloqueio de login por conta permite travar a conta de outra pessoa por 15 min (D-10) | Baixa | Aceito para o porte do projeto |
| R-14 | Cadastro sem limite de taxa (criação de contas em massa) | Baixa | Em aberto. Exige limite por IP, confiando no cabeçalho do proxy da Vercel |
| R-15 | Login com e-mail inexistente respondia mais rápido (sem cálculo de hash): permitia descobrir e-mails cadastrados pelo tempo | Baixa | **Resolvido**: conta inexistente verifica um hash fictício (`two_factor.password_login`, `test_login_de_conta_inexistente_tambem_calcula_hash`) |

### R-01 em detalhe

Uma credencial que foi commitada em repositório público deve ser
considerada **comprometida**, independentemente de ter sido removida
depois. Ordem correta: (1) rotacionar a senha no painel do Neon; (2)
atualizar o `DATABASE_URL`; (3) só então, opcionalmente, reescrever o
histórico do Git. Remover a linha do arquivo sem o passo 1 dá falsa
sensação de segurança.

---

## 7. Onde encontrar as coisas

| Procurando por | Vá para |
|---|---|
| Rotas de autenticação | `backend/routes/auth_api.py` |
| Rotas de conversa, mensagens, TTS | `backend/routes/chats_api.py` |
| Rotas de conta e LGPD | `backend/routes/account_api.py` |
| Rotas de 2FA | `backend/routes/two_factor_api.py` (regras em `backend/two_factor.py`) |
| Sessão, senha, tokens, limite de tentativas | `backend/auth.py` |
| Leitura/validação do corpo das requisições | `backend/validation.py` |
| Regras globais (CSP, origem, erros, páginas) | `backend/factory.py` |
| Acesso ao banco | `backend/db.py` |
| Estrutura das tabelas | `backend/schema.sql` |
| Personalidades e prompts | `backend/personalities.py` |
| Chamada ao Gemini (texto e voz) | `backend/ai.py` |
| Configuração necessária | `.env.example` |
