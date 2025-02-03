# test_user_service.py
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backendeldery.crud.users import crud_specialized_user
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
            "state": "NY"
        }
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
            "code_address": "12345"
        }
    )


@pytest.mark.asyncio
async def test_register_client_success(db_session, mocker, user_data):
    mocker.patch.object(UserValidator, 'validate_subscriber',
                        return_value=None)
    mocker.patch.object(crud_specialized_user, 'create_subscriber',
                        return_value={"user": {}, "client": {}})

    result = await UserService.register_client(db_session,
                                               user_data,
                                               created_by=1,
                                               user_ip="127.0.0.1")
    assert result == {"user": {}, "client": {}}


@pytest.mark.asyncio
async def test_register_client_validation_error(db_session, mocker, user_data):
    mocker.patch.object(
        UserValidator,
        'validate_subscriber',
        side_effect=HTTPException(status_code=422, detail="Validation error")
    )

    with pytest.raises(HTTPException):
        await UserService.register_client(db_session,
                                          user_data,
                                          created_by=1,
                                          user_ip="127.0.0.1")


@pytest.mark.asyncio
async def test_register_client_unexpected_error(db_session, mocker, user_data):
    mocker.patch.object(UserValidator,
                        'validate_subscriber', return_value=None)
    mocker.patch.object(crud_specialized_user,
                        'create_subscriber',
                        side_effect=Exception("Unexpected error"))
    with pytest.raises(HTTPException) as excinfo:
        await UserService.register_client(db_session,
                                          user_data,
                                          created_by=1,
                                          user_ip="127.0.0.1")
    assert excinfo.value.status_code == 500


@pytest.mark.asyncio
async def test_search_subscriber_success(db_session, mocker):
    # Mock a User object with an ID
    mock_user = mocker.Mock()
    mock_user.id = 1

    # Patch the CRUD method to return the mock_user
    mocker.patch.object(crud_specialized_user,
                        'search_subscriber',
                        return_value=mock_user)

    # Call the service
    result = await UserService.search_subscriber(db_session,
                                                 {"cpf": "123.456.789-00"})
    assert result == 1  # Expect the ID to be returned


@pytest.mark.asyncio
async def test_search_subscriber_not_found(db_session, mocker):
    # Mock result from CRUD as None

    mocker.patch.object(crud_specialized_user,
                        'search_subscriber', return_value=None)

    # Call the service
    result = await UserService.search_subscriber(db_session,
                                                 {"cpf": "000.000.000-00"})
    assert result is None


@pytest.mark.asyncio
async def test_search_subscriber_db_error(db_session, mocker):
    # Simulate a database error
    mocker.patch.object(crud_specialized_user,
                        'search_subscriber',
                        side_effect=Exception("Database error"))

    with pytest.raises(HTTPException) as excinfo:
        await UserService.search_subscriber(db_session,
                                            {"cpf": "123.456.789-00"})
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
            code_address="12345"
        )
    )

    # Patch the CRUD method to return the mock_user_info
    mocker.patch.object(crud_specialized_user,
                        'get_user_with_client',
                        return_value=mock_user_info)

    # Call the service method
    result = await UserService.get_subscriber_by_id(db_session, user_id=1)

    # Assert the result
    assert result.id == 1
    assert result.name == "John Doe"
    assert result.client_data.cpf == "12345678900"


@pytest.mark.asyncio
async def test_get_subscriber_by_id_user_not_found(db_session, mocker):
    # Patch the CRUD method to return None
    mocker.patch.object(crud_specialized_user,
                        'get_user_with_client',
                        return_value=None)

    # Call the service method
    result = await UserService.get_subscriber_by_id(db_session, user_id=1)

    # Assert the result is None
    assert result is None


@pytest.mark.asyncio
async def test_get_subscriber_by_id_exception(db_session, mocker):
    # Patch the CRUD method to raise an exception
    mocker.patch.object(crud_specialized_user, 'get_user_with_client',
                        side_effect=Exception("Unexpected error"))

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
            code_address="12345"
        )
    )

    with patch.object(UserValidator, 'validate_user', return_value=None):
        with patch.object(crud_specialized_user,
                          'update_user_and_client',
                          return_value={"message": "User and Client are updated!"}):
            with patch.object(crud_specialized_user,
                              'get_user_with_client',
                              return_value=mock_user_info):
                result = await UserService.update_subscriber(
                    db=db_session,
                    user_id=1,
                    user_update=user_update_data,
                    user_ip="127.0.0.1",
                    updated_by=1
                )
                assert result.id == 1


@pytest.mark.asyncio
async def test_update_subscriber_validation_error(db_session, user_update_data):
    with patch.object(UserValidator, 'validate_user',
                      side_effect=HTTPException(status_code=422, detail="Validation error")):
        with pytest.raises(HTTPException) as excinfo:
            await UserService.update_subscriber(
                db=db_session,
                user_id=1,
                user_update=user_update_data,
                user_ip="127.0.0.1",
                updated_by=1
            )
        assert excinfo.value.status_code == 422
        assert excinfo.value.detail == "Validation error"


@pytest.mark.asyncio
async def test_update_subscriber_user_not_found(db_session, user_update_data):
    with patch.object(UserValidator, 'validate_user', return_value=None):
        with patch.object(crud_specialized_user, 'update_user_and_client', return_value={"error": "User not found"}):
            with pytest.raises(HTTPException) as excinfo:
                await UserService.update_subscriber(
                    db=db_session,
                    user_id=1,
                    user_update=user_update_data,
                    user_ip="127.0.0.1",
                    updated_by=1
                )
            assert excinfo.value.status_code == 400
            assert excinfo.value.detail == "User not found"


@pytest.mark.asyncio
async def test_update_subscriber_unexpected_exception(db_session, user_update_data):
    with patch.object(UserValidator, 'validate_user', return_value=None):
        with patch.object(crud_specialized_user, 'update_user_and_client', side_effect=Exception("Unexpected error")):
            with pytest.raises(HTTPException) as excinfo:
                await UserService.update_subscriber(
                    db=db_session,
                    user_id=1,
                    user_update=user_update_data,
                    user_ip="127.0.0.1",
                    updated_by=1
                )
            assert excinfo.value.status_code == 500
            assert excinfo.value.detail == "Error on updating: Unexpected error"


@pytest.mark.asyncio
async def test_update_subscriber_value_error(db_session, user_update_data):
    with patch.object(UserValidator, 'validate_user', side_effect=ValueError("Invalid value")):
        with pytest.raises(HTTPException) as excinfo:
            await UserService.update_subscriber(
                db=db_session,
                user_id=1,
                user_update=user_update_data,
                user_ip="127.0.0.1",
                updated_by=1
            )
        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Invalid value"


@pytest.mark.asyncio
async def test_update_subscriber_user_not_found_after_update(db_session, user_update_data):
    with patch.object(UserValidator, 'validate_user', return_value=None):
        with patch.object(crud_specialized_user, 'update_user_and_client', return_value={"message": "User and Client are updated!"}):
            with patch.object(crud_specialized_user, 'get_user_with_client', return_value=None):
                with pytest.raises(HTTPException) as excinfo:
                    await UserService.update_subscriber(
                        db=db_session,
                        user_id=1,
                        user_update=user_update_data,
                        user_ip="127.0.0.1",
                        updated_by=1
                    )
                assert excinfo.value.status_code == 404
                assert excinfo.value.detail == "User not found"