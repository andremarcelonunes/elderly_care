# test_user_service.py
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backendeldery.schemas import UserCreate
from backendeldery.services.users import UserService
from backendeldery.validators.user_validator import UserValidator
from backendeldery.crud.users import crud_specialized_user

@pytest.fixture
def db_session(mocker):
    return mocker.Mock(spec=Session)

@pytest.fixture
def user_data():
    return UserCreate(
        name="John Doe",
        email="john.doe@example.com",
        phone="+123456789",
        role="subscriber",
        password="Strong@123",
        active=True,
        client_data={
            "cpf": "123.456.789-00",
            "birthday": "1990-01-01",
            "address": "123 Main St",
            "city": "Metropolis",
            "neighborhood": "Downtown",
            "code_address": "12345",
            "state": "NY"
        }
    )

@pytest.mark.asyncio
async def test_register_client_success(db_session, mocker, user_data):
    mocker.patch.object(UserValidator, 'validate_subscriber', return_value=None)
    mocker.patch.object(crud_specialized_user, 'create_subscriber', return_value={"user": {}, "client": {}})

    result = await UserService.register_client(db_session, user_data, created_by=1, user_ip="127.0.0.1")
    assert result == {"user": {}, "client": {}}

@pytest.mark.asyncio
async def test_register_client_validation_error(db_session, mocker, user_data):
    mocker.patch.object(
        UserValidator,
        'validate_subscriber',
        side_effect=HTTPException(status_code=422, detail="Validation error")
    )

    with pytest.raises(HTTPException) as excinfo:
        await UserService.register_client(db_session, user_data, created_by=1, user_ip="127.0.0.1")


@pytest.mark.asyncio
async def test_register_client_unexpected_error(db_session, mocker, user_data):
    mocker.patch.object(UserValidator, 'validate_subscriber', return_value=None)
    mocker.patch.object(crud_specialized_user, 'create_subscriber', side_effect=Exception("Unexpected error"))
    with pytest.raises(HTTPException) as excinfo:
        await UserService.register_client(db_session, user_data, created_by=1, user_ip="127.0.0.1")
    assert excinfo.value.status_code == 500

