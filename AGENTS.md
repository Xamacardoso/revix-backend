# Contexto técnico do backend Revix

## Leitura inicial

- Leia `docs/ARCHITECTURE.md` para conhecer a arquitetura e decisões já tomadas.
- Leia `docs/API.md` antes de alterar endpoints, schemas ou publicação OpenAPI.
- Consulte também `../revix-app/AGENTS.md` e os requisitos em `../revix-app/openspec/` ao implementar recursos compartilhados com o aplicativo.

## Stack e comandos

- Projeto gerado pelo Cookiecutter Django, Python 3.14, Django 6, Django Ninja e Pydantic 2.
- PostgreSQL é o banco de aplicação configurado; Docker Compose oferece o ambiente local.
- Use `uv` para dependências e `uv run` para executar comandos Python.
- Comandos usuais: `uv sync --group dev`, `uv run python manage.py migrate`, `uv run python manage.py runserver`, `uv run pytest`, `uv run ruff check .`.

## Regras para evolução

- O usuário customizado `users.User` usa email como identificador e deve permanecer definido antes da primeira migração de produção.
- Schemas Pydantic/Django Ninja são contratos públicos; mantenha APIs sob `/api/v1` e documente mudanças em `docs/API.md`.
- Toda consulta a dados de usuário deve derivar o proprietário da identidade autenticada no servidor. Nunca aceite `user_id` do cliente como autorização.
- Login social Google e os endpoints móveis de autenticação/recuperação ainda não estão implementados. Não habilite provedor OAuth sem especificação, credenciais e fluxo de vinculação de conta.
- Mudanças no modelo devem incluir migrações e testes. Preserve os dados locais do app; sincronização com backend exige contrato e estratégia de conflito definidos.
- Swagger e OpenAPI ficam disponíveis em desenvolvimento apenas para usuários staff; ambos são desativados em produção.
