"""
routes/chats_api.py
====================
Endpoints protegidos por login ligados às conversas: dados do dashboard
(usuário + lista de conversas), ler/criar/renomear/excluir conversa,
enviar mensagem, parar uma resposta, trocar personalidade/esforço e o
áudio das respostas (TTS). As rotas de conta/LGPD ficam em account_api.py.

Todas as rotas abaixo passam por @require_auth, então `g.user` sempre está
preenchido. Conversa de outra pessoa (ou inexistente) responde 404 em
todas elas - 403 confirmaria que o id existe (docs/processo.md, D-06).
"""

import logging

from flask import Blueprint, Response, g, jsonify

from backend.ai import (
    DEFAULT_EFFORT,
    EFFORTS,
    EFFORTS_PUBLIC,
    generate_reply,
    synthesize_speech,
)
from backend.auth import needs_consent, require_auth
from backend.avatars import ILLUSTRATED_AVATARS
from backend.db import execute, get_owned_chat, new_id, query, query_one
from backend.personalities import (
    DEFAULT_PERSONALITY,
    LAZY_HANDOFF_TO,
    PERSONALITIES,
    PERSONALITIES_PUBLIC,
    get_handoff_line,
    should_hand_off,
)
from backend.validation import json_body, text_field

chats_api = Blueprint("chats_api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

# Uma mensagem de 8000 caracteres já são várias páginas de texto; o teto
# existe porque cada mensagem vai inteira para o Gemini (custo e latência).
MAX_MESSAGE_CHARS = 8000
MAX_TITLE_CHARS = 100

# Quantas mensagens recentes vão para a IA a cada resposta. Conversa longa
# mandada inteira toda vez só aumenta custo e latência e, no limite,
# estoura a janela de contexto do modelo.
MAX_HISTORY_MESSAGES = 40

# As respostas são curtas (1-3 frases); o limite só evita que a rota vire
# um gerador de áudio de texto arbitrário às custas da cota do Gemini.
MAX_TTS_CHARS = 2000

NOT_FOUND = ({"error": "Conversa não encontrada"}, 404)


def _consent_required_response():
    """403 para rotas que mandam dado à IA quando a conta ainda não aceitou
    a versão atual dos termos (ver auth.needs_consent). O frontend reabre a
    janela de aceite ao ver needsConsent."""
    return jsonify({
        "error": "Para conversar, aceite os termos atualizados.",
        "needsConsent": True,
    }), 403


def _choice(body, field, options):
    """Valor de `field` se for uma das chaves de `options`; senão None."""
    value = body.get(field)
    return value if isinstance(value, str) and value in options else None


@chats_api.route("/dashboard", methods=["GET"])
@require_auth
def dashboard():
    """
    Dados usados em TODA página do dashboard: usuário logado + lista de
    conversas (para montar a sidebar). Chamado por public/js/layout.js.
    """
    chats = query(
        "SELECT * FROM chats WHERE user_id = %s ORDER BY updated_at DESC",
        (g.user["id"],),
    )
    # image e created_at não vêm de get_session_user() (que devolve só os
    # campos leves usados em toda rota autenticada) - buscados à parte
    # porque só as páginas do painel usam.
    account = query_one(
        "SELECT image, created_at FROM users WHERE id = %s", (g.user["id"],)
    ) or {"image": None, "created_at": None}
    user = {**g.user, "image": account["image"], "created_at": account["created_at"]}
    return jsonify(
        {
            "user": user,
            "chats": chats,
            "illustratedAvatars": ILLUSTRATED_AVATARS,
            "personalities": PERSONALITIES_PUBLIC,
            "efforts": EFFORTS_PUBLIC,
            # Conta sem o aceite da versão atual: layout.js abre a janela.
            "needsConsent": needs_consent(g.user),
        }
    )


@chats_api.route("/chats/<chat_id>", methods=["GET"])
@require_auth
def get_chat(chat_id):
    """Dados de uma conversa específica + suas mensagens (public/js/chat.js)."""
    chat = get_owned_chat(chat_id, g.user["id"])
    if not chat:
        return NOT_FOUND

    messages = query(
        "SELECT * FROM messages WHERE chat_id = %s ORDER BY created_at ASC",
        (chat["id"],),
    )
    return jsonify({"chat": chat, "messages": messages})


@chats_api.route("/chats", methods=["POST"])
@require_auth
def create_chat():
    """Cria uma nova conversa vazia e devolve o id (o frontend navega até ela)."""
    body = json_body()
    # Ausente/inválido cai no padrão em vez de recusar: são campos
    # opcionais, não devem travar a ação principal.
    personality = _choice(body, "personality", PERSONALITIES) or DEFAULT_PERSONALITY
    effort = _choice(body, "effort", EFFORTS) or DEFAULT_EFFORT

    chat_id = new_id()
    execute(
        "INSERT INTO chats (id, user_id, title, personality, effort) "
        "VALUES (%s, %s, %s, %s, %s)",
        (chat_id, g.user["id"], "New Chat", personality, effort),
    )
    return jsonify({"id": chat_id}), 201


@chats_api.route("/chats/<chat_id>/messages", methods=["POST"])
@require_auth
def send_message(chat_id):
    """
    Salva a mensagem do usuário, chama a IA (Gemini) com o histórico recente
    da conversa e salva/devolve a resposta.
    """
    chat = get_owned_chat(chat_id, g.user["id"])
    if not chat:
        return NOT_FOUND
    # Antes de gravar qualquer coisa: sem o aceite atual, nada vai à IA.
    if needs_consent(g.user):
        return _consent_required_response()

    content = text_field(
        json_body(), "content", MAX_MESSAGE_CHARS,
        f"Mensagem longa demais (máximo de {MAX_MESSAGE_CHARS} caracteres).",
    ).strip()
    if not content:
        return jsonify({"error": "Mensagem vazia"}), 400

    user_message_id = new_id()
    execute(
        "INSERT INTO messages (id, chat_id, role, content) VALUES (%s, %s, %s, %s)",
        (user_message_id, chat_id, "user", content),
    )
    execute("UPDATE chats SET updated_at = now() WHERE id = %s", (chat_id,))

    # Só as mensagens mais recentes (ver MAX_HISTORY_MESSAGES), em ordem
    # cronológica. Se o corte cair no meio de uma resposta, ela é descartada:
    # o histórico mandado à IA sempre começa com uma fala da pessoa.
    history = query(
        "SELECT role, content FROM ("
        "  SELECT role, content, created_at FROM messages WHERE chat_id = %s "
        "  ORDER BY created_at DESC LIMIT %s"
        ") recentes ORDER BY created_at ASC",
        (chat_id, MAX_HISTORY_MESSAGES),
    )
    first_message = len(history) == 1
    while history and history[0]["role"] != "user":
        history.pop(0)

    # Primeira mensagem da conversa: usa ela como título automático em
    # vez de deixar "New Chat" até o usuário renomear na mão.
    if first_message:
        title = content[:40] + ("…" if len(content) > 40 else "")
        execute("UPDATE chats SET title = %s WHERE id = %s", (title, chat_id))

    # Preguiça do MathIAs (ver personalities.py): num textão ele entrega os
    # pontos e a conversa passa pro TrashTalker. Decidido aqui, mas só
    # GRAVADO depois que a IA responder - se a chamada falhar (502 abaixo),
    # a conversa fica exatamente como estava e dá pra tentar de novo.
    personality = chat["personality"]
    handoff_line = None
    if should_hand_off(personality, content):
        handoff_line = get_handoff_line()
        personality = LAZY_HANDOFF_TO

    try:
        reply_text = generate_reply(history, g.user, personality, chat["effort"])
    except Exception:
        logger.exception("Falha ao gerar resposta da IA (conversa %s)", chat_id)
        return jsonify(
            {"error": "Não foi possível falar com a IA agora. Tente de novo."}
        ), 502

    # A pessoa pode ter apertado "parar" enquanto a IA pensava. A chamada ao
    # Gemini é bloqueante e não dá pra abortar do lado do servidor, então o
    # combinado é outro: POST /chats/<id>/cancel apaga a mensagem do usuário,
    # e aqui a gente confere se ela ainda existe antes de gravar qualquer
    # coisa. Sem isso a resposta seria salva assim mesmo e apareceria sozinha
    # na conversa no próximo carregamento.
    user_message = query_one("SELECT * FROM messages WHERE id = %s", (user_message_id,))
    if not user_message:
        return jsonify({"cancelled": True})

    # Daqui pra baixo os INSERT/UPDATE usam RETURNING * - a linha gravada já
    # volta na mesma consulta, sem um SELECT extra. Cada resposta guarda
    # quem a escreveu (messages.personality) para o histórico mostrar o
    # autor certo e o "ouvir" usar a voz certa.

    # Gravada ANTES da resposta pra ficar na ordem certa no histórico
    # (created_at): textão -> "tô com preguiça" -> resposta do TrashTalker.
    handoff_message = None
    if handoff_line:
        execute(
            "UPDATE chats SET personality = %s, updated_at = now() WHERE id = %s",
            (personality, chat_id),
        )
        handoff_message = query_one(
            "INSERT INTO messages (id, chat_id, role, content, personality) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING *",
            (new_id(), chat_id, "assistant", handoff_line, chat["personality"]),
        )

    assistant_message = query_one(
        "INSERT INTO messages (id, chat_id, role, content, personality) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING *",
        (new_id(), chat_id, "assistant", reply_text, personality),
    )
    chat = query_one(
        "UPDATE chats SET updated_at = now() WHERE id = %s RETURNING *", (chat_id,)
    )
    return jsonify(
        {
            "chat": chat,
            "userMessage": user_message,
            # None quando não houve troca - o frontend só desenha a bolha
            # extra e sincroniza o seletor quando este campo vem preenchido.
            "handoffMessage": handoff_message,
            "assistantMessage": assistant_message,
        }
    )


@chats_api.route("/tts", methods=["POST"])
@require_auth
def text_to_speech():
    """
    Áudio (WAV) de uma resposta da IA, com a voz da personalidade - usado
    pelo botão "ouvir" (public/js/voice.js). Em qualquer falha devolve 502
    e o frontend lê com a voz do próprio navegador.
    """
    if needs_consent(g.user):
        return _consent_required_response()
    body = json_body()
    text = text_field(body, "text", MAX_TTS_CHARS, "Texto longo demais para virar áudio").strip()
    if not text:
        return jsonify({"error": "Texto vazio"}), 400
    personality = _choice(body, "personality", PERSONALITIES) or DEFAULT_PERSONALITY

    try:
        audio = synthesize_speech(text, personality)
    except Exception:
        logger.exception("Falha ao gerar áudio (TTS)")
        return jsonify({"error": "Não foi possível gerar o áudio agora."}), 502

    # Sem cache HTTP (é POST): quem guarda o áudio pra tocar de novo sem
    # gastar outra chamada é o próprio voice.js, na bolha da mensagem.
    return Response(audio, mimetype="audio/wav")


@chats_api.route("/chats/<chat_id>/delete", methods=["POST"])
@require_auth
def delete_chat(chat_id):
    deleted = query_one(
        "DELETE FROM chats WHERE id = %s AND user_id = %s RETURNING id",
        (chat_id, g.user["id"]),
    )
    return jsonify({"ok": True}) if deleted else NOT_FOUND


@chats_api.route("/chats/<chat_id>/title", methods=["POST"])
@require_auth
def rename_chat(chat_id):
    title = text_field(
        json_body(), "title", MAX_TITLE_CHARS,
        f"Título longo demais (máximo de {MAX_TITLE_CHARS} caracteres)",
    ).strip()
    if not title:
        return jsonify({"error": "Título inválido"}), 400
    return _update_owned_chat(chat_id, "title", title)


@chats_api.route("/chats/<chat_id>/cancel", methods=["POST"])
@require_auth
def cancel_message(chat_id):
    """
    Chamado quando a pessoa aperta "parar" enquanto a IA está pensando.

    Não dá pra abortar a chamada ao Gemini: ela é bloqueante e a thread que
    atende o POST /messages segue até o fim mesmo depois de o navegador
    largar a conexão. Em vez de tentar matar a chamada, esta rota apaga a
    mensagem do usuário que estava sendo respondida - e o send_message, logo
    antes de gravar, confere se ela ainda existe e desiste se não existir.
    O efeito prático é o combinado com o usuário: a rodada inteira é
    descartada e a conversa volta a ficar como estava.
    """
    chat = get_owned_chat(chat_id, g.user["id"])
    if not chat:
        return NOT_FOUND

    ultima = query_one(
        "SELECT id FROM messages WHERE chat_id = %s AND role = 'user' "
        "ORDER BY created_at DESC LIMIT 1",
        (chat_id,),
    )
    if not ultima:
        return jsonify({"ok": True})

    execute("DELETE FROM messages WHERE id = %s", (ultima["id"],))

    # Se a conversa ficou vazia, era a primeira mensagem - e o título
    # automático veio justamente dela (ver send_message). Desfaz também,
    # senão sobra na barra lateral uma conversa vazia batizada com um texto
    # que não existe mais em lugar nenhum.
    restantes = query_one(
        "SELECT COUNT(*) AS total FROM messages WHERE chat_id = %s", (chat_id,)
    )
    if restantes and restantes["total"] == 0:
        execute("UPDATE chats SET title = %s WHERE id = %s", ("New Chat", chat_id))

    return jsonify({"ok": True})


@chats_api.route("/chats/<chat_id>/personality", methods=["POST"])
@require_auth
def update_chat_personality(chat_id):
    personality = _choice(json_body(), "personality", PERSONALITIES)
    if not personality:
        return jsonify({"error": "Personalidade inválida"}), 400
    return _update_owned_chat(chat_id, "personality", personality)


@chats_api.route("/chats/<chat_id>/effort", methods=["POST"])
@require_auth
def update_chat_effort(chat_id):
    effort = _choice(json_body(), "effort", EFFORTS)
    if not effort:
        return jsonify({"error": "Nível de esforço inválido"}), 400
    return _update_owned_chat(chat_id, "effort", effort)


# Colunas que _update_owned_chat aceita - o nome da coluna entra no SQL, por
# isso é uma lista fixa e nunca vem da requisição.
_EDITABLE_CHAT_COLUMNS = {"title", "personality", "effort"}


def _update_owned_chat(chat_id, column, value):
    """Atualiza uma coluna da conversa do usuário logado; 404 se não for dele."""
    assert column in _EDITABLE_CHAT_COLUMNS
    updated = query_one(
        f"UPDATE chats SET {column} = %s, updated_at = now() "
        "WHERE id = %s AND user_id = %s RETURNING id",
        (value, chat_id, g.user["id"]),
    )
    return jsonify({"ok": True}) if updated else NOT_FOUND
