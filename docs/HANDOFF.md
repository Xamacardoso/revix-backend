# Handoff: autenticação móvel WIP

## Objetivo

Adicionar autenticação básica à API do Revix, modular para futuros provedores, com rate limits, armazenamento seguro de credenciais e base funcional para recuperação de senha.

## Estado atual

Implementação WIP no backend, sem integração com o app Flutter e sem Google OAuth. As rotas usam schemas Pydantic/Django Ninja e ficam sob `/api/v1/auth/`.

## O que foi feito

- Criado `revix_backend/authentication/` com contrato/registro de provedores e provedor de email/senha.
- Adicionados cadastro e login, access/refresh bearer tokens opacos, rotação de refresh, logout e endpoint de identidade atual.
- Criados modelos de sessão e token de redefinição, com migração inicial.
- Adicionados pedidos e confirmação de redefinição: resposta uniforme para contas existentes/desconhecidas, token aleatório de uso único, expiração, armazenamento HMAC e revogação de sessões após troca.
- Configurados limites por IP e por identidade para cadastro, login, refresh e recuperação. Em produção, os contadores dependem do Redis/cache compartilhado configurado no projeto.
- Documentadas rotas e decisões em `docs/API.md`, `docs/ARCHITECTURE.md` e `docs/SECURITY.md`; atualizado este arquivo de continuidade e a orientação em `AGENTS.md`.

## Decisões

- Senhas usam os validadores do Django e o hasher Argon2 já priorizado em `PASSWORD_HASHERS`; o Argon2 gera salt aleatório por senha.
- O banco guarda HMACs das credenciais opacas; tokens brutos só são devolvidos na emissão ou enviados ao email de recuperação.
- Google OAuth permanece desativado até definir validação de identidade, vinculação de conta e credenciais.
- Autenticação móvel é independente das rotas de perfil herdadas, que ainda usam sessão Django.

## Arquivos relevantes

- `revix_backend/authentication/`: provedores, schemas, rotas, serviços, modelos, tokens e limites.
- `revix_backend/authentication/migrations/0001_initial.py`: tabelas de sessão e redefinição.
- `revix_backend/authentication/tests/test_api.py`: fluxos, hashing, rotação, expiração, recuperação e rate limit.
- `config/api.py`, `config/settings/base.py`: registro das rotas e defaults.
- `docs/API.md`, `docs/SECURITY.md`, `docs/ARCHITECTURE.md`: contrato e decisões.

## Validação executada

- `uv run pytest`: **54 passaram**.
- `uv run ruff check .`: passou.
- `uv run mypy revix_backend/authentication`: passou.
- `DJANGO_SETTINGS_MODULE=config.settings.test uv run python manage.py makemigrations --check --dry-run`: sem alterações pendentes.
- `DJANGO_SETTINGS_MODULE=config.settings.test uv run python manage.py check`: sem problemas no system check.

O Django reportou avisos de diretório `staticfiles/` ausente durante testes; eles não causaram falhas.

## Pendências e limitações conhecidas

- Cadastro móvel ainda não verifica posse do email. Definir confirmação antes de integrar OAuth ou sincronização com dados reais.
- O email de recuperação é enviado de forma síncrona. Corpo e status não enumeram contas, mas o tempo de resposta pode variar; mover o envio para uma fila durável antes de depender dessa rota em produção sensível.
- Produção precisa configurar e monitorar entrega de email, Redis compartilhado e, se houver proxy, um cabeçalho de IP confiável sobrescrito pelo proxy (`AUTH_CLIENT_IP_HEADER`).
- O app Flutter continua offline-first e não consome esses endpoints. Definir o contrato de integração e estratégia de sincronização separadamente.
- Ainda não há rotina de limpeza para sessões e tokens expirados; avaliar retenção e agendamento.

## Próxima ação recomendada

Revisar os contratos com o app, decidir confirmação de email e entrega assíncrona de recuperação; depois executar testes de concorrência/rotação em PostgreSQL e integrar o app usando autenticação bearer.
