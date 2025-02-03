from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette.responses import JSONResponse
from backendeldery.main import app

client = TestClient(app, raise_server_exceptions=False)

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
        raise RequestValidationError([{"loc": ["body", "item"], "msg": "Invalid item", "type": "value_error"}])

    response = client.post("/validation_exception", json={"item": "invalid"})
    assert response.status_code == 400
    assert "detail" in response.json()


def test_pydantic_validation_exception_handler():
    @app.post("/pydantic_validation_exception")
    async def pydantic_validation_exception_route(dict):
        raise ValidationError([{
            "loc": ("body", "item"),
            "msg": "Invalid item",
            "type": "value_error"
        }], model=dict)

    response = client.post("/pydantic_validation_exception", json={"item": "invalid"})
    assert response.status_code == 400
    assert "detail" in response.json()


def test_generic_exception_handler():
    @app.get("/generic_exception")
    async def generic_exception_route():
        raise Exception("Unexpected error")

    response = client.get("/generic_exception")
    print(response.status_code, response.json())
    assert response.status_code == 500
    assert response.json() == {
        "detail": "An unexpected error occurred. Please try again later.",
        "error": "Unexpected error"
    }


def test_users_router():
    response = client.get("/api/v1/users/subscriber/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Subscriber not found."}
