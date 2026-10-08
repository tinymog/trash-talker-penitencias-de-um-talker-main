# Segurança

Como o Trash Talker protege contas e dados, onde cada proteção está e qual
teste a comprova. Decisões e histórico das correções: `processo.md`
(D-02, D-07 a D-16). Referência usada como checklist: OWASP Top 10 e
OWASP Cheat Sheets (ver `tcc/fundamentacao-teorica.md`).

## 1. Autenticação
| Proteção | Implementação | Prova |
|---|---|---|
| Senha forte obrigatória (RN01) | `auth.get_password_requirement_failures` (backend) e checklist em `auth.js` (só conveniência) | `test_cadastro_com_senha_curta_e_recusado`, `test_redefinicao_com_senha_curta_e_recusada` |
| Senha guardada só como hash com sal | `werkzeug.security.generate_password_hash` | `test_cadastro_nao_guarda_senha_em_texto_puro` |
| Mesma resposta para e-mail inexistente e senha errada | `two_factor.password_login` | `test_login_com_email_inexistente_devolve_401` |
| Sem diferença de tempo entre os dois casos | hash fictício quando a conta não existe | `test_login_de_conta_inexistente_tambem_calcula_hash` |
| Limite de tentativas: 10 falhas/15 min por conta | `auth.rate_limit_*`, tabela `auth_rate_limits` | `test_login_bloqueia_apos_dez_falhas_mesmo_com_a_senha_certa` + 3 testes; cenário Behave |
| Segundo fator opcional (TOTP) com códigos de recuperação | `two_factor.py` (pyotp; segredo cifrado com Fernet) | `test_two_factor_api.py` (30); `dois_fatores.feature` |
| Recuperação de senha que não revela contas | resposta sempre igual; até 3 e-mails/h | `test_esqueci_senha_com_email_inexistente_tambem_devolve_ok`, `test_esqueci_a_senha_limita_*` |

## 2. Sessão
| Proteção | Implementação | Prova |
|---|---|---|
| Token aleatório de 256 bits | `secrets.token_urlsafe(32)` | — |
| Banco guarda só o SHA-256 do token | `auth.hash_token` | `test_banco_guarda_so_o_hash_dos_tokens` |
| Cookie `httponly` (JavaScript não lê), `SameSite=Lax`, `Secure` em produção | `auth.set_session_cookie` | `test_login_valido_cria_sessao_e_cookie` |
| Expira em 30 dias | `sessions.expires_at` | `test_sessao_expirada_nao_autentica` |
| Logout apaga no servidor | `auth.destroy_session` | `test_logout_remove_sessao_do_banco` |
| Trocar/redefinir senha derruba outras sessões | `auth.destroy_all_sessions` | `test_trocar_senha_derruba_*`, `test_redefinicao_derruba_sessoes_abertas` |
| Ativar/desativar 2FA renova a sessão | `two_factor._rotate_session` | `test_ativacao_gera_oito_hashes_e_revoga_sessoes_anteriores` |

## 3. Autorização
Não há papéis (não existe administrador). A regra única é **cada pessoa só
acessa os próprios dados**: toda rota protegida usa `@require_auth`, e toda
consulta a conversas filtra pelo dono (`get_owned_chat` ou
`WHERE … AND user_id = %s`). Recurso alheio ou inexistente → **404**, que não
confirma que o id existe (D-06). Provas: `test_nao_e_possivel_*`,
`test_alterar_conversa_alheia_devolve_404_e_nao_altera`,
`test_exportacao_nao_inclui_dados_de_outro_usuario`, 4 cenários Behave.

## 4. Validação de entrada
- Todo corpo JSON passa por `validation.json_body`/`text_field`: tipo errado →
  400, nunca 500 (`test_rotas_*_corpo_malformado`, `…tipos_invalidos_com_400`).
- Limites de tamanho em todo texto (RN14, RN18, RN19) e no corpo (1 MB → 413).
- Valores de lista fechada (persona, esforço, avatar) só são aceitos se
  existirem (`_choice`, `_valid_image`).
- A validação no navegador (`maxlength`, checklist de senha) é só
  conveniência; a regra vale no servidor.

## 5. SQL Injection
Todo SQL usa parâmetros do psycopg2 (`%s` + tupla) - o valor nunca é
concatenado na consulta. A única interpolação de texto em SQL é o **nome de
coluna** em `chats_api._update_owned_chat`, restrito a uma lista fixa
(`title`, `personality`, `effort`) que nunca vem da requisição.

## 6. XSS (injeção de script na página)
- Dado do usuário entra no DOM só por `textContent`/propriedades; o avatar é
  montado como elemento (`avatar.js`), sem HTML em texto.
- O servidor só aceita avatar em formatos conhecidos (`avatar:<id>` ou
  foto JPEG/PNG/WebP/GIF em base64; SVG fora, por poder conter script).
- **CSP** sem `unsafe-inline` e sem `unsafe-eval`: mesmo que um texto
  escapasse, o navegador não executaria script inline.
- Provas: `test_avatar_em_formato_desconhecido_e_recusado` (7 variações),
  `test_cabecalhos_de_seguranca_presentes`, e2e
  `test_nome_com_aspas_aparece_como_texto_e_nao_executa`; os testes e2e
  falham se o navegador registrar qualquer violação de CSP.
- Histórico: havia XSS armazenado no avatar (corrigido, D-09).

## 7. CSRF (requisição forjada por outro site)
Defesa em duas camadas: cookie `SameSite=Lax` (o navegador não o envia em
POST vindo de outro site) e checagem de `Origin`/`Sec-Fetch-Site` em todo
POST de `/api/` (`factory.block_cross_site_mutations`) → 403. Os POSTs do 2FA
exigem ainda `Content-Type: application/json`. Provas:
`test_post_de_outra_origem_e_bloqueado`,
`test_post_marcado_como_cross_site_e_bloqueado`, cenário Behave.

## 8. Cabeçalhos HTTP
`Content-Security-Policy`, `X-Frame-Options: DENY` (impede embutir o site
num iframe - clickjacking na exclusão de conta), `X-Content-Type-Options:
nosniff`, `Referrer-Policy: same-origin` (o token de redefinição vai na URL),
`Cache-Control: no-store` nas respostas da API. Definidos em `factory.py` e
repetidos em `vercel.json` (na Vercel o HTML sai da CDN).

## 9. Informações sensíveis e configuração
- Chaves e senhas só em variáveis de ambiente (`.env`, fora do Git;
  `.env.example` sem valores). Nada sensível vai ao navegador.
- Segredo TOTP cifrado (Fernet); tokens e códigos como SHA-256.
- Erros inesperados: detalhe só no log; resposta genérica
  (`test_erro_inesperado_devolve_500_generico_sem_detalhes`).
- Link de redefinição nunca no log em produção
  (`test_link_de_redefinicao_nao_vai_para_o_log_em_producao`).
- Exportação dos dados não inclui hash nem segredos
  (`test_dados_publicos_e_exportacao_nao_revelam_segredos`).
- Servidor local só em `127.0.0.1` e sem o debugger do Werkzeug por padrão.

## 10. Privacidade (LGPD)
Consentimento específico e versionado para o envio das mensagens à IA
(dado sensível em potencial, art. 11), registro de data/versão do aceite,
exportação (portabilidade), exclusão em cascata (inclusive o registro de
tentativas), minimização (a IA não recebe e-mail nem nome completo; foto
sem metadados). Política de Privacidade em `public/privacy.html`. Detalhes
em `requisitos.md` (RF11, RNF11).

## 11. Riscos em aberto
| ID | Risco | Situação |
|---|---|---|
| R-01 | Credencial do banco esteve no histórico público do Git | **Ação fora do código:** rotacionar a senha no painel do Neon |
| R-02 | Nome dos modelos Gemini não confirmado neste ambiente | Conferir com a chave real |
| R-13 | Bloqueio por conta permite travar o login de alguém por 15 min | Aceito (documentado) |
| R-14 | Cadastro sem limite de taxa | Em aberto (exigiria limite por IP) |
| — | Plano gratuito do Gemini: o Google pode usar o conteúdo | Declarado na Política; resolver com plano pago |
| — | Idade mínima (18+) é autodeclarada | Limitação comum; declarada nos Termos |
| — | Dependência de terceiros sem testes de segurança próprios (Neon, Vercel, Google) | Fora do escopo |

**Não executado:** teste de invasão (pentest) por pessoa externa e
varredura automatizada (ex.: OWASP ZAP). Procedimento sugerido em
`qualidade.md`.
