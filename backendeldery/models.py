from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "elderly_care"}  # Substitua "meu_schema" pelo seu schema
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "elderly", "contact", "nurse"
    password_hash = Column(String, nullable=False)

class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = {"schema": "elderly_care"}
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("elderly_care.users.id"), nullable=False)
    medical_conditions = Column(Text, nullable=True)
    notify_contacts = Column(Boolean, default=True)
    notify_nurses = Column(Boolean, default=True)
    user = relationship("User")

class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = {"schema": "elderly_care"}
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("elderly_care.patients.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("elderly_care.users.id"), nullable=False)