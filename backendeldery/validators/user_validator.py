from fastapi import HTTPException
from sqlalchemy.orm import Session
from backendeldery.models import User, Client
from backendeldery.schemas import UserCreate, SubscriberCreate

class UserValidator:
    @staticmethod
    def validate_user(db: Session, user_data: UserCreate):
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(status_code=422, detail="Email already exists")
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
        # Check if a user with the same email and phone already exists
        existing_user = db.query(User).filter(
            User.email == user_data["email"],
            User.phone == user_data["phone"]
        ).first()

        if existing_user:
            existing_client = db.query(Client).filter(Client.user_id == existing_user.id).first()
            if existing_client and existing_client.cpf != user_data["client_data"]["cpf"]:
                raise HTTPException(status_code=422, detail="This user is already a client with another CPF")

        if db.query(Client).join(User).filter(
                (Client.cpf == user_data["client_data"]["cpf"]) &
                (User.email == user_data["email"]) &
                (User.phone == user_data["phone"])
        ).first():
            raise HTTPException(status_code=422, detail="The subscriber already exists")

        existing_client = db.query(Client).filter(Client.cpf == user_data["client_data"]["cpf"]).first()
        if existing_client:
            raise HTTPException(status_code=422, detail="This cpf  already exists")
        return False

        existing_client_with_email = db.query(Client).join(User).filter(User.email == user_data["email"]).first()
        existing_client_with_phone = db.query(Client).join(User).filter(User.phone == user_data["phone"]).first()
        if existing_client_with_email or existing_client_with_phone:
            raise HTTPException(status_code=422, detail="A client with this email or phone already exists")

