import os
import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Depends, BackgroundTasks, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("qoneqt-backend")

from backend.app.database import init_db, get_db
from backend.app.schemas.project import ContentRequestCreate

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup lifecycle hooks
    logger.info("Initializing Qoneqt AI Content Factory Backend...")
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"Database auto-creation skipped or failed on startup: {e}")
    yield
    # Shutdown lifecycle hooks
    logger.info("Shutting down Qoneqt AI Content Factory Backend...")


app = FastAPI(
    title="Qoneqt AI Content Factory API",
    description="Automated pipeline from topic selection to short-form video production and publishing to Qoneqt.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
from backend.app.routers.projects import router as projects_router
from backend.app.routers.publish import router as publish_router
from backend.app.routers.subscription import router as subscription_router

# Mount static media storage directory
os.makedirs("./storage", exist_ok=True)
app.mount("/storage", StaticFiles(directory="./storage"), name="storage")

# Register API Routers
app.include_router(projects_router)
app.include_router(publish_router)
app.include_router(subscription_router)

@app.post("/api/generate-pipeline", tags=["Projects Pipeline"], status_code=201)
async def generate_pipeline_direct(
    request: ContentRequestCreate,
    background_tasks: BackgroundTasks,
    execution_mode: Optional[str] = Query(default=None),
    x_user_id: Optional[str] = Header(default="default_user", alias="X-User-Id"),
    db: AsyncSession = Depends(get_db)
):
    from backend.app.routers.projects import create_project
    return await create_project(
        request=request,
        background_tasks=background_tasks,
        execution_mode=execution_mode,
        x_user_id=x_user_id,
        db=db
    )

@app.get("/health", tags=["System"])
async def healthcheck():
    """
    System healthcheck endpoint used by Docker and load balancers.
    """
    return {
        "status": "healthy",
        "service": "qoneqt-ai-content-factory-backend",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/", tags=["System"])
async def root():
    return {
        "name": "Qoneqt AI Content Factory API",
        "status": "online",
        "documentation": "/docs"
    }

