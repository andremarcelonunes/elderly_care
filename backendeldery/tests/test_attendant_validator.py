# test_attendant_validator.py
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backendeldery.models import User, Attendant
from backendeldery.schemas import UserCreate, AttendantCreate
from backendeldery.validators.attendant_validator import AttendantValidator


@pytest.fixture
def db_session(mocker):
    return mocker.Mock(spec=Session)


@pytest.fixture
def user():
    return User(id=1, email="john.doe@example.com", phone="+123456789")


@pytest.fixture
def attendant_data():
    return AttendantCreate(
        cpf="12345678900",
        birthday="1980-01-01",
        nivel_experiencia="senior",
        specialties=["Cardiology"]
    )


def test_validate_attendant_already_exists(db_session, user, attendant_data):
    db_session.query.return_value.filter.return_value.first.return_value = Attendant()
    with pytest.raises(HTTPException) as excinfo:
        AttendantValidator.validate_attendant(db_session, user, attendant_data)
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "Attendant already exists"


def test_validate_attendant_cpf_already_exists(db_session, user, attendant_data, mocker):
    query_mock = mocker.MagicMock()
    query_mock.filter.return_value.first.side_effect = [None, Attendant()]
    db_session.query.return_value = query_mock
    with pytest.raises(HTTPException) as excinfo:
        AttendantValidator.validate_attendant(db_session, user, attendant_data)
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "CPF already exists"


def test_validate_attendant_success(db_session, user, attendant_data):
    db_session.query.return_value.filter.return_value.first.return_value = None
    # No exception should be raised
    AttendantValidator.validate_attendant(db_session, user, attendant_data)


