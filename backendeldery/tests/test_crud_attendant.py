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
    Specialty,
)
from backendeldery.schemas import (
    UserCreate,
    AttendantCreate,
    AttendantResponse,
    UserInfo,
    AttendantUpdate,
    UserUpdate,
)
from backendeldery.services.attendantAssociationService import (
    AttendantAssociationService,
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
            # Add the required fields
            address="123 Main St",
            neighborhood="Downtown",
            city="Test City",
            state="TS",
            code_address="12345",
            registro_conselho="REG123",
            formacao="Medicine",
        ),
    )


# Create simple dummy classes to use as returned objects.
class DummyUser:
    pass


class DummyAttendant:
    pass


@pytest.mark.asyncio
async def test_create_attendant_success(db_session, user_data, mocker):
    # Convert db_session to AsyncMock
    db_session = MagicMock()
    db_session.commit = MagicMock()
    db_session.refresh = MagicMock()
    db_session.add = MagicMock()

    # Create crud_attendant with its dependencies mocked
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

    # For synchronous specialty lookup
    dummy_query = DummyQuery(return_value=None)
    db_session.query = MagicMock(return_value=dummy_query)

    # Mock the team-related async method
    mock_team = Team(team_name="Team A")
    mocker.patch(
        "backendeldery.crud.team.CRUDTeam.get_by_name",
        return_value=mock_team,
    )

    # Mock the function-related async method
    mock_function = Function(name="Doctor")
    mocker.patch(
        "backendeldery.crud.function.CRUDFunction.get_by_name",
        return_value=mock_function,
    )

    # Run the test
    created_user = await crud_attendant.create(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )

    # Check basic assertions
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
    # Convert db_session to AsyncMock
    db_session = MagicMock()
    db_session.commit = MagicMock()
    db_session.refresh = MagicMock()
    db_session.add = MagicMock()

    # Modify the attendant_data to include a new specialty.
    user_data.attendant_data.specialties = ["New Specialty"]

    # For synchronous specialty lookup
    dummy_query = mocker.MagicMock()
    dummy_query.filter.return_value.first.return_value = None
    db_session.query = MagicMock(return_value=dummy_query)

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

    # Mock the team-related async method
    mock_team = Team(team_name="Team A")
    mocker.patch(
        "backendeldery.crud.team.CRUDTeam.get_by_name",
        return_value=mock_team,
    )

    # Mock the function-related async method
    mock_function = Function(name="Doctor")
    mocker.patch(
        "backendeldery.crud.function.CRUDFunction.get_by_name",
        return_value=mock_function,
    )

    created_user = await crud_attendant.create(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )

    # Directly check the specialty_names list.
    assert created_user.attendant_data is not None
    assert "New Specialty" in created_user.attendant_data.specialty_names


@pytest.mark.asyncio
async def test_create_attendant_with_new_team(db_session, user_data, mocker):
    # Convert db_session to AsyncMock
    db_session = MagicMock()
    db_session.commit = MagicMock()
    db_session.refresh = MagicMock()
    db_session.add = MagicMock()

    # Modify the attendant_data to include a new team.
    user_data.attendant_data.team_names = ["New Team"]

    # For synchronous lookups
    dummy_query = mocker.MagicMock()
    # Simulate team not found
    dummy_query.filter.return_value.first.return_value = None
    db_session.query = MagicMock(return_value=dummy_query)

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

    # Mock the team-related async method - return None to simulate team not found
    mocker.patch(
        "backendeldery.crud.team.CRUDTeam.get_by_name",
        return_value=None,
    )

    # Mock the team creation method
    mock_team = Team(team_name="New Team")
    mocker.patch(
        "backendeldery.crud.team.CRUDTeam.create",
        return_value=mock_team,
    )

    # Mock the function-related async method
    mock_function = Function(name="Doctor")
    mocker.patch(
        "backendeldery.crud.function.CRUDFunction.get_by_name",
        return_value=mock_function,
    )

    created_user = await crud_attendant.create(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )

    # Directly check the team_names list.
    assert created_user.attendant_data is not None
    assert "New Team" in created_user.attendant_data.team_names


@pytest.mark.asyncio
async def test_create_attendant_with_new_function(async_db_session, user_data, mocker):
    # Create the synchronous db_session mock.
    db_session = MagicMock()
    db_session.commit = MagicMock()
    db_session.refresh = MagicMock()
    db_session.add = MagicMock()

    user_data.attendant_data.function_names = "New Function"

    # Set up query on db_session, not async_db_session.
    dummy_query = mocker.MagicMock()
    dummy_query.filter.return_value.first.return_value = None
    db_session.query = MagicMock(return_value=dummy_query)

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
    mocker.patch.object(
        CRUDUser, "create", new_callable=AsyncMock, return_value=dummy_user
    )

    # Mock the team-related method.
    mock_team = Team(team_name="Team A")
    mocker.patch(
        "backendeldery.crud.team.CRUDTeam.get_by_name",
        return_value=mock_team,
    )

    # Mock the function-related methods.
    mocker.patch(
        "backendeldery.crud.function.CRUDFunction.get_by_name",
        return_value=None,
    )
    mock_function = Function(name="New Function")
    mocker.patch(
        "backendeldery.crud.function.CRUDFunction.create",
        return_value=mock_function,
    )

    # Pass the correct db_session to the create method.
    created_user = await crud_attendant.create(
        db=db_session, obj_in=user_data, created_by=1, user_ip="127.0.0.1"
    )

    # Directly check the function_names attribute in the response
    assert created_user.attendant_data is not None
    assert created_user.attendant_data.function_names == "New Function"

    # Verify synchronous query-related calls
    db_session.query.assert_called_once()
    db_session.query.return_value.filter.assert_called_once()
    db_session.query.return_value.filter.return_value.first.assert_called_once()
    CRUDUser.create.assert_awaited_once()

    # Since commit is synchronous, check that it was called three times.
    assert db_session.commit.call_count == 3

    # Check that refresh was called with dummy_user at least once.
    refresh_called_with_dummy_user = any(
        call.args[0] == dummy_user for call in db_session.refresh.call_args_list
    )
    assert refresh_called_with_dummy_user


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
async def test_get_async_retrieves_user_with_attendant_data(mocker):
    # Arrange
    db = mocker.AsyncMock()
    user_id = 1

    # Mock user with attendant data
    mock_user = mocker.Mock()
    mock_user.id = user_id
    mock_user.name = "Test User"
    mock_user.email = "test@example.com"
    mock_user.phone = "123456789"
    mock_user.role = "attendant"
    mock_user.active = True
    mock_user.client_data = None

    # Mock attendant data
    mock_attendant = mocker.Mock()
    mock_attendant.cpf = "12345678901"
    mock_attendant.birthday = date(1990, 1, 1)
    mock_attendant.nivel_experiencia = "senior"
    mock_attendant.specialty_names = ["Specialty1", "Specialty2"]
    mock_attendant.team_names = ["Team1"]

    mock_user.attendant_data = mock_attendant

    # Mock the database execution
    mock_result = mocker.AsyncMock()
    mock_result.scalar_one_or_none = mocker.Mock(return_value=mock_user)
    db.execute.return_value = mock_result

    # Mock the AttendantResponse validation
    mock_attendant_model = mocker.Mock()
    mock_attendant_model.dict.return_value = {
        "cpf": "12345678901",
        "birthday": date(1990, 1, 1),
        "nivel_experiencia": "senior",
        "specialty_names": ["Specialty1", "Specialty2"],
        "team_names": ["Team1"],
        "address": None,
        "neighborhood": None,
        "city": None,
        "state": None,
        "code_address": None,
        "registro_conselho": None,
        "formacao": None,
        "function_names": None,
    }
    mocker.patch(
        "backendeldery.schemas.AttendantResponse.model_validate",
        return_value=mock_attendant_model,
    )

    # Mock the UserInfo validation
    expected_result = {
        "id": user_id,
        "name": "Test User",
        "email": "test@example.com",
        "phone": "123456789",
        "role": "attendant",
        "active": True,
        "client_data": None,
        "attendant_data": mock_attendant_model.dict.return_value,
    }
    mock_user_info = mocker.Mock()
    mock_user_info.model_dump.return_value = expected_result
    mocker.patch(
        "backendeldery.schemas.UserInfo.model_validate", return_value=mock_user_info
    )

    # Create the CRUD instance
    crud = CRUDAttendant()

    # Act
    result = await crud.get_async(db, user_id)

    # Assert
    assert result == expected_result
    db.execute.assert_called_once()
    assert result["id"] == user_id
    assert result["attendant_data"] is not None


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
async def test_add_existing_specialty(mocker):
    # Arrange
    db = mocker.MagicMock()

    # Instead of using spec=Attendant (which triggers evaluation of hybrid properties),
    # define a custom spec_set with only the attributes _add_specialties will use.
    attendant_spec = ["user_id", "specialty_associations", "specialties"]
    attendant = mocker.MagicMock(spec_set=attendant_spec)

    # Set required attributes manually.
    attendant.user_id = 1
    attendant.specialty_associations = []  # where new associations will be appended
    attendant.specialties = []  # used by the hybrid property (but we won't rely on it)

    # Mock the query to return a Specialty instance
    mock_specialty = Specialty(name="Cardiology")
    db.query.return_value.filter.return_value.first.return_value = mock_specialty

    # Instantiate your CRUD object.
    crud_attendant = CRUDAttendant()

    # Act: Call the function that adds specialties.
    # Your _add_specialties method is expected to create a new association,
    # assign a new Specialty instance with name "Cardiology", and append it to specialty_associations.
    crud_attendant._add_specialties(
        db=db,
        attendant=attendant,
        specialties_list=["Cardiology"],
        created_by=1,
        user_ip="127.0.0.1",
    )

    # Assert: Verify that one new association was added.
    assert len(attendant.specialty_associations) == 1
    association = attendant.specialty_associations[0]

    # Check that the association has a 'specialty' attribute with name "Cardiology".
    assert hasattr(association, "specialty")
    assert isinstance(association.specialty, Specialty)
    assert association.specialty.name == "Cardiology"


def test_empty_specialties_list(mocker):
    # Arrange
    db = mocker.MagicMock()

    # Define a custom spec_set with only the attributes _add_specialties will use.
    attendant_spec = ["user_id", "specialty_associations", "specialties"]
    attendant = mocker.MagicMock(spec_set=attendant_spec)

    # Set required attributes manually.
    attendant.specialty_associations = []

    specialties_list = []
    created_by = 1
    user_ip = "127.0.0.1"

    # Create instance of the class that contains _add_specialties
    crud_attendant = CRUDAttendant()

    # Act
    crud_attendant._add_specialties(
        db, attendant, specialties_list, created_by, user_ip
    )

    # Assert
    db.query.assert_not_called()
    db.add.assert_not_called()
    assert len(attendant.specialty_associations) == 0


@pytest.mark.asyncio
async def test_create_attendant_type_error(mocker):
    # Arrange
    db = mocker.MagicMock()
    db.rollback = mocker.MagicMock()  # Explicitly mock rollback
    created_by = 1
    user_ip = "127.0.0.1"

    # Valid attendant data with correct field name
    valid_attendant_data = {
        "cpf": "12345678901",
        "address": "123 Main St",
        "neighborhood": "Downtown",
        "city": "Test City",
        "state": "TS",
        "code_address": "12345",
        "birthday": date(2000, 1, 1),
        "registro_conselho": "Registro123",
        "nivel_experiencia": "junior",
        "formacao": "Bachelor's Degree",
        "specialties": [],  # Correct field name for the Pydantic model
        "team_names": [],
        "function_names": "Test Function",
    }

    # Create a UserCreate input with attendant role
    obj_in = UserCreate(
        name="Test Attendant",
        email="test@example.com",
        phone="+123456789",
        role="attendant",
        password="password123",
        attendant_data=valid_attendant_data,
    )

    crud_attendant = CRUDAttendant()

    # Mock CRUDUser.create to return a user
    dummy_user = User(
        id=1,
        email="test@example.com",
        phone="+123456789",
        name="Test Attendant",
        role="attendant",
    )
    dummy_user.attendant = None
    mocker.patch.object(CRUDUser, "create", new=AsyncMock(return_value=dummy_user))

    # Mock _create_attendant as an AsyncMock since it's called with await
    mocker.patch.object(
        crud_attendant,
        "_create_attendant",
        new=AsyncMock(side_effect=TypeError("model_dump error")),
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.create(
            db=db, obj_in=obj_in, created_by=created_by, user_ip=user_ip
        )
    assert exc_info.value.status_code == 400
    assert "Error while creating Attendant" in exc_info.value.detail
    db.rollback.assert_called_once()  # Verify rollback was called


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
    # Core fields update is asynchronous
    dummy_update_service.update_attendant_core_fields = AsyncMock()

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
        1, update_data, 1, "127.0.0.1"
    )
    dummy_update_service.get_attendant.assert_awaited_once_with(1)
    dummy_update_service.update_attendant_core_fields.assert_awaited_once_with(
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


@pytest.mark.asyncio
async def test_update_with_team_names(mocker):
    # Arrange
    mock_db = mocker.AsyncMock()
    # Explicitly set commit and refresh as AsyncMock objects
    mock_db.commit = mocker.AsyncMock()
    mock_db.refresh = mocker.AsyncMock()

    mock_user_id = 1
    mock_updated_by = 2
    mock_user_ip = "127.0.0.1"

    # Create a complete AttendantUpdate object with all required fields
    attendant_update = AttendantUpdate(
        team_names=["Team A", "Team B"],
        address="Test Address",
        neighborhood="Test Neighborhood",
        city="Test City",
        state="TS",
        code_address="12345",
        registro_conselho="RC12345",
        formacao="Degree",
        nivel_experiencia="senior",
    )

    # Create the UserUpdate with the complete attendant_update
    mock_update_data = UserUpdate(
        email="andre@gmail.com", attendant_data=attendant_update
    )

    # Override the model_dump method to return only team_names
    object.__setattr__(
        mock_update_data,
        "model_dump",
        lambda *, exclude_unset=True: {
            "attendant_data": {"team_names": ["Team A", "Team B"]}
        },
    )

    # Mock service setup
    mock_update_service = mocker.patch(
        "backendeldery.crud.attendant.AttendantUpdateService"
    )
    mock_update_service_instance = mock_update_service.return_value
    mock_user = mocker.MagicMock()
    mock_user.id = mock_user_id
    mock_update_service_instance.update_user = mocker.AsyncMock(return_value=mock_user)
    mock_update_service_instance.get_attendant = mocker.AsyncMock()
    mock_update_service_instance.update_attendant_core_fields = mocker.AsyncMock()

    dummy_attendant = mocker.MagicMock()
    dummy_attendant.user_id = mock_user_id
    mock_update_service_instance.get_attendant.return_value = dummy_attendant

    mock_association_service = mocker.patch(
        "backendeldery.crud.attendant.AttendantAssociationService"
    )
    mock_association_service_instance = mock_association_service.return_value
    mock_association_service_instance.update_team_associations = mocker.AsyncMock()

    # Create CRUD instance
    crud_attendant = CRUDAttendant()
    crud_attendant.crud_team = mocker.MagicMock()
    crud_attendant.crud_function = mocker.MagicMock()

    # Act
    result = await crud_attendant.update(
        mock_db, mock_user_id, mock_update_data, mock_updated_by, mock_user_ip
    )

    # Assert
    mock_association_service_instance.update_team_associations.assert_awaited_once_with(
        ["Team A", "Team B"], crud_attendant.crud_team
    )
    mock_db.commit.assert_awaited_once()
    assert result == dummy_attendant


@pytest.mark.asyncio
async def test_get_handles_unexpected_exception(mocker):
    # Arrange
    mock_db = mocker.Mock()
    mock_query = mock_db.query.return_value
    mock_options = mock_query.options.return_value
    mock_filter = mock_options.filter.return_value

    # Simulate an unexpected exception during query execution
    mock_filter.first.side_effect = Exception("Unexpected error")

    # Create the CRUD instance
    crud = CRUDAttendant()

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await crud.get(mock_db, 1)

    assert exc_info.value.status_code == 500
    assert "Error retrieving user with attendant data" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_search_attendant_by_cpf_success(mocker):
    # Arrange
    mock_db = mocker.AsyncMock(spec=AsyncSession)
    mock_execute = mock_db.execute
    mock_result = mocker.MagicMock()
    mock_execute.return_value = mock_result

    # Create a mock user to return
    mock_user = mocker.MagicMock(spec=User)
    mock_result.scalars.return_value.first.return_value = mock_user

    # Create criteria with CPF
    criteria = {"cpf": "12345678900"}

    # Act
    from backendeldery.crud.attendant import CRUDAttendant

    crud_attendant = CRUDAttendant()
    result = await crud_attendant.search_attendant(mock_db, criteria)

    # Assert
    mock_execute.assert_called_once()
    assert result == mock_user


@pytest.mark.asyncio
async def test_search_attendant_by_email(mocker):
    # Arrange
    mock_db = mocker.AsyncMock(spec=AsyncSession)
    mock_execute = mock_db.execute
    mock_result = mocker.MagicMock()
    mock_execute.return_value = mock_result
    mock_scalars = mocker.MagicMock()
    mock_result.scalars.return_value = mock_scalars

    # Create a mock user to return
    mock_user = mocker.MagicMock(spec=User)
    mock_scalars.first.return_value = mock_user

    # Create the criteria dictionary
    criteria = {"email": "test@example.com"}

    # Act
    from backendeldery.crud.attendant import CRUDAttendant

    crud_attendant = CRUDAttendant()
    result = await crud_attendant.search_attendant(mock_db, criteria)

    # Assert
    assert result == mock_user
    mock_db.execute.assert_called_once()
    mock_result.scalars.assert_called_once()
    mock_scalars.first.assert_called_once()


@pytest.mark.asyncio
async def test_search_attendant_error_propagation(mocker):
    # Arrange
    mock_db = mocker.AsyncMock(spec=AsyncSession)
    mock_db.execute.side_effect = Exception("Database error")
    criteria = {"cpf": "12345678900"}

    # Act & Assert
    crud_attendant = CRUDAttendant()
    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.search_attendant(mock_db, criteria)

    assert exc_info.value.status_code == 500
    assert "Error to search subscriber" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_search_attendant_invalid_field(mocker):
    # Arrange
    mock_db = mocker.AsyncMock(spec=AsyncSession)
    criteria = {"invalid_field": "some_value"}

    # Act
    from backendeldery.crud.attendant import CRUDAttendant

    crud_attendant = CRUDAttendant()
    result = await crud_attendant.search_attendant(mock_db, criteria)

    # Assert
    assert result is None
    mock_db.execute.assert_not_called()

    # Successfully updates team associations when team_names is provided


@pytest.mark.asyncio
async def test_update_with_only_team_names(mocker):
    # Arrange
    mock_db = mocker.AsyncMock()
    user_id = 1
    updated_by = 2
    user_ip = "127.0.0.1"
    team_names = ["Team A", "Team B"]

    # Create a real AttendantUpdate and UserUpdate object.
    attendant_update = AttendantUpdate(
        team_names=team_names,
        address="Test Address",
        neighborhood="Test Neighborhood",
        city="Test City",
        state="TS",
        code_address="12345",
        registro_conselho="RC12345",
        formacao="Degree",
        nivel_experiencia="senior",  # Based on other tests, this is required too
    )
    update_data = UserUpdate(attendant_data=attendant_update)

    # Override the model_dump method on update_data (bypassing Pydantic restrictions)
    object.__setattr__(
        update_data,
        "model_dump",
        lambda *, exclude_unset=True: {"attendant_data": {"team_names": team_names}},
    )

    # Create mock objects to be returned by the service methods.
    mock_user = MagicMock()
    mock_user.id = user_id

    mock_attendant = MagicMock()
    mock_attendant.user_id = user_id

    # Setup AttendantUpdateService mock.
    mock_update_service = MagicMock()
    mock_update_service.update_user = AsyncMock(return_value=mock_user)
    mock_update_service.get_attendant = AsyncMock(return_value=mock_attendant)
    mock_update_service.update_attendant_core_fields = AsyncMock()

    # Patch the constructor of AttendantUpdateService.
    mocker.patch(
        "backendeldery.crud.attendant.AttendantUpdateService",
        return_value=mock_update_service,
    )

    # Setup AttendantAssociationService mock.
    mock_assoc_service = MagicMock()
    mock_assoc_service.update_team_associations = AsyncMock()

    # Patch the constructor of AttendantAssociationService.
    mocker.patch(
        "backendeldery.crud.attendant.AttendantAssociationService",
        return_value=mock_assoc_service,
    )

    # Create the CRUD instance and set the required attribute.
    crud_attendant = CRUDAttendant()
    crud_attendant.crud_team = MagicMock()

    # Act - call the update method.
    result = await crud_attendant.update(
        mock_db, user_id, update_data, updated_by, user_ip
    )

    # Assert - verify that update_team_associations was called with the expected parameters.
    mock_assoc_service.update_team_associations.assert_awaited_once_with(
        team_names, crud_attendant.crud_team
    )

    # Also check that other service methods and db operations were called as expected.
    mock_update_service.update_user.assert_awaited_once()
    mock_update_service.get_attendant.assert_awaited_once()
    mock_update_service.update_attendant_core_fields.assert_awaited_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(mock_attendant)
    assert result == mock_attendant


@pytest.mark.asyncio
async def test_update_attendant_not_found(mocker):
    # Arrange
    db = mocker.Mock(spec=AsyncMock)  # or AsyncSession, if available
    user_id = 1
    update_data = UserUpdate()
    updated_by = 1
    user_ip = "127.0.0.1"

    # Ensure update_data.model_dump returns a dictionary with empty attendant_data.
    object.__setattr__(
        update_data, "model_dump", lambda *, exclude_unset=True: {"attendant_data": {}}
    )

    # Patch AttendantUpdateService in the namespace where it's used by CRUDAttendant.
    patch_target = "backendeldery.crud.attendant.AttendantUpdateService"
    mock_update_service = mocker.patch(patch_target)
    mock_update_service_instance = mock_update_service.return_value

    # To avoid user not found error, make update_user return a fake user.
    fake_user = MagicMock()
    fake_user.id = user_id
    mock_update_service_instance.update_user = AsyncMock(return_value=fake_user)
    # Patch get_attendant to simulate "attendant not found" by returning None.
    mock_update_service_instance.get_attendant = AsyncMock(return_value=None)

    # Create an instance of CRUDAttendant (where update is defined)
    crud_attendant = CRUDAttendant()
    crud_attendant.crud_team = mocker.MagicMock()
    crud_attendant.crud_function = mocker.MagicMock()

    # Act & Assert: Since get_attendant returns None, update should raise an HTTPException.
    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.update(db, user_id, update_data, updated_by, user_ip)

    # Verify that the exception details match "Attendant not found"
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Attendant not found"


@pytest.mark.asyncio
async def test_update_handles_user_not_found(mocker):
    # Arrange
    mock_db = mocker.AsyncMock()
    mock_user_id = 1
    mock_updated_by = 2
    mock_user_ip = "127.0.0.1"

    # Create a real UserUpdate instance with a field (e.g., email)
    mock_update_data = UserUpdate(email="test@example.com")
    # Override model_dump so that it returns a dict with an empty attendant_data.
    object.__setattr__(
        mock_update_data,
        "model_dump",
        lambda *, exclude_unset=True: {"attendant_data": {}},
    )

    # Patch the AttendantUpdateService in the namespace where it's used.
    # First, override __init__ so it does nothing.
    from backendeldery.crud.attendant import AttendantUpdateService

    mocker.patch.object(
        AttendantUpdateService, "__init__", lambda self, db, updated_by, user_ip: None
    )

    # Then patch the class itself so that we can control its methods.
    patch_target = "backendeldery.crud.attendant.AttendantUpdateService"
    mock_update_service = mocker.patch(patch_target)
    mock_update_service_instance = mock_update_service.return_value
    # Make sure update_user is an AsyncMock returning None (simulating user not found).
    mock_update_service_instance.update_user = AsyncMock(return_value=None)

    # Create the CRUDAttendant instance and assign required attributes.
    crud_attendant = CRUDAttendant()
    crud_attendant.crud_team = mocker.MagicMock()
    crud_attendant.crud_function = mocker.MagicMock()

    # Act & Assert: update should raise an HTTPException with status 404 ("User not found").
    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.update(
            mock_db, mock_user_id, mock_update_data, mock_updated_by, mock_user_ip
        )

    # Verify that the exception details match the expected "User not found" error.
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


def test_user_without_attendant_returns_basic_info(mocker):
    # Arrange
    from backendeldery.schemas import AttendandInfo
    from backendeldery.models import User

    # Create a mock user without attendant
    mock_user = mocker.Mock(spec=User)
    mock_user.id = 1
    mock_user.name = "Jane Doe"
    mock_user.email = "jane@example.com"
    mock_user.phone = "987654321"
    mock_user.role = "user"
    mock_user.active = True
    mock_user.attendant = None

    # Patch the model_validate method on AttendandInfo so that it returns a fake schema instance.
    mock_user_info = mocker.Mock(spec=AttendandInfo)
    mocker.patch.object(AttendandInfo, "model_validate", return_value=mock_user_info)

    # Patch logger if necessary.
    mocker.patch("backendeldery.crud.attendant.logger")

    # Create an instance of CRUDAttendant (child of CRUDUser) that contains build_response.
    from backendeldery.crud.attendant import CRUDAttendant

    crud_attendant = CRUDAttendant()

    # Act - call the build_response method on the CRUDAttendant instance.
    result = crud_attendant._build_response(mock_user)

    # Assert - verify that the response is built as expected.
    assert result == mock_user_info


@pytest.mark.asyncio
async def test_set_function_association_with_empty_function_name(mocker):
    # Arrange
    db = mocker.MagicMock()
    # Instead of using spec=Attendant (which triggers hybrid property evaluation),
    # simply create a plain MagicMock.
    attendant = mocker.MagicMock()
    updated_by = 1
    user_ip = "127.0.0.1"
    # Set an empty function name.
    function_name = ""

    # Setup a mock for crud_function with async methods.
    mock_crud_function = mocker.MagicMock()
    mock_crud_function.create = AsyncMock()
    mock_crud_function.update = AsyncMock()

    # Instantiate the association service and assign the mock crud_function.
    service = AttendantAssociationService(db, updated_by, updated_by, user_ip)
    service.crud_function = mock_crud_function

    # Act: Call update_function_association with an empty function name.
    # (Assuming your service method returns None when function_name is empty.)
    result = await service.update_function_association(
        function_name, mock_crud_function
    )

    # Assert: Verify that neither create nor update was awaited.
    mock_crud_function.create.assert_not_awaited()
    mock_crud_function.update.assert_not_awaited()
    # And assert that result is None (or whatever your business logic dictates).
    assert result is None


@pytest.mark.asyncio
async def test_update_function_association_creates_function_when_not_exists(mocker):
    # Arrange
    db = mocker.AsyncMock()  # AsyncMock for asynchronous DB calls.
    function_name = "NewFunction"
    created_by = 1
    user_ip = "127.0.0.1"

    # Setup fake result for the execute call to simulate no existing function.
    fake_result = mocker.AsyncMock()
    fake_scalars = mocker.Mock()
    fake_scalars.first.return_value = None  # Simulate no existing function.
    fake_result.scalars = mocker.Mock(return_value=fake_scalars)
    db.execute.return_value = fake_result

    # Setup async mock for crud_function.create.
    mock_crud_function = mocker.MagicMock()
    mock_func_obj = mocker.MagicMock()
    mock_crud_function.create = AsyncMock(return_value=mock_func_obj)

    # Instantiate the service.
    service = AttendantAssociationService(db, created_by, created_by, user_ip)
    service.crud_function = mock_crud_function

    # Act: Call the update_function_association method.
    result = await service.update_function_association(
        function_name, mock_crud_function
    )

    # Assert: Ensure that create was awaited with the expected positional arguments.
    mock_crud_function.create.assert_awaited_once_with(
        db,
        function_name,
        "Auto-created function",
        created_by,
        user_ip,
    )

    # Optionally, assert that the result is as expected.
    assert result == mock_func_obj


@pytest.mark.asyncio
async def test_create_attendant_type_error(mocker):
    # Arrange
    db = mocker.MagicMock()
    created_by = 1
    user_ip = "127.0.0.1"

    # Valid attendant data as expected by your input schema.
    valid_attendant_data = {
        "cpf": "12345678901",
        "address": "123 Main St",
        "neighborhood": "Downtown",
        "city": "Test City",
        "state": "TS",
        "code_address": "12345",
        "birthday": date(2000, 1, 1),
        "registro_conselho": "Registro123",
        "nivel_experiencia": "junior",
        "formacao": "Bachelor's Degree",
        "specialties": [],
        "team_names": [],
        "function_names": "Test Function",
    }

    # Create a UserCreate input with attendant role.
    obj_in = UserCreate(
        name="Test Attendant",
        email="test@example.com",
        phone="+123456789",
        role="attendant",
        password="password123",
        attendant_data=valid_attendant_data,
    )

    # Create a fake user (using SimpleNamespace) with proper attributes.
    fake_user = SimpleNamespace(
        id=1,
        name="Test Attendant",
        email="test@example.com",
        phone="+123456789",
        role="attendant",
        attendant=None,  # initially no attendant
    )

    # Patch the parent's create method (from CRUDUser) to return our fake user.
    mocker.patch.object(CRUDUser, "create", new=AsyncMock(return_value=fake_user))

    # Patch _create_attendant so that it raises a TypeError.
    mocker.patch.object(
        CRUDAttendant,
        "_create_attendant",
        new=AsyncMock(side_effect=TypeError("Invalid attendant data")),
    )

    # Patch _commit_and_refresh and _finalize_user so they do nothing.
    mocker.patch.object(CRUDAttendant, "_commit_and_refresh", return_value=None)
    mocker.patch.object(CRUDAttendant, "_finalize_user", return_value=None)

    # Ensure that db.rollback is a MagicMock so we can assert it is called.
    db.rollback = MagicMock()

    # Create an instance of CRUDAttendant and set required attributes.
    crud_attendant = CRUDAttendant()
    crud_attendant.crud_team = MagicMock()
    crud_attendant.crud_function = MagicMock()

    # Act & Assert: Calling create() should raise an HTTPException with status 400.
    with pytest.raises(HTTPException) as exc_info:
        await crud_attendant.create(db, obj_in, created_by, user_ip)

    assert exc_info.value.status_code == 400
    assert (
        "Error while creating Attendant: Invalid attendant data"
        in exc_info.value.detail
    )
    db.rollback.assert_called_once()
