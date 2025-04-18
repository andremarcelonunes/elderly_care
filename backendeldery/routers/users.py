from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from backendeldery.schemas import (
    AssistedCreate,
    AssistedResponse,
    UserCreate,
    UserResponse,
    UserSearch,
    UserUpdate,
)
from backendeldery.services.users import UserService
from backendeldery.utils import get_db

router = APIRouter()


@router.post("/users/register/subscriber/")
async def register_subscriber(
    user: UserCreate = Body(  # noqa: B008
        examples=[
            {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+123456789",
                "receipt_type": 1,
                "role": "subscriber",
                "password": "Strong@123",
                "active": True,
                "client_data": {
                    "cpf": "123.456.789-00",
                    "team_id": 1,
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
    db: Session = Depends(get_db),  # noqa: B008
    request: Request = None,
    x_user_id: int = Header(...),
):
    """
    Register a new subscriber.
    This endpoint registers a new subscriber using the provided user details.
    A subscriber can be registered either as a regular subscriber or as a client.


    Parameters:

        user (UserCreate): An object containing the subscriber's details including:
            - name (str): Full name of the user.
            - phone (str): Contact phone number.
            - receipt_type (int): Type of receipt (1 - WhatsApp, 2 - SMS, 3 - Todos os
             canais )
            - role (str): Role of the user, expected to be "subscriber".
            - password (str): Account password.
            - active (bool): Indicates whether the account is active.
            - client_data (dict): Additional client-specific data:
                - cpf (str): CPF identifier.
                - team_id (int): Identifier for the team associated with the client.
                - birthday (str): Birth date in YYYY-MM-DD format.
                - address (str): Street address.
                - city (str): City name.
                - neighborhood (str): Neighborhood name.
                - code_address (str): Postal code.
                - state (str): State abbreviation.
        db (Session): Database session dependency.
        request (Request, optional): Incoming request object which is used to obtain the
        client IP address. Defaults to None.
        x_user_id (int): Identifier of the user performing the registration, provided
        via the header.

    Returns:

        The response from UserService.register_client, typically including details of
          the newly registered subscriber.

    Raises:

        HTTPException:
            Propagates any HTTP exceptions raised during the registration process or
            raises a new HTTPException with
            status code 500 if an unexpected error occurs.
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
        ) from e


@router.post("/users/search/")
async def search_user(
    search_criteria: UserSearch = Body(  # noqa: B008
        ..., example={"phone": "+123456789"}
    ),
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Endpoint to search for a user by a single criteria (email, phone, or CPF).

    This endpoint accepts a JSON body containing exactly one search criterion. The
    allowed criteria are:

    - CPF: for assisted clients or subscribers.
    - Email or phone: for contacts (email is optional for assisteds and contacts).

    Parameters:

    search_criteria (UserSearch): The search parameters provided in the request body.
        Example: {"phone": "+123456789"}
    db (Session): Database session dependency for performing the user search.

    Behavior:

    - Validates that exactly one search criteria is provided.
    - Invokes the user service asynchronously to search for the subscriber.
    - Returns a dictionary containing the user ID if found.
    - Raises HTTPException with status code 400 if not exactly one criterion is
    provided.
    - Raises HTTPException with status code 404 if no matching user is found.
    - Raises HTTPException with status code 500 for any internal errors during
    processing.
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
        ) from e


@router.get(
    "/users/user/{user_id}",
    response_model=UserResponse,
    response_model_exclude_none=True,
)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Endpoint to retrieve a subscriber's user information by their ID.

    Parameters:

        user_id (int): The unique identifier of the subscriber.
        db (Session, optional): The database session dependency injected by FastAPI.

    Returns:

        UserResponse: A response model representing the subscriber's details.

    Raises:

        HTTPException:
            - 404 if the subscriber is not found.
            - 500 if an unexpected error occurs during retrieval.
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
        ) from e


@router.put(
    "/users/update/{user_id}",
    response_model=UserResponse,
    response_model_exclude_none=True,
)
async def update_user(
    user_id: int,
    user_update: UserUpdate = Body(  # noqa: B008
        example={
            "email": "new.email@example.com",
            "phone": "+123456789",
            "receipt_type": 2,
            "active": True,
            "client_data": {
                "team_id": 1,
                "address": "456 New St",
                "neighborhood": "Uptown",
                "city": "New City",
                "state": "NC",
                "code_address": "67890",
            },
        }
    ),
    db: Session = Depends(get_db),  # noqa: B008
    request: Request = None,
    x_user_id: int = Header(...),
):
    """
    Update an existing user with the given update data.

    Parameters:

        user_id (int): The identifier of the user to be updated.
        user_update (UserUpdate): Object containing the updated fields.
            Only provided fields will be updated.

        db (Session): Database session dependency.
        request (Request, optional): The request object, used to extract client IP.
        x_user_id (int): The user ID from the request header, denoting who is performing
          the update.

    Returns:

        UserResponse: The updated user data.

    Raises:

        HTTPException: If there is an error during the update process.
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
            status_code=500, detail=f"Error on update subscriber: {str(e)}"
        ) from e


@router.post("/users/associate/assisted/")
async def register_assisted(
    assisted: AssistedCreate = Body(  # noqa: B008
        examples=[
            {"subscriber_id": 1, "assisted_id": 2},
        ]
    ),
    db: Session = Depends(get_db),  # noqa: B008
    request: Request = None,
    x_user_id: int = Header(...),
):
    """
        Endpoint to associate an assisted user with a subscriber.

    Parameters:

        assisted (AssistedCreate): An object containing the subscriber_id and
        assisted_id.
        db (Session): Database session dependency.
        request (Request, optional): The HTTP request object used to extract client IP
        information.
        x_user_id (int): The user ID extracted from the request header used to track
        who initiated the action.

    Returns:

        The result of creating the association between the assisted user and the
        subscriber.

    Raises:

        HTTPException: For errors related to the association process, with a 500 status
          code for general exceptions.
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
        ) from e


@router.get(
    "/users/subscribers/{subscriber_id}/assisted", response_model=list[AssistedResponse]
)
async def consult_assisted(
    subscriber_id: int,
    db: Session = Depends(get_db),  # noqa: B008
):
    assisteds = await UserService.get_assisted_clients(db, subscriber_id)
    return [AssistedResponse.from_orm(client) for client in assisteds]


@router.post("/users/register/contact/")
async def register_contact(
    user: UserCreate = Body(  # noqa: B008
        examples=[
            {
                "name": "Jane Doe",
                "phone": "+987654321",
                "receipt_type": 2,
                "role": "contact",
                "active": True,
            }
        ]
    ),
    db: Session = Depends(get_db),  # noqa: B008
    request: Request = None,
    x_user_id: int = Header(...),
):
    """
    Retrieve the list of assisted clients for a given subscriber.

    Parameters:

        subscriber_id (int): The unique identifier of the subscriber whose assisted
        clients are to be retrieved.
        db (Session, optional): Database session dependency injected into the endpoint.

    Returns:

        List[AssistedResponse]: A list of AssistedResponse objects representing the
          assisted clients associated with the subscriber.

    Notes:

        - This endpoint fetches data asynchronously using the
        UserService.get_assisted_clients method.
        - Each retrieved ORM client object is converted to an AssistedResponse instance
          before being returned.
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
        ) from e


@router.post("/users/associate/contact/")
async def create_contact_association(
    client_id: int = Body(..., example=1),
    user_contact_id: int = Body(..., example=2),
    type_contact: str = Body(..., example="emergency"),
    db: Session = Depends(get_db),  # noqa: B008
    request: Request = None,
    x_user_id: int = Header(...),
):
    """
        Creates an association between a client's record and a contact.

    Args:

        client_id (int): The identifier of the client.
        user_contact_id (int): The identifier of the contact to be associated with the
        client.
        type_contact (str): A string representing the contact type (e.g., "emergency").
        db (Session): The database session instance provided by dependency injection.
        request (Request, optional): The HTTP request object. Used to extract the
        client's IP address.
        x_user_id (int): The user identifier extracted from the request header,
        representing
        the creator of the association.

    Returns:

        The result of the contact association creation process as returned by
        UserService.create_contact_association.

    Raises:

        HTTPException: If an error occurs during the contact association creation
          process.
    """
    try:
        client_ip = request.client.host if request else "unknown"
        return await UserService.create_contact_association(
            db=db,
            client_id=client_id,
            user_contact_id=user_contact_id,
            type_contact=type_contact,
            created_by=x_user_id,
            user_ip=client_ip,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error on creating contact association: {str(e)}"
        ) from e


@router.get("/users/client/{client_id}/contacts", response_model=list[UserResponse])
async def get_client_contacts(
    client_id: int,
    db: Session = Depends(get_db),  # noqa: B008
):
    """
        Parameters:
        client_id (int): The ID of the client for which contacts are being retrieved.
        db (Session): SQLAlchemy session dependency, provided via dependency injection.

    Returns:
        list[UserResponse]: A list of UserResponse objects representing the client's
          contacts.

    Raises:
        HTTPException:
            - If an HTTP-related error occurs during the retrieval process.
            - If an unexpected error occurs during processing, an HTTPException with
              a 500 status code is raised.
    """
    try:
        contacts = await UserService.get_client_contacts(db, client_id)
        return [UserResponse.from_orm(contact) for contact in contacts]
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving contacts: {str(e)}"
        ) from e


@router.get(
    "/users/contact/{contact_id}/clients", response_model=list[AssistedResponse]
)
async def get_clients_of_contact(
    contact_id: int,
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Retrieve all clients associated with a specified contact.
    This asynchronous endpoint returns a list of clients linked to the provided
    contact ID by calling the
    UserService.get_clients_of_contact service method. Each returned client is
    transformed into an AssistedResponse
    object using the from_orm method.

    Parameters:

        contact_id (int): The unique identifier for the contact whose clients are being
          retrieved.
        db (Session): The database session instance provided by FastAPI's dependency
        injection mechanism.

    Returns:
        list[AssistedResponse]: A list of clients corresponding to the given
        contact,
        represented as AssistedResponse models.

    Raises:

        HTTPException: If an error occurs during the retrieval process or if the
        underlying service call fails.
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
        ) from e


@router.delete("/users/contact/association/")
async def delete_contact_association(
    client_id: int,
    contact_id: int,
    db: Session = Depends(get_db),  # noqa: B008
    request: Request = None,
    x_user_id: int = Header(...),
):
    """
        Deletes the association between a given client and contact. Before performing
        the deletion, updates the association record with the client IP and x_user_id
        for auditing purposes. If the contact is not associated with any other
        client after the deletion, also deletes the contact record.

    Parameters:

        client_id (int): The unique identifier of the client.
        contact_id (int): The unique identifier of the contact.
        db (Session): The SQLAlchemy database session provided via dependency injection.
        request (Request, optional): The HTTP request object used to extract the
        client
        IP address for auditing purposes. If not provided, defaults to "unknown".
        x_user_id (int): The unique identifier of the user making the request,
          provided
        via the header.

    Returns:

        The result of the deletion operation as returned by the
        UserService.delete_contact_relation method.

    Raises:

        HTTPException:
            - If there is an error raised by the deletion service.
            - For generic errors during the deletion process, with status code 500.
    """
    try:
        client_ip = request.client.host if request else "unknown"
        return await UserService.delete_contact_relation(
            db, client_id, contact_id, user_ip=client_ip, x_user_id=x_user_id
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting contact association: {str(e)}"
        ) from e
