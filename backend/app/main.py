"""Main FastAPI application."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import admin, auth, chat
from app.core.config import get_settings
from app.core.errors import MindwellError
from app.core.logging import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan context manager for startup/shutdown."""
    logger.info("Application starting up")
    yield
    logger.info("Application shutting down")


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title="Mindwell AI API",
    description="Production-ready MVP for Mindwell-style AI features",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(MindwellError)
async def mindwell_error_handler(request: Request, exc: MindwellError) -> JSONResponse:
    """Handle custom application errors."""
    logger.error(
        "Application error",
        error_type=type(exc).__name__,
        message=exc.message,
        details=exc.details,
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": exc.message, "details": exc.details},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    logger.error(
        "Unexpected error",
        error_type=type(exc).__name__,
        message=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )


# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(admin.router)


# Health check
@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


# Root
@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "name": "Mindwell AI API",
        "version": "0.1.0",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
