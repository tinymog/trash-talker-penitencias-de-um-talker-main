# language: pt

Funcionalidade: Autenticação em dois fatores (Google Authenticator)
  Como uma pessoa preocupada com a segurança da conta
  Quero que entrar exija também um código do aplicativo autenticador
  Para que só a senha não baste para chegar às minhas conversas

  Contexto:
    Dado que eu estou logado

  Cenário: Ativar a proteção exige confirmar um código do aplicativo
    Quando eu inicio a ativação do 2FA com a minha senha
    E eu confirmo a ativação com um código válido do aplicativo
    Então a proteção em dois fatores deve estar ativa
    E eu devo ter recebido 8 códigos de recuperação

  Cenário: Com a proteção ativa, a senha sozinha não entra
    Dado que a proteção em dois fatores está ativa na minha conta
    Quando eu saio da conta
    E eu entro com o e-mail "pessoa@exemplo.com" e a senha "Senha-Forte-123"
    Então eu devo receber o status 202
    E eu ainda não devo estar autenticado

  Cenário: Entrar com a senha e um código do aplicativo
    Dado que a proteção em dois fatores está ativa na minha conta
    E que eu saí e informei minha senha de novo
    Quando eu informo um código válido do aplicativo
    Então eu devo receber o status 200
    E eu devo estar autenticado

  Cenário: Código errado não entra
    Dado que a proteção em dois fatores está ativa na minha conta
    E que eu saí e informei minha senha de novo
    Quando eu informo o código "000000"
    Então eu devo receber o status 400
    E eu ainda não devo estar autenticado

  Cenário: Cada código de recuperação vale uma única vez
    Dado que a proteção em dois fatores está ativa na minha conta
    E que eu saí e informei minha senha de novo
    E que eu entrei com um código de recuperação
    E que eu saí e informei minha senha de novo
    Quando eu informo o mesmo código de recuperação
    Então eu devo receber o status 400
    E eu ainda não devo estar autenticado
