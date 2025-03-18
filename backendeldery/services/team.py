from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backendeldery.crud.team import CRUDTeam


class TeamService:
    @staticmethod
    async def get_team_by_name(db: AsyncSession, name: str):
        crud_team = CRUDTeam()
        team = await crud_team.get_by_name_async(db, name)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        return team
