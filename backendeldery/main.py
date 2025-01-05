from fastapi import FastAPI, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import db_instance
from crud.crud_user import crud_user
from schemas import UserCreate
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

app = FastAPI()

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    # Converte exceções não serializáveis para strings
    error_message = str(exc) if isinstance(exc, Exception) else "An unexpected error occurred."

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "error": error_message,  # Detalhes do erro convertidos para string
        },
    )
def get_db():
    """
    Dependency para obter a sessão do banco de dados.
    """
    yield from db_instance.get_db()

@app.post("/users/register/")
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    request: Request = None,
    x_user_id: int = Header(...),  # Header obrigatório para obter o user_id
):
    """
    Endpoint para registrar um novo usuário.
    """
    try:
        # Captura o IP do cliente
        client_ip = request.client.host if request else "unknown"

        # Adiciona auditoria usando o `x_user_id` e `client_ip`
        return crud_user.create(
            db=db,
            obj_in=user,
            created_by=x_user_id,
            user_ip=client_ip
        )
    except HTTPException as e:
        raise e  # Deixa passar exceções HTTP específicas
    except Exception as e:
        # Captura erros inesperados
        raise HTTPException(status_code=500, detail=str(e))