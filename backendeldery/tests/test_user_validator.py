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


def test_validate_deletion_contact_association_unauthorized(db_session, mocker):
    client = mocker.Mock(user_id=1)
    contact = mocker.Mock(id=2)
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        client,
        contact,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_deletion_contact_association(
            db_session, client_id=1, contact_id=2, x_user_id=3
        )
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "You are not authorized to delete this association"


def test_validate_deletion_contact_association_client_not_found(db_session, mocker):
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        None,  # Client not found
        mocker.Mock(id=2),  # Contact found
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_deletion_contact_association(
            db_session, client_id=1, contact_id=2, x_user_id=1
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Client not found"


def test_validate_deletion_contact_association_contact_not_found(db_session, mocker):
    client = mocker.Mock(user_id=1)
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        client,  # Client found
        None,  # Contact not found
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_deletion_contact_association(
            db_session, client_id=1, contact_id=2, x_user_id=1
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Contact not found"


def test_validate_user_raises_422_when_phone_already_exists(mocker):
    # Arrange
    mock_db = mocker.Mock()

    # Create a mock UserCreate with a phone number
    mock_user_data = mocker.Mock()
    mock_user_data.email = None  # Skip email check to focus on phone validation
    mock_user_data.phone = "1234567890"

    # Mock the database query result chain
    mock_existing_user = mocker.Mock()  # Represents an existing user

    # Setup the query chain: db.query().filter().first()
    mock_filter_result = mocker.Mock()
    mock_filter_result.first.return_value = (
        mock_existing_user  # User exists with this phone
    )

    mock_query_result = mocker.Mock()
    mock_query_result.filter.return_value = mock_filter_result

    mock_db.query.return_value = mock_query_result

    from fastapi import HTTPException
    import pytest

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        UserValidator.validate_user(mock_db, mock_user_data)

    # Verify exception details
    assert exc_info.value.status_code == 422
    assert "Phone already exists" in str(exc_info.value.detail)

    # Verify the query was called with the correct parameters
    mock_db.query.assert_called_once()
    mock_query_result.filter.assert_called_once()

    # Rejects when user exists and is already a client with different CPF


def test_rejects_when_user_exists_with_different_cpf(mocker):
    # Arrange
    mock_db = mocker.Mock()

    # Set up the user query
    user_query = mocker.Mock()
    user_query.first.return_value = mocker.Mock(id=1)  # existing user

    # Set up the join chain for Client query that should return None.
    client_join_mock = mocker.Mock()
    client_join_mock.join.return_value = client_join_mock
    client_join_mock.filter.return_value = client_join_mock
    client_join_mock.first.return_value = (
        None  # Important: return None so it doesn't trigger the "client already exists"
    )

    # Set up the query for checking client's CPF for existing user (second Client query)
    client_by_user_mock = mocker.Mock()
    existing_client = mocker.Mock()
    existing_client.cpf = "98765432100"  # Different than the CPF we're testing with
    client_by_user_mock.filter.return_value = client_by_user_mock
    client_by_user_mock.first.return_value = existing_client

    # Optionally, a third query if needed (for checking client by cpf)
    client_by_cpf_mock = mocker.Mock()
    client_by_cpf_mock.filter.return_value = client_by_cpf_mock
    client_by_cpf_mock.first.return_value = None

    user_data = {
        "email": "test@example.com",
        "phone": "1234567890",
        "client_data": {"cpf": "12345678900"},  # Different CPF than the existing client
    }

    # Use a side effect to return the proper mock for each call to db.query()
    def query_side_effect(model):
        if model == User:
            return user_query
        elif model == Client:
            if not hasattr(query_side_effect, "client_call_count"):
                query_side_effect.client_call_count = 0
            query_side_effect.client_call_count += 1
            if query_side_effect.client_call_count == 1:
                # First Client query: join query should return None.
                return client_join_mock
            elif query_side_effect.client_call_count == 2:
                # Second Client query: checking by user_id returns an existing client.
                return client_by_user_mock
            elif query_side_effect.client_call_count == 3:
                # Third Client query: checking by cpf (if reached) returns None.
                return client_by_cpf_mock
        return mocker.DEFAULT

    mock_db.query.side_effect = query_side_effect

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(mock_db, user_data)

    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "This user is already a client with another CPF"


def test_rejects_when_cpf_already_exists(mocker):
    mock_db = mocker.Mock()
    user_data = {
        "email": "test@example.com",
        "phone": "1234567890",
        "client_data": {"cpf": "12345678900"},
    }

    call_count = {"count": 0}

    def query_side_effect(model):
        call_count["count"] += 1
        # Call 1: existing_user query: model == User → return None
        if model == User and call_count["count"] == 1:
            user_query = mocker.Mock()
            user_query.filter.return_value.first.return_value = None
            return user_query
        # Call 2: join query (Client.join(...)): return chain that yields None
        elif model == Client and call_count["count"] == 2:
            chain = mocker.Mock()
            chain.join.return_value = chain
            chain.filter.return_value = chain
            chain.first.return_value = None
            return chain
        # Call 3: CPF query (Client.filter(Client.cpf == ...)): return truthy value
        elif model == Client and call_count["count"] == 3:
            chain = mocker.Mock()
            chain.filter.return_value = chain
            chain.first.return_value = mocker.Mock(cpf=user_data["client_data"]["cpf"])
            return chain
        # For any extra calls, return a default mock returning None.
        default = mocker.Mock()
        default.first.return_value = None
        return default

    mock_db.query.side_effect = query_side_effect

    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(mock_db, user_data)
    # Expect the CPF check to trigger
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "This cpf already exists"


def test_rejects_when_email_exists(mocker):
    mock_db = mocker.Mock()
    user_data = {
        "email": "existing@example.com",
        "phone": "1234567890",
        "client_data": {"cpf": "12345678900"},
    }

    call_count = {"count": 0}

    def query_side_effect(model):
        call_count["count"] += 1
        # Call 1: existing_user query
        if model == User and call_count["count"] == 1:
            user_query = mocker.Mock()
            user_query.filter.return_value.first.return_value = None
            return user_query
        # Call 2: join query for (Client, User, email, phone, cpf)
        elif model == Client and call_count["count"] == 2:
            chain = mocker.Mock()
            chain.join.return_value = chain
            chain.filter.return_value = chain
            chain.first.return_value = None
            return chain
        # Call 3: CPF query for Client
        elif model == Client and call_count["count"] == 3:
            chain = mocker.Mock()
            chain.filter.return_value = chain
            chain.first.return_value = None
            return chain
        # Call 4: Email query: simulate an existing user with that email
        elif model == User and call_count["count"] == 4:
            chain = mocker.Mock()
            chain.filter.return_value = chain
            chain.first.return_value = mocker.Mock(email=user_data["email"])
            return chain
        # Call 5: Phone query: return None
        elif model == User and call_count["count"] == 5:
            chain = mocker.Mock()
            chain.filter.return_value = chain
            chain.first.return_value = None
            return chain
        default = mocker.Mock()
        default.first.return_value = None
        return default

    mock_db.query.side_effect = query_side_effect

    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(mock_db, user_data)
    # Expect the final branch to trigger for email/phone conflict.
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "A client with this email or phone already exists"


def test_rejects_when_phone_exists_with_email_none(mocker):
    mock_db = mocker.Mock()
    user_data = {
        "email": None,  # Email is None; we go into the else branch.
        "phone": "1234567890",
        "client_data": {"cpf": "12345678900"},
    }

    call_count = {"count": 0}

    def query_side_effect(model):
        call_count["count"] += 1
        # Call 1: existing_user query
        if model == User and call_count["count"] == 1:
            user_query = mocker.Mock()
            user_query.filter.return_value.first.return_value = None
            return user_query
        # Call 2: join query for (Client, User, email, phone, cpf) that should be None
        elif model == Client and call_count["count"] == 2:
            chain = mocker.Mock()
            chain.join.return_value = chain
            chain.filter.return_value = chain
            chain.first.return_value = None
            return chain
        # Call 3: CPF query for Client
        elif model == Client and call_count["count"] == 3:
            chain = mocker.Mock()
            chain.filter.return_value = chain
            chain.first.return_value = None
            return chain
        # Since email is None, we go to the else branch, where we do:
        # db.query(Client).join(User).filter(User.phone == user_data["phone"]).first()
        elif model == Client and call_count["count"] == 4:
            chain = mocker.Mock()
            chain.join.return_value = chain
            chain.filter.return_value = chain
            # Here, return a truthy value to simulate phone conflict.
            chain.first.return_value = mocker.Mock()
            return chain
        default = mocker.Mock()
        default.first.return_value = None
        return default

    mock_db.query.side_effect = query_side_effect

    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(mock_db, user_data)
    # Expect the final branch (email is None, but phone conflict exists) to trigger.
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "A client with this email or phone already exists"


def test_validate_deletion_contact_association_not_authorized(mocker):
    # Arrange
    mock_db = mocker.Mock()
    client_id = 1
    contact_id = 10
    x_user_id = 2  # Different from client_id to trigger the 403

    # Create a fake client and contact objects
    fake_client = mocker.Mock()
    fake_client.user_id = client_id

    fake_contact = mocker.Mock()
    fake_contact.id = contact_id

    # Setup the client query: it should return a valid client object
    client_query = mocker.Mock()
    client_query.filter.return_value.one_or_none.return_value = fake_client

    # Setup the contact query: it should return a valid contact object
    contact_query = mocker.Mock()
    contact_query.filter.return_value.one_or_none.return_value = fake_contact

    # Define a side effect to differentiate between Client and User queries
    def query_side_effect(model):
        if model == Client:
            return client_query
        elif model == User:
            return contact_query
        return mocker.DEFAULT

    mock_db.query.side_effect = query_side_effect

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_deletion_contact_association(
            mock_db, client_id, contact_id, x_user_id
        )

    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "You are not authorized to delete this association"
