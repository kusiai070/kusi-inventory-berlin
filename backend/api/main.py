"""
Enterprise Restaurant Inventory System - Main API
Sistema Enterprise de Inventarios para Restaurantes
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

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
    print("Iniciando Sistema Enterprise de Inventarios...")
    print("API REST configurada correctamente")
    yield
    # Shutdown
    print("Cerrando sistema...")

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
# En ejecución local (sin Docker), main.py está en backend/api/
# y frontend/ está en la raíz del proyecto (dos niveles arriba)
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
static_dir = project_root / "frontend"

print(f"Ruta Base del Proyecto: {project_root}")
print(f"Buscando frontend en: {static_dir}")

if static_dir.exists():
    print("Frontend encontrado. Montando estaticos...")
    try:
        print(f"Contenido de frontend: {os.listdir(static_dir)}")
        if (static_dir / "js").exists():
            print(f"Contenido de frontend/js: {os.listdir(static_dir / 'js')}")
    except Exception as e:
        print(f"Error listando archivos: {e}")

    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Mount JS and other static assets for root-level HTML files
    if (static_dir / "js").exists():
        app.mount("/js", StaticFiles(directory=str(static_dir / "js")), name="js")
    if (static_dir / "locales").exists():
        app.mount("/locales", StaticFiles(directory=str(static_dir / "locales")), name="locales")
else:
    print(f"ERROR CRITICO: No se encuentra la carpeta frontend en {static_dir}")

# Root endpoint - serve main app
@app.get("/")
async def serve_app():
    """Serve the main application"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Enterprise Restaurant Inventory System API", "status": "running"}

# Explicit routes for all HTML pages (production compatibility)
@app.get("/dashboard.html")
async def dashboard():
    """Serve dashboard page"""
    return FileResponse(os.path.join(static_dir, "dashboard.html"))

@app.get("/admin.html")
async def admin():
    """Serve admin page"""
    return FileResponse(os.path.join(static_dir, "admin.html"))

@app.get("/count.html")
async def count():
    """Serve count page"""
    return FileResponse(os.path.join(static_dir, "count.html"))

@app.get("/inventory.html")
async def inventory():
    """Serve inventory page"""
    return FileResponse(os.path.join(static_dir, "inventory.html"))

@app.get("/ocr.html")
async def ocr():
    """Serve OCR page"""
    return FileResponse(os.path.join(static_dir, "ocr.html"))

@app.get("/reports.html")
async def reports():
    """Serve reports page"""
    return FileResponse(os.path.join(static_dir, "reports.html"))

@app.get("/waste.html")
async def waste():
    """Serve waste management page"""
    return FileResponse(os.path.join(static_dir, "waste.html"))

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
    import os
    
    print("Enterprise Restaurant Inventory System")
    print("Starting server...")
    port = int(os.environ.get("PORT", 8000))
    print(f"API available at: http://localhost:{port}")
    print(f"Documentation: http://localhost:{port}/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)