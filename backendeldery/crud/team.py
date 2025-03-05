# python
from typing import List

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backendeldery.crud.base import CRUDBase
from backendeldery.models import Team


class CRUDTeam(CRUDBase):
    def __init__(self):
        super().__init__(Team)

    async def get_by_name(self, db: Session, name: str) -> Team:
        return db.query(self.model).filter(self.model.team_name == name).first()

    async def get_by_name_async(self, db: AsyncSession, name: str) -> Team:
        result = await db.execute(
            select(self.model).filter(self.model.team_name == name)
        )
        return result.scalars().first()

    async def create(
        self, db: Session, team_name: str, team_site: str, created_by: int, user_ip: str
    ) -> Team:
        team = Team(
            team_name=team_name,
            team_site=team_site,
            created_by=created_by,
            user_ip=user_ip,
            updated_by=None,
        )
        db.add(team)
        db.flush()
        db.refresh(team)
        return team

    async def create_async(
        self,
        db: AsyncSession,
        team_name: str,
        team_site: str,
        created_by: int,
        user_ip: str,
    ) -> Team:
        team = Team(
            team_name=team_name,
            team_site=team_site,
            created_by=created_by,
            user_ip=user_ip,
        )
        db.add(team)
        # Await flush and refresh so that team_id is assigned.
        await db.flush()
        await db.refresh(team)
        return team

    async def update(
        self,
        db: Session,
        team_id: int,
        update_data: dict,
        updated_by: int,
        user_ip: str,
    ) -> Team:
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

    async def list_all(self, db: Session) -> List[Team]:
        teams = db.query(self.model).all()
        return teams

    async def list_attendants(self, db: Session, team_id: int):
        team = db.query(Team).filter(Team.team_id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        return [assoc.attendant for assoc in team.attendant_associations]
