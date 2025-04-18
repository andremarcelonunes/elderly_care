import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backendeldery.crud.users import crud_assisted, crud_contact, crud_specialized_user
from backendeldery.schemas import UserCreate, UserResponse, UserUpdate
from backendeldery.validators.user_validator import UserValidator

logger = logging.getLogger("backendeldery")
logger.setLevel(logging.CRITICAL)
if not logger.hasHandlers():
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)


class UserService:
    @staticmethod
    async def register_client(
        db: Session, user_data: UserCreate, created_by: int, user_ip: str
    ):
        """
        Registra um cliente no sistema.
        """
        try:
            logger.info("Entering register_client method")
            UserValidator.validate_subscriber(db, user_data.model_dump())
            return await crud_specialized_user.create_subscriber(
                db=db,
                user_data=user_data.model_dump(),  # Use model_dump instead of dict
                created_by=created_by,
                user_ip=user_ip,
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")

    @staticmethod
    async def search_subscriber(db: Session, criteria: dict):
        try:
            user = await crud_specialized_user.search_subscriber(db, criteria)
            if user:
                return user.id  # Return only the user ID
            return None
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error in UserService: {str(e)}"
            )

    @staticmethod
    async def get_subscriber_by_id(db: Session, user_id: int):
        """
        Get subscriber information by user ID.
        """
        try:
            user = await crud_specialized_user.get_user_with_client(
                db=db, user_id=user_id
            )
            if not user:
                return None
            if user.attendant_data:
                raise HTTPException(
                    status_code=400,
                    detail="This user is not contact, subscriber ou assisted",
                )

            client_data = (
                user.client_data.dict() if getattr(user, "client_data", None) else None
            )
            return UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                phone=user.phone,
                receipt_type=user.receipt_type,
                role=user.role,
                active=user.active,
                client_data=client_data,
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error in UserService: {str(e)}"
            )

    @staticmethod
    async def update_subscriber(
        db: Session,
        user_id: int,
        user_update: UserUpdate,
        user_ip: str,
        updated_by: int,
    ):
        """
        Serviço que chama o CRUD para atualizar um usuário e seu cliente.
        """
        try:
            # Chama o CRUD para fazer a atualização real no banco
            UserValidator.validate_user(db, user_update)
            result = await crud_specialized_user.update_user_and_client(
                db, user_id, user_update, user_ip, updated_by
            )
            if "error" in result:
                raise HTTPException(status_code=400, detail=result["error"])

            # Fetch the updated user to return the correct response
            updated_user = await crud_specialized_user.get_user_with_client(db, user_id)
            if not updated_user:
                raise HTTPException(status_code=404, detail="User not found")

            return UserResponse(
                id=updated_user.id,
                name=updated_user.name,
                email=updated_user.email,
                phone=updated_user.phone,
                receipt_type=updated_user.receipt_type,
                role=updated_user.role,
                active=updated_user.active,
                client_data=updated_user.client_data.dict(),  # Convert to dictionary
            )

        except HTTPException as e:
            raise e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error on updating: {str(e)}")

    @staticmethod
    async def create_association_assisted(
        db: Session,
        subscriber_id: int,
        assisted_id: int,
        user_ip: str,
        created_by: int,
    ):
        """
        Creates an association in the client_association table and registers a new
        client if the assisted is not the same as the subscriber.
        """
        try:
            # Validate the assisted data
            UserValidator.validate_association_assisted(db, subscriber_id, assisted_id)

            # Create the association
            return await crud_assisted.create_association(
                db, subscriber_id, assisted_id, created_by, user_ip
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    @staticmethod
    async def get_assisted_clients(db: Session, subscriber_id: int):
        """
        Retrieves the assisted clients for a given subscriber.
        """
        try:
            return await crud_assisted.get_assisted_clients_by_subscriber(
                db, subscriber_id
            )
        except HTTPException as e:
            raise e
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    @staticmethod
    async def register_contact(
        db: Session,
        user_data: UserCreate,
        created_by: int,
        user_ip: str,
    ):
        """
        Registers a contact in the system.
        """
        try:
            # Ensure user data is properly serialized
            contact_data = user_data.model_dump()
            UserValidator.validate_contact(db, user_data)
            # Call the CRUD method to register the contact
            result = await crud_contact.create_contact(
                db=db,
                user_data=contact_data,
                created_by=created_by,
                user_ip=user_ip,
            )
            # Extract the contact id in a way that works for both an object or a dict
            if hasattr(result, "id"):
                contact_id = result.id
            elif isinstance(result, dict):
                contact_id = result.get("id")
            else:
                contact_id = None

            return {"message": "Contact has been created", "user": {"id": contact_id}}

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException as e:
            raise e  # Re-raise FastAPI exceptions
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    @staticmethod
    async def create_contact_association(
        db: Session,
        client_id: int,
        user_contact_id: int,
        type_contact: str,
        created_by: int,
        user_ip: str,
    ):
        """
        Creates an association between a contact and a client.
        """
        try:
            UserValidator.validate_association_contact(db, client_id, user_contact_id)
            result = await crud_contact.create_contact_association(
                db=db,
                client_id=client_id,
                user_contact_id=user_contact_id,
                type_contact=type_contact,
                created_by=created_by,
                user_ip=user_ip,
            )
            return result
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    @staticmethod
    async def get_client_contacts(db: Session, client_id: int):
        """
        Retrieves all contacts for a given client by calling the CRUD function.
        """
        try:
            contacts = await crud_contact.get_contacts_by_client(db, client_id)
            return contacts
        except HTTPException as e:
            raise e
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    @staticmethod
    async def get_clients_of_contact(db: Session, contact_id: int):
        """
        Retrieves all clients for a given contact, excluding the contact's own client record.
        """
        try:
            clients = await crud_contact.get_clients_by_contact(db, contact_id)
            # Filter out the contact's own client record.
            filtered_clients = [
                client for client in clients if client.user_id != contact_id
            ]
            return filtered_clients
        except HTTPException as e:
            raise e
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    @staticmethod
    async def delete_contact_relation(
        db: Session, client_id: int, contact_id: int, user_ip: str, x_user_id: int
    ):
        """
        Deletes the association between a given client and contact.
        Before deletion, updates the association row with the audit data
        (updated_by and user_ip).  If the contact is no longer associated
        with any client,
        it is deleted.
        """
        try:
            UserValidator.validate_deletion_contact_association(
                db, client_id, contact_id, x_user_id
            )
            await crud_contact.delete_contact_relation(
                db=db,
                client_id=client_id,
                contact_id=contact_id,
                user_ip=user_ip,
                x_user_id=x_user_id,
            )
            return {"message": "Contact association deleted successfully"}
        except HTTPException as e:
            raise e
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
