# test_utils.py
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from backendeldery.database import db_instance
from backendeldery.models import User
from backendeldery.utils import hash_password, obj_to_dict, verify_password, get_db_aync


def test_hash_password():
    password = "Strong@123"
    hashed_password = hash_password(password)
    assert hashed_password != password


def test_obj_to_dict():
    user = User(id=1, email="test@example.com")
    result = obj_to_dict(user)
    assert result["id"] == 1
    assert result["email"] == "test@example.com"


def test_verify_password_success():
    plain_password = "Strong@123"
    hashed_password = hash_password(plain_password)
    assert verify_password(plain_password, hashed_password) is True


def test_verify_password_failure():
    plain_password = "Strong@123"
    hashed_password = hash_password("DifferentPassword")
    assert verify_password(plain_password, hashed_password) is False


def test_verify_password_none_plain():
    hashed_password = hash_password("Strong@123")
    assert verify_password(None, hashed_password) is False


def test_verify_password_none_hashed():
    assert verify_password("Strong@123", None) is False


def test_verify_password_both_none():
    assert verify_password(None, None) is False


def test_hash_password_none():
    assert hash_password(None) is None


def test_valid_foreign_key_exists(mocker):
    # Arrange
    mock_db = mocker.Mock(spec=Session)
    mock_model = mocker.Mock()
    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_filter.first.return_value = (
        mocker.Mock()
    )  # Return a mock object to simulate existing record

    field_name = "id"
    value = 1

    # Act
    from backendeldery.utils import validate_foreign_key

    result = validate_foreign_key(mock_db, mock_model, field_name, value)

    # Assert
    mock_db.query.assert_called_once_with(mock_model)
    mock_query.filter.assert_called_once()
    mock_filter.first.assert_called_once()
    assert result is None  # Function returns None when successful


@pytest.mark.asyncio
async def test_yields_async_session(mocker):
    # Arrange
    mock_session = MagicMock()

    # Create an async generator function
    async def mock_async_db():
        yield mock_session

    # Patch get_async_db to return our async generator
    mock_get_async_db = mocker.patch.object(
        db_instance, "get_async_db", return_value=mock_async_db()
    )

    # Act
    session_generator = get_db_aync()
    session = await anext(session_generator)

    # Assert
    assert session == mock_session
    mock_get_async_db.assert_called_once()


def test_get_db_yields_session(mocker):
    # Arrange
    mock_session = mocker.MagicMock()
    mock_get_db = mocker.patch("backendeldery.database.db_instance.get_db")
    mock_get_db.return_value = iter([mock_session])

    # Act
    from backendeldery.utils import get_db

    db = next(get_db())

    # Assert
    assert db == mock_session
    mock_get_db.assert_called_once()
