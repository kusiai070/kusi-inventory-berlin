"""
Products management module
Módulo de gestión de productos
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, and_, func
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import (
    Product, Category, Provider, Restaurant, StockMovement, User, get_db
)
from backend.models.enums import StockMovementType
from backend.api.auth import get_current_user, SessionLocal

# Router
router = APIRouter()

# Pydantic models
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    barcode: Optional[str] = None
    unit: str
    current_stock: Decimal = Decimal('0.0')
    min_stock: Decimal = Decimal('0.0')
    max_stock: Decimal = Decimal('100.0')
    cost_price: Decimal = Decimal('0.0')
    selling_price: Decimal = Decimal('0.0')
    category_id: int
    provider_id: int

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    barcode: Optional[str] = None
    unit: Optional[str] = None
    current_stock: Optional[Decimal] = None
    min_stock: Optional[Decimal] = None
    max_stock: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    category_id: Optional[int] = None
    provider_id: Optional[int] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    barcode: Optional[str]
    unit: str
    current_stock: Decimal
    min_stock: Decimal
    max_stock: Decimal
    cost_price: Decimal
    selling_price: Decimal
    category_id: int
    provider_id: int
    restaurant_id: int
    category_name: str
    provider_name: str
    stock_status: str
    created_at: str
    updated_at: Optional[str]

@router.post("/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new product"""
    # Validate restaurant ownership
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    # Check if barcode already exists
    if product.barcode:
        existing = db.query(Product).filter(Product.barcode == product.barcode).first()
        if existing:
            raise HTTPException(status_code=400, detail="Barcode already exists")
    
    # Create product
    db_product = Product(
        **product.dict(),
        restaurant_id=current_user.restaurant_id
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Create initial stock movement
    if product.current_stock > 0:
        movement = StockMovement(
            product_id=db_product.id,
            movement_type=StockMovementType.IN,
            quantity=product.current_stock,
            previous_stock=Decimal('0.0'),
            new_stock=product.current_stock,
            reason="Initial stock",
            user_id=current_user.id,
            restaurant_id=current_user.restaurant_id
        )
        db.add(movement)
        db.commit()
    
    return get_product_response(db_product, db)

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    stock_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all products for current user's restaurant"""
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    query = db.query(Product).filter(Product.restaurant_id == current_user.restaurant_id)
    
    # Filters
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    
    if stock_status:
        if stock_status == "low":
            query = query.filter(Product.current_stock <= Product.min_stock)
        elif stock_status == "ok":
            query = query.filter(Product.current_stock > Product.min_stock)
    
    products = query.offset(skip).limit(limit).all()
    
    return [get_product_response(p, db) for p in products]

@router.get("/categories/list")
async def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all categories"""
    categories = db.query(Category).filter(Category.is_active == True).all()
    return [{"id": c.id, "name": c.name, "type": c.type, "icon": c.icon} for c in categories]

@router.get("/providers/list")
async def get_providers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all providers"""
    providers = db.query(Provider).filter(Provider.is_active == True).all()
    return [{"id": p.id, "name": p.name, "contact_person": p.contact_person} for p in providers]

@router.get("/stats")
async def get_product_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get product statistics"""
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    # Basic stats
    total_products = db.query(Product).filter(Product.restaurant_id == current_user.restaurant_id).count()
    
    # Stock status counts
    low_stock = db.query(Product).filter(
        and_(Product.restaurant_id == current_user.restaurant_id,
             Product.current_stock <= Product.min_stock)
    ).count()
    
    # Total inventory value
    total_value = db.query(func.sum(Product.current_stock * Product.cost_price)).filter(
        Product.restaurant_id == current_user.restaurant_id
    ).scalar() or Decimal('0.0')
    
    return {
        "total_products": total_products,
        "low_stock_products": low_stock,
        "total_inventory_value": round(total_value, 2),
        "stock_status": {
            "low": low_stock,
            "ok": total_products - low_stock
        }
    }

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check restaurant ownership
    if product.restaurant_id != current_user.restaurant_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this product")
    
    return get_product_response(product, db)

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a product"""
    # Use with_for_update to lock the row during update
    product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check restaurant ownership
    if product.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this product")
    
    # Track stock changes
    old_stock = product.current_stock
    
    # Update fields
    for field, value in product_update.dict(exclude_unset=True).items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    # Create stock movement if stock changed
    if product_update.current_stock is not None:
        if product_update.current_stock < 0:
            raise HTTPException(status_code=400, detail="Stock cannot be negative")
            
        if old_stock != product.current_stock:
            movement_type = StockMovementType.IN if product.current_stock > old_stock else StockMovementType.OUT
            movement = StockMovement(
                product_id=product.id,
                movement_type=movement_type,
            quantity=abs(product.current_stock - old_stock),
            previous_stock=old_stock,
            new_stock=product.current_stock,
            reason="Manual adjustment",
            user_id=current_user.id,
            restaurant_id=current_user.restaurant_id
        )
        db.add(movement)
        db.commit()
    
    return get_product_response(product, db)

@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check restaurant ownership and admin role
    if product.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this product")
    
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admins or managers can delete products")
    
    db.delete(product)
    db.commit()
    
    return {"message": "Product deleted successfully"}



# Helper function
def get_product_response(product: Product, db: Session) -> ProductResponse:
    """Convert product to response model with additional info"""
    category = db.query(Category).filter(Category.id == product.category_id).first()
    provider = db.query(Provider).filter(Provider.id == product.provider_id).first()
    
    # Determine stock status
    if product.current_stock <= product.min_stock:
        stock_status = "low"
    elif product.current_stock >= product.max_stock:
        stock_status = "high"
    else:
        stock_status = "ok"
    
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        barcode=product.barcode,
        unit=product.unit,
        current_stock=product.current_stock,
        min_stock=product.min_stock,
        max_stock=product.max_stock,
        cost_price=product.cost_price,
        selling_price=product.selling_price,
        category_id=product.category_id,
        provider_id=product.provider_id,
        restaurant_id=product.restaurant_id,
        category_name=category.name if category else "Unknown",
        provider_name=provider.name if provider else "Unknown",
        stock_status=stock_status,
        created_at=product.created_at.isoformat() if product.created_at else None,
        updated_at=product.updated_at.isoformat() if product.updated_at else None
    )