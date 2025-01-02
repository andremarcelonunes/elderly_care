from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi import HTTPException
from datetime import datetime

# Contexto de hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def obj_to_dict(obj, exclude_fields=None):
    """
    Converte um objeto SQLAlchemy em um dicionário.

    :param obj: Objeto SQLAlchemy
    :param exclude_fields: Campos a serem excluídos do dicionário
    :return: Dicionário contendo os dados do objeto
    """
    if not obj:
        return None
    exclude_fields = exclude_fields or []
    return {
        col.name: getattr(obj, col.name)
        for col in obj.__table__.columns
        if col.name not in exclude_fields
    }


def hash_password(password: str) -> str:
    """
    Gera o hash de uma senha.

    :param password: Senha em texto claro
    :return: Hash da senha
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha em texto claro corresponde ao hash.

    :param plain_password: Senha em texto claro
    :param hashed_password: Hash da senha
    :return: True se a senha for válida, False caso contrário
    """
    return pwd_context.verify(plain_password, hashed_password)


def format_response(data=None, message="Success", status="ok"):
    """
    Formata a resposta da API.

    :param data: Dados a serem retornados
    :param message: Mensagem descritiva
    :param status: Status da resposta ('ok', 'error', etc.)
    :return: Dicionário formatado
    """
    return {
        "status": status,
        "message": message,
        "data": data
    }


def validate_foreign_key(db: Session, model, field_name: str, value: int):
    """
    Verifica se um valor de chave estrangeira existe no banco de dados.

    :param db: Sessão do banco de dados
    :param model: Modelo SQLAlchemy relacionado
    :param field_name: Nome do campo a ser validado
    :param value: Valor da chave estrangeira
    :return: None, lança uma exceção HTTP se não for válido
    """
    if not db.query(model).filter(getattr(model, field_name) == value).first():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid foreign key: {field_name} with value {value} does not exist."
        )


def current_timestamp() -> str:
    """
    Retorna o timestamp atual no formato ISO 8601.

    :return: String com o timestamp atual
    """
    return datetime.utcnow().isoformat()