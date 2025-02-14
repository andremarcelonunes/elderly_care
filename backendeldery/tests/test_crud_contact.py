from http.client import HTTPException

import pytest
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch
from backendeldery.crud.users import CRUDContact, CRUDUser
from backendeldery.models import User
from backendeldery.crud import crud_user
from backendeldery.services.users import UserService


@pytest.fixture
def db_session():
    return Mock(spec=Session)


@pytest.fixture
def user_data():
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+123456789",
        "role": "contact",
        "password": "password123",
    }


@pytest.fixture
def crud_user():
    return Mock(spec=CRUDUser)


@pytest.fixture
def crud_contact(crud_user):
    return CRUDContact(user_crud=crud_user)


@pytest.mark.asyncio
async def test_create_contact_success(db_session, crud_contact, user_data, mocker):
    # Create a mock user with id 1
    user = Mock(spec=User)
    user.id = 1

    # Patch the module-level async function that create_contact actually calls.
    mock_create = mocker.patch("backendeldery.crud.users.crud_user.create", return_value=user)

    result = await crud_contact.create_contact(
        db=db_session, user_data=user_data, created_by=1, user_ip="127.0.0.1"
    )

    assert result.id == 1
    mock_create.assert_called_once_with(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )
    db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_contact_user_not_found(db_session, crud_contact, user_data, mocker):
    # Define an async function that returns None.
    async def return_none(*args, **kwargs):
        return None

    # Patch the module-level crud_user.create since that's what's used in create_contact.
    mock_create = mocker.patch("backendeldery.crud.users.crud_user.create", side_effect=return_none)

    with pytest.raises(ValueError) as excinfo:
        await crud_contact.create_contact(
            db=db_session, user_data=user_data, created_by=1, user_ip="127.0.0.1"
        )

    assert str(excinfo.value) == "User not found"
    mock_create.assert_called_once_with(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )
    db_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_create_contact_runtime_error(db_session, crud_contact, user_data, mocker):
    # Define an async function that always raises the exception.
    async def raise_exception(*args, **kwargs):
        raise Exception("Unexpected error")

    # Patch the async create method of crud_user and capture the mock.
    mock_create = mocker.patch("backendeldery.crud.users.crud_user.create", side_effect=raise_exception)

    with pytest.raises(RuntimeError) as excinfo:
        await crud_contact.create_contact(
            db=db_session, user_data=user_data, created_by=1, user_ip="127.0.0.1"
        )

    assert str(excinfo.value) == "Error creating contact: Unexpected error"
    # Assert that the patched function was called once.
    mock_create.assert_called_once_with(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )
    db_session.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_create_contact_association_success(db_session, crud_contact):
    result = await crud_contact.create_contact_association(
        db=db_session, client_id=1, user_contact_id=2, created_by=1, user_ip="127.0.0.1"
    )

    assert result["message"] == "Association created successfully"
    db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_contact_association_runtime_error(db_session, crud_contact):
    with patch.object(
            crud_contact.model, "insert", side_effect=Exception("Unexpected error")
    ):
        with pytest.raises(RuntimeError) as excinfo:
            await crud_contact.create_contact_association(
                db=db_session,
                client_id=1,
                user_contact_id=2,
                created_by=1,
                user_ip="127.0.0.1",
            )

        assert (
                str(excinfo.value)
                == "Error creating association between contact and client: Unexpected error"
        )
        db_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_get_contacts_by_client_client_not_found(db_session, mocker, crud_contact):
    db_session.query.return_value.filter.return_value.one_or_none.return_value = None
    with pytest.raises(ValueError) as excinfo:
       await crud_contact.get_contacts_by_client(db_session, client_id=1)
    assert str(excinfo.value) == "Client not found"


@pytest.mark.asyncio
async def test_get_contacts_by_client_no_contacts(db_session, mocker, crud_contact):
    client = mocker.Mock()
    client.contacts = []
    db_session.query.return_value.filter.return_value.one_or_none.return_value = client
    contacts = await crud_contact.get_contacts_by_client(db_session, client_id=1)
    assert contacts == []


@pytest.mark.asyncio
async def test_get_contacts_by_client_with_contacts(db_session, mocker, crud_contact):
    client = mocker.Mock()
    contact1 = mocker.Mock()
    contact2 = mocker.Mock()
    client.contacts = [contact1, contact2]
    db_session.query.return_value.filter.return_value.one_or_none.return_value = client
    contacts = await crud_contact.get_contacts_by_client(db_session, client_id=1)
    assert contacts == [contact1, contact2]


@pytest.mark.asyncio
async def test_get_clients_by_contact_contact_not_found(db_session, mocker, crud_contact):
    db_session.query.return_value.filter.return_value.one_or_none.return_value = None
    with pytest.raises(ValueError) as excinfo:
        await crud_contact.get_clients_by_contact(db_session, contact_id=1)
    assert str(excinfo.value) == "User not found"


@pytest.mark.asyncio
async def test_get_clients_by_contact_no_clients(db_session, mocker, crud_contact):
    user = mocker.Mock()
    user.clients = []
    db_session.query.return_value.filter.return_value.one_or_none.return_value = user
    clients = await crud_contact.get_clients_by_contact(db_session, contact_id=1)
    assert clients == []


@pytest.mark.asyncio
async def test_get_clients_by_contact_with_clients(db_session, mocker, crud_contact):
    user = mocker.Mock()
    client1 = mocker.Mock(user_id=2)
    client2 = mocker.Mock(user_id=3)
    user.clients = [client1, client2]
    db_session.query.return_value.filter.return_value.one_or_none.return_value = user
    clients = await crud_contact.get_clients_by_contact(db_session, contact_id=1)
    assert clients == [client1, client2]


@pytest.mark.asyncio
async def test_get_clients_by_contact_contact_is_also_client(
        db_session, mocker, crud_contact
):
    user = mocker.Mock()
    client1 = mocker.Mock(user_id=1)  # This should be filtered out
    client2 = mocker.Mock(user_id=2)
    user.clients = [client1, client2]
    db_session.query.return_value.filter.return_value.one_or_none.return_value = user
    clients = await crud_contact.get_clients_by_contact(db_session, contact_id=1)
    assert clients == [client2]


@pytest.mark.asyncio
async def test_delete_contact_association_exists(db_session, crud_contact):
    db_session.query.return_value.filter.return_value.delete.return_value = 1
    deleted_count = await crud_contact.delete_contact_association(db_session, client_id=1, contact_id=2)
    assert deleted_count == 1
    db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_contact_association_not_exists(db_session, crud_contact):
    db_session.query.return_value.filter.return_value.delete.return_value = 0
    deleted_count = await crud_contact.delete_contact_association(db_session, client_id=1, contact_id=2)
    assert deleted_count == 0
    db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_contact_if_orphan_is_orphan(db_session, crud_contact):
    from backendeldery.models import User, client_contact_association
    from unittest.mock import MagicMock

    # Create a mock contact that we expect to be returned.
    contact = MagicMock(spec=User)

    # Define a side effect function for db_session.query.
    def query_side_effect(model):
        if model == client_contact_association:
            # For association queries, we want count() to return 0.
            mock_assoc_query = MagicMock()
            mock_assoc_query.filter.return_value.count.return_value = 0
            return mock_assoc_query
        elif model == User:
            # For User queries, we want one_or_none() to return our contact.
            mock_user_query = MagicMock()
            mock_user_query.filter.return_value.one_or_none.return_value = contact
            return mock_user_query
        else:
            return MagicMock()

    # Set the side effect so that the correct mock is returned based on the model.
    db_session.query.side_effect = query_side_effect

    deleted_contact = await crud_contact.delete_contact_if_orphan(db_session, contact_id=2)
    assert deleted_contact == contact
    db_session.delete.assert_called_once_with(contact)
    db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_delete_contact_if_orphan_not_orphan(db_session, crud_contact):
    db_session.query.return_value.filter.return_value.count.return_value = 1
    deleted_contact = await crud_contact.delete_contact_if_orphan(db_session, contact_id=2)
    assert deleted_contact is None
    db_session.delete.assert_not_called()
    db_session.commit.assert_not_called()

