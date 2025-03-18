import pytest


@pytest.mark.asyncio
async def test_returns_team_when_valid_name(mocker):
    # Arrange
    mock_db = mocker.AsyncMock()
    mock_team = mocker.Mock()
    mock_team.team_name = "Test Team"

    # Mock the database query result chain
    mock_scalars_result = mocker.Mock()
    mock_scalars_result.first.return_value = mock_team

    mock_result = mocker.Mock()
    mock_result.scalars.return_value = mock_scalars_result

    # Configure the AsyncMock to return our mock_result when awaited
    async def mock_execute(*args, **kwargs):
        return mock_result

    mock_db.execute.side_effect = mock_execute

    from backendeldery.services.team import TeamService

    # Act
    result = await TeamService.get_team_by_name(mock_db, "Test Team")

    # Assert
    assert result == mock_team
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_raises_404_when_team_not_found(mocker):
    # Arrange
    mock_db = mocker.AsyncMock()
    team_name = "Non-existent Team"

    # Mock the database query result chain
    mock_scalars_result = mocker.Mock()
    mock_scalars_result.first.return_value = None  # Team not found

    mock_result = mocker.Mock()
    mock_result.scalars.return_value = mock_scalars_result

    # Configure the AsyncMock to return our mock_result when awaited
    async def mock_execute(*args, **kwargs):
        return mock_result

    mock_db.execute.side_effect = mock_execute

    from backendeldery.services.team import TeamService
    from fastapi import HTTPException

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await TeamService.get_team_by_name(mock_db, team_name)

    # Verify exception details
    assert exc_info.value.status_code == 404
    assert "Team not found" in str(exc_info.value.detail)
