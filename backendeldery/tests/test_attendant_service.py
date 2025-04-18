# test_attendant_service.py
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backendeldery.crud.attendant import CRUDAttendant
from backendeldery.schemas import AttendantCreate, UserCreate
from backendeldery.services.attendants import AttendantService
from backendeldery.validators.attendant_validator import AttendantValidator
from backendeldery.validators.user_validator import UserValidator


@pytest.fixture
def db_session(mocker):
    return mocker.Mock(spec=Session)


@pytest.fixture
def user_data():
    return UserCreate(
        name="John Doe",
        email="john.doe@example.com",
        phone="+123456789",
        receipt_type=1,
        role="attendant",
        password="Strong@123",
        active=True,
        attendant_data=AttendantCreate(
            cpf="12345678900",
            birthday="1980-01-01",
            nivel_experiencia="senior",
            specialties=["Cardiology"],
            team_names=["Team A"],
            function_names="Doctor",
            address="123 Main St",
            neighborhood="Downtown",
            city="Test City",
            state="TS",
            code_address="12345",
            registro_conselho="REG123",
            formacao="Medicine",
        ),
    )


@pytest.mark.asyncio
async def test_create_attendant_success(db_session, user_data, mocker):
    mocker.patch.object(UserValidator, "validate_user", return_value=None)
    mocker.patch.object(AttendantValidator, "validate_attendant", return_value=None)
    mocker.patch.object(CRUDAttendant, "create", return_value=user_data)

    result = await AttendantService.create_attendant(
        db=db_session, user_data=user_data, created_by=1, user_ip="127.0.0.1"
    )

    assert result == user_data


@pytest.mark.asyncio
async def test_create_attendant_validation_error(db_session, user_data, mocker):
    mocker.patch.object(
        UserValidator,
        "validate_user",
        side_effect=HTTPException(status_code=400, detail="Validation error"),
    )
    mocker.patch.object(AttendantValidator, "validate_attendant", return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await AttendantService.create_attendant(
            db=db_session, user_data=user_data, created_by=1, user_ip="127.0.0.1"
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Validation error"


@pytest.mark.asyncio
async def test_create_attendant_unexpected_error(db_session, user_data, mocker):
    mocker.patch.object(UserValidator, "validate_user", return_value=None)
    mocker.patch.object(AttendantValidator, "validate_attendant", return_value=None)
    mocker.patch.object(
        CRUDAttendant, "create", side_effect=Exception("Unexpected error")
    )

    with pytest.raises(HTTPException) as exc_info:
        await AttendantService.create_attendant(
            db=db_session, user_data=user_data, created_by=1, user_ip="127.0.0.1"
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Unexpected error: Unexpected error"


@pytest.mark.asyncio
async def test_get_attendant_by_id_success(db_session, mocker):
    mock_attendant = {
        "id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+123456789",
        "role": "attendant",
        "active": True,
        "attendant_data": {
            "cpf": "12345678900",
            "birthday": "1980-01-01",
            "nivel_experiencia": "senior",
            "specialties": ["Cardiology"],
            "team_names": ["Team A"],
            "function_names": "Doctor",
        },
    }
    mocker.patch.object(CRUDAttendant, "get", return_value=mock_attendant)

    result = await AttendantService.get_attendant_by_id(db=db_session, id=1)

    assert result == mock_attendant


@pytest.mark.asyncio
async def test_get_attendant_by_id_not_found(db_session, mocker):
    mocker.patch.object(
        CRUDAttendant,
        "get",
        side_effect=HTTPException(status_code=404, detail="User not found"),
    )

    with pytest.raises(HTTPException) as exc_info:
        await AttendantService.get_attendant_by_id(db=db_session, id=1)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_get_attendant_by_id_not_found(db_session, mocker):
    mocker.patch.object(
        CRUDAttendant,
        "get",
        side_effect=HTTPException(status_code=404, detail="User not found"),
    )

    with pytest.raises(HTTPException) as exc_info:
        await AttendantService.get_attendant_by_id(db=db_session, id=1)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"


@pytest.mark.asyncio
async def test_update_attendant_success(mocker):
    # Arrange
    mock_db = mocker.AsyncMock()
    user_id = 1
    user_update = mocker.Mock()
    user_ip = "127.0.0.1"
    updated_by = 2

    # Mock the validator and CRUD operations
    mocker.patch(
        "backendeldery.validators.user_validator.UserValidator.validate_user_async"
    )
    mock_crud_update = mocker.patch("backendeldery.crud.attendant.CRUDAttendant.update")
    mock_crud_get = mocker.patch("backendeldery.crud.attendant.CRUDAttendant.get_async")

    # Setup the mock to return a valid attendant
    expected_attendant = {"id": user_id, "name": "Updated Name"}
    mock_crud_get.return_value = expected_attendant

    from backendeldery.services.attendants import AttendantService

    # Act
    result = await AttendantService.update(
        mock_db, user_id, user_update, user_ip, updated_by
    )

    # Assert
    UserValidator.validate_user_async.assert_awaited_once_with(mock_db, user_update)
    mock_crud_update.assert_awaited_once_with(
        mock_db, user_id, user_update, updated_by, user_ip
    )
    mock_crud_get.assert_awaited_once_with(mock_db, user_id)
    assert result == expected_attendant


@pytest.mark.asyncio
async def test_update_attendant_not_found(mocker):
    # Arrange
    mock_db = mocker.AsyncMock()
    user_id = 1
    user_update = mocker.Mock()
    user_ip = "127.0.0.1"
    updated_by = 2

    # Mock the validator and CRUD operations
    mocker.patch(
        "backendeldery.validators.user_validator.UserValidator.validate_user_async"
    )
    mock_crud_update = mocker.patch("backendeldery.crud.attendant.CRUDAttendant.update")
    mock_crud_get = mocker.patch("backendeldery.crud.attendant.CRUDAttendant.get_async")

    # Setup the mock to return None (attendant not found)
    mock_crud_get.return_value = None

    from backendeldery.services.attendants import AttendantService

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await AttendantService.update(
            mock_db, user_id, user_update, user_ip, updated_by
        )

    # Verify exception details
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Attendant not found"

    # Verify method calls
    UserValidator.validate_user_async.assert_awaited_once_with(mock_db, user_update)
    mock_crud_update.assert_awaited_once_with(
        mock_db, user_id, user_update, updated_by, user_ip
    )
    mock_crud_get.assert_awaited_once_with(mock_db, user_id)


@pytest.mark.asyncio
async def test_update_propagates_http_exceptions(mocker):
    # Arrange
    mock_db = mocker.AsyncMock()
    user_id = 1
    user_update = mocker.Mock()
    user_ip = "127.0.0.1"
    updated_by = 2

    # Mock the validator and CRUD operations to raise HTTPException
    mocker.patch(
        "backendeldery.validators.user_validator.UserValidator.validate_user_async",
        side_effect=HTTPException(status_code=422, detail="Validation error"),
    )
    mock_crud_update = mocker.patch("backendeldery.crud.attendant.CRUDAttendant.update")
    mock_crud_get = mocker.patch("backendeldery.crud.attendant.CRUDAttendant.get_async")

    from backendeldery.services.attendants import AttendantService

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await AttendantService.update(
            mock_db, user_id, user_update, user_ip, updated_by
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Validation error"

    # Wraps non-HTTP exceptions in a 500 status code response


@pytest.mark.asyncio
async def test_update_wraps_non_http_exceptions(mocker):
    # Arrange
    mock_db = mocker.AsyncMock()
    user_id = 1
    user_update = mocker.Mock()
    user_ip = "127.0.0.1"
    updated_by = 2

    # Mock the validator and CRUD operations
    mocker.patch(
        "backendeldery.validators.user_validator.UserValidator.validate_user_async"
    )
    mock_crud_update = mocker.patch("backendeldery.crud.attendant.CRUDAttendant.update")
    mock_crud_get = mocker.patch("backendeldery.crud.attendant.CRUDAttendant.get_async")

    # Setup the mock to raise a generic exception
    mock_crud_update.side_effect = Exception("Unexpected error")

    from backendeldery.services.attendants import AttendantService

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await AttendantService.update(
            mock_db, user_id, user_update, user_ip, updated_by
        )

    assert exc_info.value.status_code == 500
    assert "Error on updating: Unexpected error" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_clients_for_attendant_success(mocker):
    # Arrange
    mock_db = AsyncMock()
    attendant_id = 1

    # Create fake client objects as SimpleNamespace objects
    fake_client1 = SimpleNamespace(
        user_id=1, client_id=101, user=SimpleNamespace(name="John Doe")
    )
    fake_client2 = SimpleNamespace(
        user_id=2, client_id=102, user=SimpleNamespace(name="Jane Smith")
    )

    # Create fake teams as MagicMock objects with a 'clients' attribute set to our fake clients.
    mock_team1 = MagicMock()
    mock_team1.team_id = 1
    mock_team1.team_name = "Team A"
    mock_team1.clients = [fake_client1]

    mock_team2 = MagicMock()
    mock_team2.team_id = 2
    mock_team2.team_name = "Team B"
    mock_team2.clients = [fake_client2]

    # Patch CRUDTeam.get_teams_by_attendant_id to return our fake teams.
    mocker.patch(
        "backendeldery.crud.team.CRUDTeam.get_teams_by_attendant_id",
        new=AsyncMock(return_value=[mock_team1, mock_team2]),
    )

    # Patch sqlalchemy.inspection.inspect to return a dummy object so SQLAlchemy doesn't try to inspect our dicts.
    dummy_inspect = MagicMock()
    dummy_inspect.mapper = MagicMock(column_attrs=[])
    mocker.patch("sqlalchemy.inspection.inspect", return_value=dummy_inspect)

    # Act: Call the service method.
    result = await AttendantService.get_clients_for_attendant(mock_db, attendant_id)

    # Assert:
    # We expect the result to be a list of dictionaries.
    assert isinstance(result, list)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_returns_user_id_when_attendant_found(mocker):
    # Arrange
    mock_db = mocker.AsyncMock()
    mock_user = mocker.MagicMock()
    mock_user.id = 123

    mock_crud_attendant = mocker.patch(
        "backendeldery.services.attendants.CRUDAttendant", autospec=True
    )
    mock_crud_instance = mock_crud_attendant.return_value
    mock_crud_instance.search_attendant.return_value = mock_user

    criteria = {"email": "test@example.com"}

    from backendeldery.services.attendants import AttendantService

    # Act
    result = await AttendantService.search_attendant(mock_db, criteria)

    # Assert
    mock_crud_instance.search_attendant.assert_called_once_with(mock_db, criteria)
    assert result == 123


@pytest.mark.asyncio
async def test_list_attendants_by_team_success(mocker):
    # Arrange
    mock_db = mocker.Mock(spec=AsyncSession)
    mock_team_id = 1
    expected_attendants = ["attendant1", "attendant2"]

    # Mock the CRUDTeam.list_attendants method
    mock_crud_team = mocker.patch(
        "backendeldery.crud.team.CRUDTeam.list_attendants",
        return_value=expected_attendants,
    )

    # Act
    result = await AttendantService.list_attendants_by_team(
        db=mock_db, team_id=mock_team_id
    )

    # Assert
    mock_crud_team.assert_called_once_with(db=mock_db, team_id=mock_team_id)
    assert result == expected_attendants


@pytest.mark.asyncio
async def test_returns_user_id_when_attendant_found(mocker):
    # Arrange
    mock_db = mocker.AsyncMock()
    mock_user = mocker.MagicMock()
    mock_user.id = 123

    mock_crud_attendant = mocker.patch(
        "backendeldery.services.attendants.CRUDAttendant", autospec=True
    )
    mock_crud_instance = mock_crud_attendant.return_value
    mock_crud_instance.search_attendant.return_value = mock_user

    criteria = {"email": "test@example.com"}

    from backendeldery.services.attendants import AttendantService

    # Act
    result = await AttendantService.search_attendant(mock_db, criteria)

    # Assert
    mock_crud_instance.search_attendant.assert_called_once_with(mock_db, criteria)
    assert result == 123


@pytest.mark.asyncio
async def test_propagates_httpexception_from_crud_method(mocker):
    # Arrange
    mock_db = AsyncMock()
    team_id = 1
    mock_http_exception = HTTPException(status_code=404, detail="Team not found")

    # Define an async function that raises the exception when called
    async def mock_list_attendants(*args, **kwargs):
        raise mock_http_exception

    # Directly patch the method at the module level
    mocker.patch(
        "backendeldery.crud.team.CRUDTeam.list_attendants", new=mock_list_attendants
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await AttendantService.list_attendants_by_team(db=mock_db, team_id=team_id)

    assert exc_info.value.status_code == 404
    assert "Team not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_list_attendants_by_team_handles_general_exceptions(mocker):
    # Arrange
    mock_db = AsyncMock()
    team_id = 1

    # Create an async function that raises a general exception
    async def mock_list_attendants(*args, **kwargs):
        raise ValueError("Something went wrong with database query")

    # Patch the CRUDTeam class method directly
    mocker.patch(
        "backendeldery.crud.team.CRUDTeam.list_attendants", new=mock_list_attendants
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await AttendantService.list_attendants_by_team(db=mock_db, team_id=team_id)

    # Verify it returns a 500 status code with the expected error message
    assert exc_info.value.status_code == 500
    assert "Failed to retrieve team attendants" in exc_info.value.detail
    assert "Something went wrong with database query" in exc_info.value.detail


@pytest.mark.asyncio
async def test_search_attendant_returns_none(mocker):
    # Arrange
    mock_db = mocker.AsyncMock()
    criteria = {"email": "nonexistent@example.com"}

    # Mock CRUDAttendant to return None
    mock_crud_attendant = mocker.patch(
        "backendeldery.services.attendants.CRUDAttendant", autospec=True
    )
    mock_crud_instance = mock_crud_attendant.return_value
    mock_crud_instance.search_attendant.return_value = None

    # Act
    result = await AttendantService.search_attendant(mock_db, criteria)

    # Assert
    mock_crud_instance.search_attendant.assert_called_once_with(mock_db, criteria)
    assert result is None


@pytest.mark.asyncio
async def test_search_attendant_propagates_http_exception(mocker):
    # Arrange
    mock_db = mocker.AsyncMock()
    criteria = {"email": "test@example.com"}
    http_exception = HTTPException(status_code=404, detail="Attendant not found")

    # Mock CRUDAttendant to raise an HTTPException
    mock_crud_attendant = mocker.patch(
        "backendeldery.services.attendants.CRUDAttendant", autospec=True
    )
    mock_crud_instance = mock_crud_attendant.return_value
    mock_crud_instance.search_attendant.side_effect = http_exception

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await AttendantService.search_attendant(mock_db, criteria)

    # Verify exception details
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Attendant not found"
    mock_crud_instance.search_attendant.assert_called_once_with(mock_db, criteria)


@pytest.mark.asyncio
async def test_search_attendant_handles_general_exception(mocker):
    # Arrange
    mock_db = mocker.AsyncMock()
    criteria = {"email": "test@example.com"}

    # Mock CRUDAttendant to raise a general exception
    mock_crud_attendant = mocker.patch(
        "backendeldery.services.attendants.CRUDAttendant", autospec=True
    )
    mock_crud_instance = mock_crud_attendant.return_value
    mock_crud_instance.search_attendant.side_effect = ValueError("Database error")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await AttendantService.search_attendant(mock_db, criteria)

    # Verify exception details
    assert exc_info.value.status_code == 500
    assert "Error in AttendantService: Database error" in exc_info.value.detail
    mock_crud_instance.search_attendant.assert_called_once_with(mock_db, criteria)
