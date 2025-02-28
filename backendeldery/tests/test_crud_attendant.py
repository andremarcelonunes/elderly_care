from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backendeldery import CRUDUser
from backendeldery.crud.attendant import CRUDAttendant
from backendeldery.models import (
    User,
    Attendant,
    Function,
    Team,
)
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
    mocker.patch.object(CRUDUser, "create", return_value=dummy_user)

    created_user = await crud_attendant.create(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )
    assert created_user.email == user_data.email
    assert created_user.phone == user_data.phone


@pytest.mark.asyncio
async def test_create_attendant_exception(db_session, user_data, mocker):
    crud_attendant = CRUDAttendant()
    mocker.patch.object(CRUDUser, "create", side_effect=Exception("Database error"))
    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.create(
            db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
        )
    assert exc_info.value.status_code == 500
    assert "Error to register Attendant: Database error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_attendant_rollback_on_error(db_session, user_data, mocker):
    crud_attendant = CRUDAttendant()

    # Create a proper mock session
    db_session_mock = mocker.MagicMock()
    db_session_mock.commit = mocker.MagicMock(side_effect=Exception("Database error"))
    db_session_mock.rollback = mocker.MagicMock()

    # Mock query() behavior to avoid "Mock object is not subscriptable"
    db_session_mock.query.return_value.filter.return_value.first.return_value = None

    # Mock async function calls
    mocker.patch.object(
        crud_attendant.crud_team,
        "get_by_name",
        new_callable=AsyncMock,
        return_value=None,
    )
    mocker.patch.object(
        crud_attendant.crud_team,
        "create",
        new_callable=AsyncMock,
        return_value=mocker.MagicMock(),
    )

    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.create(
            db=db_session_mock, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
        )

    assert exc_info.value.status_code == 500
    db_session_mock.rollback.assert_called_once()


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
    mocker.patch.object(CRUDUser, "create", return_value=dummy_user)

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
    mocker.patch.object(CRUDUser, "create", return_value=dummy_user)

    created_user = await crud_attendant.create(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )
    # Directly check the team_names list.
    assert created_user.attendant_data is not None
    assert "New Team" in created_user.attendant_data.team_names


@pytest.mark.asyncio
async def test_create_attendant_with_new_function(db_session, user_data, mocker):
    # Modify the attendant_data to include a new function as a string.
    user_data.attendant_data.function_names = "New Function"
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
    mocker.patch.object(CRUDUser, "create", return_value=dummy_user)

    created_user = await crud_attendant.create(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )
    # Directly check the function_names list.
    assert created_user.attendant_data is not None
    assert created_user.attendant_data.function_names == "New Function"


@pytest.mark.asyncio
async def test_get_attendant_success(mocker):
    crud_attendant = CRUDAttendant()

    # Create a fake attendant ORM object with correct types.
    fake_attendant = SimpleNamespace(
        cpf="12345678900",
        address="123 Main St",
        neighborhood="Downtown",
        city="Metropolis",
        state="State",
        code_address="001",
        birthday=date(1980, 1, 1),
        registro_conselho="123",
        nivel_experiencia="senior",
        formacao="degree",
        specialty_names=["Cardiology"],  # <-- Added this field
        teams=[SimpleNamespace(team_name="Team A")],
        function=SimpleNamespace(name="Doctor"),
    )

    # Create a fake user ORM object that has the expected attributes.
    fake_user = SimpleNamespace(
        id=1,
        name="John Doe",
        email="john@example.com",
        phone="+123456789",
        role="attendant",
        active=True,
        attendant=fake_attendant,  # Note: using an attribute, not a dict key.
    )

    # Create a fake db session that returns fake_user from the query chain.
    fake_db = MagicMock()
    fake_db_query = fake_db.query.return_value
    fake_outerjoin = fake_db_query.outerjoin.return_value
    fake_filter = fake_outerjoin.filter.return_value
    fake_filter.first.return_value = fake_user

    result = await crud_attendant.get(db=fake_db, id=1)
    assert result is not None


@pytest.mark.asyncio
async def test_get_attendant_not_found(mocker):
    crud_attendant = CRUDAttendant()

    # Create a fake db session that returns None for the query chain.
    fake_db = MagicMock()
    # Set up the chain: query().outerjoin().filter().first() returns None.
    fake_db.query.return_value.outerjoin.return_value.filter.return_value.first.return_value = (
        None
    )

    # Now, get should return None.
    result = await crud_attendant.get(db=fake_db, id=1)
    assert result is None


@pytest.mark.asyncio
async def test_get_attendant_no_attendant_data(mocker):
    crud_attendant = CRUDAttendant()

    # Create a fake user object WITH the 'attendant' attribute set to None.
    fake_user = SimpleNamespace(
        id=2,
        name="Jane Doe",
        email="jane@example.com",
        phone="+987654321",
        role="attendant",
        active=True,
        attendant=None,  # This simulates no attendant data.
    )

    fake_db = MagicMock()
    # Configure the query chain so that first() returns our fake user.
    fake_db.query.return_value.outerjoin.return_value.filter.return_value.first.return_value = (
        fake_user
    )

    result = await crud_attendant.get(db=fake_db, id=2)
    assert result is not None
    # Since there is no attendant, attendant_data should be absent or None.
    assert getattr(result, "attendant_data", None) is None


@pytest.mark.asyncio
async def test_set_function_association(db_session, user_data, mocker):
    crud_attendant = CRUDAttendant()
    attendant = Attendant(user_id=1)
    mocker.patch.object(crud_attendant.crud_function, "get_by_name", return_value=None)
    mocker.patch.object(
        crud_attendant.crud_function,
        "create",
        return_value=Function(name="Doctor"),
    )
    await crud_attendant._set_function_association(
        db=db_session,
        attendant=attendant,
        function_name="Doctor",
        created_by=1,
        user_ip="127.0.0.1",
    )
    assert attendant.function.name == "Doctor"


@pytest.mark.asyncio
async def test_add_team_associations(db_session, user_data, mocker):
    crud_attendant = CRUDAttendant()
    attendant = Attendant(user_id=1)
    mocker.patch.object(crud_attendant.crud_team, "get_by_name", return_value=None)
    mocker.patch.object(
        crud_attendant.crud_team,
        "create",
        return_value=Team(
            team_id=1,
            team_name="Team A",
            team_site="default",
            created_by=1,
            user_ip="127.0.0.1",
        ),
    )
    await crud_attendant._add_team_associations(
        db=db_session,
        attendant=attendant,
        team_names=["Team A"],
        created_by=1,
        user_ip="127.0.0.1",
    )
    assert len(attendant.team_associations) == 1
    assert attendant.team_associations[0].team.team_name == "Team A"


@pytest.mark.asyncio
async def test_add_specialties(db_session, user_data, mocker):
    crud_attendant = CRUDAttendant()
    attendant = Attendant(user_id=1)
    mocker.patch.object(db_session, "query", return_value=DummyQuery())
    crud_attendant._add_specialties(
        db=db_session,
        attendant=attendant,
        specialties_list=["Cardiology"],
        created_by=1,
        user_ip="127.0.0.1",
    )
    assert len(attendant.specialty_associations) == 1
    assert attendant.specialty_associations[0].specialty.name == "Cardiology"


@pytest.mark.asyncio
async def test_create_attendant_type_error(db_session, user_data, mocker):
    crud_attendant = CRUDAttendant()
    dummy_user = User(
        id=1,
        email=user_data.email,
        phone=user_data.phone,
        name=user_data.name,
        role=user_data.role,
    )
    dummy_user.attendant = None
    mocker.patch.object(CRUDUser, "create", return_value=dummy_user)
    # Patch model_dump on the class, not the instance
    mocker.patch.object(
        type(user_data.attendant_data),
        "model_dump",
        side_effect=TypeError("model_dump error"),
    )
    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.create(
            db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
        )
    assert exc_info.value.status_code == 400
    assert "Error while creating Attendant" in exc_info.value.detail
