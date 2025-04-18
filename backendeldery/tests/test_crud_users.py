from collections import namedtuple
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backendeldery.crud.users import CRUDClient, CRUDUser
from backendeldery.models import User  # Ensure this import is correct
from backendeldery.schemas import SubscriberCreate, UserCreate, UserUpdate


@pytest.fixture
def db_session(mocker):
    return mocker.Mock(spec=Session)


@pytest.fixture
def user_data():
    return UserCreate(
        name="Jane Doe",
        email="jane.doe@example.com",
        phone="+987654321",
        receipt_type=1,
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


@pytest.mark.asyncio
async def test_update_user_with_valid_data(mocker):
    # Arrange
    mock_db = mocker.AsyncMock(spec=AsyncSession)
    mock_user = mocker.Mock(spec=User)
    mock_user.id = 1
    mock_user.name = "Old Name"
    mock_user.email = "old@example.com"

    # Mock the database query result
    mock_result = mocker.AsyncMock()
    # Use a regular Mock for scalar_one_or_none to avoid returning a coroutine
    mock_result.scalar_one_or_none = mocker.Mock(return_value=mock_user)
    mock_db.execute.return_value = mock_result

    # Create update data
    update_data = UserUpdate(email="new@example.com", active=True)

    # Create CRUD instance
    crud = CRUDUser()

    # Act
    result = await crud.update(
        db=mock_db,
        user_id=1,
        update_data=update_data,
        updated_by=2,
        user_ip="192.168.1.1",
    )

    # Assert
    assert result == mock_user
    assert result.email == "new@example.com"
    assert result.active is True
    assert result.updated_by == 2
    assert result.user_ip == "192.168.1.1"
    mock_db.add.assert_called_once_with(mock_user)


@pytest.mark.asyncio
async def test_get_attendant_user_with_attendant_data(mocker):
    # Arrange
    db = mocker.MagicMock()
    user_id = 1

    # Create mock user with attendant role and attendant_data
    mock_user = mocker.MagicMock()
    mock_user.id = user_id
    mock_user.role = "attendant"
    mock_user.name = "Test Attendant"
    mock_user.email = "attendant@example.com"

    # Create mock attendant_data
    mock_attendant_data = mocker.MagicMock()
    mock_user.attendant_data = mock_attendant_data

    # Create a fake __table__ with columns for both mocks
    FakeColumn = namedtuple("FakeColumn", ["name"])
    user_columns = [FakeColumn(name=col) for col in ["id", "name", "email", "role"]]
    attendant_columns = [FakeColumn(name=col) for col in ["id", "specialty"]]

    mock_user.__table__ = mocker.MagicMock()
    mock_user.__table__.columns = user_columns

    mock_attendant_data.__table__ = mocker.MagicMock()
    mock_attendant_data.__table__.columns = attendant_columns

    # Setup query mock chain
    db.query.return_value.filter.return_value.first.return_value = mock_user

    # Mock obj_to_dict function
    user_dict = {
        "id": user_id,
        "name": "Test Attendant",
        "role": "attendant",
        "email": "attendant@example.com",
    }

    obj_to_dict_mock = mocker.patch("backendeldery.crud.users.obj_to_dict")
    obj_to_dict_mock.return_value = user_dict

    # Initialize the class
    from backendeldery.crud.users import CRUDBase
    from backendeldery.models import User

    crud = CRUDBase(User)

    # Act
    result = await crud.get(db, user_id)

    # Assert
    assert result == user_dict
    db.query.assert_called_once_with(crud.model)
    # Just check that filter was called once without comparing the expression
    assert db.query.return_value.filter.call_count == 1


@pytest.mark.asyncio
async def test_create_client_with_valid_data(mocker):
    # Arrange
    db = mocker.MagicMock()
    user = mocker.MagicMock(spec=User)
    user.id = 1

    obj_in = SubscriberCreate(
        cpf="123.456.789-00",
        address="Test Street 123",
        neighborhood="Test Neighborhood",
        city="Test City",
        state="TS",
        code_address="12345-678",
        birthday=date(1980, 1, 1),
    )

    created_by = 2
    user_ip = "192.168.1.1"

    # Mock the crud_client model and save the mock
    mock_client = mocker.MagicMock()
    crud_client_model_mock = mocker.patch(
        "backendeldery.crud.users.crud_client.model", return_value=mock_client
    )

    # Act
    crud = CRUDClient()
    result = await crud.create(db, user, obj_in, created_by, user_ip)

    # Assert
    assert result == mock_client

    # Verify client data was correctly set
    expected_data = obj_in.model_dump()
    expected_data["user_id"] = user.id
    expected_data["created_by"] = created_by
    expected_data["user_ip"] = user_ip

    crud_client_model_call = crud_client_model_mock.call_args[1]
    for key, value in expected_data.items():
        assert crud_client_model_call[key] == value
