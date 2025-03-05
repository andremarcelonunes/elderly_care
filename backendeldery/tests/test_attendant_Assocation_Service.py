from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

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
    db_mock = MagicMock(spec=AsyncSession)
    crud_team_mock = MagicMock()
    service = AttendantAssociationService(
        db_mock, user_id=1, updated_by=1, user_ip="127.0.0.1"
    )

    async def mock_get_by_name_async(db, name):
        return None

    async def mock_create(db, team_name, team_site, created_by, user_ip):
        return Team(team_id=1, team_name=team_name)

    mocker.patch.object(
        crud_team_mock, "get_by_name_async", side_effect=mock_get_by_name_async
    )
    mocker.patch.object(crud_team_mock, "create", side_effect=mock_create)

    result = await service._get_or_create_teams(["Team A"], crud_team_mock)

    expected_team = Team(team_id=1, team_name="Team A")
    assert result["Team A"].team_id == expected_team.team_id
    assert result["Team A"].team_name == expected_team.team_name


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
