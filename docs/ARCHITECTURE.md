# Arquitetura inicial

## Escopo

Este repositório inicia a base do backend Revix a partir do [Cookiecutter Django](https://github.com/cookiecutter/cookiecutter-django). O template fornece projeto Django com settings separados por ambiente, usuário customizado, PostgreSQL, Docker Compose, testes e ferramentas de qualidade. Django Ninja publica a API; seus schemas são baseados em Pydantic 2.

Esta base inclui autenticação móvel por email/senha e sessões bearer com rotação e revogação, além de recuperação de senha por token de uso único. Ainda não implementa sincronização de veículos/manutenções com o app nem OAuth Google.

## Componentes

- `config/`: configurações Django e roteamento, incluindo `config/api.py` para API Ninja.
- `revix_backend/users/`: modelo customizado e telas de conta incluídas pelo template.
- `revix_backend/authentication/`: provedores de credenciais, sessões móveis, limites de requisição e recuperação de senha.
- `revix_backend/api_schemas.py`: schemas Pydantic expostos pelo Ninja.
- `tests/`: testes da fundação da API.
- `docker-compose.local.yml`: ambiente local com Django, PostgreSQL e Mailpit.
- `docs/API.md`: rotas, Swagger e estratégia futura de autenticação.

## Banco de dados

PostgreSQL é o banco configurado para desenvolvimento e produção. As credenciais são carregadas via variáveis de ambiente no padrão do Cookiecutter Django. Use Docker Compose localmente; não armazene credenciais reais no repositório. O SQLite do app Flutter continua sendo a fonte de dados local até que a sincronização seja especificada.

O template criou o usuário `users.User`, com email como identificador, e a migração inicial. Mantenha `AUTH_USER_MODEL` definido antes de novas migrações ou da criação de dados de produção.

## Contas e segurança

Django Allauth e as views web de conta do template estão instalados. A API de perfil do template continua usando sessão Django. A API móvel independente oferece cadastro/login, rotação de refresh token, logout, identidade atual e recuperação de senha; veja `docs/SECURITY.md` e `docs/API.md`.

Google OAuth está reservado para uma etapa posterior. Antes de ativá-lo, definir verificação do token de identidade, validação de audience/issuer, política para vincular email existente, estados de email verificado, revogação e ciclo de vida da sessão. A autenticação atual não vincula contas de provedores externos.

Toda futura consulta de veículo/manutenção deverá derivar o dono de `request.auth` no servidor. Não aceitar `user_id` arbitrário do cliente como controle de acesso.
