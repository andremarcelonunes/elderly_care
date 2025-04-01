# test_user_validator.py
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backendeldery.models import Client, User
from backendeldery.schemas import UserCreate
from backendeldery.validators.user_validator import UserValidator


@pytest.fixture
def db_session(mocker):
    return mocker.Mock(spec=Session)


@pytest.fixture
def user_data():
    return UserCreate(
        name="John Doe",
        email="john.doe@example.com",
        phone="+123456789",
        role="subscriber",
        password="Strong@123",
        active=True,
        client_data={
            "cpf": "123.456.789-00",
            "birthday": "1990-01-01",
            "address": "123 Main St",
            "city": "Metropolis",
            "neighborhood": "Downtown",
            "code_address": "12345",
            "state": "NY",
        },
    )


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mock_database_url")
    monkeypatch.setenv("MONGO_URI", "mock_mongo_uri")
    monkeypatch.setenv("MONGO_DB", "mock_mongo_db")


def test_validate_user_email_exists(db_session, user_data):
    db_session.query.return_value.filter.return_value.first.return_value = User()
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_user(db_session, user_data)
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "Email already exists"


def test_validate_user_phone_exists(db_session, user_data):
    db_session.query.return_value.filter.return_value.first.side_effect = [
        None,
        User(),
    ]  # Email None, Phone exists
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_user(db_session, user_data)
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "Phone already exists"


def test_validate_client_exists(db_session, user_data):
    user = User(id=1)
    db_session.query.return_value.filter.return_value.first.return_value = Client()
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_client(db_session, user, user_data.client_data)
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "Client already exists"


def test_validate_subscriber_missing_client_data(db_session, user_data):
    user_data.client_data = None
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(db_session, user_data.model_dump())
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "You must inform client data"


def test_validate_subscriber_exists(db_session, user_data):
    db_session.query(Client).join(User).filter(
        (Client.cpf == user_data.client_data.cpf)  # Use dot notation
        & (User.email == user_data.email)
        & (User.phone == user_data.phone)
    ).first.return_value = Client()
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(db_session, user_data.model_dump())
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "The client already exists"


def test_validate_subscriber_user_exists_with_different_cpf(db_session, user_data):
    user_data.client_data.cpf = "123.456.789-40"
    db_session.query(Client).join(User).filter(
        (Client.cpf == "987.654.321-00")  # Existing client CPF
        & (User.email == user_data.email)
        & (User.phone == user_data.phone)
    ).first.return_value = Client(cpf="987.654.321-00")

    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(db_session, user_data.model_dump())
    assert excinfo.value.status_code == 422


def test_validate_subscriber_client_with_email_exists(db_session, user_data):
    db_session.query(Client).join(User).filter(
        User.phone == user_data.email
    ).first.return_value = Client()
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(db_session, user_data.model_dump())
    assert excinfo.value.status_code == 422


def test_validate_subscriber_client_with_phone_exists(db_session, user_data):
    db_session.query(Client).join(User).filter(
        User.phone == user_data.phone
    ).first.return_value = Client()
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(db_session, user_data.model_dump())
    assert excinfo.value.status_code == 422


def test_validate_association_assisted_subscriber_not_found(db_session):
    db_session.query.return_value.filter.return_value.one_or_none.return_value = None
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_assisted(
            db_session, subscriber_id=1, assisted_id=2
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Subscriber not found"


def test_validate_association_assisted_subscriber_wrong_role(db_session, mocker):
    subscriber = mocker.Mock()
    subscriber.role = "user"
    db_session.query.return_value.filter.return_value.one_or_none.return_value = (
        subscriber
    )
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_assisted(
            db_session, subscriber_id=1, assisted_id=2
        )
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "User does not have the 'subscriber' role"


def test_validate_association_assisted_assisted_not_found(db_session, mocker):
    subscriber = mocker.Mock()
    subscriber.role = "subscriber"
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        subscriber,
        None,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_assisted(
            db_session, subscriber_id=1, assisted_id=2
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Assisted not found"


def test_validate_association_assisted_another_subscriber_association(
    db_session, mocker
):
    subscriber = mocker.Mock()
    subscriber.role = "subscriber"
    assisted = mocker.Mock()
    assisted.role = "subscriber"
    assisted.id = 2
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        subscriber,
        assisted,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_assisted(
            db_session, subscriber_id=1, assisted_id=2
        )
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Another subscriber cannot be associated"


def test_validate_association_assisted_already_associated_with_another_subscriber(
    db_session, mocker
):
    subscriber = mocker.Mock()
    subscriber.role = "subscriber"
    assisted = mocker.Mock()
    assisted.role = "user"
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        subscriber,
        assisted,
    ]
    db_session.query.return_value.filter.return_value.first.side_effect = [
        True,
        None,
        None,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_assisted(
            db_session, subscriber_id=1, assisted_id=2
        )
    assert excinfo.value.status_code == 422
    assert (
        excinfo.value.detail
        == "Assisted  has been already associated with another subscriber"
    )


def test_validate_association_assisted_already_associated_with_same_subscriber(
    db_session, mocker
):
    subscriber = mocker.Mock()
    subscriber.role = "subscriber"
    assisted = mocker.Mock()
    assisted.role = "user"
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        subscriber,
        assisted,
    ]
    db_session.query.return_value.filter.return_value.first.side_effect = [
        None,
        True,
        None,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_assisted(
            db_session, subscriber_id=1, assisted_id=2
        )
    assert excinfo.value.status_code == 422
    assert (
        excinfo.value.detail
        == "Assisted  has been  already associated with this subscriber"
    )


def test_validate_association_assisted_association_already_exists(db_session, mocker):
    subscriber = mocker.Mock()
    subscriber.role = "subscriber"
    assisted = mocker.Mock()
    assisted.role = "user"
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        subscriber,
        assisted,
    ]
    db_session.query.return_value.filter.return_value.first.side_effect = [
        None,
        None,
        True,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_assisted(
            db_session, subscriber_id=1, assisted_id=2
        )
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "Association already exists"


def test_validate_association_assisted_success(db_session, mocker):
    subscriber = mocker.Mock()
    subscriber.role = "subscriber"
    assisted = mocker.Mock()
    assisted.role = "user"
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        subscriber,
        assisted,
    ]
    db_session.query.return_value.filter.return_value.first.side_effect = [
        None,
        None,
        None,
    ]
    UserValidator.validate_association_assisted(
        db_session, subscriber_id=1, assisted_id=2
    )
    # No exception should be raised


def test_validate_association_contact_client_not_found(db_session):
    db_session.query.return_value.filter.return_value.one_or_none.return_value = None
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_contact(
            db_session, client_id=1, contact_id=2
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Client not found"


def test_validate_association_contact_contact_not_found(db_session, mocker):
    client = mocker.Mock()
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        client,
        None,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_contact(
            db_session, client_id=1, contact_id=2
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Contact not found"


def test_validate_association_contact_client_own_contact(db_session, mocker):
    client = mocker.Mock(user_id=1)
    contact = mocker.Mock(id=1)
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        client,
        contact,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_contact(
            db_session, client_id=1, contact_id=1
        )
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Clients cannot be their own contacts"


def test_validate_association_contact_already_associated(db_session, mocker):
    client = mocker.Mock(user_id=1)
    contact = mocker.Mock(id=2)
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        client,
        contact,
    ]
    db_session.query.return_value.filter.return_value.first.return_value = True
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_association_contact(
            db_session, client_id=1, contact_id=2
        )
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "This contact is already associated with the client"


def test_validate_association_contact_success(db_session, mocker):
    client = mocker.Mock(user_id=1)
    contact = mocker.Mock(id=2)
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        client,
        contact,
    ]
    db_session.query.return_value.filter.return_value.first.return_value = None
    UserValidator.validate_association_contact(db_session, client_id=1, contact_id=2)
    # No exception should be raised


def test_validate_deletion_contact_association_unauthorized(db_session, mocker):
    client = mocker.Mock(user_id=1)
    contact = mocker.Mock(id=2)
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        client,
        contact,
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_deletion_contact_association(
            db_session, client_id=1, contact_id=2, x_user_id=3
        )
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "You are not authorized to delete this association"


def test_validate_deletion_contact_association_client_not_found(db_session, mocker):
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        None,  # Client not found
        mocker.Mock(id=2),  # Contact found
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_deletion_contact_association(
            db_session, client_id=1, contact_id=2, x_user_id=1
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Client not found"


def test_validate_deletion_contact_association_contact_not_found(db_session, mocker):
    client = mocker.Mock(user_id=1)
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        client,  # Client found
        None,  # Contact not found
    ]
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_deletion_contact_association(
            db_session, client_id=1, contact_id=2, x_user_id=1
        )
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Contact not found"


def test_validate_user_raises_422_when_phone_already_exists(mocker):
    # Arrange
    mock_db = mocker.Mock()

    # Create a mock UserCreate with a phone number
    mock_user_data = mocker.Mock()
    mock_user_data.email = None  # Skip email check to focus on phone validation
    mock_user_data.phone = "1234567890"

    # Mock the database query result chain
    mock_existing_user = mocker.Mock()  # Represents an existing user

    # Setup the query chain: db.query().filter().first()
    mock_filter_result = mocker.Mock()
    mock_filter_result.first.return_value = (
        mock_existing_user  # User exists with this phone
    )

    mock_query_result = mocker.Mock()
    mock_query_result.filter.return_value = mock_filter_result

    mock_db.query.return_value = mock_query_result

    import pytest
    from fastapi import HTTPException

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        UserValidator.validate_user(mock_db, mock_user_data)

    # Verify exception details
    assert exc_info.value.status_code == 422
    assert "Phone already exists" in str(exc_info.value.detail)

    # Verify the query was called with the correct parameters
    mock_db.query.assert_called_once()
    mock_query_result.filter.assert_called_once()

    # Rejects when user exists and is already a client with different CPF


def test_rejects_when_cpf_already_exists(mocker):
    mock_db = mocker.Mock()
    user_data = {
        "email": "test@example.com",
        "phone": "1234567890",
        "client_data": {"cpf": "12345678900"},
    }

    call_count = {"count": 0}

    def query_side_effect(model):
        call_count["count"] += 1
        # Call 1: existing_user query: model == User → return None
        if model == User and call_count["count"] == 1:
            user_query = mocker.Mock()
            user_query.filter.return_value.first.return_value = None
            return user_query
        # Call 2: join query (Client.join(...)): return chain that yields None
        elif model == Client and call_count["count"] == 2:
            chain = mocker.Mock()
            chain.join.return_value = chain
            chain.filter.return_value = chain
            chain.first.return_value = None
            return chain
        # Call 3: CPF query (Client.filter(Client.cpf == ...)): return truthy value
        elif model == Client and call_count["count"] == 3:
            chain = mocker.Mock()
            chain.filter.return_value = chain
            chain.first.return_value = mocker.Mock(cpf=user_data["client_data"]["cpf"])
            return chain
        # For any extra calls, return a default mock returning None.
        default = mocker.Mock()
        default.first.return_value = None
        return default

    mock_db.query.side_effect = query_side_effect

    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(mock_db, user_data)
    # Expect the CPF check to trigger
    assert excinfo.value.status_code == 422
    assert excinfo.value.detail == "This cpf already exists"


def test_validate_deletion_contact_association_not_authorized(mocker):
    # Arrange
    mock_db = mocker.Mock()
    client_id = 1
    contact_id = 10
    x_user_id = 2  # Different from client_id to trigger the 403

    # Create a fake client and contact objects
    fake_client = mocker.Mock()
    fake_client.user_id = client_id

    fake_contact = mocker.Mock()
    fake_contact.id = contact_id

    # Setup the client query: it should return a valid client object
    client_query = mocker.Mock()
    client_query.filter.return_value.one_or_none.return_value = fake_client

    # Setup the contact query: it should return a valid contact object
    contact_query = mocker.Mock()
    contact_query.filter.return_value.one_or_none.return_value = fake_contact

    # Define a side effect to differentiate between Client and User queries
    def query_side_effect(model):
        if model == Client:
            return client_query
        elif model == User:
            return contact_query
        return mocker.DEFAULT

    mock_db.query.side_effect = query_side_effect

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_deletion_contact_association(
            mock_db, client_id, contact_id, x_user_id
        )

    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "You are not authorized to delete this association"

    # Rejects when email or phone belongs to existing user with different CPF


def test_rejects_when_phone_belongs_to_existing_user_with_different_cpf(
    mocker, user_data
):
    # Para esse teste, não alteramos o telefone, deixando-o como definido no fixture.
    # Mas garantimos que o existing_user tenha o mesmo telefone e um email diferente (não influencia na verificação do telefone).
    # Assim, a condição `if existing_user.phone == user_data["phone"]` será verdadeira.

    mock_db = mocker.Mock()

    # Simula um usuário existente com o mesmo telefone que o user_data, mas email diferente
    existing_user = mocker.Mock()
    existing_user.id = 1
    existing_user.email = "different@example.com"  # email diferente
    existing_user.phone = user_data.phone  # mesmo telefone que user_data

    # Simula um client associado ao usuário existente com CPF diferente do informado em user_data
    existing_client = mocker.Mock()
    existing_client.cpf = "09876543210"

    # Configura os mocks para as queries executadas no método:
    # 1. Query para User: retorna o existing_user.
    # 2. Query para Client com join (verificando CPF, email e phone): retorna None para não disparar "The client already exists".
    # 3. Query para Client filtrando por user_id: retorna o existing_client.
    # 4. Query para Client filtrando por CPF: retorna None para não disparar "This cpf already exists".
    def query_side_effect(model):
        if model == User:
            query_mock = mocker.Mock()
            query_mock.filter.return_value.first.return_value = existing_user
            return query_mock
        elif model == Client:
            if not hasattr(query_side_effect, "client_count"):
                query_side_effect.client_count = 0
            query_side_effect.client_count += 1
            if query_side_effect.client_count == 1:
                # Query com join: retorna None para evitar o erro "The client already exists"
                join_query_mock = mocker.Mock()
                join_query_mock.join.return_value.filter.return_value.first.return_value = (
                    None
                )
                return join_query_mock
            elif query_side_effect.client_count == 2:
                # Query para obter Client pelo user_id
                query_mock = mocker.Mock()
                query_mock.filter.return_value.first.return_value = existing_client
                return query_mock
            elif query_side_effect.client_count == 3:
                # Query para obter Client pelo CPF
                query_mock = mocker.Mock()
                query_mock.filter.return_value.first.return_value = None
                return query_mock

    mock_db.query.side_effect = query_side_effect

    # Patch no logger para não produzir logs reais
    mocker.patch("backendeldery.validators.user_validator.logger")

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(mock_db, user_data.dict())

    assert excinfo.value.status_code == 422
    assert "This phone user has  already belonged to a client with another CPF" in str(
        excinfo.value.detail
    )


def test_rejects_when_email_belongs_to_existing_user_with_different_cpf(
    mocker, user_data
):
    # Arrange
    # Sobrescreve o telefone para um valor diferente do existente
    user_data.phone = "+111111111"

    mock_db = mocker.Mock()

    # Simula o usuário existente
    existing_user = mocker.Mock()
    existing_user.id = 1
    existing_user.email = user_data.email
    existing_user.phone = "+123456789"  # telefone diferente do user_data

    # Simula um client associado ao usuário existente com CPF diferente
    existing_client = mocker.Mock()
    existing_client.cpf = "09876543210"

    # --- Configuração dos mocks para as queries ---

    # Query para User: deve retornar o usuário existente
    user_query_mock = mocker.Mock()
    user_query_mock.filter.return_value.first.return_value = existing_user

    # Query para Client com join (primeira chamada): retorna None para não disparar "The client already exists"
    client_join_query_mock = mocker.Mock()
    client_join_query_mock.join.return_value.filter.return_value.first.return_value = (
        None
    )

    # Query para Client filtrando por user_id (segunda chamada): retorna o client associado
    client_user_query_mock = mocker.Mock()
    client_user_query_mock.filter.return_value.first.return_value = existing_client

    # Query para Client filtrando por CPF (terceira chamada): retorna None para não disparar "This cpf already exists"
    client_cpf_query_mock = mocker.Mock()
    client_cpf_query_mock.filter.return_value.first.return_value = None

    # Função para decidir qual mock retornar dependendo do modelo e da ordem da chamada para Client
    def query_side_effect(model):
        if model == User:
            return user_query_mock
        elif model == Client:
            if not hasattr(query_side_effect, "client_count"):
                query_side_effect.client_count = 0
            query_side_effect.client_count += 1
            if query_side_effect.client_count == 1:
                # Essa é a query com join para verificar se já existe um Client com CPF, email e phone
                return client_join_query_mock
            elif query_side_effect.client_count == 2:
                # Query para obter Client pelo user_id
                return client_user_query_mock
            elif query_side_effect.client_count == 3:
                # Query para obter Client pelo CPF
                return client_cpf_query_mock

    mock_db.query.side_effect = query_side_effect

    # Patch do logger para não gerar logs reais
    mocker.patch("backendeldery.validators.user_validator.logger")

    # Act & Assert
    with pytest.raises(HTTPException) as excinfo:
        UserValidator.validate_subscriber(mock_db, user_data.dict())

    assert excinfo.value.status_code == 422
    assert "This email user has  already belonged to a client with another CPF" in str(
        excinfo.value.detail
    )


def test_validate_user_success(db_session, user_data):
    # Simula que nenhuma query encontra um usuário com o email ou telefone
    db_session.query.return_value.filter.return_value.first.return_value = None

    # Se a função não levanta exceção, ela "passa" e pode retornar None ou algum valor padrão
    result = UserValidator.validate_user(db_session, user_data)

    # Se a função não tiver retorno (apenas valida e segue), não precisamos de assert extra.
    # Apenas garantir que nenhuma exceção foi levantada.


def test_validate_client_success(db_session, user_data):
    user = User(id=1)
    # Simula que a query não encontra nenhum client existente
    db_session.query.return_value.filter.return_value.first.return_value = None

    # Se a função não levantar exceção, a validação passou.
    result = UserValidator.validate_client(db_session, user, user_data.client_data)


def test_validate_subscriber_success(db_session, user_data, mocker):
    # Configura um side_effect para o db_session.query que simula as queries para User e Client
    def query_side_effect(model):
        if model == User:
            q = mocker.Mock()
            # Ao filtrar por email ou phone, não encontra nenhum usuário existente
            q.filter.return_value.first.return_value = None
            return q
        elif model == Client:
            q = mocker.Mock()
            # Simula o comportamento do join: quando join é chamado, retorna outro mock
            join_mock = mocker.Mock()
            # O join com filter deve retornar None para que não dispare "The client already exists"
            join_mock.filter.return_value.first.return_value = None
            q.join.return_value = join_mock
            # Se o Client for consultado diretamente (por exemplo, para buscar pelo user_id ou CPF), também retorna None
            q.filter.return_value.first.return_value = None
            return q

    db_session.query.side_effect = query_side_effect

    # Executa a validação; como nenhum conflito é encontrado, nenhuma exceção deve ser levantada.
    result = UserValidator.validate_subscriber(db_session, user_data.dict())

    # Se a função não retorna nada (apenas valida e segue), podemos assertar que o retorno é None.
    assert result is None


def test_validate_deletion_contact_association_success(db_session, mocker):
    client = mocker.Mock(user_id=1)
    contact = mocker.Mock(id=2)

    # Simula que as queries para client e contato retornam os objetos corretos
    db_session.query.return_value.filter.return_value.one_or_none.side_effect = [
        client,
        contact,
    ]
    # Simula que não há associação conflitante (first() retorna None)
    db_session.query.return_value.filter.return_value.first.return_value = None

    # x_user_id igual ao user_id do client: autorizado
    UserValidator.validate_deletion_contact_association(
        db_session, client_id=1, contact_id=2, x_user_id=1
    )
    # Se não levanta exceção, a deleção está autorizada.
