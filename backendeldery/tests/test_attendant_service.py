# test_attendant_service.py
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backendeldery.services.attendants import AttendantService
from backendeldery.schemas import UserCreate, AttendantCreate
from backendeldery.validators.user_validator import UserValidator
from backendeldery.validators.attendant_validator import AttendantValidator
from backendeldery.crud.attendant import CRUDAttendant


@pytest.fixture
def db_session(mocker):
    return mocker.Mock(spec=Session)


@pytest.fixture
def user_data():
    return UserCreate(
        name="John Doe",
        email="john.doe@example.com",
        phone="+123456789",
        role="attendant",
        password="Strong@123",
        active=True,
        attendant_data=AttendantCreate(
            cpf="12345678900",
            birthday="1980-01-01",
            nivel_experiencia="senior",
            specialties=["Cardiology"]
        )
    )


@pytest.mark.asyncio
async def test_create_attendant_success(db_session, user_data, mocker):
    mocker.patch.object(UserValidator, 'validate_user', return_value=None)
    mocker.patch.object(AttendantValidator, 'validate_attendant', return_value=None)
    mocker.patch.object(CRUDAttendant, 'create', return_value=user_data)

    result = await AttendantService.create_attendant(
        db=db_session, user_data=user_data, created_by=1, user_ip="127.0.0.1"
    )

    assert result == user_data


@pytest.mark.asyncio
async def test_create_attendant_validation_error(db_session, user_data, mocker):
    mocker.patch.object(UserValidator, 'validate_user', side_effect=HTTPException(status_code=400, detail="Validation error"))
    mocker.patch.object(AttendantValidator, 'validate_attendant', return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await AttendantService.create_attendant(
            db=db_session, user_data=user_data, created_by=1, user_ip="127.0.0.1"
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Validation error"


@pytest.mark.asyncio
async def test_create_attendant_unexpected_error(db_session, user_data, mocker):
    mocker.patch.object(UserValidator, 'validate_user', return_value=None)
    mocker.patch.object(AttendantValidator, 'validate_attendant', return_value=None)
    mocker.patch.object(CRUDAttendant, 'create', side_effect=Exception("Unexpected error"))

    with pytest.raises(HTTPException) as exc_info:
        await AttendantService.create_attendant(
            db=db_session, user_data=user_data, created_by=1, user_ip="127.0.0.1"
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Unexpected error: Unexpected error"