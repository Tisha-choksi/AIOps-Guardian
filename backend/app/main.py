import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

from backend.app.config import settings
from backend.app.logging_config import configure_logging, correlation_id_var, get_logger
from backend.app.routers import auth, health, investigate, investigations

configure_logging(settings.log_level)
logger = get_logger(__name__)


class CorrelationIdMiddleware:
    """Pure ASGI middleware threading a correlation ID through the request.

    Also stashes the ID on `scope["state"]` (not just the contextvar): a
    handler registered for the bare `Exception` class is special-cased by
    Starlette and hoisted to ServerErrorMiddleware, the true outermost ASGI
    layer - by the time it runs, this middleware's `finally` has already
    reset the contextvar, so the crash-path handler below reads state
    instead to still report the right ID.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        correlation_id = headers.get(b"x-correlation-id", b"").decode() or str(uuid.uuid4())
        scope.setdefault("state", {})["correlation_id"] = correlation_id
        token = correlation_id_var.set(correlation_id)

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(scope=message)
                response_headers.append("X-Correlation-ID", correlation_id)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            correlation_id_var.reset(token)


fastapi_app = FastAPI(title="AIOps Guardian", version="0.1.0")
fastapi_app.add_middleware(CorrelationIdMiddleware)

fastapi_app.include_router(health.router)
fastapi_app.include_router(auth.router)
fastapi_app.include_router(investigate.router)
fastapi_app.include_router(investigations.router)


@fastapi_app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception")
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": str(exc),
            "correlation_id": getattr(request.state, "correlation_id", correlation_id_var.get()),
        },
    )


# Wrapped around the FastAPI instance itself (not fastapi_app.add_middleware)
# so CORS headers still apply to responses from the generic `Exception`
# handler above: Starlette hoists that handler to ServerErrorMiddleware,
# which sits outside every add_middleware() layer, CORS included. `app` is
# the ASGI entrypoint (what uvicorn serves); `fastapi_app` stays directly
# reachable for things CORSMiddleware doesn't proxy, e.g. dependency_overrides
# in tests.
app = CORSMiddleware(
    fastapi_app,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
