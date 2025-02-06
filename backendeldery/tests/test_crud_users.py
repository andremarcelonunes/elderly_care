# test_crud_users.py
import pytest
from sqlalchemy.orm import Session
from backendeldery.crud.users import CRUDUser
from backendeldery.schemas import UserCreate


@pytest.fixture
def db_session(mocker):
    return mocker.Mock(spec=Session)


@pytest.fixture
def user_data():
    return UserCreate(
        name="Jane Doe",
        email="jane.doe@example.com",
        phone="+987654321",
        role="subscriber",
        password="Strong@123",
        active=True,
        client_data={
            "cpf": "987.654.321-00",
            "birthday": "1992-02-02",
            "address": "456 Main St",
            "city": "Gotham",
            "neighborhood": "Uptown",
            "code_address": "67890",
            "state": "CA",
        },
    )


def test_create_user(db_session, user_data):
    crud_user = CRUDUser()
    created_user = crud_user.create(
        db_session, user_data.model_dump(), created_by=1, user_ip="127.0.0.1"
    )
    assert created_user.email == user_data.email
    assert created_user.phone == user_data.phone
    assert created_user.role == user_data.role
    assert created_user.active == user_data.active
