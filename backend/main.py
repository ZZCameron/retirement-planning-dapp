import os
from fastapi.responses import FileResponse
"""
Main FastAPI application entry point.
Retirement Planning DApp - Canadian Rules Implementation.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from backend.api.v1 import retirement, batch_retirement
from backend.config import settings
from backend.models.retirement_plan import HealthCheckResponse

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Solana Network: {settings.solana_network}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info(f"CORS Origins: {settings.cors_origins}")
    logger.info(f"CORS Origins List: {settings.cors_origins_list}")
    yield
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Canadian Retirement Planning Service with Web3 Integration",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Security Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*"] if settings.debug else ["yourdomain.com"],
)

# Serve static files (templates, Excel, etc.)
from fastapi.staticfiles import StaticFiles
# Skip static files in test mode
if not os.getenv('TESTING'):
    app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Template download endpoints
@app.get("/api/v1/templates/excel")
async def download_excel_template():
    """Download Excel analysis template"""
    import os
    from fastapi.responses import FileResponse
    
    template_path = os.path.join(os.path.dirname(__file__), "static", "templates", "Retirement_Analysis_Template.xlsx")
    
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail=f"Template not found at {template_path}")
    
    return FileResponse(
        path=template_path,
        filename="Retirement_Analysis_Template.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=Retirement_Analysis_Template.xlsx",
            "Cache-Control": "no-cache"
        }
    )

@app.get("/api/v1/templates/sheets-guide")
async def download_sheets_guide():
    """Download Google Sheets guide"""
    import os
    guide_path = os.path.join(os.path.dirname(__file__), "static", "templates", "google_sheets_guide.html")
    if not os.path.exists(guide_path):
        raise HTTPException(status_code=404, detail="Guide not found")
    return FileResponse(
        path=guide_path,
        filename="Google_Sheets_Retirement_Analysis_Guide.html",
        media_type="text/html"
    )

def download_sheets_guide():
    """Download Google Sheets guide"""
    from pathlib import Path
    guide_path = Path(__file__).parent / "static" / "templates" / "GOOGLE_SHEETS_GUIDE.md"
    return FileResponse(
        path=str(guide_path),
        filename="GOOGLE_SHEETS_GUIDE.md",
        media_type="text/markdown"
    )


# CORS Middleware (must be added before other middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],
)

# Serve static files (templates, Excel, etc.)
from fastapi.staticfiles import StaticFiles
# Skip static files in test mode
if not os.getenv('TESTING'):
    app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Template download endpoints
@app.get("/api/v1/templates/excel")
async def download_excel_template():
    """Download Excel analysis template"""
    from pathlib import Path
    template_path = Path(__file__).parent / "static" / "templates" / "Retirement_Analysis_Template.xlsx"
    return FileResponse(
        path=str(template_path),
        filename="Retirement_Analysis_Template.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.get("/api/v1/templates/sheets-guide")
async def download_sheets_guide():
    """Download Google Sheets guide"""
    from pathlib import Path
    guide_path = Path(__file__).parent / "static" / "templates" / "GOOGLE_SHEETS_GUIDE.md"
    return FileResponse(
        path=str(guide_path),
        filename="GOOGLE_SHEETS_GUIDE.md",
        media_type="text/markdown"
    )



@app.get("/", response_model=HealthCheckResponse)
async def root():
    """Root endpoint with basic info."""
    return HealthCheckResponse(
        status="online",
        version=settings.app_version,
        environment=settings.environment,
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    return HealthCheckResponse(
        status="healthy",
        version=settings.app_version,
        environment=settings.environment,
    )


# Include API routers
app.include_router(
    retirement.router,
    prefix="/api/v1/retirement",
    tags=["retirement"]
)

app.include_router(
    batch_retirement.router,
    prefix="/api/v1/retirement",
    tags=["Batch Calculations"]
)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
