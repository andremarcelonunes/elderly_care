# test_user_validator.py
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backendeldery.models import User, Client
from backendeldery.schemas import UserCreate
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
    db_session.query.return_value.filter.return_value.first.side_effect = [
        None,
        User(),
    ]  # Email None, Phone exists
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
        (Client.cpf == user_data.client_data.cpf)  # Use dot notation
        & (User.email == user_data.email)
        & (User.phone == user_data.phone)
    ).first.return_value = Client()
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(db_session, user_data.model_dump())
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "The client already exists"


def test_validate_subscriber_user_exists_with_different_cpf(db_session, user_data):
    user_data.client_data.cpf = "123.456.789-40"
    db_session.query(Client).join(User).filter(
        (Client.cpf == "987.654.321-00")  # Existing client CPF
        & (User.email == user_data.email)
        & (User.phone == user_data.phone)
    ).first.return_value = Client(cpf="987.654.321-00")

    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(db_session, user_data.model_dump())
    assert excinfo.value.status_code == 422


def test_validate_subscriber_client_with_email_exists(db_session, user_data):
    db_session.query(Client).join(User).filter(
        User.phone == user_data.email
    ).first.return_value = Client()
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(db_session, user_data.model_dump())
    assert excinfo.value.status_code == 422


def test_validate_subscriber_client_with_phone_exists(db_session, user_data):
    db_session.query(Client).join(User).filter(
        User.phone == user_data.phone
    ).first.return_value = Client()
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(db_session, user_data.model_dump())
    assert excinfo.value.status_code == 422


def test_validate_association_assisted_subscriber_not_found(db_session):
    db_session.query.return_value.filter.return_value.one_or_none.return_value = None
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_assisted(
            db_session, subscriber_id=1, assisted_id=2
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Subscriber not found"


def test_validate_association_assisted_subscriber_wrong_role(db_session, mocker):
    subscriber = mocker.Mock()
    subscriber.role = "user"
    db_session.query.return_value.filter.return_value.one_or_none.return_value = (
        subscriber
    )
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_assisted(
            db_session, subscriber_id=1, assisted_id=2
        )
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "User does not have the 'subscriber' role"


def test_validate_association_assisted_assisted_not_found(db_session, mocker):
    subscriber = mocker.Mock()
    subscriber.role = "subscriber"
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        subscriber,
        None,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_assisted(
            db_session, subscriber_id=1, assisted_id=2
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Assisted not found"


def test_validate_association_assisted_another_subscriber_association(
    db_session, mocker
):
    subscriber = mocker.Mock()
    subscriber.role = "subscriber"
    assisted = mocker.Mock()
    assisted.role = "subscriber"
    assisted.id = 2
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        subscriber,
        assisted,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_assisted(
            db_session, subscriber_id=1, assisted_id=2
        )
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Another subscriber cannot be associated"


def test_validate_association_assisted_already_associated_with_another_subscriber(
    db_session, mocker
):
    subscriber = mocker.Mock()
    subscriber.role = "subscriber"
    assisted = mocker.Mock()
    assisted.role = "user"
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        subscriber,
        assisted,
    ]
    db_session.query.return_value.filter.return_value.first.side_effect = [
        True,
        None,
        None,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_assisted(
            db_session, subscriber_id=1, assisted_id=2
        )
    assert excinfo.value.status_code == 422
    assert (
        excinfo.value.detail
        == "Assisted  has been already associated with another subscriber"
    )


def test_validate_association_assisted_already_associated_with_same_subscriber(
    db_session, mocker
):
    subscriber = mocker.Mock()
    subscriber.role = "subscriber"
    assisted = mocker.Mock()
    assisted.role = "user"
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        subscriber,
        assisted,
    ]
    db_session.query.return_value.filter.return_value.first.side_effect = [
        None,
        True,
        None,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_assisted(
            db_session, subscriber_id=1, assisted_id=2
        )
    assert excinfo.value.status_code == 422
    assert (
        excinfo.value.detail
        == "Assisted  has been  already associated with this subscriber"
    )


def test_validate_association_assisted_association_already_exists(db_session, mocker):
    subscriber = mocker.Mock()
    subscriber.role = "subscriber"
    assisted = mocker.Mock()
    assisted.role = "user"
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        subscriber,
        assisted,
    ]
    db_session.query.return_value.filter.return_value.first.side_effect = [
        None,
        None,
        True,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_assisted(
            db_session, subscriber_id=1, assisted_id=2
        )
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "Association already exists"


def test_validate_association_assisted_success(db_session, mocker):
    subscriber = mocker.Mock()
    subscriber.role = "subscriber"
    assisted = mocker.Mock()
    assisted.role = "user"
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        subscriber,
        assisted,
    ]
    db_session.query.return_value.filter.return_value.first.side_effect = [
        None,
        None,
        None,
    ]
    UserValidator.validate_association_assisted(
        db_session, subscriber_id=1, assisted_id=2
    )
    # No exception should be raised


def test_validate_association_contact_client_not_found(db_session):
    db_session.query.return_value.filter.return_value.one_or_none.return_value = None
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_contact(
            db_session, client_id=1, contact_id=2
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Client not found"


def test_validate_association_contact_contact_not_found(db_session, mocker):
    client = mocker.Mock()
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        client,
        None,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_contact(
            db_session, client_id=1, contact_id=2
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Contact not found"


def test_validate_association_contact_client_own_contact(db_session, mocker):
    client = mocker.Mock(user_id=1)
    contact = mocker.Mock(id=1)
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        client,
        contact,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_contact(
            db_session, client_id=1, contact_id=1
        )
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Clients cannot be their own contacts"


def test_validate_association_contact_already_associated(db_session, mocker):
    client = mocker.Mock(user_id=1)
    contact = mocker.Mock(id=2)
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        client,
        contact,
    ]
    db_session.query.return_value.filter.return_value.first.return_value = True
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_contact(
            db_session, client_id=1, contact_id=2
        )
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "This contact is already associated with the client"


def test_validate_association_contact_success(db_session, mocker):
    client = mocker.Mock(user_id=1)
    contact = mocker.Mock(id=2)
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        client,
        contact,
    ]
    db_session.query.return_value.filter.return_value.first.return_value = None
    UserValidator.validate_association_contact(db_session, client_id=1, contact_id=2)
    # No exception should be raised
