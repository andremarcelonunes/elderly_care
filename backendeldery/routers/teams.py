from fastapi import HTTPException, APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backendeldery.schemas import AttendantTimeResponse
from backendeldery.services.team import TeamService
from backendeldery.utils import get_db_aync

router = APIRouter()


@router.get("/teams/{team_id}/attendants", response_model=list[AttendantTimeResponse])
async def list_team_attendants(
    team_id: int,
    db: AsyncSession = Depends(get_db_aync),
):
    try:
        from backendeldery.services.attendants import AttendantService

        attendants = await AttendantService.list_attendants_by_team(db, team_id)
        if not attendants:
            raise HTTPException(status_code=404, detail="Team not found")

        results = []
        for attendant in attendants:
            user = attendant.user  # One-to-one relationship with User
            results.append(AttendantTimeResponse.from_orm(user))
        return results

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving team attendants: {str(e)}"
        )


@router.get("/teams/by-name/{name}")
async def get_team_by_name(name: str, db: AsyncSession = Depends(get_db_aync)):
    team = await TeamService.get_team_by_name(db, name)
    return {"team_id": team.team_id}
