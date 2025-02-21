# test_crud_attendant.py
import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backendeldery.crud.attendant import CRUDAttendant
from backendeldery.schemas import UserCreate, AttendantCreate


class DummyQuery:
    def __init__(self, return_value=None):
        self._return_value = return_value
    def filter(self, *args, **kwargs):
        return self
    def first(self):
        return self._return_value


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
    # Patch db.query so that it returns a DummyQuery instance that returns None
    dummy_query = DummyQuery(return_value=None)
    mocker.patch.object(db_session, "query", return_value=dummy_query)

    crud_attendant = CRUDAttendant()
    created_user = await crud_attendant.create(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )
    assert created_user.email == user_data.email
    assert created_user.phone == user_data.phone
    assert created_user.role == user_data.role
    assert created_user.active == user_data.active


@pytest.mark.asyncio
async def test_create_attendant_exception(db_session, user_data, mocker):
    crud_attendant = CRUDAttendant()
    mocker.patch.object(crud_attendant.crud_user, 'create', side_effect=Exception("Database error"))
    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.create(
            db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
        )
    assert exc_info.value.status_code == 500
    assert "Error to register Attendant: Database error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_attendant_rollback_on_error(db_session, user_data, mocker):
    crud_attendant = CRUDAttendant()
    # Mock a database error during attendant creation
    mocker.patch.object(db_session, 'commit', side_effect=Exception("Database error"))

    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.create(
            db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
        )

    assert exc_info.value.status_code == 500
    db_session.rollback.assert_called_once()  # Verify rollback was called


@pytest.mark.asyncio
async def test_create_attendant_new_specialty(db_session, user_data, mocker):
    # Modify user_data to include a new specialty
    user_data.attendant_data.specialties = ["New Specialty"]

    # Patch the db.query method for Specialty to return a dummy query object.
    dummy_query = mocker.MagicMock()
    # When filter().first() is called, return None (simulate specialty not found)
    dummy_query.filter.return_value.first.return_value = None
    mocker.patch.object(db_session, "query", return_value=dummy_query)

    crud_attendant = CRUDAttendant()
    created_user = await crud_attendant.create(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )

    # Now the new specialty should be created and associated.
    # Assuming the created user now has an 'attendant' attribute with a specialties relationship.
    assert "New Specialty" in [s.name for s in created_user.attendant.specialties]