# python
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from backendeldery.models import Team, Attendant
from backendeldery.crud.team import CRUDTeam


@pytest.fixture
def crud():
    return CRUDTeam()


def test_get_by_name(crud):
    db = MagicMock()
    fake_team = Team(
        team_name="UniqueTeam",
        team_site="SiteA",
        created_by=1,
        user_ip="127.0.0.1",
        updated_by=None
    )
    db.query.return_value.filter.return_value.first.return_value = fake_team
    result = crud.get_by_name(db, "UniqueTeam")
    assert result is fake_team
    db.query.assert_called_once_with(Team)


def test_create_team(crud):
    db = MagicMock()
    team = crud.create(db, "TestTeam", "TestSite", 1, "127.0.0.1")
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


def test_update_team(crud):
    db = MagicMock()
    original = Team(
        team_name="OldTeam",
        team_site="OldSite",
        created_by=1,
        user_ip="127.0.0.1",
        updated_by=None
    )
    original.team_id = 10
    db.query.return_value.filter.return_value.first.return_value = original
    update_data = {"team_name": "NewTeam", "team_site": "NewSite"}
    updated = crud.update(db, 10, update_data, 2, "192.168.0.1")
    assert updated.team_name == "NewTeam"
    assert updated.team_site == "NewSite"
    assert updated.updated_by == 2
    assert updated.user_ip == "192.168.0.1"
    db.add.assert_called_with(original)
    db.commit.assert_called_once()
    db.refresh.assert_called_with(original)


def test_list_all_teams(crud):
    db = MagicMock()
    team_list = [
        Team(team_name="TeamA", team_site="SiteA", created_by=1, user_ip="127.0.0.1", updated_by=None),
        Team(team_name="TeamB", team_site="SiteB", created_by=2, user_ip="127.0.0.1", updated_by=None)
    ]
    db.query.return_value.all.return_value = team_list
    result = crud.list_all(db)
    assert result == team_list


def test_list_attendants_found(crud):
    db = MagicMock()
    fake_team = Team(
        team_name="TeamWithAttendants",
        team_site="SiteC",
        created_by=1,
        user_ip="127.0.0.1",
        updated_by=None
    )
    attendant1 = Attendant(user_id=100)
    attendant2 = Attendant(user_id=101)
    fake_team.attendants = [attendant1, attendant2]
    db.query.return_value.filter.return_value.first.return_value = fake_team
    result = crud.list_attendants(db, 10)
    assert result == [attendant1, attendant2]


def test_list_attendants_not_found(crud):
    db = MagicMock()
    # Simulate no matching team found.
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(HTTPException) as exc:
        crud.list_attendants(db, -1)
    assert exc.value.status_code == 404