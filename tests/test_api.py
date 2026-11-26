import json
from http import HTTPStatus

import pytest


def test_health_endpoint_is_public_and_versioned(client):
    response = client.get("/api/v1/health")

    assert response.status_code == HTTPStatus.OK
    assert json.loads(response.content) == {
        "status": "ok",
        "service": "revix-api",
    }


@pytest.mark.django_db
def test_openapi_schema_includes_versioned_health_contract(admin_client):
    response = admin_client.get("/api/openapi.json")

    assert response.status_code == HTTPStatus.OK
    paths = response.json()["paths"]
    health_path = next(path for path in paths if path.endswith("/v1/health"))
    assert "get" in paths[health_path]
    assert paths[health_path]["get"]["tags"] == ["system"]

