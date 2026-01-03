from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from werkzeug.security import generate_password_hash
import sys
import os

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import Restaurant, User
from backend.api.auth import get_current_user, SessionLocal

# Router
router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schemas
class RestaurantCreate(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    admin_email: EmailStr
    admin_name: str
    admin_password: str

class RestaurantResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: datetime
    admin_email: Optional[str]

    class Config:
        from_attributes = True

# Middleware de seguridad (Mock por ahora, idealmente verificar role="super_admin")
def check_super_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "super_admin":
        # Por simplicidad en desarrollo, permitimos al admin del ID 1 actuar como super admin
        # En producción esto debe ser estricto
        if current_user.id != 1: 
             raise HTTPException(status_code=403, detail="Requiere privilegios de Super Admin")
    return current_user

@router.post("/tenants", response_model=RestaurantResponse)
async def create_tenant(
    tenant: RestaurantCreate,
    current_user: User = Depends(check_super_admin),
    db: Session = Depends(get_db)
):
    """Crear un nuevo restaurante (Inquilino)"""
    
    # 1. Verificar si existe
    existing = db.query(Restaurant).filter(Restaurant.name == tenant.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="El restaurante ya existe")
        
    # 2. Verificar email admin
    existing_user = db.query(User).filter(User.email == tenant.admin_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El email del administrador ya está en uso")

    try:
        # 3. Crear Restaurante
        new_restaurant = Restaurant(
            name=tenant.name,
            address=tenant.address,
            phone=tenant.phone,
            email=tenant.email,
            is_active=True
        )
        db.add(new_restaurant)
        db.flush() # Para obtener ID
        
        # 4. Crear Admin del Restaurante
        new_admin = User(
            email=tenant.admin_email,
            hashed_password=generate_password_hash(tenant.admin_password),
            full_name=tenant.admin_name,
            role="admin",
            restaurant_id=new_restaurant.id
        )
        db.add(new_admin)
        
        db.commit()
        db.refresh(new_restaurant)
        
        return {
            "id": new_restaurant.id,
            "name": new_restaurant.name,
            "is_active": new_restaurant.is_active,
            "created_at": new_restaurant.created_at,
            "admin_email": tenant.admin_email
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tenants", response_model=List[RestaurantResponse])
async def list_tenants(
    current_user: User = Depends(check_super_admin),
    db: Session = Depends(get_db)
):
    """Listar todos los restaurantes"""
    restaurants = db.query(Restaurant).all()
    # Enriquecer con email del admin (costoso pero simple para MVP)
    results = []
    for r in restaurants:
        admin = db.query(User).filter(User.restaurant_id == r.id, User.role == "admin").first()
        results.append({
            "id": r.id,
            "name": r.name,
            "is_active": r.is_active,
            "created_at": r.created_at,
            "admin_email": admin.email if admin else None
        })
    return results

@router.put("/tenants/{tenant_id}/status")
async def toggle_tenant_status(
    tenant_id: int,
    is_active: bool,
    current_user: User = Depends(check_super_admin),
    db: Session = Depends(get_db)
):
    """Activar/Suspender restaurante"""
    restaurant = db.query(Restaurant).filter(Restaurant.id == tenant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurante no encontrado")
        
    restaurant.is_active = is_active
    db.commit()
    
    status_msg = "activado" if is_active else "suspendido"
    return {"message": f"Restaurante {restaurant.name} ha sido {status_msg}"}
