"""
seed_demo.py
============
Cria a conta de demonstração usada na apresentação do TCC
(docs/tcc/demonstracao.md) e nas capturas de tela do manual: perfil
preenchido e duas conversas já respondidas - uma com o TrashTalker e outra
mostrando o MathIAs passando um textão para o TrashTalker.

As respostas abaixo são TEXTO FIXO escrito para a demonstração, no estilo
das personas. NÃO foram geradas pela IA e não servem como evidência do
comportamento dela (para isso: tools/avaliar_ia.py).

Uso, só em banco de desenvolvimento (recusa produção):

    python -m tools.seed_demo

Entrar com: demo@trashtalker.example / Demo-Banca-2026!
"""

import sys

from dotenv import load_dotenv

from backend import db
from backend.auth import CONSENT_VERSION, hash_password, is_production
from backend.personalities import _LAZY_HANDOFF_LINES

DEMO_EMAIL = "demo@trashtalker.example"  # .example: domínio reservado, nunca recebe e-mail
DEMO_PASSWORD = "Demo-Banca-2026!"

_TEXTAO = (
    "Então, essa semana foi bem estranha. Na segunda eu cheguei no curso e todo mundo já "
    "estava em grupinho, conversando sobre um trabalho que eu nem sabia que existia. Fiquei "
    "parado na porta uns segundos sem saber se entrava na conversa ou se ia direto pro meu "
    "lugar, e acabei indo pro meu lugar. Na terça um colega me chamou pra almoçar com a "
    "turma dele, eu fui, mas passei o almoço inteiro sem falar quase nada, só rindo das "
    "piadas. Na quarta fiquei pensando que eles devem me achar chato. Na quinta nem fui no "
    "intervalo, fiquei mexendo no celular na sala. Hoje é sexta e tem uma festa da turma "
    "amanhã, e eu queria muito ir, mas só de pensar em chegar lá e ficar sozinho num canto "
    "eu já desanimo. Não sei se vou ou se invento uma desculpa. E o pior é que todo mundo "
    "parece fazer isso sem esforço nenhum, enquanto eu fico ensaiando frase na cabeça e, "
    "quando chega a hora, não sai nada."
)
# Precisa passar de LAZY_MAX_CHARS (800), senão a demo mostraria uma troca de
# persona que o sistema real não faria (tests/test_seed_demo.py confere).

# (título, personalidade atual da conversa, mensagens [(papel, autor, texto)])
CONVERSAS = [
    (
        "Puxar assunto no intervalo",
        "trashtalker",
        [
            ("user", None, "Sempre travo quando preciso puxar assunto com alguém novo no curso."),
            ("assistant", "trashtalker",
             "Cara, travar nessa hora é muito mais comum do que parece. Tenta começar pelo que "
             "vocês dois estão vivendo ali, tipo a aula ou o trabalho, que tira a pressão de "
             "inventar assunto. Quer ensaiar uma abertura comigo?"),
            ("user", None, "Quero. Tipo o quê?"),
            ("assistant", "trashtalker",
             "Algo simples como \"você entendeu o que era pra entregar na sexta?\". É pergunta "
             "fácil de responder e abre espaço pra conversa continuar. Manda como você falaria "
             "e eu respondo como o colega."),
        ],
    ),
    (
        "A semana no curso",
        "trashtalker",  # começou com o MathIAs e passou para o TrashTalker (textão)
        [
            ("user", None, _TEXTAO),
            ("assistant", "mathias", _LAZY_HANDOFF_LINES[0]),
            ("assistant", "trashtalker",
             "Pô, dá pra ver que essa semana pesou, e o almoço com a turma já foi um passo e "
             "tanto, mesmo falando pouco. Sobre a festa, que tal combinar com aquele colega do "
             "almoço de chegarem juntos? Assim você não chega sozinho."),
        ],
    ),
]


def seed():
    """
    Cria a conta demo e as conversas numa transação só. Devolve True se
    criou, False se a conta demo já existia (nada é alterado nesse caso).
    Usa o pool já iniciado (db.init_pool).
    """
    with db.get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM users WHERE email = %s", (DEMO_EMAIL,))
        if cur.fetchone():
            return False
        user_id = db.new_id()
        cur.execute(
            "INSERT INTO users (id, name, email, password_hash, display_name, pronoun, interests, "
            "image, terms_accepted_at, consent_version) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now(), %s)",
            (user_id, "Conta Demonstração", DEMO_EMAIL, hash_password(DEMO_PASSWORD), "Demo",
             "ele/dele", ["Games", "Música"], "avatar:avatar_robot", CONSENT_VERSION),
        )
        # Horários no passado e crescentes, para a ordem do histórico e da
        # barra lateral sair igual à da narrativa.
        minutos = 60 * len(CONVERSAS) * 10
        for titulo, personality, mensagens in CONVERSAS:
            chat_id = db.new_id()
            cur.execute(
                "INSERT INTO chats (id, user_id, title, personality, created_at, updated_at) "
                "VALUES (%s, %s, %s, %s, now() - make_interval(mins => %s), "
                "now() - make_interval(mins => %s))",
                (chat_id, user_id, titulo, personality, minutos, minutos - len(mensagens)),
            )
            for papel, autor, texto in mensagens:
                cur.execute(
                    "INSERT INTO messages (id, chat_id, role, personality, content, created_at) "
                    "VALUES (%s, %s, %s, %s, %s, now() - make_interval(mins => %s))",
                    (db.new_id(), chat_id, papel, autor, texto, minutos),
                )
                minutos -= 1
            minutos -= 30
    return True


def main():
    load_dotenv()
    if is_production():
        sys.exit("Recusado: a conta demo tem senha pública e não pode existir em produção.")
    db.init_pool()
    criada = seed()
    print(("Conta demo criada." if criada else "A conta demo já existia; nada foi alterado.")
          + f"\nEntrar com: {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
