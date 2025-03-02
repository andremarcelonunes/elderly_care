from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backendeldery import CRUDUser
from backendeldery.crud.attendant import CRUDAttendant
from backendeldery.models import (
    User,
    Attendant,
    Function,
    Team,
)
from backendeldery.schemas import (
    UserCreate,
    AttendantCreate,
    AttendantResponse,
    UserInfo,
    AttendantUpdate,
    UserUpdate,
)


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


class DummyAsyncContextManager:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        pass


@pytest.fixture
def async_db_session(mocker):
    session = mocker.Mock(spec=AsyncSession)

    # Set up begin to return an async context manager.
    session.begin = MagicMock(return_value=DummyAsyncContextManager(session))
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()

    return session


@pytest.fixture
def user_update_data():
    return UserUpdate(
        email="updated.email@example.com",
        phone="+987654321",
        attendant_data=AttendantUpdate(
            address="Updated Address",
            specialties=["Updated Specialty"],
            team_names=["Updated Team"],
            function_names="Updated Function",
            nivel_experiencia="senior",  # Add the required field
        ),
    )


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
async def test_get_attendant_success():
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
        specialty_names=["Cardiology"],
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
        attendant_data=fake_attendant,  # Use the correct attribute name
    )

    # Create a fake db session that returns fake_user from the query chain.
    fake_db = MagicMock()
    fake_db.query.return_value.options.return_value.filter.return_value.first.return_value = (
        fake_user
    )

    # Run the method
    result = await crud_attendant.get(db=fake_db, id=1)

    # Validate that result is not None
    assert result is not None
    assert isinstance(result, UserInfo)
    assert result.id == fake_user.id
    assert result.name == fake_user.name
    assert result.email == fake_user.email
    assert result.phone == fake_user.phone
    assert result.role == fake_user.role
    assert result.active == fake_user.active

    # Validate the attendant data
    assert result.attendant_data is not None
    assert isinstance(result.attendant_data, AttendantResponse)
    assert result.attendant_data.cpf == fake_attendant.cpf
    assert result.attendant_data.address == fake_attendant.address
    assert result.attendant_data.city == fake_attendant.city
    assert result.attendant_data.birthday == fake_attendant.birthday


@pytest.mark.asyncio
async def test_get_attendant_not_found():
    crud_attendant = CRUDAttendant()

    # Create a fake db session that returns None for the query chain.
    fake_db = MagicMock()

    # Ensure that query().options().filter().first() returns None.
    fake_db.query.return_value.options.return_value.filter.return_value.first.return_value = (
        None
    )

    # Call the method
    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.get(db=fake_db, id=1)

    # Validate that the exception has the correct status code and detail
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_attendant_no_attendant_data():
    crud_attendant = CRUDAttendant()

    # Create a fake user object WITH 'attendant_data' set to None.
    fake_user = SimpleNamespace(
        id=2,
        name="Jane Doe",
        email="jane@example.com",
        phone="+987654321",
        role="attendant",
        active=True,
        attendant_data=None,  # Ensuring this matches the expected attribute name.
    )

    fake_db = MagicMock()
    # Ensure query().options().filter().first() returns our fake user.
    fake_db.query.return_value.options.return_value.filter.return_value.first.return_value = (
        fake_user
    )

    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.get(db=fake_db, id=2)

    assert exc_info.value.status_code == 404


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


@pytest.mark.asyncio
async def test_update_success_full(mocker, async_db_session):
    crud_attendant = CRUDAttendant()

    # Dummy update_data with attendant_data
    update_dict = {
        "attendant_data": {
            "team_names": ["Team A"],
            "function_names": "Doctor",
            "specialties": ["Cardiology"],
            "address": "New Address",  # extra field for core update
        }
    }
    update_data = MagicMock()
    update_data.model_dump = lambda **kwargs: update_dict.copy()

    # Dummy user and attendant objects
    dummy_user = MagicMock()
    dummy_user.id = 1
    dummy_attendant = MagicMock()
    dummy_attendant.user_id = 1

    # Patch update service methods
    dummy_update_service = MagicMock()
    dummy_update_service.update_user = AsyncMock(return_value=dummy_user)
    dummy_update_service.get_attendant = AsyncMock(return_value=dummy_attendant)
    # Core fields update is synchronous
    dummy_update_service.update_attendant_core_fields = mocker.Mock()

    # Patch association service methods
    dummy_association_service = MagicMock()
    dummy_association_service.update_team_associations = AsyncMock()
    dummy_association_service.update_function_association = AsyncMock(
        return_value=MagicMock(name="DummyFunction")
    )
    dummy_association_service.update_specialty_associations = AsyncMock()

    # Patch constructors to return our dummy services
    mocker.patch(
        "backendeldery.crud.attendant.AttendantUpdateService",
        return_value=dummy_update_service,
    )
    mocker.patch(
        "backendeldery.crud.attendant.AttendantAssociationService",
        return_value=dummy_association_service,
    )

    # Patch refresh to do nothing
    async_db_session.refresh = AsyncMock()

    # Invoke the update method
    result = await crud_attendant.update(
        async_db_session, 1, update_data, 1, "127.0.0.1"
    )

    # Assertions for update service calls
    dummy_update_service.update_user.assert_awaited_once_with(
        1, update_data, crud_attendant
    )
    dummy_update_service.get_attendant.assert_awaited_once_with(1)
    dummy_update_service.update_attendant_core_fields.assert_called_once_with(
        dummy_attendant, update_dict["attendant_data"]
    )
    # Assertions for association service calls
    dummy_association_service.update_team_associations.assert_awaited_once_with(
        ["Team A"], crud_attendant.crud_team
    )
    dummy_association_service.update_function_association.assert_awaited_once_with(
        "Doctor", crud_attendant.crud_function
    )
    dummy_association_service.update_specialty_associations.assert_awaited_once_with(
        ["Cardiology"]
    )
    async_db_session.refresh.assert_awaited_once_with(dummy_attendant)
    assert result == dummy_attendant


# Test 2: Update with no attendant_data (skip core fields and associations)
@pytest.mark.asyncio
async def test_update_without_attendant_data(mocker, async_db_session):
    crud_attendant = CRUDAttendant()

    update_data = MagicMock()
    update_data.model_dump.return_value = {}  # no attendant_data provided

    dummy_user = MagicMock()
    dummy_user.id = 1
    dummy_attendant = MagicMock()
    dummy_attendant.user_id = 1

    dummy_update_service = MagicMock()
    dummy_update_service.update_user = AsyncMock(return_value=dummy_user)
    dummy_update_service.get_attendant = AsyncMock(return_value=dummy_attendant)
    dummy_update_service.update_attendant_core_fields = mocker.Mock()

    dummy_association_service = MagicMock()
    dummy_association_service.update_team_associations = AsyncMock()
    dummy_association_service.update_function_association = AsyncMock()
    dummy_association_service.update_specialty_associations = AsyncMock()

    mocker.patch(
        "backendeldery.crud.attendant.AttendantUpdateService",
        return_value=dummy_update_service,
    )
    mocker.patch(
        "backendeldery.crud.attendant.AttendantAssociationService",
        return_value=dummy_association_service,
    )

    async_db_session.refresh = AsyncMock()

    result = await crud_attendant.update(
        async_db_session, 1, update_data, 1, "127.0.0.1"
    )

    # Ensure that core fields and associations were not updated.
    dummy_update_service.update_attendant_core_fields.assert_not_called()
    dummy_association_service.update_team_associations.assert_not_called()
    dummy_association_service.update_function_association.assert_not_called()
    dummy_association_service.update_specialty_associations.assert_not_called()
    async_db_session.refresh.assert_awaited_once_with(dummy_attendant)
    assert result == dummy_attendant


# Test 3: update_user returns None -> raise HTTPException(404)
@pytest.mark.asyncio
async def test_update_user_not_found(mocker, async_db_session):
    crud_attendant = CRUDAttendant()

    update_data = MagicMock()
    update_data.model_dump.return_value = {"attendant_data": {}}

    dummy_update_service = MagicMock()
    dummy_update_service.update_user = AsyncMock(return_value=None)
    mocker.patch(
        "backendeldery.crud.attendant.AttendantUpdateService",
        return_value=dummy_update_service,
    )

    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.update(async_db_session, 1, update_data, 1, "127.0.0.1")
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


# Test 4: SQLAlchemyError during update -> rollback and raise HTTPException with code 500
@pytest.mark.asyncio
async def test_update_sqlalchemy_error(mocker, async_db_session):
    crud_attendant = CRUDAttendant()

    update_data = MagicMock()
    update_data.model_dump.return_value = {"attendant_data": {}}

    dummy_update_service = MagicMock()
    dummy_update_service.update_user = AsyncMock(
        side_effect=SQLAlchemyError("DB error")
    )
    mocker.patch(
        "backendeldery.crud.attendant.AttendantUpdateService",
        return_value=dummy_update_service,
    )

    async_db_session.rollback = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.update(async_db_session, 1, update_data, 1, "127.0.0.1")
    assert exc_info.value.status_code == 500
    assert "Failed to update attendant: DB error" in exc_info.value.detail
    async_db_session.rollback.assert_awaited()


# Test 5: General Exception during update -> rollback and raise HTTPException with code 500
@pytest.mark.asyncio
async def test_update_general_exception(mocker, async_db_session):
    crud_attendant = CRUDAttendant()

    update_data = MagicMock()
    update_data.model_dump.return_value = {"attendant_data": {}}

    dummy_update_service = MagicMock()
    dummy_update_service.update_user = AsyncMock(side_effect=Exception("General error"))
    mocker.patch(
        "backendeldery.crud.attendant.AttendantUpdateService",
        return_value=dummy_update_service,
    )

    async_db_session.rollback = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.update(async_db_session, 1, update_data, 1, "127.0.0.1")
    assert exc_info.value.status_code == 500
    assert "General error" in exc_info.value.detail
    async_db_session.rollback.assert_awaited()


@pytest.mark.asyncio
async def test_create_attendant_type_error(mocker):
    crud_attendant = CRUDAttendant()
    db_mock = MagicMock()
    db_mock.rollback = MagicMock()

    # Dummy user data with attendant info to trigger the branch
    user_data = MagicMock()
    user_data.role = "attendant"
    user_data.attendant_data = MagicMock()

    # Patch parent's create to return a dummy user
    dummy_user = MagicMock()
    dummy_user.id = 1
    dummy_user.attendant = None
    mocker.patch(
        "backendeldery.crud.attendant.CRUDUser.create",
        return_value=dummy_user,
    )

    # Patch _create_attendant to raise TypeError so that the except branch is followed
    mocker.patch.object(
        crud_attendant,
        "_create_attendant",
        new=AsyncMock(side_effect=TypeError("Bad data")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.create(db_mock, user_data, 1, "127.0.0.1")
    assert exc_info.value.status_code == 400
    assert "Bad data" in exc_info.value.detail
    db_mock.rollback.assert_called_once()
