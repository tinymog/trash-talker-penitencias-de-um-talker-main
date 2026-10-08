"""
routes/account_api.py
=====================
Endpoints da conta logada: perfil (nome, avatar, apelido, pronome,
interesses), troca de senha, novo aceite dos termos e os direitos da LGPD
(exportar e excluir os dados). Antes moravam em chats_api.py junto com as
conversas; as URLs não mudaram.
"""

import re
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request

from backend.auth import (
    CONSENT_VERSION,
    MAX_NAME_LENGTH,
    MAX_PASSWORD_LENGTH,
    SESSION_COOKIE_NAME,
    clear_session_cookie,
    destroy_all_sessions,
    forget_rate_limits,
    get_password_requirement_failures,
    has_required_consents,
    hash_password,
    require_auth,
    verify_password,
)
from backend.avatars import ILLUSTRATED_AVATARS
from backend.db import execute, query, query_one
from backend.validation import json_body, text_field

account_api = Blueprint("account_api", __name__, url_prefix="/api")

MAX_INTERESTS = 25
MAX_INTEREST_LENGTH = 60
# Apelido e pronome entram no system prompt da IA a cada mensagem (ai.py):
# texto longo ali é custo em toda conversa e espaço para "instruções" que
# não deveriam estar no prompt.
MAX_DISPLAY_NAME_LENGTH = 50
MAX_PRONOUN_LENGTH = 30

# A foto chega já reduzida pelo navegador (account.js: no máximo 256px, JPEG,
# sem EXIF/localização) - uns poucos KB em base64. O limite barra fotos
# originais enviadas por fora do formulário (vários MB, com metadados), que
# ainda viajariam em toda resposta de /api/dashboard.
MAX_IMAGE_CHARS = 350_000

# Únicos formatos de avatar que o frontend produz: um dos ilustrados
# ("avatar:<id>") ou a foto reduzida em data-URL de imagem rasterizada. Antes
# qualquer texto era aceito e ia parar num atributo src/alt da página
# (XSS armazenado); SVG fica de fora por poder carregar script.
_AVATAR_IDS = {avatar["id"] for avatar in ILLUSTRATED_AVATARS}
_PHOTO_RE = re.compile(r"data:image/(?:jpeg|png|webp|gif);base64,[A-Za-z0-9+/]+={0,2}")

DELETE_CONFIRMATION = "eu quero excluir essa conta"


def _valid_image(image):
    if image.startswith("avatar:"):
        return image[len("avatar:"):] in _AVATAR_IDS
    return _PHOTO_RE.fullmatch(image) is not None


def _clean_interests(raw):
    """
    Normaliza a lista de interesses do corpo da requisição: só aceita
    lista de textos, tira espaço das pontas, descarta vazios, remove
    duplicatas (mantendo a ordem). O limite existe porque essa lista é
    reenviada pro Gemini a cada mensagem do chat (ver ai.py) - sem limite,
    um valor abusivo aqui vira custo/latência extra em toda conversa, não
    só neste formulário.
    """
    if not isinstance(raw, list):
        return []
    seen = set()
    cleaned = []
    for item in raw:
        tag = item.strip()[:MAX_INTEREST_LENGTH] if isinstance(item, str) else ""
        if tag and tag not in seen:
            seen.add(tag)
            cleaned.append(tag)
        if len(cleaned) >= MAX_INTERESTS:
            break
    return cleaned


@account_api.route("/account/consent", methods=["POST"])
@require_auth
def accept_consent():
    """Novo aceite (contas antigas ou termos atualizados) - mesmas duas
    confirmações do cadastro, registradas com data e versão."""
    if not has_required_consents(json_body()):
        return jsonify({"error": "Marque as duas confirmações para continuar."}), 400
    execute(
        "UPDATE users SET terms_accepted_at = now(), consent_version = %s WHERE id = %s",
        (CONSENT_VERSION, g.user["id"]),
    )
    return jsonify({"ok": True})


@account_api.route("/account", methods=["POST"])
@require_auth
def update_account():
    body = json_body()
    name = text_field(
        body, "name", MAX_NAME_LENGTH, f"Nome longo demais (máximo de {MAX_NAME_LENGTH} caracteres)"
    ).strip()
    image = text_field(body, "image", MAX_IMAGE_CHARS, "Imagem inválida ou grande demais") or None
    display_name = text_field(
        body, "displayName", MAX_DISPLAY_NAME_LENGTH,
        f"Apelido longo demais (máximo de {MAX_DISPLAY_NAME_LENGTH} caracteres)",
    ).strip() or None
    pronoun = text_field(
        body, "pronoun", MAX_PRONOUN_LENGTH,
        f"Pronome longo demais (máximo de {MAX_PRONOUN_LENGTH} caracteres)",
    ).strip() or None
    interests = _clean_interests(body.get("interests"))

    # Validação equivalente ao updateProfileSchema (zod) do original.
    if len(name) < 2:
        return jsonify({"error": "Nome precisa ter ao menos 2 caracteres"}), 400
    if image and not _valid_image(image):
        return jsonify({"error": "Imagem inválida ou grande demais"}), 400

    execute(
        "UPDATE users SET name = %s, image = %s, display_name = %s, "
        "pronoun = %s, interests = %s, updated_at = now() WHERE id = %s",
        (name, image, display_name, pronoun, interests, g.user["id"]),
    )
    return jsonify(
        {
            "ok": True,
            "user": {
                **g.user,
                "name": name,
                "image": image,
                "display_name": display_name,
                "pronoun": pronoun,
                "interests": interests,
            },
        }
    )


@account_api.route("/account/password", methods=["POST"])
@require_auth
def update_password():
    """
    Troca a senha da conta logada, exigindo a senha atual como
    reconfirmação (mesmo padrão de delete_account, que também reconsulta
    a linha inteira de users porque g.user não traz password_hash).
    Diferente de reset_password (auth_api.py), que funciona sem sessão
    via token de e-mail - esta rota exige estar logado.
    """
    body = json_body()
    current_password = text_field(body, "currentPassword", MAX_PASSWORD_LENGTH)
    new_password = text_field(body, "newPassword", MAX_PASSWORD_LENGTH, "Senha longa demais")

    password_errors = get_password_requirement_failures(new_password)
    if password_errors:
        return jsonify({"error": "\n".join(password_errors)}), 400

    full_user = query_one("SELECT * FROM users WHERE id = %s", (g.user["id"],))
    if not full_user or not verify_password(current_password, full_user["password_hash"]):
        return jsonify({"error": "Senha atual incorreta"}), 401

    execute(
        "UPDATE users SET password_hash = %s, updated_at = now() WHERE id = %s",
        (hash_password(new_password), g.user["id"]),
    )
    # Derruba as sessões abertas em outros dispositivos, mas mantém a
    # atual: quem acabou de trocar a senha estando logado não deve ser
    # deslogado da própria tela. Ver docs/processo.md (decisão D-02).
    destroy_all_sessions(g.user["id"], exceto=request.cookies.get(SESSION_COOKIE_NAME))
    return jsonify({"ok": True})


@account_api.route("/account/export", methods=["GET"])
@require_auth
def export_account_data():
    """
    Exportação dos dados pessoais do usuário logado, em JSON, pro
    frontend disparar o download (settings.js, wireExportDataButton) -
    o mecanismo concreto por trás do direito de portabilidade citado
    na Política de Privacidade (seção 7).

    Datas em ISO-8601 (.isoformat()), diferente do resto da API (que
    devolve datetime cru pro jsonify padrão formatar em RFC-1123): este
    endpoint gera um arquivo pensado pra sair do app, não pra ser
    consumido pelo JS deste app - ISO-8601 é o formato esperado nesse
    caso.
    """
    full_user = query_one("SELECT * FROM users WHERE id = %s", (g.user["id"],))
    if not full_user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    chats = query(
        "SELECT * FROM chats WHERE user_id = %s ORDER BY created_at ASC",
        (g.user["id"],),
    )

    chat_ids = [chat["id"] for chat in chats]
    if chat_ids:
        messages = query(
            "SELECT * FROM messages WHERE chat_id = ANY(%s) ORDER BY created_at ASC",
            (chat_ids,),
        )
    else:
        # ANY(%s) com lista Python vazia vira `= ANY(ARRAY[])`, e o
        # Postgres rejeita isso ("cannot determine type of empty
        # array") - evita a query quando a conta ainda não tem chat.
        messages = []

    messages_by_chat = {}
    for message in messages:
        messages_by_chat.setdefault(message["chat_id"], []).append(
            {
                "id": message["id"],
                "role": message["role"],
                "personality": message["personality"],
                "content": message["content"],
                "createdAt": message["created_at"].isoformat(),
            }
        )

    return jsonify(
        {
            "exportedAt": datetime.now(timezone.utc).isoformat(),
            "profile": {
                "name": full_user["name"],
                "email": full_user["email"],
                "image": full_user["image"],
                "displayName": full_user["display_name"],
                "pronoun": full_user["pronoun"],
                "interests": full_user["interests"],
                "createdAt": full_user["created_at"].isoformat(),
                "updatedAt": full_user["updated_at"].isoformat(),
            },
            # O que a pessoa aceitou e quando (direito de acesso, LGPD art. 18).
            "consent": {
                "acceptedAt": full_user["terms_accepted_at"].isoformat()
                if full_user["terms_accepted_at"]
                else None,
                "version": full_user["consent_version"],
            },
            "chats": [
                {
                    "id": chat["id"],
                    "title": chat["title"],
                    "personality": chat["personality"],
                    "createdAt": chat["created_at"].isoformat(),
                    "updatedAt": chat["updated_at"].isoformat(),
                    "messages": messages_by_chat.get(chat["id"], []),
                }
                for chat in chats
            ],
        }
    )


@account_api.route("/account/delete", methods=["POST"])
@require_auth
def delete_account():
    """
    Apaga a conta de vez (exige a senha atual e a frase de confirmação).
    schema.sql já tem ON DELETE CASCADE em toda tabela que aponta para
    users, então apagar a linha do usuário já limpa tudo o mais.
    """
    body = json_body()
    password = text_field(body, "password", MAX_PASSWORD_LENGTH)

    full_user = query_one("SELECT * FROM users WHERE id = %s", (g.user["id"],))
    if not full_user or not verify_password(password, full_user["password_hash"]):
        return jsonify({"error": "Senha incorreta"}), 401

    if body.get("confirmation") != DELETE_CONFIRMATION:
        return jsonify({"error": f"Digite exatamente: {DELETE_CONFIRMATION}"}), 400

    execute("DELETE FROM users WHERE id = %s", (g.user["id"],))
    # Única tabela com dado da pessoa que não está ligada a users por FK
    # (o e-mail vai dentro do "bucket" do limite de tentativas).
    forget_rate_limits(full_user["email"])
    response = jsonify({"ok": True})
    return clear_session_cookie(response)
