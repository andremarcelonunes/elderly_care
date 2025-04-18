from datetime import date
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from backendeldery.crud.users import CRUDSpecializedUser
from backendeldery.models import Client, User
from backendeldery.schemas import UserCreate, UserInfo, UserUpdate


@pytest.fixture
def db_session(mocker):
    return mocker.Mock(spec=Session)


async def raise_exception(*args, **kwargs):
    raise Exception("Unexpected error")


@pytest.fixture
def user_data():
    return UserCreate(
        name="John Doe",
        email="john.doe@example.com",
        phone="+123456789",
        receipt_type=1,
        password="Strong@123",
        active=True,
        role="assisted",  # Add the required role field
        client_data={
            "cpf": "123.456.789-00",
            "birthday": "1990-01-01",
            "address": "123 Main St",
            "city": "Metropolis",
            "neighborhood": "Downtown",
            "code_address": "12345",
            "state": "NY",
        },
    )


@pytest.fixture
def user_update_data():
    return UserUpdate(
        email="updated.email@example.com",
        phone="+123456789",
        receipt_type=1,
        active=True,
        client_data={
            "address": "456 New St",
            "neighborhood": "Uptown",
            "city": "New City",
            "state": "NC",
            "code_address": "67890",
        },
    )


@pytest.mark.asyncio
async def test_create_subscriber_success(db_session, mocker, user_data):
    # Create a mock User with required attributes.
    mock_user = User(
        id=1,
        name="John Doe",
        email="john.doe@example.com",
        phone="+123456789",
        receipt_type=1,
        role="subscriber",
        active=True,
        created_at="2025-01-01T12:00:00",
        updated_at=None,
        created_by=1,
        updated_by=None,
        user_ip="127.0.0.1",
        password_hash="hashed_password",
    )

    # Create a mock Client with required attributes.
    mock_client = Client(
        user_id=1,  # using user_id as the primary key
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
        user_ip="127.0.0.1",
    )

    # IMPORTANT: Attach the client to the user so that user.client is truthy.
    mock_user.client = mock_client

    # Patch the CRUD methods to return our mock objects.
    mocker.patch("backendeldery.crud.users.CRUDUser.create", return_value=mock_user)
    mocker.patch("backendeldery.crud.users.CRUDClient.create", return_value=mock_client)

    # Instantiate your specialized user crud and call create_subscriber.
    crud_specialized_user = CRUDSpecializedUser()
    result = await crud_specialized_user.create_subscriber(
        db_session, user_data.model_dump(), created_by=1, user_ip="127.0.0.1"
    )

    # Assert that the result is an instance of UserInfo.
    assert isinstance(
        result, UserInfo
    ), "The returned object is not a UserInfo instance."

    # Now check the fields of the UserInfo.
    assert result.id == 1
    assert result.name == "John Doe"
    assert result.email == "john.doe@example.com"
    assert result.phone == "+123456789"
    assert result.receipt_type == 1
    assert result.role == "subscriber"
    assert result.active is True

    # Assert the nested SubscriberInfo (client_data) fields.
    client_data = result.client_data
    assert client_data is not None, "Expected client_data to be populated."
    assert client_data.cpf == "12345678900"
    assert client_data.address == "123 Main St"
    assert client_data.neighborhood == "Downtown"
    assert client_data.city == "Metropolis"
    assert client_data.state == "NY"
    assert client_data.code_address == "12345"
    # Convert the birthday string to a date object for comparison.
    assert client_data.birthday == date(1990, 1, 1)


@pytest.mark.asyncio
async def test_create_subscriber_error(db_session, mocker, user_data):
    mocker.patch(
        "backendeldery.crud.users.CRUDUser.create",
        side_effect=raise_exception,
    )

    crud_specialized_user = CRUDSpecializedUser()
    with pytest.raises(HTTPException) as excinfo:
        await crud_specialized_user.create_subscriber(
            db=db_session,
            user_data=user_data.model_dump(),
            created_by=1,
            user_ip="127.0.0.1",
        )
    assert excinfo.value.status_code == 500


# assert excinfo.value.detail == "Erro inesperado: Unexpected error"


@pytest.mark.asyncio
async def test_search_subscriber_success_by_cpf(db_session, mocker):
    # Mock User object with proper attributes
    mock_user = User(
        id=1,
        name="John Doe",
        email="john.doe@example.com",
        phone="+123456789",
        role="subscriber",
        active=True,
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

    result = await crud_specialized_user.search_subscriber(db_session, criteria)

    assert result.id == 1, f"Expected user ID 1, got {result.id}"


@pytest.mark.asyncio
async def test_search_subscriber_success_by_email(db_session, mocker):
    # Mock User object
    mock_user = User(
        id=2,
        name="Jane Doe",
        email="jane.doe@example.com",
        phone="+987654321",
        role="subscriber",
        active=True,
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

    result = await crud_specialized_user.search_subscriber(db_session, criteria)

    # Assert that the correct user is returned
    assert result.id == 2, f"Expected user ID 2, got {result.id}"


@pytest.mark.asyncio
async def test_search_subscriber_user_not_found(db_session, mocker):
    # Mock the query chain to return None for `first()`
    mock_query = mocker.Mock()
    mock_query.filter.return_value = mock_query  # Ensure `filter` returns the same mock
    mock_query.first.return_value = None  # Simulate no result found

    # Patch the session's `query` method to return the mock query
    mocker.patch.object(db_session, "query", return_value=mock_query)

    # Create CRUD instance and criteria
    crud_specialized_user = CRUDSpecializedUser()
    criteria = {"phone": "+111222333"}

    result = await crud_specialized_user.search_subscriber(db_session, criteria)

    assert result is None, "Expected no user to be found, but got a result"


@pytest.mark.asyncio
async def test_get_user_with_client_success(db_session, mocker):
    # Mock User and Client objects with proper attributes
    mock_user = User(
        id=1,
        name="John Doe",
        email="john.doe@example.com",
        phone="+123456789",
        receipt_type=1,
        role="subscriber",
        active=True,
    )
    mock_client = Client(
        user_id=1,
        cpf="12345678900",
        birthday="1990-01-01",
        address="123 Main St",
        neighborhood="Downtown",
        city="Metropolis",
        state="NY",
        code_address="12345",
    )
    mock_user.client = mock_client

    # Mock the query chain
    mock_query = mocker.Mock()
    mock_query.outerjoin.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = mock_user

    # Patch the session's `query` method
    mocker.patch.object(db_session, "query", return_value=mock_query)

    # Create CRUD instance
    crud_specialized_user = CRUDSpecializedUser()

    # Call the method
    result = await crud_specialized_user.get_user_with_client(db_session, user_id=1)

    # Assert the result
    assert result.id == 1
    assert result.name == "John Doe"
    assert result.client_data.cpf == "12345678900"


@pytest.mark.asyncio
async def test_get_user_with_client_user_not_found(db_session, mocker):
    # Mock the query chain to return None for `first()`
    mock_query = mocker.Mock()
    mock_query.outerjoin.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = None

    # Patch the session's `query` method
    mocker.patch.object(db_session, "query", return_value=mock_query)

    # Create CRUD instance
    crud_specialized_user = CRUDSpecializedUser()

    # Call the method
    result = await crud_specialized_user.get_user_with_client(db_session, user_id=1)

    # Assert the result is None
    assert result is None


@pytest.mark.asyncio
async def test_get_user_with_client_exception(db_session, mocker):
    # Mock the query chain to raise an exception
    mock_query = mocker.Mock()
    mock_query.outerjoin.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.side_effect = Exception("Unexpected error")

    # Patch the session's `query` method
    mocker.patch.object(db_session, "query", return_value=mock_query)

    # Create CRUD instance
    crud_specialized_user = CRUDSpecializedUser()

    # Call the method and assert HTTPException is raised
    with pytest.raises(HTTPException) as excinfo:
        await crud_specialized_user.get_user_with_client(db=db_session, user_id=1)
    assert excinfo.value.status_code == 500
    assert excinfo.value.detail == (
        "Error retrieving user with client data: Unexpected error"
    )


@pytest.mark.asyncio
async def test_update_user_and_client_success(db_session, user_update_data):
    crud_specialized_user = CRUDSpecializedUser()
    user = Mock()
    user.client = Mock()

    db_session.execute.return_value.scalars().one_or_none.return_value = user

    result = await crud_specialized_user.update_user_and_client(
        db_session=db_session,
        user_id=1,
        user_update=user_update_data,
        user_ip="127.0.0.1",
        updated_by=1,
    )

    assert result == {"message": "User and Client are updated!"}
    db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_and_client_user_not_found(db_session, user_update_data):
    crud_specialized_user = CRUDSpecializedUser()

    db_session.execute.return_value.scalars().one_or_none.return_value = None

    result = await crud_specialized_user.update_user_and_client(
        db_session=db_session,
        user_id=1,
        user_update=user_update_data,
        user_ip="127.0.0.1",
        updated_by=1,
    )

    assert result == {"error": "User not found"}


@pytest.mark.asyncio
async def test_update_user_and_client_no_changes(db_session, user_update_data):
    crud_specialized_user = CRUDSpecializedUser()
    user = Mock()
    user.client = Mock()

    db_session.execute.return_value.scalars().one_or_none.return_value = user

    user_update_data.email = None
    user_update_data.phone = None
    user_update_data.receipt_type = None
    user_update_data.active = None
    user_update_data.client_data = None

    result = await crud_specialized_user.update_user_and_client(
        db_session=db_session,
        user_id=1,
        user_update=user_update_data,
        user_ip="127.0.0.1",
        updated_by=1,
    )

    assert result == {"message": "Nothing to update."}


@pytest.mark.asyncio
async def test_update_user_and_client_invalid_data(db_session):
    crud_specialized_user = CRUDSpecializedUser()

    try:
        user_update_data = UserUpdate(
            email="invalid-email",
            phone="+123456789",
            active=True,
            client_data={
                "address": "456 New St",
                "neighborhood": "Uptown",
                "city": "New City",
                "state": "NC",
                "code_address": "67890",
            },
        )
    except ValidationError as exc:
        assert exc.errors()[0]["type"] == "value_error"
        return

    user = Mock()
    user.client = Mock()

    db_session.execute.return_value.scalars().one_or_none.return_value = user

    with pytest.raises(ValidationError):
        await crud_specialized_user.update_user_and_client(
            db_session=db_session,
            user_id=1,
            user_update=user_update_data,
            user_ip="127.0.0.1",
            updated_by=1,
        )


@pytest.mark.asyncio
async def test_update_user_and_client_exception(db_session, user_update_data):
    db_session.execute.side_effect = Exception("Unexpected error")
    result = await CRUDSpecializedUser.update_user_and_client(
        self=CRUDSpecializedUser,
        db_session=db_session,
        user_id=1,
        user_update=user_update_data,
        user_ip="127.0.0.1",
        updated_by=1,
    )
    assert result == {"error": "Error to update: Unexpected error"}


@pytest.mark.asyncio
async def test_update_user_and_client_no_result_found(db_session, user_update_data):
    db_session.execute.side_effect = NoResultFound("User not found")
    result = await CRUDSpecializedUser.update_user_and_client(
        self=CRUDSpecializedUser,
        db_session=db_session,
        user_id=1,
        user_update=user_update_data,
        user_ip="127.0.0.1",
        updated_by=1,
    )
    assert result == {"error": "User not found."}
