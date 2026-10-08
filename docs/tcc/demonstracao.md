# Roteiro da demonstração

Objetivo: mostrar o máximo de funcionalidades em ~6 minutos **sem depender
do que é imprevisível** (resposta do Gemini, internet, digitação ao vivo).
Tudo o que precisa dar certo usa dados preparados; a resposta ao vivo da IA
é um bônus - e, se falhar, a própria falha vira demonstração.

## 1. Preparação (na véspera e 30 min antes)
| Item | Como |
|---|---|
| Banco com o esquema atual | `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/schema.sql` |
| Conta demo | `python -m tools.seed_demo` → `demo@trashtalker.example` / `Demo-Banca-2026!` (duas conversas prontas; textos de exemplo, não gerados pela IA). **Nunca** no banco de produção com dados reais. |
| Chave do Gemini com cota | `python tools/check_gemini_tier.py` no dia |
| `TOTP_ENCRYPTION_KEY` definida | para mostrar o QR do 2FA |
| Navegador | janela anônima, zoom 125%, notificações do sistema desligadas; aviso de cookies já dispensado; abas: site, `docs/rastreabilidade.md`, terminal |
| Terminal pronto | comando do passo 9 digitado |
| Plano B | vídeo da demo gravado + capturas em `docs/img/` |

## 2. Sequência (≈ 6 min)
| # | Ação | Funcionalidade mostrada | Resultado esperado |
|---|---|---|---|
| 1 | Abrir a página inicial e clicar em **Entrar**; entrar com a conta demo | RF02, landing | Painel com "Demo" e duas conversas na barra lateral |
| 2 | Abrir "Puxar assunto no intervalo" | RF05, RF06 | Histórico com autor "TrashTalker" em cada resposta |
| 3 | Abrir "A semana no curso" | RF07 (RN15) | Textão → fala do **MathIAs** passando a conversa → resposta do **TrashTalker** |
| 4 | Abrir o seletor de persona/esforço | RF07 | TrashTalker/MathIAs e Mais rápida/Mais elaborada |
| 5 | **Ao vivo (bônus):** nova conversa, enviar "Como eu começo uma conversa com alguém novo no curso?" | RF06 + IA real | Resposta curta, em texto corrido. Se falhar: aviso "A resposta falhou", mensagem preservada (RNF10) |
| 6 | Enviar outra mensagem e clicar em **parar** durante "Preparando resposta…" | RF08 | Texto volta ao campo, envio desfeito |
| 7 | Conta: trocar o avatar ilustrado e salvar | RF09 | Avatar atualizado na barra lateral |
| 8 | Configurações: mostrar 2FA (iniciar e cancelar), **Exportar meus dados** (abrir o JSON), etapa 1 de **Excluir conta** e cancelar | RF04, RF11 | QR code; arquivo baixado; exclusão protegida por 3 etapas |
| 9 | Terminal: `python -m behave features/seguranca.feature` | Testes em Gherkin pt-BR | ~10 cenários verdes em português em poucos segundos (precisa de `TEST_DATABASE_URL`) |
| 10 | DevTools → modo celular (375 px) → abrir o menu | RNF12 | Layout de celular, menu funcionando |

**Não fazer ao vivo:** cadastro com digitação longa (mostrar a captura
`img/02-cadastro.png` ou já ter o e-mail copiado), excluir a conta demo,
2FA completo (depende do celular), mensagens sobre crise (tema sensível; o
resultado do protocolo A é mostrado em slide).

## 3. Riscos e plano B
| Risco | Sinal | Plano B |
|---|---|---|
| Gemini fora/sem cota | aviso "A resposta falhou" | Mostrar que a mensagem não se perdeu (é requisito); seguir com as conversas preparadas; mostrar relatório do protocolo A |
| Sem internet | site não abre | Servidor local (`python app.py`) com banco local e conta demo; sem IA, como acima |
| Login não funciona | erro no passo 1 | Rodar `python -m tools.seed_demo` de novo (não duplica); vídeo gravado |
| Bloqueio por tentativas | "Muitas tentativas…" | Não errar a senha ao vivo; se acontecer, usar o vídeo (o bloqueio dura até 15 min) |
| Tempo estourado | — | Pular passos 6, 8 e 10 (cobertos por capturas) |
| Projetor/resolução | layout quebrado | Zoom do navegador; capturas em `docs/img/` |
