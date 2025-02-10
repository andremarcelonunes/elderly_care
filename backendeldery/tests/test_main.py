import json
import pytest
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import ValidationError, BaseModel
from backendeldery.main import pydantic_validation_exception_handler
from backendeldery.main import app

client = TestClient(app, raise_server_exceptions=False)


class DummyModel(BaseModel):
    item: int


def test_http_exception_handler():
    @app.get("/http_exception")
    async def http_exception_route():
        raise HTTPException(status_code=404, detail="Not found")

    response = client.get("/http_exception")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


def test_validation_exception_handler():
    @app.post("/validation_exception")
    async def validation_exception_route():
        raise RequestValidationError(
            [{"loc": ["body", "item"], "msg": "Invalid item", "type": "value_error"}]
        )

    response = client.post("/validation_exception", json={"item": "invalid"})
    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_pydantic_validation_exception_handler_directly():
    # Create a dummy request object.
    request = Request({"type": "http"})

    # Trigger a real ValidationError by providing an invalid type.
    try:
        DummyModel.parse_obj({"item": "invalid"})
    except ValidationError as exc:
        validation_error = exc

    # Pass the caught ValidationError to the exception handler.
    response = await pydantic_validation_exception_handler(request, validation_error)

    # Assert that the handler returns a 400 status.
    assert response.status_code == 400

    # Decode the response body.
    body = json.loads(response.body.decode("utf-8"))

    # Check that the response contains the expected error details.
    assert "detail" in body
    # (The exact structure may vary with Pydantic v2, so we check for a relevant substring.)
    assert any("integer" in err["msg"].lower() for err in body["detail"])


def test_generic_exception_handler():
    @app.get("/generic_exception")
    async def generic_exception_route():
        raise Exception("Unexpected error")

    response = client.get("/generic_exception")
    print(response.status_code, response.json())
    assert response.status_code == 500
    assert response.json() == {
        "detail": "An unexpected error occurred. Please try again later.",
        "error": "Unexpected error",
    }


#   def test_users_router():
#    response = client.get("/api/v1/users/subscriber/30")
#    assert response.status_code == 404
#    assert response.json() == {"detail": "Subscriber not found."}


def test_request_validation_exception_handler():
    @app.post("/request_validation_exception")
    async def request_validation_exception_route():
        raise RequestValidationError(
            [{"loc": ["body", "item"], "msg": "Invalid item", "type": "value_error"}]
        )

    response = client.post("/request_validation_exception", json={"item": "invalid"})
    assert response.status_code == 400
    assert "detail" in response.json()
