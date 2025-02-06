import pytest
from unittest.mock import Mock
from sqlalchemy.orm import Session
from backendeldery.models import User
from backendeldery.crud.users import CRUDAssisted


def test_create_association_success(mocker):
    db_session = Mock(spec=Session)
    mock_user = User(id=1, role="subscriber")

    # Mock the query chain
    mock_query = mocker.Mock()
    mock_query.filter.return_value.one_or_none.return_value = mock_user
    mocker.patch.object(db_session, "query", return_value=mock_query)

    # Create CRUD instance
    crud_assisted = CRUDAssisted()

    # Call the method
    result = crud_assisted.create_association(
        db_session, subscriber_id=1, assisted_id=2
    )

    # Assert the result
    assert result == {"message": "Association created successfully"}
    db_session.commit.assert_called_once()


def test_create_association_user_not_found(mocker):
    db_session = Mock(spec=Session)

    # Mock the query chain to return None
    mock_query = mocker.Mock()
    mock_query.filter.return_value.one_or_none.return_value = None
    mocker.patch.object(db_session, "query", return_value=mock_query)

    # Create CRUD instance
    crud_assisted = CRUDAssisted()

    # Call the method and assert ValueError is raised
    with pytest.raises(ValueError) as excinfo:
        crud_assisted.create_association(db_session, subscriber_id=1, assisted_id=2)
    assert str(excinfo.value) == "User not found"
    db_session.rollback.assert_called_once()


def test_create_association_exception(mocker):
    db_session = Mock(spec=Session)

    # Mock the query chain to raise an exception
    mock_query = mocker.Mock()
    mock_query.filter.return_value.one_or_none.side_effect = Exception(
        "Unexpected error"
    )
    mocker.patch.object(db_session, "query", return_value=mock_query)

    # Create CRUD instance
    crud_assisted = CRUDAssisted()

    # Call the method and assert RuntimeError is raised
    with pytest.raises(RuntimeError) as excinfo:
        crud_assisted.create_association(db_session, subscriber_id=1, assisted_id=2)
    assert str(excinfo.value) == "Error creating association: Unexpected error"
    db_session.rollback.assert_called_once()
