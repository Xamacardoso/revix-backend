from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from ninja import NinjaAPI
from ninja.security import SessionAuth

from revix_backend.api_schemas import HealthResponse

api = NinjaAPI(
    title="Revix API",
    version="1.0.0",
    description=(
        "API do Revix para gerenciamento de veículos e histórico de manutenção. "
        "Os endpoints de domínio serão adicionados nas próximas etapas."
    ),
    urls_namespace="api",
    auth=SessionAuth(),
    # O esquema OpenAPI e o Swagger UI existem apenas em desenvolvimento e são
    # restritos a usuários staff, evitando publicar detalhes da API em produção.
    docs_url="/docs" if settings.API_DOCS_ENABLED else None,
    openapi_url="/openapi.json" if settings.API_DOCS_ENABLED else None,
    docs_decorator=staff_member_required,
)

api.add_router("/v1/users/", "revix_backend.users.api.views.router")


@api.get("/v1/health", auth=None, response=HealthResponse, tags=["system"])
def health_check(request):
    """Verificação pública de disponibilidade, sem consultar o banco."""
    return {"status": "ok", "service": "revix-api"}
