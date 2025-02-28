from collections import namedtuple

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backendeldery.crud.users import CRUDUser
from backendeldery.models import User  # Ensure this import is correct
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


@pytest.mark.asyncio
async def test_create_user(db_session, user_data):
    crud_user = CRUDUser()
    created_user = await crud_user.create(
        db=db_session, obj_in=user_data.model_dump(), created_by=1, user_ip="127.0.0.1"
    )
    assert created_user.email == user_data.email
    assert created_user.phone == user_data.phone
    assert created_user.role == user_data.role
    assert created_user.active == user_data.active


@pytest.mark.asyncio
async def test_get_user_not_found(db_session):
    crud_user = CRUDUser()

    # Use .first() to simulate no user found
    db_session.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await crud_user.get(db=db_session, id=1)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_user_found(db_session):
    crud_user = CRUDUser()

    # Create a fake __table__ with fake columns for the User instance
    FakeColumn = namedtuple("FakeColumn", ["name"])
    fake_columns = [
        FakeColumn(name=col)
        for col in ["id", "name", "email", "phone", "role", "active"]
    ]
    faketable = type("faketable", (), {"columns": fake_columns})

    # Create a user instance with the necessary attributes
    mock_user = User(id=1, name="John Doe", email="john.doe@example.com")
    mock_user.phone = "123456789"
    mock_user.role = "subscriber"
    mock_user.active = True
    # Assign the fake __table__ to support obj_to_dict
    mock_user.__table__ = faketable()

    # Use .first() to return the fake user
    db_session.query.return_value.filter.return_value.first.return_value = mock_user

    result = await crud_user.get(db=db_session, id=1)

    # Verify the returned dict matches the mock user's data
    assert result["id"] == mock_user.id
    assert result["name"] == mock_user.name
    assert result["email"] == mock_user.email
    assert result["phone"] == mock_user.phone
    assert result["role"] == mock_user.role
    assert result["active"] == mock_user.active
