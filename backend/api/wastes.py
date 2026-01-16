"""
Waste Management module
Módulo de gestión de mermas
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import WasteLog, Product, User
from backend.models.enums import WasteType
from backend.api.auth import get_current_user, SessionLocal

# Router
router = APIRouter()

# Pydantic models
class WasteCreate(BaseModel):
    product_id: int
    quantity: Decimal
    waste_type: WasteType
    reason: Optional[str] = None

class WasteUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    waste_type: Optional[WasteType] = None
    reason: Optional[str] = None

class WasteResponse(BaseModel):
    id: int
    product_name: str
    quantity: Decimal
    unit: str
    waste_type: str
    reason: Optional[str]
    cost: Decimal
    user_name: str
    created_at: str

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=dict)
async def create_waste_log(
    waste: WasteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new waste log entry"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    # Validate waste type (Handled by Pydantic)
    # valid_types = ["preparation", "expired", "damaged"]
    # if waste.waste_type not in valid_types:
    #    raise HTTPException(status_code=400, detail=f"Invalid waste type. Must be one of: {', '.join(valid_types)}")
    
    # Get product with row lock to prevent race conditions
    product = db.query(Product).filter(Product.id == waste.product_id).with_for_update().first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check restaurant ownership
    if product.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=403, detail="Not authorized to create waste log for this product")
    
    # Validate quantity
    if waste.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
    
    if waste.quantity > product.current_stock:
        raise HTTPException(status_code=400, detail="Waste quantity cannot exceed current stock")
    
    # Calculate cost
    cost = waste.quantity * product.cost_price
    
    # Create waste log
    waste_log = WasteLog(
        product_id=waste.product_id,
        restaurant_id=current_user.restaurant_id,
        quantity=waste.quantity,
        waste_type=waste.waste_type,
        reason=waste.reason,
        cost=cost,
        user_id=current_user.id
    )
    
    db.add(waste_log)
    db.flush()  # Get waste_log.id before stock update

    # Anomaly detection (MVP Z-Score)
    try:
        from backend.utils.anomaly_detector import AnomalyDetector
        
        anomaly_analysis = AnomalyDetector.analyze_waste(
            db=db,
            product_id=waste.product_id,
            quantity=waste.quantity,
            restaurant_id=current_user.restaurant_id,
            days=30
        )
        
        # If anomalous, create Alert
        if anomaly_analysis.get("analysis_possible") and anomaly_analysis["detection"]["is_anomalous"]:
            from backend.models.database import Alert
            
            alert = Alert(
                restaurant_id=current_user.restaurant_id,
                alert_type="waste_anomaly",
                severity=anomaly_analysis["detection"]["severity"],
                title=f"Anomalous waste detected: {product.name}",
                message=anomaly_analysis["interpretation"],
                is_active=True
            )
            db.add(alert)
    except Exception as e:
        print(f"Anomaly check failed: {e}")  # Non-blocking

    
    # Update product stock atomically (prevent race conditions)
    rows_updated = db.query(Product).filter(
        Product.id == waste.product_id
    ).update({
        "current_stock": Product.current_stock - waste.quantity
    }, synchronize_session=False)
    
    if rows_updated == 0:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update stock")
    
    db.commit()
    db.refresh(waste_log)
    
    # Get updated stock for response
    product = db.query(Product).filter(Product.id == waste.product_id).first()
    
    return {
        "message": "Waste log created successfully",
        "waste_id": waste_log.id,
        "cost": cost,
        "remaining_stock": product.current_stock
    }

@router.get("/", response_model=List[dict])
async def get_waste_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    waste_type: Optional[WasteType] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get waste logs with filtering"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    query = db.query(WasteLog).filter(
        WasteLog.restaurant_id == current_user.restaurant_id
    )
    
    # Apply filters
    if waste_type:
        query = query.filter(WasteLog.waste_type == waste_type)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(WasteLog.created_at >= from_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_from format")
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            to_date = to_date.replace(hour=23, minute=59, second=59)
            query = query.filter(WasteLog.created_at <= to_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date_to format")
    
    waste_logs = query.order_by(WasteLog.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for log in waste_logs:
        product = db.query(Product).filter(Product.id == log.product_id).first()
        user = db.query(User).filter(User.id == log.user_id).first()
        
        result.append({
            "id": log.id,
            "product_id": log.product_id,
            "product_name": product.name if product else "Unknown",
            "quantity": log.quantity,
            "unit": product.unit if product else "unit",
            "waste_type": log.waste_type,
            "reason": log.reason,
            "cost": round(log.cost, 2),
            "user_name": user.full_name if user else "Unknown",
            "created_at": log.created_at.isoformat() if log.created_at else None
        })
    
    return result

@router.get("/{waste_id}")
async def get_waste_log(
    waste_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific waste log"""
    
    waste_log = db.query(WasteLog).filter(WasteLog.id == waste_id).first()
    if not waste_log:
        raise HTTPException(status_code=404, detail="Waste log not found")
    
    if waste_log.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this waste log")
    
    product = db.query(Product).filter(Product.id == waste_log.product_id).first()
    user = db.query(User).filter(User.id == waste_log.user_id).first()
    
    return {
        "id": waste_log.id,
        "product_id": waste_log.product_id,
        "product_name": product.name if product else "Unknown",
        "quantity": waste_log.quantity,
        "unit": product.unit if product else "unit",
        "waste_type": waste_log.waste_type,
        "reason": waste_log.reason,
        "cost": round(waste_log.cost, 2),
        "user_name": user.full_name if user else "Unknown",
        "created_at": waste_log.created_at.isoformat() if waste_log.created_at else None,
        "product": {
            "id": product.id if product else None,
            "name": product.name if product else None,
            "current_stock": product.current_stock if product else None,
            "unit": product.unit if product else None,
            "cost_price": product.cost_price if product else None
        } if product else None
    }

@router.put("/{waste_id}")
async def update_waste_log(
    waste_id: int,
    waste_update: WasteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a waste log"""
    
    waste_log = db.query(WasteLog).filter(WasteLog.id == waste_id).first()
    if not waste_log:
        raise HTTPException(status_code=404, detail="Waste log not found")
    
    if waste_log.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this waste log")
    
    # Only allow updates for recent logs (within 24 hours)
    if datetime.utcnow() - waste_log.created_at > timedelta(days=1):
        raise HTTPException(status_code=400, detail="Cannot update waste log older than 24 hours")
    
    # Update fields
    for field, value in waste_update.dict(exclude_unset=True).items():
        setattr(waste_log, field, value)
    
    db.commit()
    db.refresh(waste_log)
    
    return {
        "message": "Waste log updated successfully",
        "waste_id": waste_log.id
    }

@router.delete("/{waste_id}")
async def delete_waste_log(
    waste_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a waste log"""
    
    waste_log = db.query(WasteLog).filter(WasteLog.id == waste_id).first()
    if not waste_log:
        raise HTTPException(status_code=404, detail="Waste log not found")
    
    if waste_log.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this waste log")
    
    # Only allow deletion for recent logs or by admin
    if current_user.role != "admin" and datetime.utcnow() - waste_log.created_at > timedelta(days=1):
        raise HTTPException(status_code=400, detail="Cannot delete waste log older than 24 hours")
    
    # Get product and restore stock (with lock)
    product = db.query(Product).filter(Product.id == waste_log.product_id).with_for_update().first()
    if product:
        product.current_stock += waste_log.quantity
    
    db.delete(waste_log)
    db.commit()
    
    return {"message": "Waste log deleted successfully"}

@router.get("/stats/summary")
async def get_waste_summary(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get waste summary statistics"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get waste statistics
    waste_stats = db.query(
        WasteLog.waste_type,
        func.count(WasteLog.id).label('count'),
        func.sum(WasteLog.quantity).label('total_quantity'),
        func.sum(WasteLog.cost).label('total_cost')
    ).filter(
        WasteLog.restaurant_id == current_user.restaurant_id,
        WasteLog.created_at >= start_date
    ).group_by(WasteLog.waste_type).all()
    
    total_waste_value = Decimal('0.0')
    waste_types = []
    
    for waste_type, count, total_quantity, total_cost in waste_stats:
        cost = total_cost if total_cost is not None else Decimal('0.0')
        total_waste_value += cost
        
        waste_types.append({
            "type": waste_type,
            "count": count,
            "quantity": round(total_quantity if total_quantity is not None else Decimal('0.0'), 2),
            "cost": round(cost, 2),
            "percentage": 0  # Will calculate after getting total
        })
    
    # Calculate percentages
    for item in waste_types:
        item["percentage"] = round((item["cost"] / total_waste_value * 100) if total_waste_value > 0 else 0, 1)
    
    # Get top waste products
    top_products = db.query(
        Product.name,
        func.sum(WasteLog.quantity).label('total_waste'),
        func.sum(WasteLog.cost).label('total_cost')
    ).join(
        WasteLog, Product.id == WasteLog.product_id
    ).filter(
        WasteLog.restaurant_id == current_user.restaurant_id,
        WasteLog.created_at >= start_date
    ).group_by(
        Product.name
    ).order_by(
        func.sum(WasteLog.cost).desc()
    ).limit(5).all()
    
    top_waste_products = []
    for product_name, total_waste, total_cost in top_products:
        top_waste_products.append({
            "product_name": product_name,
            "quantity": round(total_waste if total_waste is not None else Decimal('0.0'), 2),
            "cost": round(total_cost if total_cost is not None else Decimal('0.0'), 2)
        })
    
    return {
        "period_days": days,
        "total_waste_value": round(total_waste_value, 2),
        "waste_types": sorted(waste_types, key=lambda x: x["cost"], reverse=True),
        "top_products": top_waste_products,
        "total_records": db.query(WasteLog).filter(
            WasteLog.restaurant_id == current_user.restaurant_id,
            WasteLog.created_at >= start_date
        ).count()
    }

@router.get("/types")
async def get_waste_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available waste types"""
    
    return {
        "waste_types": [
            {
                "type": "preparation",
                "name": "Preparación",
                "description": "Mermas durante la preparación de alimentos"
            },
            {
                "type": "expired",
                "name": "Vencido",
                "description": "Productos vencidos o en mal estado"
            },
            {
                "type": "damaged",
                "name": "Dañado",
                "description": "Productos dañados o en malas condiciones"
            }
        ]
    }