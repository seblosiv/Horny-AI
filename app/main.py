"""
FastAPI main application
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.rate_limiter import rate_limiter
from app.routers import auth, api_keys, bots, wallet, chat, webhooks

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting B2B Chat API...")

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Connect to Redis
    try:
        await rate_limiter.connect()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down B2B Chat API...")
    await rate_limiter.disconnect()


app = FastAPI(
    title="B2B Chat API",
    description="CandyAI-style B2B Chat API Provider with DeepInfra backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID and timing middleware
@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    """Add request ID and timing to all requests"""
    request_id = f"req_{int(time.time() * 1000)}"
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.3f}"

    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s - "
        f"ID: {request_id}"
    )

    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "type": "server_error"
            }
        }
    )


# Include routers
app.include_router(auth.router)
app.include_router(api_keys.router)
app.include_router(bots.router)
app.include_router(wallet.router)
app.include_router(chat.router)
app.include_router(webhooks.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "B2B Chat API",
        "version": "0.1.0",
        "description": "CandyAI-style B2B Chat API Provider",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": int(time.time())
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )
