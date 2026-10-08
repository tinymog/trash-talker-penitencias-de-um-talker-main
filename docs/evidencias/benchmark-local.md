# Medição local de tempo (B1, ambiente de desenvolvimento)

**Isto não é o desempenho em produção.** Servidor (`python app.py`, servidor
de desenvolvimento do Flask) e PostgreSQL 17.7 na **mesma máquina**, sem
rede entre eles; na Vercel + Neon cada consulta atravessa a rede e os tempos
serão maiores. Serve para mostrar o procedimento e a ordem de grandeza do
processamento do próprio servidor.

- **Data:** 2026-10-08 · Windows 10 Pro · Python 3.14.2
- **Procedimento:** script B1 de `docs/qualidade.md` (100 requisições
  sequenciais por rota, logado com a conta demo), executado duas vezes;
  vale a segunda (a primeira aquece o pool de conexões).

| Rota | O que faz | Mediana | p95 |
|---|---|---|---|
| `GET /api/me` | valida a sessão + busca a foto | 3,3 ms | 3,5 ms |
| `GET /api/dashboard` | sessão + lista de conversas + foto e data de criação | 3,8 ms | 4,0 ms |

Primeira execução (aquecimento): `/api/me` 3,5 / 3,9 ms; `/api/dashboard`
3,8 / 4,3 ms.

**A REALIZAR:** repetir com o banco de produção (Neon) e medir B2 (tempo de
resposta da IA por nível de esforço) e B3 (Lighthouse), como descrito em
`docs/qualidade.md`.
