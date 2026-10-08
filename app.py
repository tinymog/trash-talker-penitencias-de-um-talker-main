"""
Ponto de entrada. A Vercel importa a variável `app`; localmente:

    python app.py

O servidor escuta só em 127.0.0.1 e sem o debugger do Werkzeug: com
debug ligado e escutando em 0.0.0.0 (o padrão anterior), qualquer pessoa
na mesma rede chegava ao console interativo. Para mudar, use HOST,
PORT e FLASK_DEBUG=1 (ver .env.example).
"""

import os

from backend.factory import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
