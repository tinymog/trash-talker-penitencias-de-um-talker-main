"""
validation.py
=============
Leitura defensiva do corpo JSON das requisições.

O corpo vem do navegador (ou de qualquer cliente HTTP), então nada nele é
confiável: pode não ser um objeto, pode trazer número onde se espera
texto, pode ser gigante. Antes daqui, cada rota fazia
`(body.get("x") or "").strip()` - que estoura com 500 quando "x" é um
número ou o corpo é uma lista. Estes helpers transformam tudo isso em 400
com mensagem clara (ver o handler de InvalidInput em factory.py).

As rotas de 2FA têm os próprios `_body`/`_text` (two_factor_api.py)
porque os erros delas carregam um `code` que o frontend interpreta.
"""

from flask import request


class InvalidInput(Exception):
    """Entrada recusada; vira HTTP 400 com a mensagem (factory.py)."""


def json_body():
    """Corpo JSON como dict; qualquer outra coisa (lista, texto, nada) vira {}."""
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else {}


def text_field(body, field, max_length, too_long="Dados inválidos."):
    """
    Valor de texto de `field`: "" se ausente/None, InvalidInput se não for
    string ou passar de `max_length` caracteres. Não faz strip - quem chama
    decide (senha, por exemplo, não pode ser alterada).
    """
    value = body.get(field)
    if value is None:
        return ""
    if not isinstance(value, str):
        raise InvalidInput("Dados inválidos.")
    if len(value) > max_length:
        raise InvalidInput(too_long)
    return value
