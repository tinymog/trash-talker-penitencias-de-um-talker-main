# language: pt

Funcionalidade: Proteções da conta e da aplicação
  Como uma pessoa que confia as próprias conversas ao Trash Talker
  Quero que a aplicação resista aos abusos mais comuns
  Para que ninguém entre na minha conta nem derrube o serviço

  Cenário: Muitas senhas erradas bloqueiam o login por um tempo
    Dado que existe uma conta com o e-mail "pessoa@exemplo.com" e a senha "Senha-Forte-123"
    Quando alguém erra a senha de "pessoa@exemplo.com" 10 vezes
    E eu entro com o e-mail "pessoa@exemplo.com" e a senha "Senha-Forte-123"
    Então eu devo receber o status 429
    E eu não devo estar autenticado

  Cenário: Pedidos repetidos de redefinição não lotam a caixa de entrada
    Dado que existe uma conta com o e-mail "pessoa@exemplo.com" e a senha "Senha-Forte-123"
    Quando eu peço a redefinição de senha do e-mail "pessoa@exemplo.com" 5 vezes
    Então eu devo receber o status 200
    E no máximo 3 e-mails de redefinição devem ter sido enviados

  Cenário: Alteração vinda de outro site é recusada
    Dado que eu estou logado
    Quando um site de outra origem tenta criar uma conversa em meu nome
    Então eu devo receber o status 403
    E eu não devo ter nenhuma conversa

  Cenário: Avatar com código escondido é recusado
    Dado que eu estou logado
    Quando eu tento salvar como avatar o texto 'avatar:x" onerror="alert(1)'
    Então eu devo receber o status 400

  Cenário: Mensagem gigante é recusada sem chamar a IA
    Dado que eu estou logado
    E que eu tenho uma conversa aberta
    Quando eu envio uma mensagem com 8001 caracteres
    Então eu devo receber o status 400
    E a conversa deve ter 0 mensagens guardadas

  Esquema do Cenário: Dados em formato errado não derrubam o servidor
    Dado que eu estou logado
    E que eu tenho uma conversa aberta
    Quando eu envio para "<rota>" o campo "<campo>" com um número no lugar de texto
    Então eu devo receber o status 400

    Exemplos:
      | rota                     | campo       |
      | /api/chats/{c}/messages  | content     |
      | /api/chats/{c}/title     | title       |
      | /api/account             | name        |
      | /api/account/password    | newPassword |
      | /api/tts                 | text        |
