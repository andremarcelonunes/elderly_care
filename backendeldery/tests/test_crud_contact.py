import pytest
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch
from backendeldery.crud.users import CRUDContact, CRUDUser
from backendeldery.models import User


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


def test_create_contact_success(db_session, crud_contact, user_data):
    user = Mock(spec=User)
    user.id = 1
    crud_contact.user_crud.create.return_value = user

    result = crud_contact.create_contact(
        db=db_session,
        user_data=user_data,
        created_by=1,
        user_ip="127.0.0.1"
    )

    assert result == {"message": "Contact has been created"}
    crud_contact.user_crud.create.assert_called_once_with(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )
    db_session.commit.assert_called_once()


def test_create_contact_user_not_found(db_session, crud_contact, user_data):
    crud_contact.user_crud.create.return_value = None

    with pytest.raises(ValueError) as excinfo:
        crud_contact.create_contact(
            db=db_session,
            user_data=user_data,
            created_by=1,
            user_ip="127.0.0.1"
        )

    assert str(excinfo.value) == "User not found"
    crud_contact.user_crud.create.assert_called_once_with(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )
    db_session.rollback.assert_called_once()


def test_create_contact_runtime_error(db_session, crud_contact, user_data):
    crud_contact.user_crud.create.side_effect = Exception("Unexpected error")

    with pytest.raises(RuntimeError) as excinfo:
        crud_contact.create_contact(
            db=db_session,
            user_data=user_data,
            created_by=1,
            user_ip="127.0.0.1"
        )

    assert str(excinfo.value) == "Error creating contact: Unexpected error"
    crud_contact.user_crud.create.assert_called_once_with(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )
    db_session.rollback.assert_called_once()


def test_create_contact_association_success(db_session, crud_contact):
    result = crud_contact.create_contact_association(
        db=db_session,
        client_id=1,
        user_contact_id=2,
        created_by=1,
        user_ip="127.0.0.1"
    )

    assert result == {"message": "Contact has been associated"}
    db_session.commit.assert_called_once()


def test_create_contact_association_runtime_error(db_session, crud_contact):
    with patch.object(crud_contact.model, 'insert', side_effect=Exception("Unexpected error")):
        with pytest.raises(RuntimeError) as excinfo:
            crud_contact.create_contact_association(
                db=db_session,
                client_id=1,
                user_contact_id=2,
                created_by=1,
                user_ip="127.0.0.1"
            )

        assert str(excinfo.value) == "Error creating association between contact and client: Unexpected error"
        db_session.rollback.assert_called_once()
