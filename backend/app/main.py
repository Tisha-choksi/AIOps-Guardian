import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.config import settings
from backend.app.logging_config import configure_logging, correlation_id_var, get_logger
from backend.app.routers import health, investigate

configure_logging(settings.log_level)
logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        token = correlation_id_var.set(correlation_id)
        try:
            response = await call_next(request)
        finally:
            correlation_id_var.reset(token)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


app = FastAPI(title="AIOps Guardian", version="0.1.0")
app.add_middleware(CorrelationIdMiddleware)

app.include_router(health.router)
app.include_router(investigate.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": str(exc),
            "correlation_id": correlation_id_var.get(),
        },
    )
