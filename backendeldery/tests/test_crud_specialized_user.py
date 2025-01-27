# test_crud_specialized_user.py
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backendeldery.models import User, Client
from backendeldery.schemas import UserCreate, SubscriberCreate
from backendeldery.crud.users import CRUDSpecializedUser

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

def test_create_subscriber_success(db_session, mocker, user_data):
    # Mock User and Client objects with proper attributes
    mock_user = User(
        id=1,
        name="John Doe",
        email="john.doe@example.com",
        phone="+123456789",
        role="subscriber",
        active=True,
        created_at="2025-01-01T12:00:00",
        updated_at=None,
        created_by=1,
        updated_by=None,
        user_ip="127.0.0.1",
        password_hash="hashed_password"
    )

    mock_client = Client(
        user_id=1,  # Use user_id as the primary key
        team_id=None,
        cpf="12345678900",
        birthday="1990-01-01",
        address="123 Main St",
        neighborhood="Downtown",
        city="Metropolis",
        state="NY",
        code_address="12345",
        created_at="2025-01-01T12:00:00",
        updated_at=None,
        created_by=1,
        updated_by=None,
        user_ip="127.0.0.1"
    )

    # Mock CRUD methods
    mocker.patch('backendeldery.crud.users.CRUDUser.create', return_value=mock_user)
    mocker.patch('backendeldery.crud.users.CRUDClient.create', return_value=mock_client)
    crud_specialized_user = CRUDSpecializedUser()
    result = crud_specialized_user.create_subscriber(
        db_session,
        user_data.model_dump(),
        created_by=1,
        user_ip="127.0.0.1"
    )

    assert result['user'] == {
        "id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+123456789",
        "role": "subscriber",
        "active": True,
        "created_at": "2025-01-01T12:00:00",
        "updated_at": None,
        "created_by": 1,
        "updated_by": None,
        "user_ip": "127.0.0.1",
        "password_hash": "hashed_password"
    }, f"User mismatch: {result['user']}"
    assert result['client'] == {
        "user_id": 1,  # Use user_id as the primary key
        "team_id": None,
        "cpf": "12345678900",
        "birthday": "1990-01-01",
        "address": "123 Main St",
        "neighborhood": "Downtown",
        "city": "Metropolis",
        "state": "NY",
        "code_address": "12345",
        "created_at": "2025-01-01T12:00:00",
        "updated_at": None,
        "created_by": 1,
        "updated_by": None,
        "user_ip": "127.0.0.1"
    }, f"Client mismatch: {result['client']}"

def test_create_subscriber_error(db_session, mocker, user_data):
    mocker.patch('backendeldery.crud.users.CRUDUser.create', side_effect=Exception("Unexpected error"))

    crud_specialized_user = CRUDSpecializedUser()
    with pytest.raises(HTTPException) as excinfo:
        crud_specialized_user.create_subscriber(db_session, user_data.model_dump(), created_by=1, user_ip="127.0.0.1")
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == "Erro inesperado: Unexpected error"