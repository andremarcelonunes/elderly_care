import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backendeldery.models import User, Attendant
from backendeldery.schemas import AttendantCreate
from backendeldery.validators.attendant_validator import AttendantValidator


@pytest.fixture
def db_session(mocker):
    return mocker.Mock(spec=Session)


@pytest.fixture
def user():
    return User(id=1, email='john.doe@example.com', phone='+123456789')


@pytest.fixture
def attendant_data():
    return AttendantCreate(
        cpf='12345678900',
        birthday='1980-01-01',
        nivel_experiencia='senior',
        specialties=['Cardiology']
    )


def test_validate_attendant_success(db_session, user, attendant_data):
    # Simulate no duplicate CPF found
    db_session.query.return_value.filter.return_value.first.return_value = None
    # No exception should be raised
    result = AttendantValidator.validate_attendant(db_session, user, attendant_data)
    # Validator returns None when successful
    assert result is None


def test_validate_attendant_cpf_already_exists(db_session, user, attendant_data, mocker):
    # Simulate the first call returns None and the second call returns an existing Attendant
    attendant_instance = Attendant()
    query_mock = mocker.MagicMock()
    query_mock.filter.return_value.first.side_effect = [None, attendant_instance]
    db_session.query.return_value = query_mock

    # First call should pass as nothing is found
    AttendantValidator.validate_attendant(db_session, user, attendant_data)
    # Second call should raise HTTPException due to duplicate CPF
    with pytest.raises(HTTPException) as excinfo:
        AttendantValidator.validate_attendant(db_session, user, attendant_data)
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "CPF already exists"


def test_validate_attendant_filter_called_correctly(db_session, user, attendant_data):
    # Set up the query to return None (no duplicate)
    db_session.query.return_value.filter.return_value.first.return_value = None
    AttendantValidator.validate_attendant(db_session, user, attendant_data)

    # Ensure query was called first with Attendant and then filter was applied with the CPF condition
    db_session.query.assert_called_once_with(Attendant)
    # We extract the actual condition passed to filter and convert it to string for simplicity
    condition = db_session.query.return_value.filter.call_args[0][0]
    expected_condition = (Attendant.cpf == attendant_data.cpf)
    assert str(condition) == str(expected_condition)

