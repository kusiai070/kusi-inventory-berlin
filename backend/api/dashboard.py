"""
Dashboard module
Módulo de dashboard ejecutivo
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, and_, case
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import (
    Product, StockMovement, Invoice, WasteLog, Alert, 
    PhysicalCount, User, Category
)
from backend.models.enums import StockMovementType, InvoiceStatus
from backend.api.auth import get_current_user, SessionLocal
from backend.utils.calculations import ReportCalculator

# Router
router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard summary data"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    # Basic stats
    total_products = db.query(Product).filter(
        Product.restaurant_id == current_user.restaurant_id
    ).count()
    
    # Inventory value
    inventory_value = db.query(func.sum(Product.current_stock * Product.cost_price)).filter(
        Product.restaurant_id == current_user.restaurant_id
    ).scalar() or Decimal('0.0')
    
    # Low stock products
    low_stock_count = db.query(Product).filter(
        Product.restaurant_id == current_user.restaurant_id,
        Product.current_stock <= Product.min_stock
    ).count()
    
    # Active alerts
    active_alerts = db.query(Alert).filter(
        Alert.restaurant_id == current_user.restaurant_id,
        Alert.is_active == True
    ).count()
    
    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    recent_movements = db.query(StockMovement).filter(
        StockMovement.restaurant_id == current_user.restaurant_id,
        StockMovement.created_at >= week_ago
    ).count()
    
    recent_invoices = db.query(Invoice).filter(
        Invoice.restaurant_id == current_user.restaurant_id,
        Invoice.created_at >= week_ago
    ).count()
    
    # Weekly consumption (with explicit JOIN to prevent tenant data leakage)
    weekly_consumption = db.query(
        func.sum(StockMovement.quantity * Product.cost_price)
    ).join(
        Product, StockMovement.product_id == Product.id
    ).filter(
        StockMovement.restaurant_id == current_user.restaurant_id,
        Product.restaurant_id == current_user.restaurant_id,  # Prevent tenant leakage
        StockMovement.movement_type == StockMovementType.OUT,
        StockMovement.created_at >= week_ago
    ).scalar() or Decimal('0.0')
    
    return {
        "summary": {
            "total_products": total_products,
            "inventory_value": round(inventory_value, 2),
            "low_stock_products": low_stock_count,
            "active_alerts": active_alerts
        },
        "recent_activity": {
            "movements_7days": recent_movements,
            "invoices_7days": recent_invoices,
            "consumption_7days": round(weekly_consumption, 2)
        }
    }

@router.get("/alerts")
async def get_dashboard_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active alerts for dashboard"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    # Get active alerts
    alerts = db.query(Alert).filter(
        Alert.restaurant_id == current_user.restaurant_id,
        Alert.is_active == True
    ).order_by(
        case(
            {"critical": 0, "high": 1, "medium": 2, "low": 3},
            value=Alert.severity
        )
    ).limit(10).all()
    
    alert_list = []
    for alert in alerts:
        alert_list.append({
            "id": alert.id,
            "type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "created_at": alert.created_at.isoformat() if alert.created_at else None
        })
    
    return {"alerts": alert_list}

@router.get("/weekly-consumption")
async def get_weekly_consumption_chart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weekly consumption data for chart"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    # Get last 30 days consumption by day
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    daily_consumption = {}
    current_date = start_date
    
    while current_date <= end_date:
        next_date = current_date + timedelta(days=1)
        
        consumption = db.query(func.sum(
            StockMovement.quantity * Product.cost_price
        )).filter(
            StockMovement.restaurant_id == current_user.restaurant_id,
            StockMovement.movement_type == StockMovementType.OUT,
            StockMovement.created_at >= current_date,
            StockMovement.created_at < next_date
        ).scalar() or Decimal('0.0')
        
        daily_consumption[current_date.strftime('%Y-%m-%d')] = round(consumption, 2)
        current_date = next_date
    
    return {
        "chart_data": {
            "labels": list(daily_consumption.keys()),
            "values": list(daily_consumption.values())
        },
        "summary": {
            "total_days": 30,
            "total_consumption": sum(daily_consumption.values()),
            "avg_daily_consumption": round(sum(daily_consumption.values()) / 30, 2)
        }
    }

@router.get("/category-distribution")
async def get_category_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get category distribution data"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    # Get products grouped by category
    products_by_category = db.query(
        Category.name,
        Category.type,
        func.count(Product.id).label('product_count'),
        func.sum(Product.current_stock * Product.cost_price).label('total_value')
    ).join(
        Product, Category.id == Product.category_id
    ).filter(
        Product.restaurant_id == current_user.restaurant_id
    ).group_by(
        Category.name, Category.type
    ).all()
    
    categories_data = []
    total_value = Decimal('0.0')
    
    for category_name, category_type, product_count, category_value in products_by_category:
        value = category_value if category_value else Decimal('0.0')
        total_value += value
        
        categories_data.append({
            "name": category_name,
            "type": category_type,
            "product_count": product_count,
            "value": round(value, 2),
            "percentage": 0  # Will calculate after getting total
        })
    
    # Calculate percentages
    for item in categories_data:
        item["percentage"] = round((item["value"] / total_value * 100) if total_value > 0 else 0, 1)
    
    return {
        "categories": sorted(categories_data, key=lambda x: x["value"], reverse=True),
        "total_value": round(total_value, 2)
    }

@router.get("/top-products")
async def get_top_products(
    limit: int = Query(10, ge=1, le=50),
    metric: str = Query("consumption", regex="^(consumption|value|movement)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get top products by different metrics"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    products = db.query(Product).filter(
        Product.restaurant_id == current_user.restaurant_id
    ).all()
    
    product_data = []
    
    for product in products:
        if metric == "consumption":
            # Get consumption in last 30 days
            month_ago = datetime.utcnow() - timedelta(days=30)
            consumption = db.query(func.sum(StockMovement.quantity)).filter(
                StockMovement.product_id == product.id,
                StockMovement.movement_type == StockMovementType.OUT,
                StockMovement.created_at >= month_ago
            ).scalar() or Decimal('0.0')
            
            value = consumption
            unit = product.unit
            
        elif metric == "value":
            value = product.current_stock * product.cost_price
            unit = "USD"
            
        else:  # movement
            month_ago = datetime.utcnow() - timedelta(days=30)
            movements = db.query(StockMovement).filter(
                StockMovement.product_id == product.id,
                StockMovement.created_at >= month_ago
            ).count()
            
            value = movements
            unit = "movements"
        
        product_data.append({
            "id": product.id,
            "name": product.name,
            "category": product.category.name if product.category else "Unknown",
            "value": round(float(value), 2),
            "unit": unit
        })
    
    # Sort and limit
    top_products = sorted(product_data, key=lambda x: x["value"], reverse=True)[:limit]
    
    return {
        "metric": metric,
        "products": top_products
    }

@router.get("/quick-actions")
async def get_quick_actions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get quick actions for dashboard"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    actions = []
    
    # Check if count is needed
    last_week = datetime.utcnow() - timedelta(days=7)
    recent_count = db.query(PhysicalCount).filter(
        PhysicalCount.restaurant_id == current_user.restaurant_id,
        PhysicalCount.created_at >= last_week
    ).count()
    
    if recent_count == 0:
        actions.append({
            "type": "count",
            "title": "Realizar conteo físico",
            "description": "No se ha realizado conteo en la última semana",
            "priority": "medium",
            "action": "start_count"
        })
    
    # Check for pending invoices
    pending_invoices = db.query(Invoice).filter(
        Invoice.restaurant_id == current_user.restaurant_id,
        Invoice.status == InvoiceStatus.PENDING
    ).count()
    
    if pending_invoices > 0:
        actions.append({
            "type": "invoice",
            "title": "Procesar facturas pendientes",
            "description": f"Tienes {pending_invoices} facturas pendientes de procesar",
            "priority": "high",
            "action": "process_invoices"
        })
    
    # Check for low stock
    low_stock_products = db.query(Product).filter(
        Product.restaurant_id == current_user.restaurant_id,
        Product.current_stock <= Product.min_stock
    ).count()
    
    if low_stock_products > 0:
        actions.append({
            "type": "stock",
            "title": "Reabastecer productos",
            "description": f"{low_stock_products} productos con stock bajo",
            "priority": "high",
            "action": "restock_products"
        })
    
    # Check for waste registration
    today = datetime.utcnow().date()
    today_waste = db.query(WasteLog).filter(
        WasteLog.restaurant_id == current_user.restaurant_id,
        func.date(WasteLog.created_at) == today
    ).count()
    
    if today_waste == 0:
        actions.append({
            "type": "waste",
            "title": "Registrar mermas del día",
            "description": "No se han registrado mermas hoy",
            "priority": "low",
            "action": "register_waste"
        })
    
    return {"actions": actions}

@router.get("/stats-cards")
async def get_stats_cards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics cards data"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    # Current stats
    total_products = db.query(Product).filter(
        Product.restaurant_id == current_user.restaurant_id
    ).count()
    
    inventory_value = db.query(func.sum(Product.current_stock * Product.cost_price)).filter(
        Product.restaurant_id == current_user.restaurant_id
    ).scalar() or 0.0
    
    low_stock_count = db.query(Product).filter(
        Product.restaurant_id == current_user.restaurant_id,
        Product.current_stock <= Product.min_stock
    ).count()
    
    # Compare with last month
    month_ago = datetime.utcnow() - timedelta(days=30)
    
    # Products count change
    products_last_month = db.query(Product).filter(
        Product.restaurant_id == current_user.restaurant_id,
        Product.created_at < month_ago
    ).count()
    
    products_change = total_products - products_last_month
    
    # Value change (approximation)
    movements_last_month = db.query(StockMovement).filter(
        StockMovement.restaurant_id == current_user.restaurant_id,
        StockMovement.created_at >= month_ago
    ).all()
    
    value_change = Decimal('0.0')
    for movement in movements_last_month:
        product = db.query(Product).filter(Product.id == movement.product_id).first()
        if product:
            if movement.movement_type == StockMovementType.IN:
                value_change += movement.quantity * product.cost_price
            else:
                value_change -= movement.quantity * product.cost_price
    
    return {
        "cards": [
            {
                "title": "Total Productos",
                "value": total_products,
                "change": products_change,
                "change_type": "increase" if products_change > 0 else "decrease",
                "icon": "📦"
            },
            {
                "title": "Valor Inventario",
                "value": f"${inventory_value:,.2f}",
                "change": value_change,
                "change_type": "increase" if value_change > 0 else "decrease",
                "icon": "💰"
            },
            {
                "title": "Stock Bajo",
                "value": low_stock_count,
                "change": 0,
                "change_type": "neutral",
                "icon": "⚠️"
            },
            {
                "title": "Alertas Activas",
                "value": db.query(Alert).filter(
                    Alert.restaurant_id == current_user.restaurant_id,
                    Alert.is_active == True
                ).count(),
                "change": 0,
                "change_type": "neutral",
                "icon": "🚨"
            }
        ]
    }