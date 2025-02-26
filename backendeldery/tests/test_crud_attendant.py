import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backendeldery.crud.attendant import CRUDAttendant
from backendeldery.models import User
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
        active=True,
        password="Strong@123",
        client_data=None,
        attendant_data=AttendantCreate(
            cpf="12345678900",
            birthday="1980-01-01",
            nivel_experiencia="senior",
            specialties=["Cardiology"],
            team_names=["Team A"],
            function_names="Doctor",
        ),
    )


@pytest.mark.asyncio
async def test_create_attendant_success(db_session, user_data, mocker):
    # Patch to return None for specialty lookup.
    dummy_query = DummyQuery(return_value=None)
    mocker.patch.object(db_session, "query", return_value=dummy_query)
    crud_attendant = CRUDAttendant()

    # Patch user creation to return a dummy user with valid id, name, and role.
    dummy_user = User(
        id=1,
        email=user_data.email,
        phone=user_data.phone,
        name=user_data.name,
        role=user_data.role,
    )
    dummy_user.attendant = None
    mocker.patch.object(crud_attendant.crud_user, "create", return_value=dummy_user)

    created_user = await crud_attendant.create(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )
    assert created_user.email == user_data.email
    assert created_user.phone == user_data.phone


@pytest.mark.asyncio
async def test_create_attendant_exception(db_session, user_data, mocker):
    crud_attendant = CRUDAttendant()
    mocker.patch.object(
        crud_attendant.crud_user, "create", side_effect=Exception("Database error")
    )
    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.create(
            db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
        )
    assert exc_info.value.status_code == 500
    assert "Error to register Attendant: Database error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_attendant_rollback_on_error(db_session, user_data, mocker):
    crud_attendant = CRUDAttendant()
    # Mock a database error during attendant creation.
    mocker.patch.object(db_session, "commit", side_effect=Exception("Database error"))
    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.create(
            db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
        )
    assert exc_info.value.status_code == 500
    db_session.rollback.assert_called_once()


@pytest.mark.asyncio
async def test_create_attendant_new_specialty(db_session, user_data, mocker):
    # Modify the attendant_data to include a new specialty.
    user_data.attendant_data.specialties = ["New Specialty"]
    dummy_query = mocker.MagicMock()
    # Simulate specialty not found.
    dummy_query.filter.return_value.first.return_value = None
    mocker.patch.object(db_session, "query", return_value=dummy_query)
    crud_attendant = CRUDAttendant()

    # Patch user creation to return a dummy user with valid id, name, and role.
    dummy_user = User(
        id=1,
        email=user_data.email,
        phone=user_data.phone,
        name=user_data.name,
        role=user_data.role,
    )
    dummy_user.attendant = None
    mocker.patch.object(crud_attendant.crud_user, "create", return_value=dummy_user)

    created_user = await crud_attendant.create(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )
    # Directly check the specialty_names list.
    assert created_user.attendant_data is not None
    assert "New Specialty" in created_user.attendant_data.specialty_names


@pytest.mark.asyncio
async def test_create_attendant_with_new_team(db_session, user_data, mocker):
    # Modify the attendant_data to include a new team.
    user_data.attendant_data.team_names = ["New Team"]
    dummy_query = mocker.MagicMock()
    # Simulate team not found.
    dummy_query.filter.return_value.first.return_value = None
    mocker.patch.object(db_session, "query", return_value=dummy_query)
    crud_attendant = CRUDAttendant()

    # Patch user creation to return a dummy user with valid id, name, and role.
    dummy_user = User(
        id=1,
        email=user_data.email,
        phone=user_data.phone,
        name=user_data.name,
        role=user_data.role,
    )
    dummy_user.attendant = None
    mocker.patch.object(crud_attendant.crud_user, "create", return_value=dummy_user)

    created_user = await crud_attendant.create(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )
    # Directly check the team_names list.
    assert created_user.attendant_data is not None
    assert "New Team" in created_user.attendant_data.team_names


@pytest.mark.asyncio
async def test_create_attendant_with_new_function(db_session, user_data, mocker):
    # Modify the attendant_data to include a new function.
    user_data.attendant_data.function_names = ["New Function"]
    dummy_query = mocker.MagicMock()
    # Simulate function not found.
    dummy_query.filter.return_value.first.return_value = None
    mocker.patch.object(db_session, "query", return_value=dummy_query)
    crud_attendant = CRUDAttendant()

    # Patch user creation to return a dummy user with valid id, name, and role.
    dummy_user = User(
        id=1,
        email=user_data.email,
        phone=user_data.phone,
        name=user_data.name,
        role=user_data.role,
    )
    dummy_user.attendant = None
    mocker.patch.object(crud_attendant.crud_user, "create", return_value=dummy_user)

    created_user = await crud_attendant.create(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )
    # Directly check the function_names list.
    assert created_user.attendant_data is not None
    assert "New Function" in created_user.attendant_data.function_names
