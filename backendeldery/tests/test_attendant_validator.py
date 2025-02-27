import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backendeldery.models import Attendant
from backendeldery.schemas import AttendantCreate
from backendeldery.validators.attendant_validator import AttendantValidator


@pytest.fixture
def db_session(mocker):
    return mocker.Mock(spec=Session)


@pytest.fixture
def attendant_data():
    return AttendantCreate(
        cpf="12345678900",
        birthday="1980-01-01",
        nivel_experiencia="senior",
        specialties=["Cardiology"],
    )


def test_validate_attendant_success(db_session, attendant_data):
    validator = AttendantValidator()
    # Simulate no duplicate CPF found
    db_session.query.return_value.filter.return_value.first.return_value = None
    # No exception should be raised
    result = validator.validate_attendant(db_session, attendant_data)
    # Validator returns None when successful
    assert result is None


def test_validate_attendant_cpf_already_exists(db_session, attendant_data, mocker):
    validator = AttendantValidator()
    # Simulate the first call returns None and the second call returns an existing Attendant
    attendant_instance = Attendant()
    query_mock = mocker.MagicMock()
    query_mock.filter.return_value.first.side_effect = [None, attendant_instance]
    db_session.query.return_value = query_mock

    # First call should pass as nothing is found
    validator.validate_attendant(db_session, attendant_data)
    # Second call should raise HTTPException due to duplicate CPF
    with pytest.raises(HTTPException) as excinfo:
        validator.validate_attendant(db_session, attendant_data)
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "CPF already exists"


def test_validate_attendant_filter_called_correctly(db_session, attendant_data):
    validator = AttendantValidator()
    # Set up the query to return None (no duplicate)
    db_session.query.return_value.filter.return_value.first.return_value = None
    validator.validate_attendant(db_session, attendant_data)

    # Ensure query was called first with Attendant and then filter was applied with the CPF condition
    db_session.query.assert_called_once_with(Attendant)
    # We extract the actual condition passed to filter and convert it to string for simplicity
    condition = db_session.query.return_value.filter.call_args[0][0]
    expected_condition = Attendant.cpf == attendant_data.cpf
    assert str(condition) == str(expected_condition)
