from unittest.mock import MagicMock, AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backendeldery.crud.team import CRUDTeam
from backendeldery.models import (
    Team,
    Specialty,
)
from backendeldery.services.attendantAssociationService import (
    AttendantAssociationService,
)


@pytest.mark.asyncio
async def test_update_team_associations_no_teams(mocker):
    db_mock = MagicMock(spec=AsyncSession)
    crud_team_mock = MagicMock()
    service = AttendantAssociationService(
        db_mock, user_id=1, updated_by=1, user_ip="127.0.0.1"
    )

    mocker.patch.object(service, "_get_existing_team_ids")
    mocker.patch.object(service, "_get_or_create_teams")
    mocker.patch.object(service, "_create_new_team_associations")

    await service.update_team_associations(None, crud_team_mock)
    await service.update_team_associations([], crud_team_mock)

    service._get_existing_team_ids.assert_not_called()
    service._get_or_create_teams.assert_not_called()
    service._create_new_team_associations.assert_not_called()


@pytest.mark.asyncio
async def test_update_team_associations(mocker):
    db_mock = MagicMock(spec=AsyncSession)
    crud_team_mock = MagicMock()
    service = AttendantAssociationService(
        db_mock, user_id=1, updated_by=1, user_ip="127.0.0.1"
    )

    mocker.patch.object(service, "_get_existing_team_ids", return_value=set())
    mocker.patch.object(
        service,
        "_get_or_create_teams",
        return_value={"Team A": Team(team_id=1, team_name="Team A")},
    )
    mocker.patch.object(service, "_create_new_team_associations")

    await service.update_team_associations(["Team A"], crud_team_mock)

    service._get_existing_team_ids.assert_called_once()
    service._get_or_create_teams.assert_called_once_with(["Team A"], crud_team_mock)
    service._create_new_team_associations.assert_called_once()


@pytest.mark.asyncio
async def test_update_function_association_no_functions(mocker):
    db_mock = MagicMock(spec=AsyncSession)
    crud_function_mock = MagicMock()
    service = AttendantAssociationService(
        db_mock, user_id=1, updated_by=1, user_ip="127.0.0.1"
    )

    result = await service.update_function_association(None, crud_function_mock)
    assert result is None

    result = await service.update_function_association([], crud_function_mock)
    assert result is None


@pytest.mark.asyncio
async def test_update_function_association(mocker):
    db_mock = MagicMock(spec=AsyncSession)
    crud_function_mock = MagicMock()
    service = AttendantAssociationService(
        db_mock, user_id=1, updated_by=1, user_ip="127.0.0.1"
    )

    mocker.patch.object(service, "_get_existing_specialty_ids", return_value=set())
    mocker.patch.object(
        service,
        "_get_or_create_specialties",
        return_value={"Specialty A": Specialty(id=1, name="Specialty A")},
    )
    mocker.patch.object(service, "_create_specialty_associations")

    await service.update_specialty_associations(["Specialty A"])

    service._get_existing_specialty_ids.assert_called_once()
    service._get_or_create_specialties.assert_called_once_with(["Specialty A"])
    service._create_specialty_associations.assert_called_once()


@pytest.mark.asyncio
async def test_update_specialty_associations_no_specialties(mocker):
    db_mock = MagicMock(spec=AsyncSession)
    service = AttendantAssociationService(
        db_mock, user_id=1, updated_by=1, user_ip="127.0.0.1"
    )

    mocker.patch.object(service, "_get_existing_specialty_ids")
    mocker.patch.object(service, "_get_or_create_specialties")
    mocker.patch.object(service, "_create_specialty_associations")

    await service.update_specialty_associations(None)
    await service.update_specialty_associations([])

    service._get_existing_specialty_ids.assert_not_called()
    service._get_or_create_specialties.assert_not_called()
    service._create_specialty_associations.assert_not_called()


@pytest.mark.asyncio
async def test_update_specialty_associations(mocker):
    db_mock = MagicMock(spec=AsyncSession)
    service = AttendantAssociationService(
        db_mock, user_id=1, updated_by=1, user_ip="127.0.0.1"
    )

    mocker.patch.object(service, "_get_existing_specialty_ids", return_value=set())
    mocker.patch.object(
        service,
        "_get_or_create_specialties",
        return_value={"Specialty A": Specialty(id=1, name="Specialty A")},
    )
    mocker.patch.object(service, "_create_specialty_associations")

    await service.update_specialty_associations(["Specialty A"])

    service._get_existing_specialty_ids.assert_called_once()
    service._get_or_create_specialties.assert_called_once_with(["Specialty A"])
    service._create_specialty_associations.assert_called_once()


@pytest.mark.asyncio
async def test_get_existing_team_ids(mocker):
    db_mock = MagicMock(spec=AsyncSession)
    service = AttendantAssociationService(
        db_mock, user_id=1, updated_by=1, user_ip="127.0.0.1"
    )

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [1, 2, 3]
    mock_execute = MagicMock()
    mock_execute.scalars.return_value = mock_scalars

    mocker.patch.object(db_mock, "execute", return_value=mock_execute)

    result = await service._get_existing_team_ids()

    assert result == {1, 2, 3}


@pytest.mark.asyncio
async def test_get_or_create_teams(mocker):
    # Arrange
    db = mocker.AsyncMock()
    user_id = 1
    updated_by = 2
    user_ip = "127.0.0.1"

    service = AttendantAssociationService(db, user_id, updated_by, user_ip)

    # Create mock team and crud_team
    mock_team = mocker.MagicMock()
    mock_team.team_id = 1
    mock_team.team_name = "Team A"

    mock_crud_team = mocker.AsyncMock()
    mock_crud_team.get_by_name_async.return_value = mock_team

    # Act
    result = await service._get_or_create_teams(["Team A"], mock_crud_team)

    # Assert
    mock_crud_team.get_by_name_async.assert_called_once_with(db, "Team A")
    mock_crud_team.create_async.assert_not_called()
    assert "Team A" in result
    assert result["Team A"] == mock_team


@pytest.mark.asyncio
async def test_create_new_team_associations(mocker):
    db_mock = MagicMock(spec=AsyncSession)
    service = AttendantAssociationService(
        db_mock, user_id=1, updated_by=1, user_ip="127.0.0.1"
    )

    # Ensure the Team class accepts the correct attributes
    team_map = {"Team A": Team(team_id=1, team_name="Team A")}
    existing_team_ids = set()

    mocker.patch.object(db_mock, "add_all")

    await service._create_new_team_associations(team_map, existing_team_ids)

    db_mock.add_all.assert_called_once()


@pytest.mark.asyncio
async def test_get_existing_specialty_ids(mocker):
    db_mock = MagicMock(spec=AsyncSession)
    service = AttendantAssociationService(
        db_mock, user_id=1, updated_by=1, user_ip="127.0.0.1"
    )

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [1, 2, 3]
    mocker.patch.object(
        db_mock,
        "execute",
        return_value=MagicMock(scalars=MagicMock(return_value=mock_scalars)),
    )

    result = await service._get_existing_specialty_ids()

    assert result == {1, 2, 3}
    db_mock.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_or_create_specialties(mocker):
    db_mock = MagicMock(spec=AsyncSession)
    service = AttendantAssociationService(
        db_mock, user_id=1, updated_by=1, user_ip="127.0.0.1"
    )

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mocker.patch.object(
        db_mock,
        "execute",
        return_value=MagicMock(scalars=MagicMock(return_value=mock_scalars)),
    )
    mocker.patch.object(db_mock, "flush")

    result = await service._get_or_create_specialties(["Specialty A"])

    assert "Specialty A" in result
    db_mock.execute.assert_called_once()
    db_mock.flush.assert_called_once()


@pytest.mark.asyncio
async def test_create_specialty_associations(mocker):
    db_mock = MagicMock(spec=AsyncSession)
    service = AttendantAssociationService(
        db_mock, user_id=1, updated_by=1, user_ip="127.0.0.1"
    )

    specialty_map = {"Specialty A": Specialty(id=1, name="Specialty A")}
    existing_ids = set()

    mocker.patch.object(db_mock, "add_all")

    await service._create_specialty_associations(
        ["Specialty A"], specialty_map, existing_ids
    )

    db_mock.add_all.assert_called_once()


@pytest.mark.asyncio
async def test_delete_team_relation_success(mocker):
    # Arrange
    db = mocker.AsyncMock()
    attendant_id = 1
    team_id = 2
    user_ip = "192.168.1.1"
    updated_by = 3

    # Mock the association object
    mock_association = mocker.MagicMock()

    # Mock the query result
    mock_result = mocker.MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_association
    db.execute.return_value = mock_result

    # Create service instance with audit information
    service = AttendantAssociationService(
        db=db, user_id=attendant_id, updated_by=updated_by, user_ip=user_ip
    )

    # Act
    result = await service.delete_team_relation(
        db=db, attendant_id=attendant_id, team_id=team_id
    )

    # Assert
    assert result["status"] == "success"
    assert (
        f"Team association between attendant {attendant_id} and team {team_id} deleted successfully"
        in result["message"]
    )
    assert mock_association.updated_by == updated_by
    assert mock_association.user_ip == user_ip
    db.delete.assert_called_once_with(mock_association)
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_creates_new_team_associations(mocker):
    # Arrange
    db_mock = mocker.AsyncMock()
    user_id = 1
    updated_by = 2
    user_ip = "127.0.0.1"

    service = AttendantAssociationService(db_mock, user_id, updated_by, user_ip)

    # Mock existing team IDs
    existing_team_ids = {1}
    mocker.patch.object(
        service, "_get_existing_team_ids", return_value=existing_team_ids
    )

    # Create team objects
    team1 = mocker.MagicMock(team_id=1)
    team2 = mocker.MagicMock(team_id=2)
    team_map = {"Team1": team1, "Team2": team2}

    # Mock get_or_create_teams
    mocker.patch.object(service, "_get_or_create_teams", return_value=team_map)

    # Mock create_new_team_associations
    create_associations_mock = mocker.patch.object(
        service, "_create_new_team_associations"
    )

    crud_team = mocker.MagicMock(spec=CRUDTeam)

    # Act
    await service.update_team_associations(["Team1", "Team2"], crud_team)

    # Assert
    service._get_existing_team_ids.assert_called_once()
    service._get_or_create_teams.assert_called_once_with(["Team1", "Team2"], crud_team)
    create_associations_mock.assert_called_once_with(team_map, existing_team_ids)


@pytest.mark.asyncio
async def test_function_creation_when_not_exists(mocker):
    # Arrange
    mock_db = AsyncMock()

    # Create a result mock that will be returned when execute is awaited
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None

    # Configure execute to return the expected result when awaited
    mock_db.execute = AsyncMock(return_value=mock_result)

    mock_crud_function = MagicMock()
    mock_function = MagicMock()
    # Set up the create method as an AsyncMock
    mock_crud_function.create = AsyncMock(return_value=mock_function)

    service = AttendantAssociationService(
        db=mock_db, user_id=1, updated_by=2, user_ip="127.0.0.1"
    )

    # Act
    result = await service.update_function_association(
        "new_function", mock_crud_function
    )

    # Assert
    mock_db.execute.assert_called_once()
    mock_crud_function.create.assert_called_once_with(
        mock_db, "new_function", "Auto-created function", 2, "127.0.0.1"
    )
    assert result == mock_function


@pytest.mark.asyncio
async def test_delete_team_relation_general_exception(mocker):
    # Arrange
    mock_db = AsyncMock()

    # Mock the database to raise an exception
    mock_db.execute = AsyncMock(side_effect=ValueError("Database error"))

    # Mock the logger to avoid actual logging during test
    mocker.patch("backendeldery.services.attendantAssociationService.logger")
    mocker.patch("backendeldery.services.attendantAssociationService.traceback")

    service = AttendantAssociationService(
        db=mock_db, user_id=1, updated_by=3, user_ip="127.0.0.1"
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.delete_team_relation(mock_db, 1, 2)

    assert exc_info.value.status_code == 500
    assert "Failed to delete team association" in exc_info.value.detail
    mock_db.rollback.assert_called_once()
