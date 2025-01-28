# test_user_validator.py
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backendeldery.models import User, Client
from backendeldery.schemas import UserCreate, SubscriberCreate
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


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mock_database_url")
    monkeypatch.setenv("MONGO_URI", "mock_mongo_uri")
    monkeypatch.setenv("MONGO_DB", "mock_mongo_db")


def test_validate_user_email_exists(db_session, user_data):
    db_session.query.return_value.filter.return_value.first.return_value = User()
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_user(db_session, user_data)
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "Email already exists"


def test_validate_user_phone_exists(db_session, user_data):
    db_session.query.return_value.filter.return_value.first.side_effect = [None, User()]  # Email None, Phone exists
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_user(db_session, user_data)
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "Phone already exists"


def test_validate_client_exists(db_session, user_data):
    user = User(id=1)
    db_session.query.return_value.filter.return_value.first.return_value = Client()
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_client(db_session, user, user_data.client_data)
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "Client already exists"


def test_validate_subscriber_missing_client_data(db_session, user_data):
    user_data.client_data = None
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(db_session, user_data.model_dump())
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "You must inform client data"


def test_validate_subscriber_exists(db_session, user_data):
    db_session.query(Client).join(User).filter(
        (Client.cpf == user_data.client_data.cpf) &  # Use dot notation
        (User.email == user_data.email) &
        (User.phone == user_data.phone)
    ).first.return_value = Client()
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(db_session, user_data.model_dump())
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "The subscriber already exists"


def test_validate_subscriber_user_exists_with_different_cpf(db_session, user_data):
    user_data.client_data.cpf = "123.456.789-40"
    db_session.query(Client).join(User).filter(
        (Client.cpf == "987.654.321-00") &  # Existing client CPF
        (User.email == user_data.email) &
        (User.phone == user_data.phone)
    ).first.return_value = Client(cpf="987.654.321-00")

    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(db_session, user_data.model_dump())
    assert excinfo.value.status_code == 422


def test_validate_subscriber_client_with_email_exists(db_session, user_data):
    db_session.query(Client).join(User).filter(User.phone == user_data.email).first.return_value = Client()
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(db_session, user_data.model_dump())
    assert excinfo.value.status_code == 422


def test_validate_subscriber_client_with_phone_exists(db_session, user_data):
    db_session.query(Client).join(User).filter(User.phone == user_data.phone).first.return_value = Client()
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(db_session, user_data.model_dump())
    assert excinfo.value.status_code == 422
