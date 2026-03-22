from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from application.services.errors import IntegrationError, NotFoundError, PermissionDenied, ServiceError, ValidationError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ServiceError)
    async def handle_service_error(_: Request, exc: ServiceError) -> JSONResponse:
        status_code = 400
        if isinstance(exc, NotFoundError):
            status_code = 404
        elif isinstance(exc, PermissionDenied):
            status_code = 403
        elif isinstance(exc, ValidationError):
            status_code = 422
        elif isinstance(exc, IntegrationError):
            status_code = 503
        return JSONResponse(status_code=status_code, content={"error_code": exc.code, "message": exc.message})
