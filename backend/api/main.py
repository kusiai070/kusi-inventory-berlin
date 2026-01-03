"""
Enterprise Restaurant Inventory System - Main API
Sistema Enterprise de Inventarios para Restaurantes
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import Base, engine
from backend.api.auth import router as auth_router, get_current_user
from backend.api.products import router as products_router
from backend.api.invoices import router as invoices_router
from backend.api.counts import router as counts_router
from backend.api.reports import router as reports_router
from backend.api.wastes import router as wastes_router
from backend.api.dashboard import router as dashboard_router
from backend.api.admin import router as admin_router
from backend.config import settings

# Lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Iniciando Sistema Enterprise de Inventarios...")
    print("📡 API REST configurada correctamente")
    yield
    # Shutdown
    print("🛑 Cerrando sistema...")

# Create FastAPI app
app = FastAPI(
    title="Enterprise Restaurant Inventory System",
    description="Sistema Enterprise de Inventarios Multi-Restaurante con OCR",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration - Secure
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(products_router, prefix="/api/products", tags=["Products"])
app.include_router(invoices_router, prefix="/api/invoices", tags=["Invoices"])
app.include_router(counts_router, prefix="/api/counts", tags=["Physical Counts"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])
app.include_router(wastes_router, prefix="/api/wastes", tags=["Waste Management"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(admin_router, prefix="/api/admin", tags=["Super Admin"])

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Root endpoint - serve main app
@app.get("/")
async def serve_app():
    """Serve the main application"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Enterprise Restaurant Inventory System API", "status": "running"}

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Enterprise Restaurant Inventory System",
        "version": "1.0.0"
    }

# Protected test endpoint
@app.get("/api/test-auth")
async def test_auth(current_user = Depends(get_current_user)):
    """Test endpoint to verify authentication"""
    return {
        "message": "Authentication working correctly",
        "user": current_user.email,
        "role": current_user.role
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🏪 Enterprise Restaurant Inventory System")
    print("🚀 Starting server...")
    print("📡 API available at: http://localhost:8000")
    print("📊 Documentation: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)