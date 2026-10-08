# Auditoria automática de acessibilidade (axe-core)

- **Data:** 2026-10-08
- **Ferramenta:** axe-core 4.11.0 (Deque), injetado no navegador pelo Playwright
- **Navegador:** Microsoft Edge 154.0.4258.62, 1280 × 800
- **Regras:** etiquetas `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`
- **Páginas (14):** `/`, `/login`, `/signup`, `/forgot-password`,
  `/reset-password?token=x`, `/reset-password`, `/privacy`, `/terms`,
  `/cookies`, página inexistente (404), e - logado com a conta demo -
  `/dashboard`, uma conversa, `/dashboard/account`, `/dashboard/settings`
- **Temas:** claro e escuro (28 execuções)
- **Dados brutos:** [`acessibilidade-axe.json`](acessibilidade-axe.json)

## Resultado
| Medida | Valor |
|---|---|
| Violações | **0** |
| Aprovações de regra (soma das 28 execuções) | 588 |
| Itens inconclusivos (exigem olho humano) | 8, de 2 tipos |

## Itens inconclusivos e revisão manual
| Regra | Onde | Por que o axe não decidiu | Revisão |
|---|---|---|---|
| `color-contrast` | `/privacy` (um item de lista) e `/cookies` (uma célula de tabela), nos dois temas | Elemento parcialmente sobreposto a outro: a ferramenta não determina a cor de fundo | Cores computadas no navegador: texto `rgb(45,29,26)` sobre `rgb(236,234,223)` = **13,36:1** (claro); `rgb(244,245,239)` sobre `rgb(45,29,26)` = **14,71:1** (escuro). Mínimo AA: 4,5:1. **Aprovado** |
| `aria-valid-attr-value` | Botão do seletor de persona (`/dashboard` e conversa), nos dois temas | `aria-controls` aponta para o menu, que fica `inert` enquanto fechado | Padrão de botão que abre menu; o menu existe no DOM e o `aria-expanded` acompanha. **Aceito** |

## Complementos já automatizados
- Login completo usando só o teclado, com foco visível em cada campo
  (`e2e/test_fluxo_navegador.py::test_login_usando_so_o_teclado_com_foco_visivel`).
- Celular (375 px) sem rolagem horizontal e com o menu alcançável.

## Limites
Ferramentas automáticas pegam só parte dos problemas de acessibilidade.
**A REALIZAR:** percorrer cadastro, conversa e configurações com leitor de
tela (NVDA no Windows) e registrar o que for encontrado; teste com pessoas
(protocolo B em `docs/tcc/metodologia-e-avaliacao.md`).
