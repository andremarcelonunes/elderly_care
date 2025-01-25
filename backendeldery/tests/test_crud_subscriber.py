import pytest
from sqlalchemy.orm import Session
from backendeldery.crud.users import CRUDSpecializedUser
from backendeldery.schemas import UserCreate
from backendeldery.models import User, Client  # Import the User and Client classes
from fastapi import HTTPException
from unittest.mock import MagicMock

@pytest.fixture
def db_session(mocker):
    session = mocker.Mock(spec=Session)
    session.begin = MagicMock()
    return session

@pytest.fixture
def crud_specialized_user():
    return CRUDSpecializedUser()

def test_create_subscriber(db_session, crud_specialized_user):
    user_data = UserCreate(
        name="Test User",
        email="test@example.com",
        phone="+123456789",
        role="subscriber",
        password="password123",
        client_data={"cpf": "12345678901", "birthday": "2000-01-01"}
    )
    created_by = 1
    user_ip = "127.0.0.1"

    # Mocking the database session methods
    db_session.query.return_value.filter.return_value.first.return_value = None
    db_session.add.return_value = None
    db_session.flush.return_value = None
    db_session.refresh.return_value = None

    # Test successful creation
    result = crud_specialized_user.create_subscriber(
        db=db_session,
        user_data=user_data.model_dump(),
        created_by=created_by,
        user_ip=user_ip
    )
    assert result["user"]["email"] == user_data.email
    client_data_dict = user_data.client_data.model_dump()
    assert result["client"]["cpf"] == client_data_dict["cpf"]

    # Test missing client_data
    user_data_missing_client_data = user_data.model_copy(update={"client_data": None})
    with pytest.raises(HTTPException) as excinfo:
        crud_specialized_user.create_subscriber(
            db=db_session,
            user_data=user_data_missing_client_data.model_dump(),
            created_by=created_by,
            user_ip=user_ip
        )
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "client_data é obrigatório para registro de cliente."

    # Test user already exists
    existing_user = User(id=1, email="test@example.com", phone="+123456789")
    db_session.query.return_value.filter.return_value.first.return_value = User(email="test@example.com")
    with pytest.raises(HTTPException) as excinfo:
        crud_specialized_user.create_subscriber(
            db=db_session,
            user_data=user_data.model_dump(),
            created_by=created_by,
            user_ip=user_ip
        )
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Email already exists"

    # Test divergent email
    existing_client = Client(cpf="12345678901", user_id=1)
    existing_user = User(id=1, email="different@example.com", phone="+123456789")
    db_session.query.return_value.filter.side_effect = [existing_client, existing_user]
    with pytest.raises(HTTPException) as excinfo:
        crud_specialized_user.create_subscriber(
            db=db_session,
            user_data=user_data.model_dump(),
            created_by=created_by,
            user_ip=user_ip
        )
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Email is divergent from the registered data"

    # Test divergent phone
    existing_user.email = "test@example.com"
    existing_user.phone = "+987654321"
    with pytest.raises(HTTPException) as excinfo:
        crud_specialized_user.create_subscriber(
            db=db_session,
            user_data=user_data.model_dump(),
            created_by=created_by,
            user_ip=user_ip
        )
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Phone number is divergent from the registered data"