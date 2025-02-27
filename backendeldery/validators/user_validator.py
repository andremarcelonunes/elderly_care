import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backendeldery.models import (
    User,
    Client,
    client_association,
    client_contact_association,
)
from backendeldery.schemas import UserCreate, SubscriberCreate

logger = logging.getLogger("backendeldery")
logger.setLevel(logging.CRITICAL)
if not logger.hasHandlers():
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)


class UserValidator:
    @staticmethod
    def validate_user(db: Session, user_data: UserCreate):
        if (
            user_data.email
            and db.query(User).filter(User.email == user_data.email).first()
        ):
            raise HTTPException(status_code=422, detail="Email already exists")
        if (
            user_data.phone
            and db.query(User).filter(User.phone == user_data.phone).first()
        ):
            raise HTTPException(status_code=422, detail="Phone already exists")

    @staticmethod
    def validate_contact(db: Session, user_data: UserCreate):
        if db.query(User).filter(User.phone == user_data.phone).first():
            raise HTTPException(status_code=422, detail="Phone already exists")

    @staticmethod
    def validate_client(db: Session, user: User, client_data: SubscriberCreate):
        if db.query(Client).filter(Client.user_id == user.id).first():
            raise HTTPException(status_code=422, detail="Client already exists")
        if db.query(Client).filter(Client.cpf == client_data.cpf).first():
            raise HTTPException(status_code=422, detail="CPF already exists")

    @staticmethod
    def validate_subscriber(db: Session, user_data: dict):
        # Check if a user with the same email or phone already exists
        logger.info("Entering validate_subscriber method")
        existing_user = (
            db.query(User)
            .filter(
                (User.email == user_data["email"]) | (User.phone == user_data["phone"])
            )
            .first()
        )
        logger.info("Existing user: %s", existing_user)
        if user_data["client_data"] is None:
            raise HTTPException(status_code=400, detail="You must inform client data")

        if (
            db.query(Client)
            .join(User)
            .filter(
                (Client.cpf == user_data["client_data"]["cpf"])
                & (User.email == user_data["email"])
                & (User.phone == user_data["phone"])
            )
            .first()
        ):
            raise HTTPException(status_code=422, detail="The client already exists")

        if existing_user:
            existing_client = (
                db.query(Client).filter(Client.user_id == existing_user.id).first()
            )
            if (
                existing_client
                and existing_client.cpf != user_data["client_data"]["cpf"]
            ):
                raise HTTPException(
                    status_code=422,
                    detail="This user is already a client with another CPF",
                )

        existing_client = (
            db.query(Client)
            .filter(Client.cpf == user_data["client_data"]["cpf"])
            .first()
        )
        if existing_client:
            raise HTTPException(status_code=422, detail="This cpf already exists")

        if user_data["email"] is not None:
            logger.info(f"Checando user com email: %s", user_data["email"])
            existing_client_with_email = (
                db.query(User).filter(User.email == user_data["email"]).first()
            )
            logger.info("Email existente: %s", existing_client_with_email)
            existing_client_with_phone = (
                db.query(User).filter(User.phone == user_data["phone"]).first()
            )
            logger.info("Telefone existente: %s", existing_client_with_email)
        else:
            existing_client_with_email = False
            existing_client_with_phone = (
                db.query(Client)
                .join(User)
                .filter(User.phone == user_data["phone"])
                .first()
            )
        logger.info("Checando user com email: %s", existing_client_with_email)
        if existing_client_with_email or existing_client_with_phone:
            raise HTTPException(
                status_code=422,
                detail="A client with this email or phone already exists",
            )

    @staticmethod
    def validate_association_assisted(
        db: Session, subscriber_id: int, assisted_id: int
    ):
        subscriber = db.query(User).filter(User.id == subscriber_id).one_or_none()
        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")
        if subscriber.role != "subscriber":
            raise HTTPException(
                status_code=403, detail="User does not have the 'subscriber' role"
            )
        assisted = db.query(User).filter(User.id == assisted_id).one_or_none()
        if not assisted:
            raise HTTPException(status_code=404, detail="Assisted not found")

        if assisted.role == "subscriber" and assisted.id != subscriber.id:
            raise HTTPException(
                status_code=403, detail="Another subscriber cannot be associated"
            )

        # Check if the assisted user is already associated with another subscriber
        existing_association = (
            db.query(client_association)
            .filter(client_association.c.assisted_id == assisted_id)
            .first()
        )
        already_existed_association = (
            db.query(client_association)
            .filter(
                client_association.c.assisted_id == assisted_id,
                client_association.c.subscriber_id == subscriber_id,
            )
            .first()
        )

        if already_existed_association:
            raise HTTPException(
                status_code=422,
                detail="Assisted  has been  already associated with this subscriber",
            )

        if existing_association:
            raise HTTPException(
                status_code=422,
                detail="Assisted  has been already associated with another subscriber",
            )

        # Check if the subscriber is already associated with the assisted user
        association = (
            db.query(client_association)
            .filter(
                client_association.c.subscriber_id == subscriber_id,
                client_association.c.assisted_id == assisted_id,
            )
            .first()
        )
        if association:
            raise HTTPException(status_code=422, detail="Association already exists")

    @staticmethod
    def validate_association_contact(db: Session, client_id: int, contact_id: int):
        """
        Validates whether a contact can be associated with a client.
        """
        # Check if the client exists
        client = db.query(Client).filter(Client.user_id == client_id).one_or_none()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        # Check if the contact exists
        contact = db.query(User).filter(User.id == contact_id).one_or_none()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

        # Prevent clients from adding themselves as contacts
        if client.user_id == contact.id:
            raise HTTPException(
                status_code=403, detail="Clients cannot be their own contacts"
            )

        # Check if this contact is already associated with this client
        already_associated = (
            db.query(client_contact_association)
            .filter(
                client_contact_association.c.user_client_id == client_id,
                client_contact_association.c.user_contact_id == contact_id,
            )
            .first()
        )

        if already_associated:
            raise HTTPException(
                status_code=422,
                detail="This contact is already associated with the client",
            )

        # Check if the contact is already associated with another client

    @staticmethod
    def validate_deletion_contact_association(
        db: Session, client_id: int, contact_id: int, x_user_id: int
    ):
        """
        Validates whether a contact association can be deleted.
        """
        # Check if the client exists
        client = db.query(Client).filter(Client.user_id == client_id).one_or_none()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        # Check if the contact exists
        contact = db.query(User).filter(User.id == contact_id).one_or_none()
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")

        # Check if this client_id is equal to x_user_id
        if client_id != x_user_id:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to delete this association",
            )
