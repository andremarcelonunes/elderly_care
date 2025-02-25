# python
from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backendeldery.models import Team, Attendant
from backendeldery.crud.base import CRUDBase


class CRUDTeam(CRUDBase):
    def __init__(self):
        super().__init__(Team)

    def get_by_name(self, db: Session, name: str) -> Team:
        return db.query(self.model).filter(self.model.team_name == name).first()

    def create(self, db: Session, team_name: str, team_site: str, created_by: int, user_ip: str) -> Team:
        team = Team(
            team_name=team_name,
            team_site=team_site,
            created_by=created_by,
            user_ip=user_ip,
            updated_by=None
        )
        db.add(team)
        db.flush()
        db.refresh(team)
        return team

    def update(self, db: Session, team_id: int, update_data: dict, updated_by: int, user_ip: str) -> Team:
        team = db.query(self.model).filter(self.model.team_id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        for field, value in update_data.items():
            setattr(team, field, value)
        team.updated_by = updated_by
        team.user_ip = user_ip
        db.add(team)
        db.commit()
        db.refresh(team)
        return team

    def list_all(self, db: Session) -> List[Team]:
        teams = db.query(self.model).all()
        return teams

    def list_attendants(self, db: Session, team_id: int) -> List[Attendant]:
        """
        Retrieves all attendants associated with the given team.
        """
        team_obj = db.query(self.model).filter(self.model.team_id == team_id).first()
        if not team_obj:
            raise HTTPException(status_code=404, detail="Team not found")
        return team_obj.attendants
