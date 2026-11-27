# API e documentação interativa

## Base e versionamento

A API Ninja está montada em `/api/`; os endpoints de produto usam o prefixo `/v1/` para permitir evolução compatível.

| Método | Caminho | Acesso | Finalidade |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | Público | Liveness da aplicação; não consulta o banco |
| `GET`, `PATCH` | `/api/v1/users/...` | Sessão Django | Rotas de perfil do template Cookiecutter Django |
| `POST` | `/api/v1/auth/register` | Público | Cria uma conta por email/senha e inicia uma sessão bearer |
| `POST` | `/api/v1/auth/login` | Público | Autentica email/senha e emite tokens |
| `POST` | `/api/v1/auth/refresh` | Público | Rotaciona o refresh token e o access token |
| `POST` | `/api/v1/auth/logout` | Bearer | Revoga a sessão atual |
| `GET` | `/api/v1/auth/me` | Bearer | Retorna a identidade autenticada |
| `POST` | `/api/v1/auth/password-reset/request` | Público | Solicita recuperação com resposta uniforme |
| `POST` | `/api/v1/auth/password-reset/confirm` | Público | Consome token de recuperação e troca a senha |

Os schemas de entrada e resposta são definidos em `revix_backend/authentication/api/schemas.py`. Os tokens são credenciais opacas aleatórias; o banco guarda apenas HMACs e o refresh token é rotacionado a cada uso. A recuperação envia um código aleatório de uso único por email e também guarda apenas seu HMAC. Os limites e detalhes de senha estão em `docs/SECURITY.md`.

O healthcheck não comprova disponibilidade do PostgreSQL. Um endpoint de readiness deve ser adicionado quando houver decisão sobre verificações de dependências e orquestração.

## Swagger UI e OpenAPI

Com `config.settings.local` (ou `API_DOCS_ENABLED=True` em uma configuração não produtiva), o Django Ninja registra:

- Swagger UI: `/api/docs`
- Esquema OpenAPI JSON: `/api/openapi.json`

As duas rotas exigem usuário staff via `staff_member_required`. Em configurações de teste e produção, `docs_url` e `openapi_url` ficam desativados. Acesse `/admin/` ou as telas de conta do template em desenvolvimento para criar/usar uma conta staff; não exponha a documentação pública em produção sem decisão explícita.

## Schemas

Use `ninja.Schema` e tipos de Pydantic 2 para validar entradas e serializar respostas. Schemas são contratos expostos ao app Flutter: mantenha nomes e formatos estáveis, e documente alterações incompatíveis com nova versão da API.

## Autenticação e evolução

As rotas de perfil herdadas do Cookiecutter usam `SessionAuth` e filtro pelo usuário autenticado. As rotas móveis usam bearer tokens opacos. Antes de expor operações sincronizadas, cada consulta deve derivar o proprietário da sessão autenticada; nunca aceite `user_id` arbitrário do cliente como autorização.

Google OAuth não está registrado. O cadastro móvel atual cria uma conta ativa sem etapa de confirmação de email; definir verificação e vinculação de contas antes de adicionar provedores sociais ou liberar sincronização com dados de produção. A base web já inclui Allauth e recuperação de senha por email. No desenvolvimento local, emails são capturados pelo Mailpit quando os containers estão em execução; produção precisa configurar e monitorar o provedor de email.
