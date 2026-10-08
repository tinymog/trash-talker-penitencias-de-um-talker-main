# Testes

Como rodar os testes do Trash Talker e como escrever novos. Para o que
cada teste prova, ver `requisitos.md`; para as decisões de processo,
`processo.md`.

---

## 1. Os tipos de teste

| Suíte | Ferramenta | Onde | Responde a pergunta |
|---|---|---|---|
| Testes de API | `pytest` | `tests/` | "Este endpoint faz a coisa certa, inclusive quando dá errado?" |
| Testes de comportamento | `behave` | `features/` | "A funcionalidade que prometemos ao usuário funciona?" |
| Testes de interface | `pytest` + Playwright | `e2e/` | "A tela funciona no navegador, no celular e sem violar a CSP?" |
| Diagnóstico 2FA sem banco | `unittest` | `tools/test_two_factor_diagnostics.py` | "O log de permissão do banco não vaza segredo?" |

As duas primeiras exercitam a aplicação pelo `test_client()` do Flask -
a mesma API HTTP que o JavaScript do frontend consome - contra um
PostgreSQL de verdade. Nenhuma chama funções internas para forçar um
resultado.

**Contagem atual:** 207 testes pytest (contando os parametrizados), 53
cenários Behave em 5 funcionalidades e 8 testes de interface.

### Níveis de teste (como explicar na banca)
| Nível | Onde | Observação |
|---|---|---|
| Unidade | `tests/test_avaliar_ia.py`, `tools/test_two_factor_diagnostics.py` | Poucos de propósito: quase toda regra depende do banco, e testá-la isolada com o banco simulado validaria um código diferente do que roda (D-04). |
| Integração | `tests/` (pytest) | Cada teste passa por HTTP → rota → regra → PostgreSQL real. |
| Sistema / interface | `e2e/` | Navegador real contra o servidor no ar. |
| Aceitação | `features/` (Behave) | Comportamento descrito em português, do ponto de vista de quem usa. |

**O que NÃO é testado automaticamente:** a qualidade das respostas do
Gemini (protocolo manual em `tcc/metodologia-e-avaliacao.md`). Ver seção 6.

---

## 2. Pré-requisitos

```bash
python -m pip install -r requirements-dev.txt
```

> No Windows/PowerShell, use `python -m pip` (com o `-m`) para garantir
> que o pacote vá para o ambiente virtual ativo.

E um **banco PostgreSQL separado** do que você usa para desenvolver.

---

## 3. Por que um banco separado é obrigatório

Os testes **apagam todas as tabelas** antes de cada caso (`TRUNCATE ...
CASCADE`). Apontar isso para o seu banco de desenvolvimento apagaria seus
dados de verdade. Por isso:

1. Sem `TEST_DATABASE_URL` definida, a suíte **para** com uma mensagem
   explicando o motivo - ela nunca cai no `DATABASE_URL` do `.env`.
2. Se `TEST_DATABASE_URL` for **igual** a `DATABASE_URL`, a suíte
   também para.
3. O banco de teste é passado explicitamente para `create_app()`.

Se você vir uma dessas mensagens, a trava está fazendo o trabalho dela.

### Por que Postgres e não SQLite em memória

`db.py` usa recursos que só existem no Postgres: placeholders `%s` do
psycopg2, `TEXT[]`, `now()`, `= ANY(%s)`, `ON CONFLICT`, `RealDictCursor`.
Testar em SQLite validaria um código diferente do que roda em produção.

---

## 4. Como rodar

### Preparar o banco (uma vez)

Com um PostgreSQL já instalado:

```bash
createdb trashtalker_test
```

**Sem PostgreSQL instalado (Windows, sem permissão de administrador):** os
binários portáteis bastam - é o que a pasta `.test-postgres/` (ignorada
pelo Git) guarda:

```powershell
# 1. Baixe e extraia https://get.enterprisedb.com/postgresql/postgresql-17.7-1-windows-x64-binaries.zip
#    para .test-postgres\  (fica .test-postgres\pgsql\bin\...)
$pg = ".test-postgres\pgsql\bin"
& "$pg\initdb.exe" -D .test-postgres\data -U postgres -A trust -E UTF8 --locale=C
& "$pg\pg_ctl.exe" -D .test-postgres\data -o "-p 54329 -c listen_addresses=127.0.0.1" -l .test-postgres\server.log start
& "$pg\createdb.exe" -h 127.0.0.1 -p 54329 -U postgres trashtalker_test
# Para desligar: & "$pg\pg_ctl.exe" -D .test-postgres\data stop
```

`-A trust` só serve porque o servidor escuta apenas em `127.0.0.1`; não
use essa configuração num banco acessível pela rede.

O schema é aplicado automaticamente pela suíte, a partir de
`backend/schema.sql`.

### Definir a variável

```bash
export TEST_DATABASE_URL="postgresql://postgres@127.0.0.1:54329/trashtalker_test"   # Linux/macOS
```
```powershell
$env:TEST_DATABASE_URL = "postgresql://postgres@127.0.0.1:54329/trashtalker_test"   # PowerShell
```

(Ou coloque `TEST_DATABASE_URL=...` no `.env`.)

### Rodar

```bash
python -m pytest                          # tudo
python -m pytest tests/test_seguranca.py  # um arquivo
python -m pytest -k redefinicao           # por nome

python -m behave                                    # tudo
python -m behave features/dois_fatores.feature      # uma funcionalidade
python -m behave -n "Enviar uma mensagem"           # um cenário

python -m unittest tools.test_two_factor_diagnostics
python -m pyflakes backend app.py tests features tools e2e   # lint
```

### Testes de interface (`e2e/`)

Precisam do servidor no ar e criam contas no banco que ele usa (use o de
desenvolvimento). Sem `E2E_BASE_URL`, são ignorados.

```bash
python -m playwright install chromium        # uma vez (ou use o Edge: E2E_BROWSER_CHANNEL=msedge)
python app.py                                # outro terminal
E2E_BASE_URL=http://127.0.0.1:5000 python -m pytest e2e
```
```powershell
$env:E2E_BASE_URL = "http://127.0.0.1:5000"; $env:E2E_BROWSER_CHANNEL = "msedge"
python -m pytest e2e
```

### Gerar as evidências de execução (`docs/evidencias/`)

```bash
python -m pytest > docs/evidencias/pytest.txt          # pytest.ini já lista teste a teste (-v)
python -m behave --no-color -f plain > docs/evidencias/behave.txt
E2E_BASE_URL=http://127.0.0.1:5000 python -m pytest e2e > docs/evidencias/e2e.txt
```

No Windows, se o console mostrar acentos quebrados ou `UnicodeEncodeError`
no Behave, defina `$env:PYTHONIOENCODING = "utf-8"`.

---

## 5. Nada externo é chamado de verdade

- **IA (Gemini)**: `generate_reply` é trocada por uma resposta fixa -
  fixtures `ia_falsa`/`ia_quebrada` (`tests/conftest.py`); no Behave,
  `before_scenario` em `features/environment.py` e o passo
  `Dado que a IA está indisponível`. O TTS é simulado nos testes de TTS.
- **E-mail**: `send_password_reset_email` é simulada nas duas suítes
  (no Behave, os "envios" ficam em `context.emails`).
- **2FA**: cada suíte gera uma `TOTP_ENCRYPTION_KEY` temporária.

O que está sob teste é o comportamento da aplicação **em volta** desses
serviços: a mensagem foi persistida? quando a IA cai, a resposta é 502
**sem perder o que o usuário escreveu**?

---

## 6. Cobertura

**Coberto:** ver a matriz em `rastreabilidade.md` (RF01-RF12, RNF01-RNF17). Destaques: isolamento entre usuários em todas as rotas de
conversa, 2FA (incluindo concorrência e rollback), entrada malformada,
limites de tamanho, força bruta, origem estrangeira, XSS no avatar,
corridas no cadastro e no link de redefinição, cancelamento de resposta,
troca de personalidade do MathIAs.

**Não coberto:**

| Lacuna | Por quê / o que seria necessário |
|---|---|
| Interface na integração contínua | `e2e/` existe, mas precisa do servidor no ar; não há CI configurado |
| Respostas e áudio reais do Gemini | Exigem `GEMINI_API_KEY` e avaliação humana: protocolo `tools/avaliar_ia.py` |
| Ditado por voz | Depende de microfone e do navegador; verificação manual |
| Leitor de tela | Verificação manual (NVDA/VoiceOver) |
| Envio real de e-mail SMTP | Depende de servidor externo |
| Carga / desempenho | Nenhum teste de desempenho |
| Reconexão do pool ao Neon | `_with_retry` em `db.py` não tem teste (precisaria derrubar conexões do servidor) |

---

## 7. Escrevendo novos testes

**Testes de API (`tests/`)**: use as fixtures do `conftest.py` -
`cliente`, `usuario_logado`, `conversa`, `ia_falsa`, `ia_quebrada`. O
banco já vem limpo (`banco_limpo` é `autouse`). Tabela nova no schema →
acrescente em `TABELAS` (conftest e `features/environment.py`).

```python
def test_alguma_coisa(cliente, conversa, ia_falsa):
    resposta = cliente.post(f"/api/chats/{conversa}/messages", json={"content": "oi"})
    assert resposta.status_code == 200
```

Para testar o handler de erro 500, desligue a propagação de exceções do
modo de teste: `monkeypatch.setitem(aplicacao.config, "PROPAGATE_EXCEPTIONS", False)`.

**Cenários Behave (`features/`)**: todo `.feature` começa com
`# language: pt` e usa `Funcionalidade`, `Contexto`, `Cenário`,
`Esquema do Cenário`/`Exemplos`, `Dado`, `Quando`, `Então`, `E`. Antes de
criar um passo novo, procure em `features/steps/` - a maioria já existe.

Descreva **comportamento observável**, não implementação:

- ✅ `Então eu devo receber uma resposta do TrashTalker`
- ❌ `Então generate_reply deve ser chamada com o histórico`

### Regra ao ver um teste falhar

Não altere o teste só para ele passar. Primeiro determine se quem está
errado é o teste ou o código. Se for divergência real entre o requisito,
o código e o teste, registre em `processo.md`, seção 5, antes de decidir.
