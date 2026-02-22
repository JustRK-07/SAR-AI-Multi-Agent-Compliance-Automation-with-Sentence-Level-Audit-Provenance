from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routers import alerts, sar, audit, transactions, websocket
from app.db.database import create_tables

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting SAR Narrative Generator...")
    create_tables()
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    description="AI-powered SAR narrative generation with complete audit trail",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(sar.router, prefix="/api/sar", tags=["SAR"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(websocket.router, tags=["WebSocket"])


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": settings.app_name}


@app.get("/")
def root():
    return {
        "message": "SAR Narrative Generator API",
        "docs": "/docs",
        "health": "/health",
    }
