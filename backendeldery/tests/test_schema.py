import pytest
from pydantic import BaseModel, ValidationError
from backendeldery.schemas import UserUpdate, ClientUpdate, SubscriberCreate, UserCreate


def test_check_extra_fields_user():
    # Test case with no extra fields
    valid_data = {"email": "test@example.com", "phone": "+123456789", "active": True}
    try:
        user_update = UserUpdate(**valid_data)
        assert user_update.email == "test@example.com"
        assert user_update.phone == "+123456789"
        assert user_update.active is True
    except ValidationError:
        pytest.fail("Unexpected ValidationError raised with valid data")

    # Test case with extra fields
    invalid_data = {
        "email": "test@example.com",
        "phone": "+123456789",
        "active": True,
        "role": "Contact",
    }
    with pytest.raises(ValidationError) as exc_info:
        UserUpdate(**invalid_data)
    assert "this change is not authorized" in str(exc_info.value)


def test_check_extra_fields_client():
    # Test case with no extra fields
    valid_data = {
        "address": "123 Main St",
        "neighborhood": "Downtown",
        "city": "Metropolis",
        "state": "NY",
        "code_address": "12345",
    }
    try:
        client_update = ClientUpdate(**valid_data)
        assert client_update.address == "123 Main St"
        assert client_update.neighborhood == "Downtown"
        assert client_update.city == "Metropolis"
        assert client_update.state == "NY"
        assert client_update.code_address == "12345"
    except ValidationError:
        pytest.fail("Unexpected ValidationError raised with valid data")

    # Test case with extra fields
    invalid_data = {
        "address": "123 Main St",
        "neighborhood": "Downtown",
        "city": "Metropolis",
        "state": "NY",
        "code_address": "12345",
        "extra_field": "not allowed",
    }
    with pytest.raises(ValidationError) as exc_info:
        ClientUpdate(**invalid_data)
    assert "this change is not authorized" in str(exc_info.value)


def test_user_create_subscriber_missing_client_data():
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            name="John Doe",
            role="subscriber",
            phone="+123456789",
            email="john.doe@example.com",
            password="password123"
        )
    assert "client_data is required when role is 'subscriber'" in str(exc_info.value)


def test_user_create_subscriber_missing_email():
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            name="John Doe",
            role="subscriber",
            phone="+123456789",
            client_data=SubscriberCreate(
                cpf="12345678900",
                birthday="2000-01-01"
            ),
            password="password123"
        )
    assert "email is required when role is 'subscriber'" in str(exc_info.value)


def test_user_create_subscriber_missing_password():
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            name="John Doe",
            role="subscriber",
            phone="+123456789",
            email="john.doe@example.com",
            client_data=SubscriberCreate(
                cpf="12345678900",
                birthday="2000-01-01"
            )
        )
    assert "password is required when role is 'subscriber'" in str(exc_info.value)


def test_user_create_invalid_phone():
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(
            name="John Doe",
            role="subscriber",
            phone="invalid_phone",
            email="john.doe@example.com",
            password="password123",
            client_data=SubscriberCreate(
                cpf="12345678900",
                birthday="2000-01-01"
            )
        )
    # Adjusted the expected substring to match the actual error message.
    assert "String should match pattern" in str(exc_info.value)