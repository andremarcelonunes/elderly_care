# test_crud_base.py
from unittest.mock import patch

import pytest
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backendeldery.crud.base import CRUDBase
from backendeldery.models import User
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


class MockUserCreate(BaseModel):
    name: str
    email: str
    phone: str
    role: str
    active: bool
    password_hash: str


class MockUserUpdate(BaseModel):
    name: str
    email: str
    phone: str
    role: str
    active: bool
    password_hash: str


@pytest.mark.asyncio
async def test_get_user(db_session):
    crud_base = CRUDBase(User)
    mocked_user = User(id=1)
    db_session.query.return_value.filter.return_value.first.return_value = mocked_user
    with patch(
        "backendeldery.utils.obj_to_dict",
        return_value={
            "id": 1,
            "name": None,
            "email": None,
            "phone": None,
            "role": None,
            "active": None,
            "password_hash": None,
            "created_at": None,
            "updated_at": None,
            "created_by": None,
            "updated_by": None,
            "user_ip": None,
        },
    ) as mock_obj_to_dict:
        result = await crud_base.get(db_session, 1)
        assert result == {
            "id": 1,
            "name": None,
            "email": None,
            "phone": None,
            "role": None,
            "active": None,
            "password_hash": None,
            "created_at": None,
            "updated_at": None,
            "created_by": None,
            "updated_by": None,
            "user_ip": None,
        }


@pytest.mark.asyncio
async def test_create_user_with_client_data(db_session, user_data):
    crud_base = CRUDBase(User)
    # Mock database session methods
    db_session.add.return_value = None
    db_session.commit.return_value = None
    db_session.refresh.return_value = None
    user_data_dict = user_data.model_dump()
    user_data_dict["password_hash"] = "hashed_password"
    user_data_dict["client_data"] = {
        "cpf": "987.654.321-00",
        "address": "456 Main St",
        "neighborhood": "Uptown",
        "city": "Gotham",
        "state": "CA",
        "code_address": "67890",
        "birthday": "1992-02-02",
    }

    # Exclude 'client_data' from the dictionary, since it's a read-only property on User
    sqlalchemy_user_data = {
        k: v
        for k, v in user_data_dict.items()
        if hasattr(User, k) and k != "client_data"
    }
    mock_user_data = MockUserCreate(**sqlalchemy_user_data)
    db_session.query.return_value.filter.return_value.first.return_value = User(
        **sqlalchemy_user_data
    )
    with patch(
        "backendeldery.utils.obj_to_dict",
        return_value={
            "id": 1,
            "email": user_data.email,
            "name": user_data.name,
            "phone": user_data.phone,
            "role": user_data.role,
            "active": user_data.active,
            "created_at": None,
            "updated_at": None,
            "created_by": None,
            "updated_by": None,
            "user_ip": None,
        },
    ):
        result = await crud_base.create(db_session, mock_user_data, 1, "127.1.1.1")
        assert result["email"] == user_data.email


@pytest.mark.asyncio
async def test_update_user(db_session, user_data):
    crud_base = CRUDBase(User)
    db_session.query.return_value.filter.return_value.first.return_value = User(id=1)
    user_data_dict = user_data.model_dump(exclude_unset=True)
    user_data_dict["password_hash"] = "hashed_password"
    user_data_dict.pop("password")  # Exclude password
    user_data_dict.pop("client_data")  # Exclude client_data as it's not valid for User
    mock_user_update = MockUserUpdate(**user_data_dict)
    result = await crud_base.update(db_session, 1, mock_user_update, 1, "127.1.1.1")
    assert result["email"] == user_data.email


@pytest.mark.asyncio
async def test_delete_user(db_session):
    crud_base = CRUDBase(User)
    db_session.query.return_value.filter.return_value.first.return_value = User(id=1)
    result = await crud_base.delete(db_session, 1)
    assert result["id"] == 1
