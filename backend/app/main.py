"""
Mosaico FastAPI Application
Modern backend for Google Sheets Add-on
NO LangChain - Direct Vertex AI SDK
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api import generate
from app.api import translate
from app.api import refine
from app.api import projects
from app.api import upload
from app.api import project_generation
from app.api import export
from app.api import optimize_prompt
# from app.api import generate_from_image

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("=" * 50)
    logger.info("MOSAICO BACKEND STARTING")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"GCP Project: {settings.gcp_project_id}")
    logger.info(f"Vertex AI Model: {settings.vertex_ai_model}")
    logger.info("=" * 50)
    yield
    # Shutdown
    logger.info("Mosaico backend shutting down")


# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="AI Content Creation Co-Pilot for Google Sheets",
    lifespan=lifespan
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.get("/", include_in_schema=False)
async def root():
    """Health check endpoint"""
    return {
        "service": "Mosaico API",
        "version": settings.api_version,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "vertex_ai_model": settings.vertex_ai_model
    }


# Include routers
app.include_router(generate.router, prefix="/api/v1", tags=["Generate"])
app.include_router(translate.router, prefix="/api/v1", tags=["Translate"])
app.include_router(refine.router, prefix="/api/v1", tags=["Refine"])
app.include_router(optimize_prompt.router, prefix="/api/v1", tags=["Optimize"])
app.include_router(projects.router, prefix="/api/v1", tags=["Projects"])
app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
app.include_router(project_generation.router, prefix="/api/v1", tags=["Projects"])
app.include_router(export.router, prefix="/api/v1", tags=["Export"])
# app.include_router(generate_from_image.router, prefix="/api/v1", tags=["Generate"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level=settings.log_level.lower()
    )
