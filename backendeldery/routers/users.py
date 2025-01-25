from fastapi import APIRouter, Depends, Body, HTTPException, Request, Header
from sqlalchemy.orm import Session
from backendeldery.schemas import UserCreate, SubscriberCreate, ContactCreate, AttendantCreate
from backendeldery.services.users import UserService
from backendeldery.crud.users import crud_specialized_user
from fastapi.logger import logger
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
    x_user_id: int = Header(...),  # Header obrigatório para obter o user_id
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
        logger.error(f"Erro HTTP: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        raise HTTPException(status_code=500, detail="Erro ao registrar cliente.")

@router.post("/users/register/contact/")
def register_contact(
    user: UserCreate = Body(
        ...,  # Torna o campo obrigatório
        examples=[
            {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+123456789",
                "role": "contact",
                "password": "Strong@123",
                "client_ids": [1, 2, 3]
            }
        ]
    ),
    db: Session = Depends(get_db),
    request: Request = None,
    x_user_id: int = Header(...),  # Header obrigatório para obter o user_id
):
    """
    Endpoint para registrar um novo contato.
    """
    try:
        # Captura o IP do cliente
        client_ip = request.client.host if request else "unknown"

        # Cria o contato e as relações com os clientes
        result = crud_specialized_user.create_contact(
            db=db,
            user_data=user,
            client_ids=user.client_ids
        )

        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/register/attendant/")
def register_attendant(
    user: UserCreate = Body(
        ...,  # Torna o campo obrigatório
        examples=[
            {
                "name": "Jane Doe",
                "email": "jane.doe@example.com",
                "phone": "+987654321",
                "role": "attendant",
                "password": "Strong@123"
            }
        ]
    ),
    attendant_data: AttendantCreate = Body(
        ...,  # Torna o campo obrigatório
        examples=[
            {
                "function_id": 1,
                "team_id": 2
            }
        ]
    ),
    db: Session = Depends(get_db),
    request: Request = None,
    x_user_id: int = Header(...),  # Header obrigatório para obter o user_id
):
    """
    Endpoint para registrar um novo atendente.
    """
    try:
        # Captura o IP do cliente
        client_ip = request.client.host if request else "unknown"

        # Cria o atendente e o usuário associado
        result = crud_specialized_user.create_attendant(
            db=db,
            user_data=user,
            attendant_data=attendant_data,
            created_by=x_user_id,
            user_ip=client_ip
        )

        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))