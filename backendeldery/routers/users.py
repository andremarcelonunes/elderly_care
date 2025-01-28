from fastapi import APIRouter, Depends, Body, HTTPException, Request, Header
from sqlalchemy.orm import Session
from backendeldery.schemas import UserCreate
from backendeldery.services.users import UserService
from backendeldery.utils import get_db


router = APIRouter()


@router.post("/users/register/subscriber/")
async def register_subscriber(
    user: UserCreate = Body(
        ...,  # Torna o campo obrigatório
        examples=[
            {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+123456789",
                "role": "subscriber",
                "password": "Strong@123",
                "active": True,
                "client_data": {
                    "cpf": "123.456.789-00",
                    "birthday": "1990-01-01",
                    "address": "123 Main St",
                    "city": "Metropolis",
                    "neighborhood": "Downtown",
                    "code_address": "12345",
                    "state": "NY"
                }
            }
        ]
    ),
    db: Session = Depends(get_db),
    request: Request = None,
    x_user_id: int = Header(...),
):
    """
    Endpoint para registrar um novo cliente.
    """
    try:
        client_ip = request.client.host if request else "unknown"
        return await UserService.register_client(
            db=db,
            user_data=user,
            created_by=x_user_id,
            user_ip=client_ip,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro registrar subscriber: {str(e)}")
