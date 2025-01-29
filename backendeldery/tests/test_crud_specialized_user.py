# test_crud_specialized_user.py
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backendeldery.models import User, Client
from backendeldery.schemas import UserCreate
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


def test_search_subscriber_success_by_cpf(db_session, mocker):
    # Mock User object with proper attributes
    mock_user = User(
        id=1,
        name="John Doe",
        email="john.doe@example.com",
        phone="+123456789",
        role="subscriber",
        active=True
    )

    # Mock the query chain
    mock_query = mocker.Mock()
    mock_query.join.return_value = mock_query  # Mock `join` to return the same mock
    mock_query.filter.return_value = mock_query  # Mock `filter` to return the same mock
    mock_query.first.return_value = mock_user  # Mock `first` to return the mock_user

    # Patch the session's `query` method
    mocker.patch.object(db_session, "query", return_value=mock_query)

    # Create CRUD instance and criteria
    crud_specialized_user = CRUDSpecializedUser()
    criteria = {"cpf": "123.456.789-00"}

    result = crud_specialized_user.search_subscriber(db_session, criteria)

    assert result.id == 1, f"Expected user ID 1, got {result.id}"


def test_search_subscriber_success_by_email(db_session, mocker):
    # Mock User object
    mock_user = User(
        id=2,
        name="Jane Doe",
        email="jane.doe@example.com",
        phone="+987654321",
        role="subscriber",
        active=True
    )

    # Mock the query chain
    mock_query = mocker.Mock()
    mock_query.filter.return_value = mock_query  # Mock `filter` to return the same mock
    mock_query.first.return_value = mock_user  # Mock `first` to return the mock_user

    # Patch the session's `query` method
    mocker.patch.object(db_session, "query", return_value=mock_query)

    # Create CRUD instance and criteria
    crud_specialized_user = CRUDSpecializedUser()
    criteria = {"email": "jane.doe@example.com"}

    result = crud_specialized_user.search_subscriber(db_session, criteria)

    # Assert that the correct user is returned
    assert result.id == 2, f"Expected user ID 2, got {result.id}"


def test_search_subscriber_user_not_found(db_session, mocker):
    # Mock the query chain to return None for `first()`
    mock_query = mocker.Mock()
    mock_query.filter.return_value = mock_query  # Ensure `filter` returns the same mock
    mock_query.first.return_value = None  # Simulate no result found

    # Patch the session's `query` method to return the mock query
    mocker.patch.object(db_session, "query", return_value=mock_query)

    # Create CRUD instance and criteria
    crud_specialized_user = CRUDSpecializedUser()
    criteria = {"phone": "+111222333"}

    result = crud_specialized_user.search_subscriber(db_session, criteria)

    assert result is None, "Expected no user to be found, but got a result"
