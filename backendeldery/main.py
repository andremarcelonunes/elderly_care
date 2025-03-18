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
    errors = exc.errors()
    for error in errors:
        if "ctx" in error and "error" in error["ctx"]:
            error["ctx"]["error"] = str(error["ctx"]["error"])
    return JSONResponse(
        status_code=400,
        content={"detail": errors, "body": exc.body},
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
