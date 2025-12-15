"""
Главный модуль приложения FastAPI - Таможенный калькулятор
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging

from app.core.config import settings
from app.api.routes import router as api_router
from app.db.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
TEMPLATES_DIR = FRONTEND_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Customs Calculator application...")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    Таможенный калькулятор для расчета платежей при импорте товаров в Узбекистан.

    ## Возможности

    * Поиск товаров по коду ТН ВЭД или названию
    * Расчет импортных пошлин, акцизов и НДС
    * Учет страны происхождения и торгового режима
    * Актуальные курсы валют от ЦБ Узбекистана

    ## Источники данных

    * Коды ТН ВЭД и ставки пошлин: lex.uz
    * Курсы валют: cbu.uz
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR)) if TEMPLATES_DIR.exists() else None

# Include API router
app.include_router(api_router)


@app.get("/")
async def index(request: Request):
    """Serve the main page"""
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    return {
        "message": "Таможенный калькулятор API",
        "docs": "/docs",
        "api": "/api",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "app": settings.APP_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
