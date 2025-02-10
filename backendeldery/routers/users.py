from fastapi import APIRouter, Depends, Body, HTTPException, Request, Header
from typing import List
from sqlalchemy.orm import Session
from backendeldery.schemas import UserCreate, UserSearch, UserUpdate, UserResponse, AssistedCreate, AssistedResponse
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
                    "state": "NY",
                },
            }
        ]
    ),
    db: Session = Depends(get_db),
    request: Request = None,
    x_user_id: int = Header(...),
):
    """
    Endpoint to register a new subscriber.
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
        raise HTTPException(
            status_code=500, detail=f"Error on register subscriber: {str(e)}"
        )


@router.post("/users/search/subscriber/")
async def search_subscriber(
    search_criteria: UserSearch = Body(..., example={"phone": "+123456789"}),
    db: Session = Depends(get_db),
):
    """
    Endpoint to search for a subscriber by email, phone, or CPF.
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
        user = await UserService.search_subscriber(db=db, criteria=criteria)
        if user:
            return {"id": user}
        raise HTTPException(status_code=404, detail="Subscriber not found.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error on searching subscriber: {str(e)}"
        )


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
        raise HTTPException(
            status_code=500, detail=f"Error retrieving subscriber: {str(e)}"
        )


@router.put("/users/subscribers/{user_id}", response_model=UserResponse)
async def update_subscriber(
    user_id: int,
    user_update: UserUpdate = Body(
        examples={
            "example": {
                "email": "new.email@example.com",
                "phone": "+123456789",
                "active": True,
                "client_data": {
                    "address": "456 New St",
                    "neighborhood": "Uptown",
                    "city": "New City",
                    "state": "NC",
                    "code_address": "67890",
                },
            }
        }
    ),
    db: Session = Depends(get_db),
    request: Request = None,
    x_user_id: int = Header(...),
):
    """
    Endpoint to update an existing subscriber.
    """
    try:
        client_ip = request.client.host if request else "unknown"
        updated_user = await UserService.update_subscriber(
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
            status_code=500, detail=f"Error on update subscriber: " f"{str(e)}"
        )


@router.post("/users/register/assisted/")
async def register_assisted(
        assisted: AssistedCreate = Body(
            examples=[
                     {"subscriber_id": 1, "assisted_id": 2},

            ]
        ),
        db: Session = Depends(get_db),
        request: Request = None,
        x_user_id: int = Header(...),
):
    """
    Endpoint to register an assisted user.
    """
    try:
        client_ip = request.client.host if request else "unknown"
        return await UserService.create_association_assisted(
            db=db,
            subscriber_id=assisted.subscriber_id,
            assisted_id=assisted.assisted_id,
            created_by=x_user_id,
            user_ip=client_ip,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error on register assisted: {str(e)}"
        )
@router.get("/users/subscribers/{subscriber_id}/assisted", response_model=List[AssistedResponse])
async def consult_assisted(
    subscriber_id: int,
    db: Session = Depends(get_db),
):
    assisteds = UserService.get_assisted_clients(db, subscriber_id)
    return [AssistedResponse.from_orm(client) for client in assisteds]