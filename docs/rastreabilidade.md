# Matriz de rastreabilidade

Responde à pergunta **"como vocês provaram que esse requisito foi
implementado?"**. Cada linha liga o requisito (`requisitos.md`) à tela em que
a pessoa o usa, ao código, ao cenário Gherkin (`features/`), aos testes
automatizados (`tests/`, `e2e/`) e ao resultado da última execução real.

**Última execução registrada:** 2026-10-08 - saídas completas em
[`evidencias/`](evidencias/README.md).

| Suíte | Resultado |
|---|---|
| `python -m pytest` (API, banco real PostgreSQL 17.7) | 207 passaram, 0 falharam |
| `python -m behave` (Gherkin pt-BR) | 53 cenários / 238 passos passaram, 0 falharam |
| `python -m pytest e2e` (navegador Edge, servidor local) | 8 passaram, 0 falharam |
| `python -m unittest tools.test_two_factor_diagnostics` | 3 passaram |
| Auditoria axe-core 4.11 (WCAG 2.1 A/AA), 14 páginas × 2 temas | 0 violações |

**Legenda:** ✅ executado e passou · ⏸️ NÃO EXECUTADO (motivo na linha) ·
🔶 verificação manual/protocolo a realizar.

---

## Requisitos funcionais

| Req. | Funcionalidade / tela | Implementação | Cenários Gherkin | Testes automatizados | Resultado |
|---|---|---|---|---|---|
| RF01 Cadastro | `/signup` | `auth_api.signup`, `public/js/signup.js` | autenticacao: *Criar uma conta com dados válidos*; *Não é possível cadastrar o mesmo e-mail duas vezes*; *Cadastro com senha muito curta é recusado* | `test_cadastro_*` (10, test_auth_api); `test_cadastros_simultaneos_do_mesmo_email_criam_uma_conta`; e2e `test_cadastro_pela_tela_leva_ao_login_com_aviso` | ✅ |
| RF02 Entrar e sair | `/login`, botão Sair | `auth_api.login/logout`, `auth.create_session/get_session_user` | autenticacao: *Entrar com as credenciais corretas*; *…senha errada*; *…e-mail que não tem conta*; *Sair da conta encerra a sessão*; seguranca: *Muitas senhas erradas bloqueiam o login…* | `test_login_*`, `test_logout_*`, `test_sessao_expirada_nao_autentica`, `test_login_bloqueia_*`, `test_bloqueio_*`, `test_login_certo_zera_*`; e2e `test_senha_errada_mostra_erro_e_a_certa_abre_o_painel`, `test_login_usando_so_o_teclado_com_foco_visivel`, `test_pagina_inexistente_e_sair_da_conta` | ✅ |
| RF03 Recuperar senha | `/forgot-password`, `/reset-password` | `auth_api.forgot_password/reset_password`, `auth.*_password_reset_token` | autenticacao: *Pedir redefinição… não revela nada*; *Redefinir a senha pelo link recebido*; *…derruba sessões…*; *Token… só vale uma vez*; seguranca: *Pedidos repetidos de redefinição…* | `test_esqueci_senha_*`, `test_redefinicao_*`, `test_token_de_redefinicao_*`, `test_novo_pedido_de_redefinicao_invalida_o_link_anterior`, `test_esqueci_a_senha_limita_*` | ✅ (e-mail simulado) · ⏸️ envio SMTP real |
| RF04 2FA | Configurações > Autenticação em dois fatores; 2ª etapa do login | `two_factor.py`, `routes/two_factor_api.py`, `public/js/two-factor.js` | dois_fatores: os 5 cenários | `test_two_factor_api.py` (30 casos: ativação, replay, tolerância, recuperação, limites, concorrência, rollback, chave ausente); e2e `test_configuracoes_mostram_a_conta_e_o_2fa` | ✅ |
| RF05 Gerenciar conversas | barra lateral, `/dashboard/chat/<id>` | `chats_api` (get/create/title/delete), `layout.js` | conversas: *Renomear uma conversa*; *Renomear com título vazio…*; *Apagar uma conversa…*; *Não é possível ler/apagar/renomear a conversa de outra pessoa*; *Conversas de outra pessoa não aparecem na minha lista*; *É preciso estar logado…* | `test_criar_*`, `test_ler_*`, `test_renomear_*`, `test_apagar_*`, `test_nao_e_possivel_*`, `test_alterar_conversa_alheia_devolve_404_e_nao_altera` | ✅ |
| RF06 Conversar com a IA | campo de mensagem do painel e da conversa | `chats_api.send_message`, `ai.generate_reply`, `chat.js` | conversas: *Enviar uma mensagem e receber resposta*; *A primeira mensagem vira o título…*; *O título não muda…*; *Mensagem vazia é recusada*; *Quando a IA falha…*; seguranca: *Mensagem gigante é recusada sem chamar a IA* | `test_enviar_mensagem_*`, `test_ia_recebe_*`, `test_falha_da_ia_*`, `test_mensagem_*`, `test_*titulo*`; e2e `test_mensagem_enviada_continua_na_tela_e_o_resultado_e_visivel` | ✅ (IA simulada) · ⏸️ resposta real do Gemini (sem `GEMINI_API_KEY` neste ambiente) |
| RF07 Personalidade e esforço | seletor no campo de mensagem | `chats_api.update_chat_*`, `personalities.py`, `personality-picker.js` | conversas: *O MathIAs passa um textão para o TrashTalker*; *Ao reabrir a conversa, cada resposta mostra quem a escreveu* | `test_criar_conversa_com_personalidade_e_esforco`, `test_trocar_personalidade_e_esforco_da_conversa`, `test_personalidade_ou_esforco_invalidos_*`, `test_mathias_*`, `test_handoff_nao_e_gravado_se_a_ia_falhar`, `test_resposta_guarda_qual_personalidade_respondeu` | ✅ |
| RF08 Parar resposta | botão de parar (quadrado) no campo de mensagem | `chats_api.cancel_message`, `chat.js` (`pararDeResponder`) | conversas: *Parar a resposta desfaz o envio inteiro* | `test_cancelar_*` (3) | ✅ |
| RF09 Perfil | `/dashboard/account` | `account_api.update_account`, `account.js`, `avatar.js`, `ai._build_user_context_section` | conta: *Personalizar o perfil…*; *Interesses repetidos…*; *Nome muito curto…*; seguranca: *Avatar com código escondido é recusado* | `test_atualizar_perfil_*`, `test_interesses_*`, `test_campos_do_perfil_tem_limite`, `test_avatar_*`, `test_ia_recebe_o_perfil_do_usuario`; e2e `test_nome_com_aspas_aparece_como_texto_e_nao_executa` | ✅ |
| RF10 Trocar senha | Configurações > Alterar senha | `account_api.update_password` | conta: os 3 cenários de troca de senha | `test_trocar_senha_*`, `test_trocar_para_senha_curta_e_recusado`, `test_troca_de_senha_invalida_setup_pendente` | ✅ |
| RF11 LGPD | janela de aceite; Configurações > Exportar / Excluir conta | `account_api` (consent/export/delete), `auth.needs_consent` | conta: *Exportar meus dados*; *…sem nenhuma conversa*; *Apagar a conta…* (2); conversas: *Sem aceitar os termos atualizados…* | `test_conta_sem_aceite_*`, `test_aceite_*`, `test_exportacao_*`, `test_excluir_*`, `test_dados_publicos_e_exportacao_nao_revelam_segredos` | ✅ |
| RF12 Voz | microfone e "ouvir" nas respostas | `chats_api.text_to_speech`, `ai.synthesize_speech`, `voice.js` | — | `test_tts_*` (6, TTS simulado) | ✅ (simulado) · ⏸️ áudio real do Gemini · 🔶 ditado: depende do navegador, verificar manualmente (Chrome/Edge) |

## Requisitos não funcionais

| Req. | Implementação | Cenários Gherkin | Testes | Resultado |
|---|---|---|---|---|
| RNF01 Senha com hash | `auth.hash_password` | — | `test_cadastro_nao_guarda_senha_em_texto_puro`, `test_login_nao_devolve_hash_da_senha`, `test_exportacao_nao_vaza_hash_de_senha` | ✅ |
| RNF02 Isolamento | `get_owned_chat`, `WHERE … user_id` | 4 cenários de "outra pessoa" | `test_nao_e_possivel_*`, `test_alterar_conversa_alheia_*`, `test_exportacao_nao_inclui_dados_de_outro_usuario` | ✅ |
| RNF03 Entrada malformada | `validation.py`, handler em `factory.py` | seguranca: *Dados em formato errado não derrubam o servidor* (5 exemplos) | `test_rotas_publicas_nao_quebram_*`, `test_rotas_autenticadas_recusam_tipos_invalidos_com_400` | ✅ |
| RNF04 Limites de tamanho | `MAX_*`, `MAX_CONTENT_LENGTH` | seguranca: *Mensagem gigante…* | `test_mensagem_*`, `test_titulo_longo_*`, `test_campos_do_perfil_*`, `test_senha_gigante_*`, `test_corpo_maior_*` | ✅ |
| RNF05 Força bruta | `auth.rate_limit_*` | seguranca: 2 cenários | `test_login_bloqueia_*`, `test_esqueci_a_senha_limita_*`, `test_login_de_conta_inexistente_tambem_calcula_hash` | ✅ |
| RNF06 CSRF | `factory.block_cross_site_mutations` | seguranca: *Alteração vinda de outro site é recusada* | `test_post_*` (3), `test_setup_exige_sessao_senha_e_json_mesma_origem` | ✅ |
| RNF07 XSS | `account_api._valid_image`, `avatar.js`, CSP | seguranca: *Avatar com código escondido…* | `test_avatar_*`, `test_cabecalhos_de_seguranca_presentes`; e2e `test_nome_com_aspas_*` + coleta de violações de CSP em todos os testes e2e | ✅ |
| RNF08 Segredos | `auth.hash_token`, Fernet em `two_factor.py` | — | `test_banco_guarda_so_o_hash_dos_tokens`, `test_estado_inicial_e_setup_*`, `test_ativacao_gera_oito_hashes_*` | ✅ |
| RNF09 Concorrência | `ON CONFLICT`, `UPDATE … RETURNING`, `FOR UPDATE` | — | `test_cadastros_simultaneos_*`, `test_token_de_redefinicao_usado_ao_mesmo_tempo_*`, `test_concorrencia_consume_desafio_*` | ✅ |
| RNF10 Falha externa | `send_message` (502), handler 500 | conversas: *Quando a IA falha…* | `test_falha_da_ia_*`, `test_tts_falha_*`, `test_erro_inesperado_devolve_500_*`, `test_erro_interno_reverte_consumo_do_codigo` | ✅ |
| RNF11 Minimização | `ai._build_user_context_section`, `MAX_HISTORY_MESSAGES` | — | `test_ia_recebe_no_maximo_as_ultimas_40_mensagens`, `test_link_de_redefinicao_nao_vai_para_o_log_em_producao` | ✅ |
| RNF12 Celular e computador | CSS responsivo | — | e2e `test_celular_menu_alcancavel_e_sem_rolagem_horizontal` | ✅ |
| RNF13 Acessibilidade | HTML semântico, ARIA, `ui.js` | — | auditoria axe-core (`evidencias/acessibilidade-axe.md`); e2e `test_login_usando_so_o_teclado_com_foco_visivel` | ✅ automatizado · 🔶 teste com leitor de tela: A REALIZAR |
| RNF14 Esquema idempotente | `schema.sql` | — | `test_schema_idempotente_preserva_conta_2fa`; aplicado 2× no banco de dev | ✅ |
| RNF15 Verificação automática | suítes | — | todas | ✅ |
| RNF16 Portabilidade | `app.py`, `vercel.json` | — | execução local ✅ | ⏸️ deploy na Vercel não verificado neste ambiente |
| RNF17 Desempenho | `get_session_user` sem foto; histórico limitado | — | `test_avatar_volta_no_painel_e_no_me_mas_nao_em_toda_requisicao` | ✅ comportamento · ⏸️ tempos: BENCHMARK A REALIZAR (`qualidade.md`) |

## Regras de comportamento da IA

| Regra | Implementação | Verificação | Resultado |
|---|---|---|---|
| RN23 Limite romântico | prompt do TrashTalker | `tools/avaliar_ia.py`, caso IA-02 | 🔶 A REALIZAR (exige `GEMINI_API_KEY` e avaliação humana) |
| RN24 Situação de risco / admitir que é IA | `_SAFETY_SECTION` (todas as personas) | casos IA-03, IA-04, IA-06 | 🔶 A REALIZAR |
| RN25 Formato e tamanho | prompts | casos IA-01, IA-05, IA-07, IA-08 | 🔶 A REALIZAR |
| Protocolo em si | `tools/avaliar_ia.py` | `tests/test_avaliar_ia.py` (3, IA simulada) | ✅ o protocolo funciona; o resultado da IA ainda não existe |
