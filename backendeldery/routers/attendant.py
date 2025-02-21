from fastapi import APIRouter, Depends, Body, HTTPException, Request, Header
from sqlalchemy.orm import Session
from backendeldery.schemas import UserCreate, UserResponse
from backendeldery.services.attendants import AttendantService
from backendeldery.utils import get_db

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
                        "specialties": ["Cardiology"]
                    }
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