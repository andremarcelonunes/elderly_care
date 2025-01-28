from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from backendeldery.routers.users import router as users_router

app = FastAPI()

# Handlers de exceções globais
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

# Inclusão dos roteadores
app.include_router(users_router, prefix="/api/v1", tags=["users"])