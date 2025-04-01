from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backendeldery.routers.attendant import router as attendants_router
from backendeldery.routers.teams import router as teams_router
from backendeldery.routers.users import router as users_router

app = FastAPI()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Verifica se é um erro de JSON
    if hasattr(exc, "body") and isinstance(exc.body, str):
        try:
            # Tenta decodificar o JSON para identificar o erro
            import json

            json.loads(exc.body)
        except json.JSONDecodeError as json_exc:
            # Extrai a linha do erro
            error_line = json_exc.lineno

            # Lê o JSON até a linha do erro
            lines = exc.body.split("\n")
            error_line_content = lines[error_line - 1]

            return JSONResponse(
                status_code=400,
                content={
                    "detail": [
                        {
                            "field": "body",
                            "message": f"Erro de formatação JSON na linha {error_line}:"
                            f" {error_line_content}",
                        }
                    ]
                },
            )

    # Se não for erro de JSON, continua com o tratamento normal
    errors = exc.errors()
    formatted_errors = []

    for error in errors:
        field = ".".join(str(x) for x in error["loc"])
        message = error["msg"]

        # Mensagens mais amigáveis para erros comuns
        if "email" in field.lower():
            message = "Por favor, insira um endereço de e-mail válido"
        elif "password" in field.lower():
            message = (
                "A senha deve conter pelo menos 8 caracteres, incluindo letras "
                "maiúsculas, minúsculas e números"
            )
        elif "cpf" in field.lower():
            message = "Por favor, insira um CPF válido"
        elif "phone" in field.lower():
            message = "Por favor, insira um número de telefone válido"

        formatted_errors.append({"field": field, "message": message})

    return JSONResponse(
        status_code=400, content={"detail": formatted_errors, "body": exc.body}
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    error_message = (
        str(exc) if isinstance(exc, Exception) else "An unexpected error occurred."
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "error": error_message,
        },
    )


app.include_router(users_router, prefix="/api/v1", tags=["users"])
app.include_router(attendants_router, prefix="/api/v1", tags=["attendants"])
app.include_router(teams_router, prefix="/api/v1", tags=["teams"])
