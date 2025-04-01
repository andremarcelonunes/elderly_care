# python
from unittest.mock import MagicMock, AsyncMock

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backendeldery.crud.team import CRUDTeam
from backendeldery.models import Team, Attendant, AttendantTeam


@pytest.fixture
def crud():
    return CRUDTeam()


@pytest.mark.asyncio
async def test_get_by_name(crud):
    db = MagicMock()

    fake_team = Team(
        team_name="UniqueTeam",
        team_site="SiteA",
        created_by=1,
        user_ip="127.0.0.1",
        updated_by=None,
    )

    # Mock the result chain
    mock_first = MagicMock(return_value=fake_team)
    mock_filter = MagicMock()
    mock_filter.first = mock_first

    db.query.return_value.filter.return_value = mock_filter

    result = await crud.get_by_name(db, "UniqueTeam")
    assert result.team_name == fake_team.team_name
    assert result.team_site == fake_team.team_site
    assert result.created_by == fake_team.created_by
    assert result.user_ip == fake_team.user_ip
    assert result.updated_by == fake_team.updated_by
    db.query.return_value.filter.assert_called_once()


@pytest.mark.asyncio
async def test_create_team(crud):
    db = MagicMock()
    team = await crud.create(db, "TestTeam", "TestSite", 1, "127.0.0.1")
    # Verify that add, flush and refresh were called with the new team instance.
    db.add.assert_called_with(team)
    db.flush.assert_called_once()
    db.refresh.assert_called_with(team)
    # Verify that the new team's fields are set.
    assert team.team_name == "TestTeam"
    assert team.team_site == "TestSite"
    assert team.created_by == 1
    assert team.user_ip == "127.0.0.1"
    assert team.updated_by is None


@pytest.mark.asyncio
async def test_update_team(crud):
    db = MagicMock()
    original = Team(
        team_name="OldTeam",
        team_site="OldSite",
        created_by=1,
        user_ip="127.0.0.1",
        updated_by=None,
    )
    original.team_id = 10
    db.query.return_value.filter.return_value.first.return_value = original
    update_data = {"team_name": "NewTeam", "team_site": "NewSite"}
    updated = await crud.update(db, 10, update_data, 2, "192.168.0.1")
    assert updated.team_name == "NewTeam"
    assert updated.team_site == "NewSite"
    assert updated.updated_by == 2
    assert updated.user_ip == "192.168.0.1"
    db.add.assert_called_with(original)
    db.commit.assert_called_once()
    db.refresh.assert_called_with(original)


@pytest.mark.asyncio
async def test_list_all_teams(crud):
    db = MagicMock()
    team_list = [
        Team(
            team_name="TeamA",
            team_site="SiteA",
            created_by=1,
            user_ip="127.0.0.1",
            updated_by=None,
        ),
        Team(
            team_name="TeamB",
            team_site="SiteB",
            created_by=2,
            user_ip="127.0.0.1",
            updated_by=None,
        ),
    ]
    db.query.return_value.all.return_value = team_list
    result = await crud.list_all(db)
    assert result == team_list


@pytest.mark.asyncio
async def test_list_attendants_found(crud):
    db = AsyncMock()
    fake_team = Team(
        team_name="TeamWithAttendants",
        team_site="SiteC",
        created_by=1,
        user_ip="127.0.0.1",
        updated_by=None,
    )
    fake_team.team_id = 10
    attendant1 = Attendant()
    attendant1.user_id = 100
    attendant2 = Attendant()
    attendant2.user_id = 101
    attendant_team1 = AttendantTeam(
        attendant_id=attendant1.user_id, team_id=fake_team.team_id
    )
    attendant_team1.attendant = attendant1  # Link the attendant
    attendant_team2 = AttendantTeam(
        attendant_id=attendant2.user_id, team_id=fake_team.team_id
    )
    attendant_team2.attendant = attendant2  # Link the attendant
    fake_team.attendant_associations = [attendant_team1, attendant_team2]
    result_mock = MagicMock()
    result_mock.scalars.return_value.first = MagicMock(return_value=fake_team)
    db.execute = AsyncMock(return_value=result_mock)
    result = await crud.list_attendants(db, 10)
    assert result == [attendant1, attendant2]


@pytest.mark.asyncio
async def test_list_attendants_not_found(crud):
    db = AsyncMock()
    # Simulate no matching team found.
    result_mock = MagicMock()
    result_mock.scalars.return_value.first = MagicMock(return_value=None)
    db.execute = AsyncMock(return_value=result_mock)

    with pytest.raises(HTTPException) as exc:
        await crud.list_attendants(db, -1)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_returns_team_when_name_exists(mocker):
    # Arrange
    db = mocker.AsyncMock()
    team_name = "Test Team"
    mock_team = Team(
        team_id=1, team_name=team_name, team_site="Test Site", created_by=1
    )

    # Mock the database execution and result
    mock_result = mocker.MagicMock()
    mock_scalars = mocker.MagicMock()
    mock_scalars.first.return_value = mock_team
    mock_result.scalars.return_value = mock_scalars
    db.execute.return_value = mock_result

    # Create the CRUD object
    from backendeldery.crud.team import CRUDTeam

    team_crud = CRUDTeam()

    # Act
    result = await team_crud.get_by_name_async(db, team_name)

    # Assert
    assert result == mock_team
    assert result.team_name == team_name
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_team_with_valid_parameters(mocker):
    # Arrange
    db = mocker.AsyncMock(spec=AsyncSession)
    team_crud = CRUDTeam()
    team_name = "Test Team"
    team_site = "Test Site"
    created_by = 1
    user_ip = "127.0.0.1"

    # Act
    result = await team_crud.create_async(
        db=db,
        team_name=team_name,
        team_site=team_site,
        created_by=created_by,
        user_ip=user_ip,
    )

    # Assert
    assert db.add.called
    assert db.flush.called
    assert db.refresh.called
    assert result.team_name == team_name
    assert result.team_site == team_site
    assert result.created_by == created_by
    assert result.user_ip == user_ip


@pytest.mark.asyncio
async def test_update_nonexistent_team_raises_404(mocker):
    # Arrange
    from fastapi import HTTPException
    import pytest

    # Create mock db session
    mock_db = mocker.MagicMock()

    # Setup mock query result to return None (team not found)
    mock_query = mocker.MagicMock()
    mock_filter = mocker.MagicMock()
    mock_first = mocker.MagicMock(return_value=None)

    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first.return_value = mock_first.return_value

    # Create test data
    update_data = {"team_name": "New Team Name", "team_site": "New Site"}
    updated_by = 2
    user_ip = "192.168.1.1"

    # Initialize CRUD object
    crud = CRUDTeam()

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await crud.update(
            db=mock_db,
            team_id=999,  # Non-existent team ID
            update_data=update_data,
            updated_by=updated_by,
            user_ip=user_ip,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Team not found"
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
    mock_db.refresh.assert_not_called()


@pytest.mark.asyncio
async def test_returns_teams_for_valid_attendant_id(mocker):
    # Arrange
    mock_db = mocker.AsyncMock()
    mock_result = mocker.MagicMock()
    mock_scalars = mocker.MagicMock()

    # Setup the mock chain
    mock_db.execute.return_value = mock_result
    mock_result.scalars.return_value = mock_scalars

    # Create test data
    attendant_id = 1
    expected_teams = [
        Team(team_id=1, team_name="Team A", team_site="Site A", created_by=1),
        Team(team_id=2, team_name="Team B", team_site="Site B", created_by=1),
    ]
    mock_scalars.all.return_value = expected_teams

    # Create instance of the class containing the method
    team_crud = CRUDTeam()

    # Act
    result = await team_crud.get_teams_by_attendant_id(mock_db, attendant_id)

    # Assert
    mock_db.execute.assert_called_once()
    assert result == expected_teams
    assert len(result) == 2
    assert result[0].team_name == "Team A"
    assert result[1].team_name == "Team B"
