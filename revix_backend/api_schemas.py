from typing import Literal

from ninja import Schema
from pydantic import Field


class HealthResponse(Schema):
    """Resposta tipada do endpoint de healthcheck."""

    status: Literal["ok"] = Field(description="Estado da aplicação.")
    service: str = Field(description="Identificador deste serviço.")
