import pytest
from sqlalchemy.orm import Session
from backendeldery.crud.users import CRUDUser
from backendeldery.models import User
from backendeldery.schemas import UserCreate
from fastapi import HTTPException

@pytest.fixture
def db_session(mocker):
    return mocker.Mock(spec=Session)

@pytest.fixture
def crud_user():
    return CRUDUser()

def test_create_user(db_session, crud_user):
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

    db_session.query.return_value.filter.return_value.first.return_value = None
    db_session.add.return_value = None
    db_session.flush.return_value = None
    db_session.refresh.return_value = None

    user = crud_user.create(db_session, user_data.model_dump(), created_by, user_ip)

    assert user.email == user_data.email
    assert user.phone == user_data.phone

    # Test invalid user creation
    invalid_user_data = user_data.model_copy(update={"email": "invalid-email"})
    with pytest.raises(ValueError):  # Pydantic raises ValueError for validation errors
        UserCreate(**invalid_user_data.model_dump())  # This will raise a validation error

def test_read_user(db_session, crud_user):
    user_id = 1
    user = User(id=user_id, email="test@example.com", phone="+123456789")
    db_session.query.return_value.get.return_value = user

    result = crud_user.read(db_session, user_id)

    assert result.id == user_id
    assert result.email == "test@example.com"

def test_update_user(db_session, crud_user):
    user_id = 1
    user = User(id=user_id, email="test@example.com", phone="+123456789")
    db_session.query.return_value.get.return_value = user
    update_data = {"email": "new@example.com"}

    updated_user = crud_user.update(db_session, user_id, update_data)

    assert updated_user.email == "new@example.com"

def test_delete_user(db_session, crud_user):
    user_id = 1
    user = User(id=user_id, email="test@example.com", phone="+123456789")
    db_session.query.return_value.get.return_value = user

    crud_user.delete(db_session, user_id)

    db_session.delete.assert_called_once_with(user)
    db_session.commit.assert_called_once()