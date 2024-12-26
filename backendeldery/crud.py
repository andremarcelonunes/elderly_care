from sqlalchemy.orm import Session
from models import User, Patient, Contact
from passlib.context import CryptContext

# Configuração para hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_user(db: Session, user_data):
    # Fazer o hash da senha
    hashed_password = get_password_hash(user_data.password)
    # Substituir a senha pelo hash no dicionário de dados
    user_data_dict = user_data.dict()
    user_data_dict.pop("password")  # Remover o campo 'password'
    user_data_dict["password_hash"] = hashed_password  # Adicionar o hash como 'password_hash'

    # Criar o usuário com os dados ajustados
    user = User(**user_data_dict)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id):
    return db.query(User).filter(User.id == user_id).first()


def create_patient(db: Session, patient_data):
    patient = Patient(**patient_data.dict())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def update_patient(db: Session, patient_id, patient_data):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient:
        for key, value in patient_data.dict(exclude_unset=True).items():
            setattr(patient, key, value)
        db.commit()
        db.refresh(patient)
    return patient


def add_contact(db: Session, contact_data):
    contact = Contact(**contact_data.dict())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact