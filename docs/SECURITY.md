# Segurança de autenticação

## Credenciais e sessões

- O fluxo de senha usa o `PasswordProvider`; provedores futuros devem implementar o contrato em `authentication/providers/base.py` e ser adicionados ao registro. Nenhum provedor social está habilitado.
- Django prioriza `Argon2PasswordHasher`, que gera hashes com salt aleatório. Senhas em texto puro nunca são persistidas.
- Access tokens duram 15 minutos; refresh tokens duram 30 dias e são rotacionados a cada uso. Cada sessão guarda somente HMAC-SHA256 das credenciais opacas. Reuso de um refresh anterior revoga a sessão inteira.
- Logout e redefinição de senha revogam sessões. Alterar `SECRET_KEY` invalida todos os tokens emitidos, pois ela participa do HMAC.
- A API de perfil herdada do template continua usando sessão Django; `/api/v1/auth/me` usa a identidade obtida do bearer token.

## Recuperação de conta

- A solicitação responde com a mesma mensagem e status para emails existentes e inexistentes.
- O envio de email é síncrono nesta primeira versão; embora corpo e status sejam uniformes, o tempo de resposta pode variar. Antes de depender dessa rota em produção sensível, mover o envio para uma fila durável.
- Tokens aleatórios expiram em 30 minutos, são armazenados apenas como HMAC e só podem ser consumidos uma vez. Uma troca bem-sucedida revoga sessões e invalida tokens de recuperação ainda pendentes.
- O token é enviado por email. Produção precisa configurar um backend de email funcional e monitorar falhas de entrega.
- O cadastro atual não exige confirmação de email. Antes de habilitar login social ou sincronização com dados de produção, estabelecer confirmação de email, vinculação de contas e política de recuperação.

## Limites de requisição

Os contadores são janelas fixas no cache Django; valores por padrão:

| Operação | Limite por IP | Limite por identidade |
| --- | --- | --- |
| Cadastro | 5/hora | 5/hora por email |
| Login | 10/minuto | 5/minuto por email |
| Refresh | 30/minuto | — |
| Pedido de recuperação | 10/hora | 3/hora por email |
| Confirmação de recuperação | 10/hora | 5/hora por token |

As chaves de cache não contêm IP, email ou token em claro. Produção configura Redis como cache compartilhado; o cache de memória local serve apenas a desenvolvimento e testes em processo único. A origem do IP é `REMOTE_ADDR` por padrão. `AUTH_CLIENT_IP_HEADER` só deve apontar para um cabeçalho que o proxy confiável sobrescreve, nunca para um valor arbitrário enviado pelo cliente. Falhas no cache bloqueiam os endpoints de autenticação.

## Configuração

Os tempos, limites e cabeçalho de IP são definidos em `config/settings/base.py` e podem ser sobrescritos por ambiente. As políticas de senha usam os validadores Django configurados pelo projeto.
