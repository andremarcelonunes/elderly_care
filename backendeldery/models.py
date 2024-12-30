from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, Date, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from database import Base

class Team(Base):
    __tablename__ = "teams"
    __table_args__ = {"extend_existing": True, "schema": "elderly_care"}
    team_id = Column(Integer, primary_key=True, index=True)
    team_name = Column(String,  unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relacionamento com clientes
    clients = relationship("Client", back_populates="team")
    attendants = relationship("Attendant", back_populates="team")


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "elderly_care"}
    user_id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(200), nullable=False)
    user_email = Column(String(150), unique=True, index=True, nullable=False)
    user_phone = Column(String(15), unique=True, index=True, nullable=False)
    user_birthday = Column(Date, nullable=True)
    user_role = Column(String(50), nullable=False)
    user_password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relacionamento com ClientContact (todos os clientes para os quais o usuário é contato)
    client_contacts = relationship("ClientContact", backref="contact")
    # Relacionamento reverso
    client = relationship("Client", uselist=False, back_populates="user")
    attendant = relationship("Attendant", uselist=False, back_populates="user")


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = {"extend_existing": True, "schema": "elderly_care"}
    user_id = Column(Integer, ForeignKey("elderly_care.users.user_id"), index=True, primary_key=True)
    team_id = Column(Integer, ForeignKey("elderly_care.teams.team_id"), index=True, nullable=True)
    user_address = Column(String, nullable=False)
    user_neighborhood = Column(String, nullable=False)
    user_city = Column(String, nullable=False)
    user_state = Column(String, nullable=False)
    user_code_address = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relacionamento com ClientContact (acessar todos os contatos do cliente)
    contacts = relationship("ClientContact", backref="client")
    # Relacionamento com Team
    team = relationship("Team", back_populates="clients")
    user = relationship("User", back_populates="client")


class ClientContact(Base):
    __tablename__ = "contacts"
    __table_args__ = {"extend_existing": True, "schema": "elderly_care"}
    user_client_id = Column(Integer, ForeignKey("elderly_care.clients.user_id"), index=True, primary_key=True)
    user_contact_id = Column(Integer, ForeignKey("elderly_care.users.user_id"), index=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class NotificationConfig(Base):
    __tablename__ = "notification_configs"
    __table_args__ = {"extend_existing": True, "schema": "elderly_care"}
    user_id = Column(Integer, ForeignKey("elderly_care.users.user_id"), primary_key=True)
    notify_level = Column(Integer, nullable=False, default=1)


class Attendant(Base):
    __tablename__ = "attendants"
    __table_args__ = (
        UniqueConstraint("user_id", "team_id", name="unique_attendant_team"),
        {"schema": "elderly_care"},
    )
    user_id = Column(Integer, ForeignKey("elderly_care.users.user_id"), nullable=False, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("elderly_care.teams.team_id"), nullable=False, primary_key=True, index=True)
    attendant_function = Column(String, nullable=False)  # Ex.: "nurse", "doctor", etc.
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relacionamento com Team
    team = relationship("Team", back_populates="attendants")
    user = relationship("User", back_populates="attendant")
