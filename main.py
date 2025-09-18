from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import time

from app.core.config import settings
from app.core.logging import logger, log_api_request
from app.models.database import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Database setup
engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting EwayAuto application...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized successfully")
    yield
    
    # Shutdown
    logger.info("Shutting down EwayAuto application...")

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Playwright-based E-way Bill Automation with Web Interface and API",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
templates = Jinja2Templates(directory=settings.templates_dir)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    log_api_request(request.method, str(request.url))
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Request processed in {process_time:.2f}s - Status: {response.status_code}")
    
    return response

# Dependency to get database session
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.app_name}

# Import and include routers
from app.api.routes.automation import router as automation_router
from app.api.routes.auth import router as auth_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.extensions import router as extensions_router

# Include routers
app.include_router(automation_router, prefix="/api/automation", tags=["automation"])
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(extensions_router, prefix="/api/extensions", tags=["extensions"])

# Root endpoint - serve the main dashboard
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "settings": settings})

# Operations page
@app.get("/operations")
async def operations_page(request: Request):
    return templates.TemplateResponse("operations.html", {"request": request, "settings": settings})

# Session manager page
@app.get("/sessions")
async def session_manager_page(request: Request):
    return templates.TemplateResponse("session_manager.html", {"request": request, "settings": settings})

# Extensions page
@app.get("/extensions")
async def extensions_page(request: Request):
    return templates.TemplateResponse("extensions.html", {"request": request, "settings": settings})

# Reports page
@app.get("/reports")
async def reports_page(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request, "settings": settings})

# Settings page
@app.get("/settings")
async def settings_page(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request, "settings": settings})

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
