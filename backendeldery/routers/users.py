from fastapi import APIRouter, Depends, Body, HTTPException, Request, Header
from sqlalchemy.orm import Session
from backendeldery.schemas import UserCreate, UserSearch
from backendeldery.services.users import UserService
from backendeldery.utils import get_db

router = APIRouter()


@router.post("/users/register/subscriber/")
async def register_subscriber(
        user: UserCreate = Body(
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
    Endpoint para registrar um novo subscriber.
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
        raise HTTPException(status_code=500,
                            detail=f"Error on register subscriber: {str(e)}")


@router.post("/users/search/subscriber/")
async def search_subscriber(
        search_criteria: UserSearch = Body(...,
                                           example={"phone": "+123456789"}),
        db: Session = Depends(get_db),
):
    """
    Endpoint to search for a subscriber by email, phone, or CPF.
    """
    try:
        # Validate search criteria
        criteria = {key: value
                    for key, value in search_criteria.dict().items()
                    if value}
        if len(criteria) != 1:
            raise HTTPException(
                status_code=400,
                detail="Provide exactly one search criteria (email, phone, or cpf)."
            )

        # Perform search
        user = await UserService.search_subscriber(db=db, criteria=criteria)
        if user:
            return {"id": user}
        raise HTTPException(status_code=404, detail="Subscriber not found.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error on searching subscriber: {str(e)}")


@router.get("/users/subscriber/{user_id}")
async def get_subscriber(
        user_id: int,
        db: Session = Depends(get_db),
):
    """
    Endpoint to get subscriber information by user ID.
    """
    try:
        user = await UserService.get_subscriber_by_id(db=db, user_id=user_id)
        if user:
            return user
        raise HTTPException(status_code=404, detail="Subscriber not found.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error retrieving subscriber: {str(e)}")
