"""
Physical Count module
Módulo de conteos físicos de inventario
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, and_, func
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, date
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import (
    PhysicalCount, PhysicalCountItem, Product, User, StockMovement
)
from backend.models.enums import CountType, CountStatus, StockMovementType
from backend.api.auth import get_current_user, SessionLocal

# Router
router = APIRouter()

# Pydantic models
class CountItemCreate(BaseModel):
    product_id: int
    system_stock: Decimal
    physical_count: Decimal

class CountItemUpdate(BaseModel):
    product_id: int
    actual_stock: Decimal
    physical_count: Decimal

class CountCreate(BaseModel):
    count_type: CountType
    items: List[CountItemCreate]

class CountItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    unit: str
    system_stock: Decimal
    physical_count: Decimal
    difference: Decimal
    adjustment_made: bool

class CountResponse(BaseModel):
    id: int
    count_type: str
    status: str
    started_by: str
    completed_by: Optional[str]
    started_at: str
    completed_at: Optional[str]
    item_count: int
    total_variance: Decimal

@router.post("/start", response_model=dict)
async def start_physical_count(
    count_type: CountType,
    category_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new physical count"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    # Check if there's an ongoing count
    ongoing_count = db.query(PhysicalCount).filter(
        PhysicalCount.restaurant_id == current_user.restaurant_id,
        PhysicalCount.status == CountStatus.IN_PROGRESS
    ).first()
    
    if ongoing_count:
        raise HTTPException(status_code=400, detail="There is already an ongoing physical count")
    
    # Create new count
    count = PhysicalCount(
        restaurant_id=current_user.restaurant_id,
        count_type=count_type,
        status=CountStatus.IN_PROGRESS,
        started_by=current_user.id
    )
    
    db.add(count)
    db.flush()
    
    # Get products for this count type
    query = db.query(Product).filter(Product.restaurant_id == current_user.restaurant_id)
    
    if count_type == CountType.DAILY:
        # Daily count: perishable items (food category)
        query = query.filter(Product.category.has(type="food"))
    elif count_type == CountType.CATEGORY and category_id:
        query = query.filter(Product.category_id == category_id)
    
    products = query.order_by(Product.name).all()
    
    # Create count items
    count_items = []
    for product in products:
        system_stock_decimal = Decimal(str(product.current_stock))
        
        count_item = PhysicalCountItem(
            count_id=count.id,
            product_id=product.id,
            system_stock=system_stock_decimal,
            physical_count=Decimal('0.0'),  # Will be filled manually
            difference=Decimal('0.0') - system_stock_decimal,
            adjustment_made=False
        )
        db.add(count_item)
        count_items.append({
            "product_id": product.id,
            "product_name": product.name,
            "unit": product.unit,
            "system_stock": system_stock_decimal,
            "physical_count": Decimal('0.0'),
            "difference": Decimal('0.0') - system_stock_decimal
        })
    
    db.commit()
    
    return {
        "message": "Physical count started successfully",
        "count_id": count.id,
        "count_type": count_type,
        "items_count": len(count_items),
        "items": count_items
    }

@router.get("/current")
async def get_current_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current ongoing physical count"""
    
    count = db.query(PhysicalCount).filter(
        PhysicalCount.restaurant_id == current_user.restaurant_id,
        PhysicalCount.status == CountStatus.IN_PROGRESS
    ).first()
    
    if not count:
        return {"message": "No ongoing physical count", "count": None}
    
    # Get count items with product info
    items = db.query(PhysicalCountItem, Product).join(
        Product, PhysicalCountItem.product_id == Product.id
    ).filter(PhysicalCountItem.count_id == count.id).order_by(Product.name).all()
    
    count_items = []
    total_variance = Decimal('0.0')
    
    for item, product in items:
        variance = abs(item.difference) * Decimal(str(product.cost_price))
        total_variance += variance
        
        count_items.append({
            "id": item.id,
            "product_id": product.id,
            "product_name": product.name,
            "unit": product.unit,
            "system_stock": item.system_stock,
            "physical_count": item.physical_count,
            "difference": item.difference,
            "adjustment_made": item.adjustment_made,
            "cost_variance": variance
        })
    
    return {
        "count": {
            "id": count.id,
            "count_type": count.count_type,
            "status": count.status,
            "started_by": count.started_by,
            "started_at": count.started_at.isoformat(),
            "item_count": len(count_items),
            "total_variance": total_variance
        },
        "items": count_items
    }

@router.put("/items/{item_id}")
async def update_count_item(
    item_id: int,
    physical_count: Decimal,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update physical count for an item"""
    
    # Get count item
    item = db.query(PhysicalCountItem).filter(PhysicalCountItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Count item not found")
    
    # Get parent count
    count = db.query(PhysicalCount).filter(PhysicalCount.id == item.count_id).first()
    if not count or count.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if count.status != CountStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Cannot update completed count")
    
    # Update item
    item.physical_count = physical_count
    item.difference = physical_count - item.system_stock
    
    db.commit()
    
    return {
        "message": "Count item updated successfully",
        "item_id": item_id,
        "physical_count": physical_count,
        "difference": item.difference
    }

@router.post("/save-partial")
async def save_partial_count(
    items: List[dict],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save partial count progress"""
    
    count = db.query(PhysicalCount).filter(
        PhysicalCount.restaurant_id == current_user.restaurant_id,
        PhysicalCount.status == CountStatus.IN_PROGRESS
    ).first()
    
    if not count:
        raise HTTPException(status_code=400, detail="No ongoing count to save")
    
    updated_count = 0
    for item_data in items:
        item = db.query(PhysicalCountItem).filter(
            PhysicalCountItem.id == item_data['item_id'],
            PhysicalCountItem.count_id == count.id
        ).first()
        
        if item:
            item.physical_count = Decimal(str(item_data['physical_count']))
            item.difference = item.physical_count - item.system_stock
            updated_count += 1
    
    db.commit()
    
    return {
        "message": f"Partial count saved. {updated_count} items updated.",
        "updated_items": updated_count
    }

@router.post("/finalize")
async def finalize_count(
    apply_adjustments: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Finalize physical count and optionally apply adjustments"""
    
    count = db.query(PhysicalCount).filter(
        PhysicalCount.restaurant_id == current_user.restaurant_id,
        PhysicalCount.status == CountStatus.IN_PROGRESS
    ).first()
    
    if not count:
        raise HTTPException(status_code=400, detail="No ongoing count to finalize")
    
    # Get all count items
    items = db.query(PhysicalCountItem).filter(PhysicalCountItem.count_id == count.id).all()
    
    adjustments_made = 0
    total_variance = Decimal('0.0')
    
    if apply_adjustments:
        for item in items:
            if item.difference != Decimal('0.0') and not item.adjustment_made:
                # Get product (with lock)
                product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
                if product:
                    # Create stock movement
                    movement_type = StockMovementType.IN if item.difference > Decimal('0.0') else StockMovementType.OUT
                    reason = f"Physical count adjustment - {count.count_type}"
                    
                    movement = StockMovement(
                        product_id=product.id,
                        movement_type=movement_type,
                        quantity=abs(item.difference),
                        previous_stock=item.system_stock,
                        new_stock=item.physical_count,
                        reason=reason,
                        reference_id=f"COUNT-{count.id}",
                        user_id=current_user.id,
                        restaurant_id=current_user.restaurant_id
                    )
                    db.add(movement)
                    
                    # Update product stock
                    product.current_stock = item.physical_count
                    product.last_count_date = datetime.now().date()
                    
                    # Mark adjustment as made
                    item.adjustment_made = True
                    adjustments_made += 1
                    
                    # Calculate variance
                    variance = abs(item.difference) * Decimal(str(product.cost_price))
                    total_variance += variance
    
    # Finalize count
    count.status = CountStatus.COMPLETED
    count.completed_by = current_user.id
    count.completed_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": f"Physical count finalized. {adjustments_made} adjustments applied.",
        "adjustments_made": adjustments_made,
        "total_variance": total_variance,
        "count_id": count.id
    }

@router.get("/history")
async def get_count_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get physical count history"""
    
    query = db.query(PhysicalCount).filter(
        PhysicalCount.restaurant_id == current_user.restaurant_id
    )
    
    # Apply date filters
    if date_from:
        query = query.filter(PhysicalCount.started_at >= datetime.strptime(date_from, '%Y-%m-%d'))
    
    if date_to:
        query = query.filter(PhysicalCount.started_at <= datetime.strptime(date_to, '%Y-%m-%d'))
    
    counts = query.order_by(PhysicalCount.started_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for count in counts:
        item_count = db.query(PhysicalCountItem).filter(PhysicalCountItem.count_id == count.id).count()
        
        result.append({
            "id": count.id,
            "count_type": count.count_type,
            "status": count.status,
            "started_by": count.started_by,
            "completed_by": count.completed_by,
            "started_at": count.started_at.isoformat(),
            "completed_at": count.completed_at.isoformat() if count.completed_at else None,
            "item_count": item_count
        })
    
    return result

@router.get("/{count_id}")
async def get_count_details(
    count_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed count information"""
    
    count = db.query(PhysicalCount).filter(PhysicalCount.id == count_id).first()
    if not count:
        raise HTTPException(status_code=404, detail="Count not found")
    
    if count.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get items with product info
    items = db.query(PhysicalCountItem, Product).join(
        Product, PhysicalCountItem.product_id == Product.id
    ).filter(PhysicalCountItem.count_id == count.id).order_by(Product.name).all()
    
    count_items = []
    total_variance = Decimal('0.0')
    
    for item, product in items:
        variance = abs(item.difference) * Decimal(str(product.cost_price))
        total_variance += variance
        
        count_items.append({
            "id": item.id,
            "product_id": product.id,
            "product_name": product.name,
            "unit": product.unit,
            "system_stock": item.system_stock,
            "physical_count": item.physical_count,
            "difference": item.difference,
            "adjustment_made": item.adjustment_made,
            "cost_variance": variance
        })
    
    return {
        "id": count.id,
        "count_type": count.count_type,
        "status": count.status,
        "started_by": count.started_by,
        "completed_by": count.completed_by,
        "started_at": count.started_at.isoformat(),
        "completed_at": count.completed_at.isoformat() if count.completed_at else None,
        "total_variance": total_variance,
        "items": count_items
    }