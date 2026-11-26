# API e documentação interativa

## Base e versionamento

A API Ninja está montada em `/api/`; os endpoints de produto usam o prefixo `/v1/` para permitir evolução compatível.

| Método | Caminho | Acesso | Finalidade |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | Público | Liveness da aplicação; não consulta o banco |
| `GET`, `PATCH` | `/api/v1/users/...` | Sessão Django | Rotas de perfil do template Cookiecutter Django |

O healthcheck não comprova disponibilidade do PostgreSQL. Um endpoint de readiness deve ser adicionado quando houver decisão sobre verificações de dependências e orquestração.

## Swagger UI e OpenAPI

Com `config.settings.local` (ou `API_DOCS_ENABLED=True` em uma configuração não produtiva), o Django Ninja registra:

- Swagger UI: `/api/docs`
- Esquema OpenAPI JSON: `/api/openapi.json`

As duas rotas exigem usuário staff via `staff_member_required`. Em configurações de teste e produção, `docs_url` e `openapi_url` ficam desativados. Acesse `/admin/` ou as telas de conta do template em desenvolvimento para criar/usar uma conta staff; não exponha a documentação pública em produção sem decisão explícita.

## Schemas

Use `ninja.Schema` e tipos de Pydantic 2 para validar entradas e serializar respostas. Schemas são contratos expostos ao app Flutter: mantenha nomes e formatos estáveis, e documente alterações incompatíveis com nova versão da API.

## Autenticação futura

As rotas de perfil herdadas do Cookiecutter usam `SessionAuth` e filtro pelo usuário autenticado. Isso atende o admin e a exploração inicial; o app mobile não deve depender de sessão de navegador. Antes de expor operações sincronizadas, definir autenticação móvel, emissão/rotação/revogação de credenciais e autorização por proprietário.

Google OAuth e endpoints móveis de login/recuperação não estão registrados. A base web já inclui Allauth e recuperação de senha por email. No desenvolvimento local, emails são capturados pelo Mailpit quando os containers estão em execução. Produção precisa configurar provedor de email e política de recuperação antes de aceitar contas reais.
