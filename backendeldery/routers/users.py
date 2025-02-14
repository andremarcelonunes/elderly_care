from fastapi import APIRouter, Depends, Body, HTTPException, Request, Header
from typing import List
from sqlalchemy.orm import Session
from backendeldery.schemas import (
    UserCreate,
    UserSearch,
    UserUpdate,
    UserResponse,
    AssistedCreate,
    AssistedResponse,
)
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
    Endpoint to register a new subscriber. TThat can be subscriber in fact or a client.
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


@router.post("/users/search/user/")
async def search_user(
        search_criteria: UserSearch = Body(..., example={"phone": "+123456789"}),
        db: Session = Depends(get_db),
):
    """
    Endpoint to search all users by email, phone, or CPF. Only one criteria is allowed. Remember
    for assisted clients or subscribers you can use CPF, for contacts you can use email or phone.
    For assiteds and contacts, email are optional.
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


@router.get("/users/user/{user_id}")
async def get_user(
        user_id: int,
        db: Session = Depends(get_db),
):
    """
    Endpoint to get information about  all kind of users by  ID.
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


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
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
    Endpoint to update an existing user. Inform only the fields you want to update.
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


@router.post("/users/associate/assisted/")
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
    Endpoint to associate  an assisted user to a subscriber.
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


@router.get(
    "/users/subscribers/{subscriber_id}/assisted", response_model=List[AssistedResponse]
)
async def consult_assisted(
        subscriber_id: int,
        db: Session = Depends(get_db),
):
    assisteds = await UserService.get_assisted_clients(db, subscriber_id)
    return [AssistedResponse.from_orm(client) for client in assisteds]


@router.post("/users/register/contact/")
async def register_contact(
        user: UserCreate = Body(
            examples=[
                {
                    "name": "Jane Doe",
                    "phone": "+987654321",
                    "role": "contact",
                    "active": True,
                }
            ]
        ),
        db: Session = Depends(get_db),
        request: Request = None,
        x_user_id: int = Header(...),
):
    """
    Endpoint to register a new contact.
    """
    try:
        client_ip = request.client.host if request else "unknown"
        return await UserService.register_contact(
            db=db,
            user_data=user,
            created_by=x_user_id,
            user_ip=client_ip,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error on creating contact: {str(e)}"
        )


@router.post("/users/associate/contact/")
async def create_contact_association(
        client_id: int = Body(..., example=1),
        user_contact_id: int = Body(..., example=2),
        db: Session = Depends(get_db),
        request: Request = None,
        x_user_id: int = Header(...),
):
    """
    Endpoint to create an association between a contact and a client.
    """
    try:
        client_ip = request.client.host if request else "unknown"
        return await UserService.create_contact_association(
            db=db,
            client_id=client_id,
            user_contact_id=user_contact_id,
            created_by=x_user_id,
            user_ip=client_ip,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error on creating contact association: {str(e)}"
        )


@router.get("/users/client/{client_id}/contacts", response_model=List[UserResponse])
async def get_client_contacts(
        client_id: int,
        db: Session = Depends(get_db),
):
    """
    Endpoint to retrieve all contacts for a given client.
    """
    try:
        contacts = await UserService.get_client_contacts(db, client_id)
        return [UserResponse.from_orm(contact) for contact in contacts]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving contacts: {str(e)}"
        )


@router.get(
    "/users/contact/{contact_id}/clients", response_model=List[AssistedResponse]
)
async def get_clients_of_contact(
        contact_id: int,
        db: Session = Depends(get_db),
):
    """
    Endpoint to retrieve all clients associated with a given contact.
    """
    try:
        # If your service method is synchronous, just call it directly.
        clients = await UserService.get_clients_of_contact(db, contact_id)
        return [AssistedResponse.from_orm(client) for client in clients]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving clients: {str(e)}"
        )


@router.delete("/users/contact/association/")
async def delete_contact_association(
    client_id: int,
    contact_id: int,
    db: Session = Depends(get_db),
    request: Request = None,
    x_user_id: int = Header(...),
):
    """
    Endpoint to delete the association between a given client and contact.
    Before deletion, the association row is updated with the user IP and x_user_id for auditing.
    If the contact is not associated with any other client, the contact record is also deleted.
    """
    try:
        client_ip = request.client.host if request else "unknown"
        return await UserService.delete_contact_relation(db, client_id,
                                                   contact_id, user_ip=client_ip, x_user_id=x_user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting contact association: {str(e)}")

