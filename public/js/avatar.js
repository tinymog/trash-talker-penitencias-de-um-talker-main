// avatar.js
// =========
// Desenha o avatar do usuário (foto, avatar ilustrado ou iniciais).
// Usada em: js/layout.js (avatar pequeno da sidebar) e js/account.js
// (avatar grande da tela de conta).
//
// Monta elementos DOM e preenche tudo por propriedade (src, alt,
// textContent) - nunca HTML em string. A versão anterior concatenava a
// imagem e o nome dentro de atributos com um escape que não tratava aspas:
// um nome ou "imagem" com " fechava o atributo e virava código (XSS). O
// backend agora também só aceita formatos conhecidos (account_api.py).

/**
 * @param {string|null} image - null, data-URL de foto, ou "avatar:<id>"
 *   apontando para um dos avatares ilustrados em /avatars/.
 * @param {string} name - nome do usuário (iniciais quando não há imagem).
 * @param {number} size - tamanho em pixels (largura/altura).
 * @returns {HTMLElement}
 */
function renderAvatar(image, name, size) {
  var el;
  if (image) {
    el = document.createElement("img");
    el.alt = name || "";
    el.src = image.indexOf("avatar:") === 0
      ? "/avatars/" + encodeURIComponent(image.slice("avatar:".length)) + ".svg"
      : image;
  } else {
    el = document.createElement("div");
    el.className = "avatar-fallback";
    el.textContent = (name || "").substring(0, 2).toUpperCase() || "??";
  }
  el.classList.add("avatar");
  el.style.width = size + "px";
  el.style.height = size + "px";
  return el;
}
