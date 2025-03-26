from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backendeldery.schemas import (
    UserCreate,
    UserResponse,
    UserSearch,
    UserUpdate,
)
from backendeldery.services.attendantAssociationService import (
    AttendantAssociationService,
)
from backendeldery.services.attendants import AttendantService
from backendeldery.utils import get_db, get_db_aync

router = APIRouter()


@router.post("/attendants/register/")
async def register_attendant(
    user: UserCreate = Body(
        examples=[
            {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+123456789",
                "role": "attendant",
                "password": "Strong@123",
                "active": True,
                "attendant_data": {
                    "cpf": "123.456.789-00",
                    "address": "123 Main St",
                    "neighborhood": "Downtown",
                    "city": "Metropolis",
                    "state": "NY",
                    "code_address": "12345",
                    "birthday": "1980-01-01",
                    "registro_conselho": "123456",
                    "nivel_experiencia": "senior",
                    "formacao": "Medicine",
                    "specialties": ["Cardiology"],
                    "team_names": ["Team A"],
                    "function_names": "Doctor",
                },
            }
        ]
    ),
    db: Session = Depends(get_db),
    request: Request = None,
    x_user_id: int = Header(...),
):
    """
    Endpoint to register a new attendant.
    """
    try:
        client_ip = request.client.host if request else "unknown"
        return await AttendantService.create_attendant(
            db=db,
            user_data=user,
            created_by=x_user_id,
            user_ip=client_ip,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error on register attendant: {str(e)}"
        )


@router.get("/attendants/{attendant_id}")
async def get_attendant(
    attendant_id: int,
    db: Session = Depends(get_db),
):
    """
    Endpoint to get information about an attendant by ID.
    """
    try:
        attendant = await AttendantService.get_attendant_by_id(db=db, id=attendant_id)
        if attendant:
            return attendant
        raise HTTPException(status_code=404, detail="Attendant not found.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving attendant: {str(e)}"
        )


@router.put("/attendants/{user_id}", response_model=UserResponse)
async def update_attendant(
    user_id: int,
    user_update: UserUpdate = Body(
        example={
            "email": "new.email@example.com",
            "phone": "+123456789",
            "active": True,
            "attendant_data": {
                "address": "456 New St",
                "neighborhood": "Uptown",
                "city": "New City",
                "state": "NC",
                "code_address": "67890",
                "registro_conselho": "RJ-123456",
                "nivel_experiencia": "senior",
                "formacao": "Nursing",
                "specialties": ["Pediatrics"],
                "team_names": ["Team B"],
                "function_names": "Nurse",
            },
        }
    ),
    db: AsyncSession = Depends(get_db_aync),
    request: Request = None,
    x_user_id: int = Header(...),
):
    """
    Endpoint to update an existing Attendant. Inform only the fields you want to update.
    """
    try:
        client_ip = request.client.host if request else "unknown"
        updated_user = await AttendantService.update(
            db=db,
            user_id=user_id,
            user_update=user_update,
            user_ip=client_ip,
            updated_by=x_user_id,
        )
        return updated_user
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error on update Attendant: {str(e)}"
        )


@router.delete("/attendants/team/association/")
async def delete_team_association(
    attendant_id: int,
    team_id: int,
    db: AsyncSession = Depends(get_db_aync),
    request: Request = None,
    x_user_id: int = Header(...),
):
    try:
        client_ip = request.client.host if request else "unknown"

        # Create service instance - use attendant_id as user_id parameter
        service = AttendantAssociationService(
            db=db, user_id=attendant_id, updated_by=x_user_id, user_ip=client_ip
        )

        # Call the instance method
        return await service.delete_team_relation(
            db, attendant_id, team_id, user_ip=client_ip, updated_by=x_user_id
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting team association: {str(e)}"
        )


@router.get(
    "/attendants/{attendant_id}/clients",
    response_model=list[UserResponse],
    response_model_exclude_none=True,
)
async def get_clients_for_attendant(
    attendant_id: int, db: AsyncSession = Depends(get_db_aync)
):
    clients = await AttendantService.get_clients_for_attendant(db, attendant_id)
    if not clients:
        raise HTTPException(
            status_code=404, detail="No clients found for the attendant"
        )
    # Now each client is a plain dict that matches the expected schema.
    return [UserResponse.parse_obj(client) for client in clients]


@router.post("/attendant/search/")
async def search_attendant(
    search_criteria: UserSearch = Body(..., example={"phone": "+123456789"}),
    db: Session = Depends(get_db_aync),
):
    """
    Endpoint to search all attendants by email, phone, or CPF. Only one
    criteria is allowed. Use only one of the fields in the search_criteria.
    """
    try:
        # Validate search criteria
        criteria = {
            key: value for key, value in search_criteria.dict().items() if value
        }
        if len(criteria) != 1:
            raise HTTPException(
                status_code=400,
                detail="Provide exactly one search criteria (email, phone, or cpf).",
            )

        # Perform search
        user = await AttendantService.search_attendant(db=db, criteria=criteria)
        if user:
            return {"id": user}
        raise HTTPException(status_code=404, detail="Attendant not found.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error on searching attendant: {str(e)}"
        )
