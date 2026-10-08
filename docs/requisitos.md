# Especificação de requisitos

O que o Trash Talker se propõe a fazer, com critérios verificáveis. Cada
requisito descreve o sistema **como ele está implementado** - nenhum foi
escrito para algo que o sistema não pretende cumprir.

- Quem prova o quê: [`rastreabilidade.md`](rastreabilidade.md)
- Fluxos de uso: [`casos-de-uso.md`](casos-de-uso.md)
- Problema, objetivos e escopo: [`tcc/projeto.md`](tcc/projeto.md)

**Prioridade (proposta da equipe técnica - validar com o grupo):**
**E** = essencial (sem isso o objetivo geral não é atingido) ·
**I** = importante (necessário para uso seguro e responsável) ·
**D** = desejável (melhora a experiência, mas o sistema cumpre o objetivo sem ele).

---

## 1. Requisitos funcionais

### RF01 — Cadastro de usuário · E
**Descrição:** a pessoa cria uma conta com e-mail, nome e senha, confirmando
que tem 18 anos ou mais, que aceita os Termos e a Política de Privacidade e
que entende que as mensagens são enviadas ao Google Gemini.
**Critérios de aceitação:**
1. E-mail em formato válido e ainda não cadastrado (comparação sem diferenciar maiúsculas) → conta criada (201).
2. Senha fora da política (RN01) → recusa com a lista do que falta (400).
3. Qualquer das duas confirmações desmarcada → recusa (400) e nenhuma conta é criada.
4. E-mail já cadastrado → recusa (409), inclusive com dois cadastros simultâneos.
5. O cadastro não deixa a pessoa logada: ela vai para o login com o aviso "Conta criada".
**Regras:** RN01, RN02, RN03, RN04. **Depende de:** —.

### RF02 — Entrar e sair · E
**Descrição:** a pessoa entra com e-mail e senha e sai quando quiser.
**Critérios de aceitação:**
1. Credenciais corretas → sessão criada e cookie de sessão definido.
2. Senha errada ou e-mail inexistente → mesma recusa (401), sem indicar qual dos dois está errado.
3. Sair apaga a sessão no servidor; o cookie antigo deixa de valer.
4. Sessão vencida (30 dias) não autentica.
5. Depois de 10 senhas erradas em 15 min, a conta recusa tentativas (429) por até 15 min.
**Regras:** RN05, RN08. **Depende de:** RF01.

### RF03 — Recuperar a senha por e-mail · I
**Descrição:** quem esqueceu a senha recebe um link para criar outra.
**Critérios de aceitação:**
1. A resposta é a mesma exista ou não a conta (não revela quem está cadastrado).
2. O link vale 1 hora e uma única vez; pedir outro invalida os anteriores.
3. Redefinir a senha encerra todas as sessões abertas da conta.
4. No máximo 3 e-mails por hora para a mesma conta.
**Regras:** RN01, RN06, RN07. **Depende de:** RF01, serviço de e-mail (SMTP).

### RF04 — Autenticação em dois fatores (opcional) · D
**Descrição:** a pessoa pode exigir, além da senha, um código do Google
Authenticator (ou outro app TOTP), com códigos de recuperação.
**Critérios de aceitação:**
1. A ativação só vale depois de confirmada com um código do aplicativo; mostra 8 códigos de recuperação uma única vez.
2. Com 2FA ativo, a senha correta não cria sessão: é preciso informar o código.
3. Código errado, vencido ou já usado é recusado; cada código de recuperação vale uma vez.
4. 5 erros em 15 min bloqueiam novas tentativas por 15 min.
5. Desativar ou gerar novos códigos exige senha e um código válido.
**Regras:** RN09. **Depende de:** RF02, chave `TOTP_ENCRYPTION_KEY` no servidor.

### RF05 — Gerenciar conversas · E
**Descrição:** a pessoa vê a lista das suas conversas (mais recente primeiro),
abre, renomeia e exclui.
**Critérios de aceitação:**
1. A lista e cada conversa mostram só o que pertence à pessoa logada.
2. Conversa de outra pessoa ou inexistente → "não encontrada" (404) em qualquer operação, sem alterar nada.
3. Renomear aceita de 1 a 100 caracteres.
4. Excluir apaga a conversa e todas as mensagens dela.
**Regras:** RN11, RN12, RN18. **Depende de:** RF02.

### RF06 — Conversar com a IA · E
**Descrição:** a pessoa envia uma mensagem e recebe a resposta da persona da
conversa; tudo fica salvo.
**Critérios de aceitação:**
1. A mensagem e a resposta ficam gravadas, em ordem.
2. A primeira mensagem vira o título da conversa.
3. Mensagem vazia ou com mais de 8000 caracteres é recusada sem chamar a IA.
4. Se a IA falhar, a pessoa recebe um aviso e a mensagem dela **não** se perde.
5. A IA recebe o histórico recente da conversa e o perfil da pessoa (RF09).
**Regras:** RN10, RN13, RN14, RN16, RN23-RN25. **Depende de:** RF05, Google Gemini (`GEMINI_API_KEY`).

### RF07 — Personalidade e esforço da conversa · I
**Descrição:** cada conversa tem uma persona (TrashTalker ou MathIAs) e um
nível de esforço (resposta mais rápida ou mais elaborada), escolhidos pela
pessoa; o MathIAs passa "textões" para o TrashTalker.
**Critérios de aceitação:**
1. Personalidade e esforço podem ser escolhidos ao criar e trocados depois; valores inexistentes são recusados.
2. Mensagem com mais de 800 caracteres numa conversa do MathIAs → ele responde com uma fala de passagem e o TrashTalker responde e assume a conversa em definitivo.
3. Se a IA falhar nesse caso, a troca de persona não é gravada.
4. Cada resposta guarda qual persona a escreveu e o histórico mostra isso ao reabrir.
**Regras:** RN12, RN15. **Depende de:** RF06.

### RF08 — Parar uma resposta · D
**Descrição:** enquanto a IA pensa, a pessoa pode parar e desfazer o envio.
**Critérios de aceitação:**
1. Parar apaga a mensagem que estava sendo respondida e devolve o texto ao campo.
2. Uma resposta que chegue depois do "parar" não é gravada.
3. Se era a primeira mensagem, o título automático é desfeito.
**Regras:** RN17. **Depende de:** RF06.

### RF09 — Perfil · I
**Descrição:** a pessoa edita nome, avatar, apelido, pronome e interesses; a IA
usa apelido, pronome e interesses para personalizar as respostas.
**Critérios de aceitação:**
1. Campos dentro dos limites da RN19 são salvos; fora deles, recusados com mensagem.
2. Interesses repetidos ou vazios são descartados.
3. Avatar: um dos ilustrados ou foto (reduzida no navegador para 256 px, sem metadados).
**Regras:** RN19. **Depende de:** RF02.

### RF10 — Trocar a senha estando logado · I
**Descrição:** a pessoa troca a senha informando a atual.
**Critérios de aceitação:**
1. Senha atual errada → recusa (401).
2. Nova senha precisa cumprir a RN01.
3. As sessões dos outros dispositivos caem; a atual continua.
**Regras:** RN01, RN07. **Depende de:** RF02.

### RF11 — Direitos sobre os dados (LGPD) · E
**Descrição:** consentimento registrado com data e versão; exportação dos
dados; exclusão definitiva da conta.
**Critérios de aceitação:**
1. Conta sem o aceite da versão atual dos termos não conversa nem usa o áudio (403) até aceitar de novo; ainda pode navegar, exportar e excluir.
2. Exportar gera um JSON com perfil, aceite, conversas e mensagens - sem hash de senha nem segredos de 2FA.
3. Excluir exige a senha e a frase exata; apaga a conta e tudo ligado a ela, inclusive o registro de tentativas de acesso.
**Regras:** RN02, RN10, RN20. **Depende de:** RF02.

### RF12 — Voz · D
**Descrição:** a pessoa pode ditar a mensagem (reconhecimento de fala do
navegador) e ouvir as respostas (voz gerada pelo Gemini, com a voz do
navegador como reserva).
**Critérios de aceitação:**
1. O texto ditado só preenche o campo; quem envia é a pessoa.
2. "Ouvir" usa a voz da persona; se o servidor falhar, o navegador lê.
3. Sem suporte do navegador ao ditado, o botão não aparece e o chat funciona igual.
**Regras:** RN21. **Depende de:** RF06; navegador com Web Speech API (ditado); Gemini TTS.

---

## 2. Requisitos não funcionais

| ID | Categoria | Requisito | Critério verificável | Prio. |
|---|---|---|---|---|
| RNF01 | Segurança | Senhas nunca guardadas em texto. | Banco guarda só hash (Werkzeug); nenhum resultado da API contém o hash. | E |
| RNF02 | Segurança | Cada pessoa só acessa os próprios dados. | Toda operação em conversa alheia → 404 sem efeito. | E |
| RNF03 | Segurança | Entrada malformada não derruba o servidor. | Tipo errado ou corpo que não é objeto → 400, nunca 500. | I |
| RNF04 | Segurança | Limites de tamanho em toda entrada. | Corpo ≤ 1 MB (413); limites da RN14, RN18, RN19. | I |
| RNF05 | Segurança | Proteção contra força bruta e abuso de e-mail. | RN08 e RN06 (item 4). | I |
| RNF06 | Segurança | Proteção contra CSRF. | POST em `/api/*` com `Origin` estranho ou `Sec-Fetch-Site: cross-site` → 403. | I |
| RNF07 | Segurança | Proteção contra XSS. | Avatar só em formatos conhecidos; dado do usuário entra na página só como texto; CSP sem script inline. | E |
| RNF08 | Segurança | Segredos fora do banco em claro. | Tokens de sessão e de redefinição guardados como SHA-256; segredo TOTP cifrado (Fernet); chaves só em variáveis de ambiente. | I |
| RNF09 | Confiabilidade | Operações concorrentes não corrompem dados. | Cadastro duplicado, link de reset e código 2FA simultâneos: só um vence. | I |
| RNF10 | Confiabilidade | Falha externa não perde dado nem vaza detalhe. | IA fora → 502 com mensagem salva; erro interno → 500 genérico em JSON, detalhe só no log. | E |
| RNF11 | Privacidade | Minimização de dados enviados à IA. | IA recebe apelido (ou primeiro nome), pronome, interesses e as últimas 40 mensagens; nunca e-mail. | I |
| RNF12 | Usabilidade | Funciona em celular e computador. | Sem rolagem horizontal em 375 px; menu e campo de mensagem sempre alcançáveis. | E |
| RNF13 | Acessibilidade | Conformidade com WCAG 2.1 A/AA verificável por ferramenta. | 0 violações no axe-core nas páginas principais, temas claro e escuro; uso completo do login só pelo teclado com foco visível. | I |
| RNF14 | Manutenibilidade | Esquema do banco evolui sem perder dado. | `schema.sql` idempotente: rodar de novo não falha nem apaga. | I |
| RNF15 | Manutenibilidade | Comportamento verificável automaticamente. | Suítes pytest e Behave passam inteiras antes de cada entrega. | E |
| RNF16 | Portabilidade | Roda localmente e na Vercel sem mudar código. | `python app.py` local; `vercel.json` + variáveis de ambiente em produção. | I |
| RNF17 | Desempenho | Rotas comuns sem trabalho desnecessário. | Sessão validada com 1 consulta; foto do avatar fora das rotas que não a usam; histórico da IA limitado. Tempos: **BENCHMARK A REALIZAR** (ver `qualidade.md`). | D |

---

## 3. Regras de negócio

Todas verificadas no código (arquivo indicado). Valores numéricos são os
configurados hoje.

| ID | Regra | Onde |
|---|---|---|
| RN01 | Senha: mínimo 8 caracteres, com maiúscula, minúscula, número e caractere especial; máximo 1024. | `auth.get_password_requirement_failures`, `MAX_PASSWORD_LENGTH` |
| RN02 | Cadastro e novo aceite exigem as duas confirmações marcadas (18+/termos e envio à IA). | `auth.has_required_consents` |
| RN03 | E-mail é único e guardado em minúsculas. | `auth_api.signup`, `users.email UNIQUE` |
| RN04 | Cadastrar não autentica; a pessoa entra em seguida. | `auth_api.signup` |
| RN05 | Sessão dura 30 dias; cookie `httponly`, `SameSite=Lax`, `Secure` em produção. | `auth.SESSION_DURATION`, `set_session_cookie` |
| RN06 | Link de redefinição: 1 h, uso único, o mais recente invalida os anteriores; resposta idêntica exista ou não a conta; até 3 por hora por conta. | `auth.create/consume_password_reset_token`, `RESET_*` |
| RN07 | Redefinir senha por e-mail encerra todas as sessões; trocar logado encerra as outras e mantém a atual. | `auth.destroy_all_sessions` |
| RN08 | 10 senhas erradas em 15 min bloqueiam o login da conta até a janela vencer, inclusive com a senha certa; acertar antes zera a contagem. | `auth.LOGIN_*`, `auth_api.login` |
| RN09 | 2FA: código de 6 dígitos a cada 30 s, tolerância de 1 intervalo, cada intervalo aceito uma vez; 8 códigos de recuperação; 5 erros/15 min bloqueiam 15 min; desafio de login vale 5 min; ativação pendente vale 10 min e só na sessão que a iniciou. | `two_factor.py` |
| RN10 | Sem o aceite da versão atual (`CONSENT_VERSION`), nada vai à IA (mensagens e áudio → 403). | `auth.needs_consent` |
| RN11 | Conversa só é visível/alterável pelo dono; alheia ou inexistente = 404. | `db.get_owned_chat`, `chats_api` |
| RN12 | Conversa nova: título "New Chat", persona TrashTalker e esforço "Trash" quando não informados ou inválidos. | `chats_api.create_chat` |
| RN13 | A primeira mensagem vira o título (40 caracteres + "…"). | `chats_api.send_message` |
| RN14 | Mensagem: 1 a 8000 caracteres, sem contar espaços das pontas. | `MAX_MESSAGE_CHARS` |
| RN15 | MathIAs + mensagem com mais de 800 caracteres → fala de passagem do MathIAs, resposta do TrashTalker, conversa passa ao TrashTalker em definitivo (só se a IA responder). | `personalities.LAZY_*` |
| RN16 | A IA recebe as últimas 40 mensagens, sempre começando por uma fala da pessoa. | `MAX_HISTORY_MESSAGES` |
| RN17 | Parar apaga a última mensagem da pessoa; resposta tardia é descartada; conversa vazia volta ao título "New Chat". | `chats_api.cancel_message` |
| RN18 | Título de conversa: 1 a 100 caracteres. | `MAX_TITLE_CHARS` |
| RN19 | Perfil: nome 2-100; apelido ≤ 50; pronome ≤ 30; até 25 interesses de até 60 caracteres, sem repetição; avatar ilustrado ou foto JPEG/PNG/WebP/GIF em base64 ≤ 350 mil caracteres. | `account_api` |
| RN20 | Excluir a conta exige senha e a frase "eu quero excluir essa conta"; apaga tudo em cascata e o registro de tentativas. | `account_api.delete_account` |
| RN21 | Áudio: texto de 1 a 2000 caracteres; voz da persona; desiste em 30 s e o navegador lê. | `MAX_TTS_CHARS`, `ai.TTS_*` |
| RN22 | Requisição: corpo ≤ 1 MB; POST vindo de outra origem é recusado. | `factory.py` |

### Regras de comportamento da IA (definidas no prompt)

Estas regras estão escritas nos prompts das personas
(`backend/personalities.py`). Como dependem do modelo de linguagem, **os
testes automatizados não as verificam** (lá a IA é simulada). A
verificação é feita pelo protocolo `tools/avaliar_ia.py` - **A REALIZAR**
(ver `tcc/metodologia-e-avaliacao.md`).

| ID | Regra | Persona |
|---|---|---|
| RN23 | Recusar flerte e interesse romântico com gentileza e firmeza, e redirecionar para relações reais. | TrashTalker |
| RN24 | Diante de autolesão, suicídio, violência ou perigo: levar a sério, sem piada, indicar o CVV (188 / cvv.org.br) e serviços de emergência; nunca dar informação sobre formas de se machucar; admitir que é uma IA quando perguntado. Vale acima de qualquer outra regra. | Todas |
| RN25 | Responder em português, em texto corrido (sem listas/markdown), curto (1 a 3 frases na maioria das vezes), no máximo uma pergunta por mensagem. | Todas |
