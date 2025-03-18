# test_user_service.py
from unittest.mock import patch, Mock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backendeldery.crud.users import crud_specialized_user, crud_assisted, crud_contact
from backendeldery.schemas import UserCreate, UserInfo, SubscriberInfo, UserUpdate
from backendeldery.services.users import UserService
from backendeldery.validators.user_validator import UserValidator


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
            "state": "NY",
        },
    )


@pytest.fixture
def user_update_data():
    return UserUpdate(
        email="john.doe@example.com",
        phone="+123456789",
        active=True,
        client_data={
            "address": "123 Main St",
            "neighborhood": "Downtown",
            "city": "Metropolis",
            "state": "NY",
            "code_address": "12345",
        },
    )


@pytest.mark.asyncio
async def test_register_client_success(db_session, mocker, user_data):
    mocker.patch.object(UserValidator, "validate_subscriber", return_value=None)
    mocker.patch.object(
        crud_specialized_user,
        "create_subscriber",
        return_value={"user": {}, "client": {}},
    )

    result = await UserService.register_client(
        db_session, user_data, created_by=1, user_ip="127.0.0.1"
    )
    assert result == {"user": {}, "client": {}}


@pytest.mark.asyncio
async def test_register_client_validation_error(db_session, mocker, user_data):
    mocker.patch.object(
        UserValidator,
        "validate_subscriber",
        side_effect=HTTPException(status_code=422, detail="Validation error"),
    )

    with pytest.raises(HTTPException):
        await UserService.register_client(
            db_session, user_data, created_by=1, user_ip="127.0.0.1"
        )


@pytest.mark.asyncio
async def test_register_client_unexpected_error(db_session, mocker, user_data):
    mocker.patch.object(UserValidator, "validate_subscriber", return_value=None)
    mocker.patch.object(
        crud_specialized_user,
        "create_subscriber",
        side_effect=Exception("Unexpected error"),
    )
    with pytest.raises(HTTPException) as excinfo:
        await UserService.register_client(
            db_session, user_data, created_by=1, user_ip="127.0.0.1"
        )
    assert excinfo.value.status_code == 500


@pytest.mark.asyncio
async def test_search_subscriber_success(db_session, mocker):
    # Mock a User object with an ID
    mock_user = mocker.Mock()
    mock_user.id = 1

    # Patch the CRUD method to return the mock_user
    mocker.patch.object(
        crud_specialized_user, "search_subscriber", return_value=mock_user
    )

    # Call the service
    result = await UserService.search_subscriber(db_session, {"cpf": "123.456.789-00"})
    assert result == 1  # Expect the ID to be returned


@pytest.mark.asyncio
async def test_search_subscriber_not_found(db_session, mocker):
    # Mock result from CRUD as None

    mocker.patch.object(crud_specialized_user, "search_subscriber", return_value=None)

    # Call the service
    result = await UserService.search_subscriber(db_session, {"cpf": "000.000.000-00"})
    assert result is None


@pytest.mark.asyncio
async def test_search_subscriber_db_error(db_session, mocker):
    # Simulate a database error
    mocker.patch.object(
        crud_specialized_user,
        "search_subscriber",
        side_effect=Exception("Database error"),
    )

    with pytest.raises(HTTPException) as excinfo:
        await UserService.search_subscriber(db_session, {"cpf": "123.456.789-00"})
    assert excinfo.value.status_code == 500
    assert "Error in UserService: Database error" in excinfo.value.detail


@pytest.mark.asyncio
async def test_get_subscriber_by_id_success(db_session, mocker):
    # Mock UserInfo and SubscriberInfo objects
    mock_user_info = UserInfo(
        id=1,
        name="John Doe",
        email="john.doe@example.com",
        phone="+123456789",
        role="subscriber",
        active=True,
        client_data=SubscriberInfo(
            cpf="12345678900",
            birthday="1990-01-01",
            address="123 Main St",
            neighborhood="Downtown",
            city="Metropolis",
            state="NY",
            code_address="12345",
        ),
    )

    # Patch the CRUD method to return the mock_user_info
    mocker.patch.object(
        crud_specialized_user, "get_user_with_client", return_value=mock_user_info
    )

    # Call the service method
    result = await UserService.get_subscriber_by_id(db_session, user_id=1)

    # Assert the result
    assert result.id == 1
    assert result.name == "John Doe"
    assert result.client_data["cpf"] == "12345678900"


@pytest.mark.asyncio
async def test_get_subscriber_by_id_user_not_found(db_session, mocker):
    # Patch the CRUD method to return None
    mocker.patch.object(
        crud_specialized_user, "get_user_with_client", return_value=None
    )

    # Call the service method
    result = await UserService.get_subscriber_by_id(db_session, user_id=1)

    # Assert the result is None
    assert result is None


@pytest.mark.asyncio
async def test_get_subscriber_by_id_exception(db_session, mocker):
    # Patch the CRUD method to raise an exception
    mocker.patch.object(
        crud_specialized_user,
        "get_user_with_client",
        side_effect=Exception("Unexpected error"),
    )

    # Call the service method and assert HTTPException is raised
    with pytest.raises(HTTPException) as excinfo:
        await UserService.get_subscriber_by_id(db_session, user_id=1)
    assert excinfo.value.status_code == 500
    assert "Error in UserService: Unexpected error" in excinfo.value.detail


@pytest.mark.asyncio
async def test_update_subscriber_success(db_session, user_update_data):
    mock_user_info = UserInfo(
        id=1,
        name="John Doe",
        email="john.doe@example.com",
        phone="+123456789",
        role="subscriber",
        active=True,
        client_data=SubscriberInfo(
            cpf="12345678900",
            birthday="1990-01-01",
            address="123 Main St",
            neighborhood="Downtown",
            city="Metropolis",
            state="NY",
            code_address="12345",
        ),
    )

    with patch.object(UserValidator, "validate_user", return_value=None):
        with patch.object(
            crud_specialized_user,
            "update_user_and_client",
            return_value={"message": "User and Client are updated!"},
        ):
            with patch.object(
                crud_specialized_user,
                "get_user_with_client",
                return_value=mock_user_info,
            ):
                result = await UserService.update_subscriber(
                    db=db_session,
                    user_id=1,
                    user_update=user_update_data,
                    user_ip="127.0.0.1",
                    updated_by=1,
                )
                assert result.id == 1


@pytest.mark.asyncio
async def test_update_subscriber_validation_error(db_session, user_update_data):
    with patch.object(
        UserValidator,
        "validate_user",
        side_effect=HTTPException(status_code=422, detail="Validation error"),
    ):
        with pytest.raises(HTTPException) as excinfo:
            await UserService.update_subscriber(
                db=db_session,
                user_id=1,
                user_update=user_update_data,
                user_ip="127.0.0.1",
                updated_by=1,
            )
        assert excinfo.value.status_code == 422
        assert excinfo.value.detail == "Validation error"


@pytest.mark.asyncio
async def test_update_subscriber_user_not_found(db_session, user_update_data):
    with patch.object(UserValidator, "validate_user", return_value=None):
        with patch.object(
            crud_specialized_user,
            "update_user_and_client",
            return_value={"error": "User not found"},
        ):
            with pytest.raises(HTTPException) as excinfo:
                await UserService.update_subscriber(
                    db=db_session,
                    user_id=1,
                    user_update=user_update_data,
                    user_ip="127.0.0.1",
                    updated_by=1,
                )
            assert excinfo.value.status_code == 400
            assert excinfo.value.detail == "User not found"


@pytest.mark.asyncio
async def test_update_subscriber_unexpected_exception(db_session, user_update_data):
    with patch.object(UserValidator, "validate_user", return_value=None):
        with patch.object(
            crud_specialized_user,
            "update_user_and_client",
            side_effect=Exception("Unexpected error"),
        ):
            with pytest.raises(HTTPException) as excinfo:
                await UserService.update_subscriber(
                    db=db_session,
                    user_id=1,
                    user_update=user_update_data,
                    user_ip="127.0.0.1",
                    updated_by=1,
                )
            assert excinfo.value.status_code == 500
            assert excinfo.value.detail == "Error on updating: Unexpected error"


@pytest.mark.asyncio
async def test_update_subscriber_value_error(db_session, user_update_data):
    with patch.object(
        UserValidator, "validate_user", side_effect=ValueError("Invalid value")
    ):
        with pytest.raises(HTTPException) as excinfo:
            await UserService.update_subscriber(
                db=db_session,
                user_id=1,
                user_update=user_update_data,
                user_ip="127.0.0.1",
                updated_by=1,
            )
        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Invalid value"


@pytest.mark.asyncio
async def test_update_subscriber_user_not_found_after_update(
    db_session, user_update_data
):
    with patch.object(UserValidator, "validate_user", return_value=None):
        with patch.object(
            crud_specialized_user,
            "update_user_and_client",
            return_value={"message": "User and Client " "are updated!"},
        ):
            with patch.object(
                crud_specialized_user, "get_user_with_client", return_value=None
            ):
                with pytest.raises(HTTPException) as excinfo:
                    await UserService.update_subscriber(
                        db=db_session,
                        user_id=1,
                        user_update=user_update_data,
                        user_ip="127.0.0.1",
                        updated_by=1,
                    )
                assert excinfo.value.status_code == 404
                assert excinfo.value.detail == "User not found"


@pytest.mark.asyncio
async def test_create_association_assisted_success(db_session, mocker):
    mocker.patch.object(
        UserValidator, "validate_association_assisted", return_value=None
    )
    mocker.patch.object(
        crud_assisted,
        "create_association",
        return_value={"message": "Association created"},
    )

    result = await UserService.create_association_assisted(
        db_session, subscriber_id=1, assisted_id=2, created_by=1, user_ip="127.0.0.1"
    )
    assert result == {"message": "Association created"}


@pytest.mark.asyncio
async def test_create_association_assisted_validation_error(db_session, mocker):
    mocker.patch.object(
        UserValidator,
        "validate_association_assisted",
        side_effect=HTTPException(status_code=422, detail="Validation error"),
    )

    with pytest.raises(HTTPException) as excinfo:
        await UserService.create_association_assisted(
            db_session,
            subscriber_id=1,
            assisted_id=2,
            created_by=1,
            user_ip="127.0.0.1",
        )
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "Validation error"


@pytest.mark.asyncio
async def test_create_association_assisted_unexpected_error(db_session, mocker):
    mocker.patch.object(
        UserValidator, "validate_association_assisted", return_value=None
    )
    mocker.patch.object(
        crud_assisted,
        "create_association",
        side_effect=Exception("Unexpected error"),
    )

    with pytest.raises(HTTPException) as excinfo:
        await UserService.create_association_assisted(
            db_session,
            subscriber_id=1,
            assisted_id=2,
            created_by=1,
            user_ip="127.0.0.1",
        )
    assert excinfo.value.status_code == 500
    assert "Unexpected error" in excinfo.value.detail


@pytest.mark.asyncio
async def test_get_assisted_clients_value_error(db_session, mocker):
    mocker.patch.object(
        crud_assisted,
        "get_assisted_clients_by_subscriber",
        side_effect=ValueError("No assisted clients found"),
    )

    with pytest.raises(HTTPException) as excinfo:
        await UserService.get_assisted_clients(db_session, subscriber_id=1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "No assisted clients found"


@pytest.mark.asyncio
async def test_register_contact_success(db_session, mocker, user_data):
    mocker.patch.object(UserValidator, "validate_contact", return_value=None)
    mocker.patch.object(
        crud_contact,
        "create_contact",
        return_value={"message": "Contact has been created"},
    )

    result = await UserService.register_contact(
        db_session, user_data=user_data, created_by=1, user_ip="127.0.0.1"
    )
    assert result == {
        "message": "Contact has been created",
        "user": {"id": result["user"]["id"]},
    }


@pytest.mark.asyncio
async def test_register_contact_validation_error(db_session, mocker, user_data):
    mocker.patch.object(
        UserValidator,
        "validate_contact",
        side_effect=HTTPException(status_code=422, detail="Validation error"),
    )
    mocker.patch.object(crud_contact, "create_contact", return_value=None)

    with pytest.raises(HTTPException) as excinfo:
        await UserService.register_contact(
            db_session, user_data=user_data, created_by=1, user_ip="127.0.0.1"
        )
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "Validation error"


@pytest.mark.asyncio
async def test_register_contact_unexpected_error(db_session, mocker, user_data):
    mocker.patch.object(UserValidator, "validate_contact", return_value=None)
    mocker.patch.object(
        crud_contact, "create_contact", side_effect=Exception("Unexpected error")
    )

    with pytest.raises(HTTPException) as excinfo:
        await UserService.register_contact(
            db_session, user_data=user_data, created_by=1, user_ip="127.0.0.1"
        )
    assert excinfo.value.status_code == 500
    assert "Unexpected error" in excinfo.value.detail


@pytest.mark.asyncio
async def test_create_contact_association_client_own_contact(db_session, mocker):
    mocker.patch.object(
        UserValidator,
        "validate_association_contact",
        side_effect=HTTPException(
            status_code=403, detail="Clients cannot be their own contacts"
        ),
    )

    with pytest.raises(HTTPException) as excinfo:
        await UserService.create_contact_association(
            db_session,
            client_id=1,
            user_contact_id=1,
            created_by=1,
            user_ip="127.0.0.1",
        )
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Clients cannot be their own contacts"


@pytest.mark.asyncio
async def test_create_contact_association_already_associated(db_session, mocker):
    mocker.patch.object(
        UserValidator,
        "validate_association_contact",
        side_effect=HTTPException(
            status_code=422, detail="This contact is already associated with the client"
        ),
    )

    with pytest.raises(HTTPException) as excinfo:
        await UserService.create_contact_association(
            db_session,
            client_id=1,
            user_contact_id=2,
            created_by=1,
            user_ip="127.0.0.1",
        )
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "This contact is already associated with the client"


@pytest.mark.asyncio
async def test_create_contact_association_unexpected_error(db_session, mocker):
    mocker.patch.object(
        UserValidator, "validate_association_contact", return_value=None
    )
    mocker.patch.object(
        crud_contact,
        "create_contact_association",
        side_effect=Exception("Unexpected error"),
    )

    with pytest.raises(HTTPException) as excinfo:
        await UserService.create_contact_association(
            db_session,
            client_id=1,
            user_contact_id=2,
            created_by=1,
            user_ip="127.0.0.1",
        )
    assert excinfo.value.status_code == 500
    assert "Unexpected error" in excinfo.value.detail


@pytest.mark.asyncio
async def test_get_client_contacts_client_not_found(db_session, mocker):
    mocker.patch.object(
        crud_contact,
        "get_contacts_by_client",
        side_effect=ValueError("Client not found"),
    )

    with pytest.raises(HTTPException) as excinfo:
        await UserService.get_client_contacts(db_session, client_id=1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Client not found"


@pytest.mark.asyncio
async def test_get_client_contacts_no_contacts(db_session, mocker):
    mocker.patch.object(crud_contact, "get_contacts_by_client", return_value=[])

    contacts = await UserService.get_client_contacts(db_session, client_id=1)
    assert contacts == []


@pytest.mark.asyncio
async def test_get_client_contacts_with_contacts(db_session, mocker):
    contact1 = mocker.Mock()
    contact2 = mocker.Mock()
    mocker.patch.object(
        crud_contact, "get_contacts_by_client", return_value=[contact1, contact2]
    )

    contacts = await UserService.get_client_contacts(db_session, client_id=1)
    assert contacts == [contact1, contact2]


@pytest.mark.asyncio
async def test_get_clients_of_contact_contact_not_found(db_session, mocker):
    mocker.patch.object(
        crud_contact, "get_clients_by_contact", side_effect=ValueError("User not found")
    )

    with pytest.raises(HTTPException) as excinfo:
        await UserService.get_clients_of_contact(db_session, contact_id=1)
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "User not found"


@pytest.mark.asyncio
async def test_get_clients_of_contact_no_clients(db_session, mocker):
    mocker.patch.object(crud_contact, "get_clients_by_contact", return_value=[])

    clients = await UserService.get_clients_of_contact(db_session, contact_id=1)
    assert clients == []


@pytest.mark.asyncio
async def test_get_clients_of_contact_with_clients(db_session, mocker):
    client1 = mocker.Mock()
    client2 = mocker.Mock()
    mocker.patch.object(
        crud_contact, "get_clients_by_contact", return_value=[client1, client2]
    )

    clients = await UserService.get_clients_of_contact(db_session, contact_id=1)
    assert clients == [client1, client2]


@pytest.mark.asyncio
async def test_get_clients_of_contact_contact_is_also_client(db_session, mocker):
    client1 = mocker.Mock(user_id=1)  # This should be filtered out
    client2 = mocker.Mock(user_id=2)
    mocker.patch.object(
        crud_contact, "get_clients_by_contact", return_value=[client1, client2]
    )

    clients = await UserService.get_clients_of_contact(db_session, contact_id=1)
    assert clients == [client2]


@pytest.mark.asyncio
async def test_delete_contact_relation_exists_and_orphan(db_session, mocker):
    mocker.patch.object(crud_contact, "delete_contact_association", return_value=1)
    mocker.patch.object(crud_contact, "delete_contact_if_orphan", return_value=Mock())

    result = await UserService.delete_contact_relation(
        db_session, client_id=1, contact_id=2, user_ip="127.0.0.1", x_user_id=1
    )
    assert result == {"message": "Contact association deleted successfully"}


@pytest.mark.asyncio
async def test_delete_contact_relation_exists_and_not_orphan(db_session, mocker):
    mocker.patch.object(crud_contact, "delete_contact_association", return_value=1)
    mocker.patch.object(crud_contact, "delete_contact_if_orphan", return_value=None)

    result = await UserService.delete_contact_relation(
        db_session, client_id=1, contact_id=2, user_ip="127.0.0.1", x_user_id=1
    )
    assert result == {"message": "Contact association deleted successfully"}


@pytest.mark.asyncio
async def test_delete_contact_relation_not_exists(db_session, mocker):
    mocker.patch.object(crud_contact, "delete_contact_association", return_value=0)

    with pytest.raises(HTTPException) as excinfo:
        await UserService.delete_contact_relation(
            db_session, client_id=1, contact_id=2, user_ip="127.0.0.1", x_user_id=1
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Association not found"


@pytest.mark.asyncio
async def test_delete_contact_relation_success(db_session, mocker):
    mocker.patch.object(
        UserValidator, "validate_deletion_contact_association", return_value=None
    )
    mocker.patch.object(crud_contact, "delete_contact_relation", return_value=None)

    result = await UserService.delete_contact_relation(
        db_session, client_id=1, contact_id=2, user_ip="127.0.0.1", x_user_id=1
    )
    assert result == {"message": "Contact association deleted successfully"}


@pytest.mark.asyncio
async def test_delete_contact_relation_not_found(db_session, mocker):
    mocker.patch.object(
        UserValidator, "validate_deletion_contact_association", return_value=None
    )
    mocker.patch.object(
        crud_contact,
        "delete_contact_relation",
        side_effect=HTTPException(status_code=404, detail="Association not found"),
    )

    with pytest.raises(HTTPException) as excinfo:
        await UserService.delete_contact_relation(
            db_session, client_id=1, contact_id=2, user_ip="127.0.0.1", x_user_id=1
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Association not found"


@pytest.mark.asyncio
async def test_delete_contact_relation_unauthorized(db_session, mocker):
    mocker.patch.object(
        UserValidator,
        "validate_deletion_contact_association",
        side_effect=HTTPException(
            status_code=403, detail="You are not authorized to delete this association"
        ),
    )

    with pytest.raises(HTTPException) as excinfo:
        await UserService.delete_contact_relation(
            db_session, client_id=1, contact_id=2, user_ip="127.0.0.1", x_user_id=3
        )
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "You are not authorized to delete this association"


@pytest.mark.asyncio
async def test_delete_contact_relation_client_not_found(db_session, mocker):
    mocker.patch.object(
        UserValidator,
        "validate_deletion_contact_association",
        side_effect=HTTPException(status_code=404, detail="Client not found"),
    )

    with pytest.raises(HTTPException) as excinfo:
        await UserService.delete_contact_relation(
            db_session, client_id=1, contact_id=2, user_ip="127.0.0.1", x_user_id=1
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Client not found"


@pytest.mark.asyncio
async def test_create_contact_association_success(db_session, mocker):
    mocker.patch.object(
        UserValidator, "validate_association_contact", return_value=None
    )
    mocker.patch.object(
        crud_contact,
        "create_contact_association",
        return_value={"message": "Association created"},
    )

    result = await UserService.create_contact_association(
        db_session, client_id=1, user_contact_id=2, created_by=1, user_ip="127.0.0.1"
    )
    assert result == {"message": "Association created"}
