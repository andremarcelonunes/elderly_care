from sqlalchemy import (
    Column,
    Integer,
    Table,
    String,
    ForeignKey,
    Boolean,
    Text,
    Enum,
    Date,
    DateTime,
    Time,
    func,
)
from sqlalchemy.orm import relationship, declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "elderly_care"}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(150), unique=True, nullable=True)
    phone = Column(String(15), unique=True, nullable=False)
    role = Column(String(50), nullable=False)
    active = Column(Boolean, default=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    user_ip = Column(String, nullable=True)

    # Relacionamento com ClientContact (todos os clientes para os quais o usuário é contato)
    client_contacts = relationship("ClientContact", back_populates="contact")
    client = relationship("Client", uselist=False, back_populates="user")
    patient_progress = relationship("PatientProgress", back_populates="attendant")
    tickets = relationship("Ticket", back_populates="attendant")  # Adicionado


class Function(Base):
    __tablename__ = "functions"
    __table_args__ = {"schema": "elderly_care"}
    function_id = Column(Integer, primary_key=True, index=True)
    function_name = Column(String(255), nullable=False, unique=True)
    function_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    user_ip = Column(String, nullable=True)

    # Relacionamento com Attendant (único)
    attendants = relationship("Attendant", back_populates="function")
    # Relacionamento com Document (muitos-para-muitos)
    documents = relationship(
        "Document",
        secondary="elderly_care.document_function",
        back_populates="functions",
    )


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = {"schema": "elderly_care"}
    team_id = Column(Integer, primary_key=True, index=True)
    team_name = Column(String, unique=True, nullable=False)
    team_site = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    user_ip = Column(String, nullable=True)

    # Relacionamento com clientes
    clients = relationship("Client", back_populates="team")
    attendants = relationship(
        "Attendant", secondary="elderly_care.attendant_team", back_populates="teams"
    )


class Attendant(Base):
    __tablename__ = "attendants"
    __table_args__ = {"schema": "elderly_care"}
    user_id = Column(
        Integer, ForeignKey("elderly_care.users.id"), index=True, primary_key=True
    )
    function_id = Column(
        Integer,
        ForeignKey("elderly_care.functions.function_id"),
        index=True,
        nullable=True,
    )
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    user_ip = Column(String, nullable=True)

    # Relacionamentos
    function = relationship("Function", back_populates="attendants")
    teams = relationship(
        "Team", secondary="elderly_care.attendant_team", back_populates="attendants"
    )
    availabilities = relationship("Availability", back_populates="attendant")
    appointments = relationship("Appointment", back_populates="attendant")


AttendantTeam = Table(
    "attendant_team",
    Base.metadata,
    Column(
        "attendant_id",
        Integer,
        ForeignKey("elderly_care.attendants.user_id"),
        primary_key=True,
    ),
    Column(
        "team_id", Integer, ForeignKey("elderly_care.teams.team_id"), primary_key=True
    ),
    schema="elderly_care",
)


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = {"schema": "elderly_care"}
    user_id = Column(
        Integer, ForeignKey("elderly_care.users.id"), index=True, primary_key=True
    )
    team_id = Column(
        Integer, ForeignKey("elderly_care.teams.team_id"), index=True, nullable=True
    )
    cpf = Column(String(20), nullable=False, unique=True)
    birthday = Column(Date, nullable=True)
    address = Column(String, nullable=True)
    neighborhood = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    code_address = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    user_ip = Column(String, nullable=True)

    # Relacionamento com ClientContact (acessar todos os contatos do cliente)
    contacts = relationship("ClientContact", backref="client")
    # Relacionamento com Team
    team = relationship("Team", back_populates="clients")
    user = relationship("User", back_populates="client")
    appointments = relationship("Appointment", back_populates="client")
    record = relationship("Record", back_populates="client", uselist=False)


client_association = Table(
    "client_association",
    Base.metadata,
    Column(
        "subscriber_id",
        Integer,
        ForeignKey("elderly_care.clients.user_id"),
        primary_key=True,
    ),
    Column(
        "assisted_id",
        Integer,
        ForeignKey("elderly_care.clients.user_id"),
        primary_key=True,
    ),
    Column("created_at", DateTime, default=func.now()),
    Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
    Column("created_by", Integer, nullable=False),
    Column("updated_by", Integer, nullable=True),
    Column("user_ip", String, nullable=True),
    schema="elderly_care",
)


class ClientContact(Base):
    __tablename__ = "contacts"
    __table_args__ = {"schema": "elderly_care"}
    user_client_id = Column(
        Integer,
        ForeignKey("elderly_care.clients.user_id"),
        index=True,
        primary_key=True,
    )
    user_contact_id = Column(
        Integer, ForeignKey("elderly_care.users.id"), index=True, nullable=False
    )
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    user_ip = Column(String, nullable=True)

    contact = relationship("User", back_populates="client_contacts")


class NotificationConfig(Base):
    __tablename__ = "notification_configs"
    __table_args__ = {"schema": "elderly_care"}
    user_id = Column(Integer, ForeignKey("elderly_care.users.id"), primary_key=True)
    notify_level = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    user_ip = Column(String, nullable=True)


class Availability(Base):
    __tablename__ = "availability"
    __table_args__ = {"schema": "elderly_care"}
    availability_id = Column(Integer, primary_key=True, autoincrement=True)
    attendant_id = Column(
        Integer, ForeignKey("elderly_care.attendants.user_id"), nullable=False
    )
    availability_day_of_week = Column(
        Integer, nullable=False
    )  # 0 = Domingo, 1 = Segunda, ..., 6 = Sábado
    availability_start_time = Column(Time, nullable=False)
    availability_end_time = Column(Time, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    user_ip = Column(String, nullable=True)

    # Relacionamento com Attendant
    attendant = relationship("Attendant", back_populates="availabilities")


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = {"schema": "elderly_care"}
    appointment_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("elderly_care.clients.user_id"), nullable=False
    )
    attendant_id = Column(
        Integer, ForeignKey("elderly_care.attendants.user_id"), nullable=False
    )
    appointment_date = Column(DateTime, nullable=False)
    appointment_start_time = Column(Time, nullable=False)
    appointment_end_time = Column(Time, nullable=False)
    appointment_status = Column(
        Enum("marcada", "cancelada", "finalizada", name="appointment_status_enum"),
        nullable=False,
    )
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    user_ip = Column(String, nullable=True)

    # Relacionamento com Client e Attendant
    client = relationship("Client", back_populates="appointments")
    attendant = relationship("Attendant", back_populates="appointments")


class Record(Base):
    __tablename__ = "records"
    __table_args__ = {"schema": "elderly_care"}
    record_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("elderly_care.clients.user_id"), nullable=False
    )
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    user_ip = Column(String, nullable=True)

    # Relacionamentos
    client = relationship("Client", back_populates="record")
    events = relationship("Event", back_populates="record")
    documents = relationship("Document", back_populates="record")
    progresses = relationship(
        "PatientProgress", back_populates="record"
    )  # Novo relacionamento


class Event(Base):
    __tablename__ = "events"
    __table_args__ = {"schema": "elderly_care"}
    event_id = Column(Integer, primary_key=True, index=True)
    record_id = Column(
        Integer, ForeignKey("elderly_care.records.record_id"), nullable=False
    )
    event_type = Column(
        Enum("help_request", "emergency", "information", name="event_type_enum"),
        nullable=False,
    )
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    user_ip = Column(String, nullable=True)

    # Relacionamento com o prontuário
    record = relationship("Record", back_populates="events")

    # Relacionamento com ticket
    ticket = relationship("Ticket", uselist=False, back_populates="event")


class PatientProgress(Base):
    __tablename__ = "patient_progress"
    __table_args__ = {"schema": "elderly_care"}
    progress_id = Column(Integer, primary_key=True, index=True)
    record_id = Column(
        Integer, ForeignKey("elderly_care.records.record_id"), nullable=False
    )
    attendant_id = Column(
        Integer, ForeignKey("elderly_care.users.id"), nullable=False
    )  # Atendente responsável
    created_at = Column(DateTime, default=func.now())
    description = Column(Text, nullable=False)  # Descrição da evolução clínica
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    user_ip = Column(String, nullable=True)
    # Relacionamento com o prontuário
    record = relationship("Record", back_populates="progresses")

    # Relacionamento com o atendente
    attendant = relationship("User", back_populates="patient_progress")


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = {"schema": "elderly_care"}
    ticket_id = Column(Integer, primary_key=True, index=True)
    event_id = Column(
        Integer, ForeignKey("elderly_care.events.event_id"), nullable=False
    )
    status = Column(
        Enum("open", "in_progress", "pending", "closed", name="ticket_status_enum"),
        nullable=False,
    )
    symptoms = Column(Text, nullable=True)
    additional_info = Column(Text, nullable=True)
    attendant_id = Column(
        Integer, ForeignKey("elderly_care.users.id"), nullable=True
    )  # Atendente responsável
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    user_ip = Column(String, nullable=True)
    due_date = Column(DateTime, nullable=True)  # Data limite para resolução
    overdue = Column(Boolean, default=False)  # Indica se o ticket está atrasado

    # Relacionamento com o evento
    event = relationship("Event", back_populates="ticket")

    # Relacionamento com atendente
    attendant = relationship("User", back_populates="tickets")  # Ajustado


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = {"schema": "elderly_care"}
    document_id = Column(Integer, primary_key=True, index=True)
    record_id = Column(
        Integer, ForeignKey("elderly_care.records.record_id"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("elderly_care.clients.user_id"), nullable=True
    )  # Cliente (opcional)
    document_type = Column(String(200), nullable=False)
    document_category = Column(String(200), nullable=False)
    document_storage_id = Column(String, nullable=False)
    document_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, nullable=False)
    updated_by = Column(Integer, nullable=True)
    user_ip = Column(String, nullable=True)
    index_status = Column(String(20), nullable=True)

    # Relacionamentos
    #  client = relationship("Client", back_populates="documents")  # Relacionamento com Cliente
    record = relationship("Record", back_populates="documents")
    functions = relationship(
        "Function",
        secondary="elderly_care.document_function",
        back_populates="documents",
    )


DocumentFunction = Table(
    "document_function",
    Base.metadata,
    Column(
        "document_id",
        Integer,
        ForeignKey("elderly_care.documents.document_id"),
        primary_key=True,
    ),
    Column(
        "function_id",
        Integer,
        ForeignKey("elderly_care.functions.function_id"),
        primary_key=True,
    ),
    schema="elderly_care",
)


class TempAuditLog(Base):
    __tablename__ = "temp_audit_logs"
    __table_args__ = {"schema": "elderly_care"}
    temp_audit_id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=True)
    old_data = Column(Text, nullable=True)
    new_data = Column(Text, nullable=True)
    user_ip = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "elderly_care"}
    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=True)
    old_data = Column(Text, nullable=True)
    new_data = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=func.now())
