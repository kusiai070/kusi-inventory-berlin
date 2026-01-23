"""
Reports module
Módulo de generación de reportes
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, and_, func, case
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta, date
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import (
    Product, StockMovement, Invoice, InvoiceItem, WasteLog, 
    PhysicalCount, User, Category, Provider, get_db
)
from backend.api.auth import get_current_user, SessionLocal
from backend.utils.calculations import ReportCalculator
from backend.utils.report_generator import ReportGenerator
from fastapi.responses import StreamingResponse

# Router
router = APIRouter()

@router.get("/inventory-valuation")
async def get_inventory_valuation_report(
    format: str = Query("json", regex="^(json|excel|pdf)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current inventory valuation report"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    # Calculate inventory value
    products = db.query(Product).filter(
        Product.restaurant_id == current_user.restaurant_id
    ).all()
    
    report_data = []
    total_value = 0.0
    
    for product in products:
        item_value = product.current_stock * product.cost_price
        total_value += item_value
        
        report_data.append({
            "product_id": product.id,
            "product_name": product.name,
            "category": product.category.name if product.category else "Unknown",
            "unit": product.unit,
            "current_stock": product.current_stock,
            "cost_price": product.cost_price,
            "total_value": round(item_value, 2),
            "stock_status": "low" if product.current_stock <= product.min_stock else "ok"
        })
    
    if format == "json":
        report = {
            "report_type": "inventory_valuation",
            "generated_at": datetime.utcnow().isoformat(),
            "restaurant_id": current_user.restaurant_id,
            "total_products": len(report_data),
            "total_inventory_value": round(total_value, 2),
            "items": sorted(report_data, key=lambda x: x["total_value"], reverse=True)
        }
        return report

    # Define columns for export
    columns = [
        {"key": "product_name", "header": "Producto"},
        {"key": "category", "header": "Categoría"},
        {"key": "current_stock", "header": "Stock"},
        {"key": "unit", "header": "Unidad"},
        {"key": "cost_price", "header": "Costo Unit."},
        {"key": "total_value", "header": "Valor Total"},
        {"key": "stock_status", "header": "Estado"}
    ]
    
    filename = f"valoracion_inventario_{datetime.now().strftime('%Y%m%d')}"
    
    if format == "excel":
        buffer = ReportGenerator.generate_excel(report_data, "Valoración de Inventario", columns)
        return StreamingResponse(
            buffer, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
        
    elif format == "pdf":
        buffer = ReportGenerator.generate_pdf(
            report_data, 
            "Valoración de Inventario", 
            columns,
            {"Total Productos": len(report_data), "Valor Total": f"${total_value:,.2f}"}
        )
        return StreamingResponse(
            buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
    
    raise HTTPException(status_code=400, detail="Invalid format")

@router.get("/consumption")
async def get_consumption_report(
    date_from: str = Query(..., description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(..., description="End date (YYYY-MM-DD)"),
    group_by: str = Query("category", regex="^(category|product)$"),
    format: str = Query("json", regex="^(json|excel|pdf)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get consumption report for a date range"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    try:
        start_date = datetime.strptime(date_from, '%Y-%m-%d')
        end_date = datetime.strptime(date_to, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Get stock movements (OUT type represents consumption)
    movements = db.query(StockMovement).filter(
        StockMovement.restaurant_id == current_user.restaurant_id,
        StockMovement.movement_type == "OUT",
        StockMovement.created_at >= start_date,
        StockMovement.created_at <= end_date
    ).all()
    
    consumption_data = {}
    total_consumption = 0.0
    
    for movement in movements:
        product = db.query(Product).filter(Product.id == movement.product_id).first()
        if not product:
            continue
        
        consumption_value = movement.quantity * product.cost_price
        total_consumption += consumption_value
        
        if group_by == "category":
            key = product.category.name if product.category else "Unknown"
        else:
            key = product.name
        
        if key not in consumption_data:
            consumption_data[key] = {
                "quantity": 0.0,
                "value": 0.0,
                "items": []
            }
        
        consumption_data[key]["quantity"] += movement.quantity
        consumption_data[key]["value"] += consumption_value
        
        if group_by == "category":
            consumption_data[key]["items"].append({
                "product_name": product.name,
                "quantity": movement.quantity,
                "unit": product.unit,
                "cost_value": round(consumption_value, 2)
            })
    
    # Format response
    report_items = []
    for key, data in consumption_data.items():
        report_items.append({
            "name": key,
            "quantity": round(data["quantity"], 2),
            "cost_value": round(data["value"], 2),
            "percentage": round((data["value"] / total_consumption * 100) if total_consumption > 0 else 0, 1),
            "items": data["items"]
        })
    
    if format == "json":
        report = {
            "report_type": "consumption",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "from": date_from,
                "to": date_to
            },
            "grouped_by": group_by,
            "total_consumption_value": round(total_consumption, 2),
            "items": sorted(report_items, key=lambda x: x["cost_value"], reverse=True)
        }
        return report

    # Flatten data for export
    flat_data = []
    for group in report_items:
        group_name = group["name"]
        for item in group["items"]:
            flat_data.append({
                "group": group_name,
                "product_name": item["product_name"],
                "quantity": item["quantity"],
                "unit": item["unit"],
                "cost_value": item["cost_value"]
            })
            
    columns = [
        {"key": "group", "header": "Grupo"},
        {"key": "product_name", "header": "Producto"},
        {"key": "quantity", "header": "Cant."},
        {"key": "unit", "header": "Unidad"},
        {"key": "cost_value", "header": "Costo"}
    ]
    
    filename = f"reporte_consumo_{date_from}_{date_to}"
    title = f"Reporte de Consumo ({date_from} a {date_to})"
    
    if format == "excel":
        buffer = ReportGenerator.generate_excel(flat_data, title, columns)
        return StreamingResponse(
            buffer, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
    elif format == "pdf":
        buffer = ReportGenerator.generate_pdf(
            flat_data, 
            title, 
            columns,
            {"Total Consumo": f"${total_consumption:,.2f}"}
        )
        return StreamingResponse(
            buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
    
    raise HTTPException(status_code=400, detail="Invalid format")

@router.get("/waste-analysis")
async def get_waste_analysis_report(
    date_from: str = Query(..., description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(..., description="End date (YYYY-MM-DD)"),
    format: str = Query("json", regex="^(json|excel|pdf)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get waste analysis report"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    try:
        start_date = datetime.strptime(date_from, '%Y-%m-%d')
        end_date = datetime.strptime(date_to, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Get waste logs
    waste_logs = db.query(WasteLog).filter(
        WasteLog.restaurant_id == current_user.restaurant_id,
        WasteLog.created_at >= start_date,
        WasteLog.created_at <= end_date
    ).all()
    
    waste_data = {}
    total_waste_value = 0.0
    
    for log in waste_logs:
        product = db.query(Product).filter(Product.id == log.product_id).first()
        if not product:
            continue
        
        total_waste_value += log.cost
        
        # Group by waste type
        waste_type = log.waste_type
        if waste_type not in waste_data:
            waste_data[waste_type] = {
                "count": 0,
                "quantity": 0.0,
                "cost": 0.0,
                "items": []
            }
        
        waste_data[waste_type]["count"] += 1
        waste_data[waste_type]["quantity"] += log.quantity
        waste_data[waste_type]["cost"] += log.cost
        
        waste_data[waste_type]["items"].append({
            "product_name": product.name,
            "quantity": log.quantity,
            "unit": product.unit,
            "cost": round(log.cost, 2),
            "reason": log.reason,
            "date": log.created_at.strftime('%Y-%m-%d')
        })
    
    # Calculate waste percentage vs consumption
    calculator = ReportCalculator(db, current_user.restaurant_id)
    waste_percentage = calculator.calculate_waste_percentage(start_date, end_date)
    
    # Format response
    report_items = []
    for waste_type, data in waste_data.items():
        report_items.append({
            "waste_type": waste_type,
            "count": data["count"],
            "quantity": round(data["quantity"], 2),
            "cost": round(data["cost"], 2),
            "percentage": round((data["cost"] / total_waste_value * 100) if total_waste_value > 0 else 0, 1),
            "items": data["items"]
        })
    
    if format == "json":
        report = {
            "report_type": "waste_analysis",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "from": date_from,
                "to": date_to
            },
            "total_waste_value": round(total_waste_value, 2),
            "waste_percentage": round(waste_percentage, 2),
            "is_abnormal": waste_percentage > 5.0,
            "waste_types": sorted(report_items, key=lambda x: x["cost"], reverse=True)
        }
        return report

    # Flatten data
    flat_data = []
    for type_group in report_items:
        waste_type = type_group["waste_type"]
        for item in type_group["items"]:
            flat_data.append({
                "waste_type": waste_type,
                "product_name": item["product_name"],
                "quantity": item["quantity"],
                "unit": item["unit"],
                "cost": item["cost"],
                "reason": item["reason"],
                "date": item["date"]
            })
            
    columns = [
        {"key": "date", "header": "Fecha"},
        {"key": "waste_type", "header": "Tipo"},
        {"key": "product_name", "header": "Producto"},
        {"key": "quantity", "header": "Cant."},
        {"key": "unit", "header": "Unidad"},
        {"key": "cost", "header": "Costo"},
        {"key": "reason", "header": "Motivo"}
    ]
    
    filename = f"reporte_mermas_{date_from}_{date_to}"
    title = f"Análisis de Mermas ({date_from} a {date_to})"
    
    if format == "excel":
        buffer = ReportGenerator.generate_excel(flat_data, title, columns)
        return StreamingResponse(
            buffer, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
    elif format == "pdf":
        buffer = ReportGenerator.generate_pdf(
            flat_data, 
            title, 
            columns,
            {
                "Total Mermas": f"${total_waste_value:,.2f}",
                "% sobre Consumo": f"{waste_percentage:.1f}%",
                "Estado": "ANORMAL" if waste_percentage > 5.0 else "Normal"
            }
        )
        return StreamingResponse(
            buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
            
    raise HTTPException(status_code=400, detail="Invalid format")

@router.get("/theoretical-vs-actual")
async def get_theoretical_vs_actual_report(
    date_from: str = Query(..., description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(..., description="End date (YYYY-MM-DD)"),
    format: str = Query("json", regex="^(json|excel|pdf)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get theoretical vs actual consumption analysis"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    try:
        start_date = datetime.strptime(date_from, '%Y-%m-%d')
        end_date = datetime.strptime(date_to, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    calculator = ReportCalculator(db, current_user.restaurant_id)
    analysis = calculator.calculate_theoretical_vs_actual(start_date, end_date)
    
    if format == "json":
        return {
            "report_type": "theoretical_vs_actual",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "from": date_from,
                "to": date_to
            },
            "theoretical_consumption": round(analysis["theoretical"], 2),
            "actual_consumption": round(analysis["actual"], 2),
            "variance": round(analysis["variance"], 2),
            "variance_percentage": round(analysis["variance_percentage"], 2),
            "is_abnormal": analysis["is_abnormal"],
            "interpretation": "Actual consumption exceeds theoretical" if analysis["variance"] > 0 else "Actual consumption is below theoretical"
        }

    # Prepare data for export
    # Since this is a specialized report, we create a summary-like table
    flat_data = [{
        "metric": "Consumo Teórico",
        "value": round(analysis["theoretical"], 2),
        "unit": "$"
    }, {
        "metric": "Consumo Real",
        "value": round(analysis["actual"], 2),
        "unit": "$"
    }, {
        "metric": "Variación",
        "value": round(analysis["variance"], 2),
        "unit": "$"
    }, {
        "metric": "% Variación",
        "value": round(analysis["variance_percentage"], 2),
        "unit": "%"
    }]
            
    columns = [
        {"key": "metric", "header": "Métrica"},
        {"key": "value", "header": "Valor"},
        {"key": "unit", "header": "Unidad"}
    ]
    
    filename = f"teorico_vs_real_{date_from}_{date_to}"
    title = f"Teórico vs Real ({date_from} a {date_to})"
    
    summary = {
        "Estado": "ANORMAL (Posible Robo)" if analysis["is_abnormal"] else "Normal",
        "Conclusión": "Consumo Real > Teórico" if analysis["variance"] > 0 else "Ahorro vs Teórico"
    }

    if format == "excel":
        buffer = ReportGenerator.generate_excel(flat_data, title, columns)
        return StreamingResponse(
            buffer, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
    elif format == "pdf":
        buffer = ReportGenerator.generate_pdf(flat_data, title, columns, summary)
        return StreamingResponse(
            buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
    
    raise HTTPException(status_code=400, detail="Invalid format")

@router.get("/purchases")
async def get_purchases_report(
    date_from: str = Query(..., description="Start date (YYYY-MM-DD)"),
    date_to: str = Query(..., description="End date (YYYY-MM-DD)"),
    provider_id: Optional[int] = None,
    format: str = Query("json", regex="^(json|excel|pdf)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get purchases report"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    try:
        start_date = datetime.strptime(date_from, '%Y-%m-%d')
        end_date = datetime.strptime(date_to, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Get invoices
    query = db.query(Invoice).filter(
        Invoice.restaurant_id == current_user.restaurant_id,
        Invoice.invoice_date >= start_date.date(),
        Invoice.invoice_date <= end_date.date()
    )
    
    if provider_id:
        query = query.filter(Invoice.provider_id == provider_id)
    
    invoices = query.order_by(Invoice.invoice_date.desc()).all()
    
    report_data = []
    total_purchases = 0.0
    
    for invoice in invoices:
        provider = db.query(Provider).filter(Provider.id == invoice.provider_id).first()
        item_count = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice.id).count()
        
        total_purchases += invoice.total
        
        report_data.append({
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.isoformat(),
            "provider_name": provider.name if provider else "Unknown",
            "subtotal": invoice.subtotal,
            "tax": invoice.tax,
            "total": invoice.total,
            "item_count": item_count,
            "status": invoice.status
        })
    
    if format == "json":
        return {
            "report_type": "purchases",
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "from": date_from,
                "to": date_to
            },
            "total_purchases": round(total_purchases, 2),
            "invoice_count": len(report_data),
            "invoices": report_data
        }

    # Setup Export
    columns = [
        {"key": "invoice_date", "header": "Fecha"},
        {"key": "invoice_number", "header": "N° Factura"},
        {"key": "provider_name", "header": "Proveedor"},
        {"key": "total", "header": "Total"},
        {"key": "status", "header": "Estado"}
    ]
    
    filename = f"reporte_compras_{date_from}_{date_to}"
    title = f"Reporte de Compras ({date_from} a {date_to})"
    
    if format == "excel":
        buffer = ReportGenerator.generate_excel(report_data, title, columns)
        return StreamingResponse(
            buffer, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
    elif format == "pdf":
        buffer = ReportGenerator.generate_pdf(
            report_data, 
            title, 
            columns,
            {"Total Compras": f"${total_purchases:,.2f}", "Documentos": len(report_data)}
        )
        return StreamingResponse(
            buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
            
    raise HTTPException(status_code=400, detail="Invalid format")

@router.get("/rotation-analysis")
async def get_rotation_analysis_report(
    days: int = Query(30, ge=1, le=365),
    format: str = Query("json", regex="^(json|excel|pdf)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get product rotation analysis"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get products with movement in the period
    products = db.query(Product).filter(
        Product.restaurant_id == current_user.restaurant_id,
        Product.stock_movements.any(
            StockMovement.created_at >= start_date
        )
    ).all()
    
    rotation_data = []
    
    for product in products:
        # Get movements in the period
        movements = db.query(StockMovement).filter(
            StockMovement.product_id == product.id,
            StockMovement.created_at >= start_date
        ).all()
        
        total_out = sum(m.quantity for m in movements if m.movement_type == "OUT")
        total_in = sum(m.quantity for m in movements if m.movement_type == "IN")
        
        # Calculate rotation rate
        avg_stock = (product.current_stock + product.current_stock + total_in - total_out) / 2
        rotation_rate = (total_out / avg_stock) if avg_stock > 0 else 0
        
        rotation_data.append({
            "product_id": product.id,
            "product_name": product.name,
            "category": product.category.name if product.category else "Unknown",
            "current_stock": product.current_stock,
            "total_out": total_out,
            "total_in": total_in,
            "rotation_rate": round(rotation_rate, 2),
            "rotation_classification": "high" if rotation_rate > 2 else "medium" if rotation_rate > 0.5 else "low"
        })
    
    if format == "json":
        return {
            "report_type": "rotation_analysis",
            "generated_at": datetime.utcnow().isoformat(),
            "period_days": days,
            "products_analyzed": len(rotation_data),
            "products": sorted(rotation_data, key=lambda x: x["rotation_rate"], reverse=True)
        }

    columns = [
        {"key": "product_name", "header": "Producto"},
        {"key": "category", "header": "Categoría"},
        {"key": "total_out", "header": "Salidas"},
        {"key": "rotation_rate", "header": "Índice Rot."},
        {"key": "rotation_classification", "header": "Clasif."}
    ]
    
    filename = f"rotacion_stock_{days}dias"
    title = f"Análisis de Rotación (Últimos {days} días)"

    if format == "excel":
        buffer = ReportGenerator.generate_excel(rotation_data, title, columns)
        return StreamingResponse(
            buffer, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
    elif format == "pdf":
        buffer = ReportGenerator.generate_pdf(rotation_data, title, columns)
        return StreamingResponse(
            buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
            
    raise HTTPException(status_code=400, detail="Invalid format")

@router.get("/obsolete-products")
async def get_obsolete_products_report(
    days_without_movement: int = Query(30, ge=1, le=365),
    format: str = Query("json", regex="^(json|excel|pdf)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get obsolete products report (no movement in specified days)"""
    
    if current_user.restaurant_id is None:
        raise HTTPException(status_code=403, detail="User not assigned to restaurant")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_without_movement)
    
    # Get products with no recent movements
    products = db.query(Product).filter(
        Product.restaurant_id == current_user.restaurant_id,
        ~Product.stock_movements.any(
            StockMovement.created_at >= cutoff_date
        )
    ).all()
    
    obsolete_products = []
    total_value = 0.0
    
    for product in products:
        item_value = product.current_stock * product.cost_price
        total_value += item_value
        
        # Get last movement date
        last_movement = db.query(StockMovement).filter(
            StockMovement.product_id == product.id
        ).order_by(StockMovement.created_at.desc()).first()
        
        obsolete_products.append({
            "product_id": product.id,
            "product_name": product.name,
            "category": product.category.name if product.category else "Unknown",
            "current_stock": product.current_stock,
            "unit": product.unit,
            "cost_price": product.cost_price,
            "total_value": round(item_value, 2),
            "last_movement_date": last_movement.created_at.strftime('%Y-%m-%d') if last_movement else "Never",
            "days_without_movement": days_without_movement
        })
    
    if format == "json":
        return {
            "report_type": "obsolete_products",
            "generated_at": datetime.utcnow().isoformat(),
            "days_without_movement": days_without_movement,
            "total_products": len(obsolete_products),
            "total_inventory_value": round(total_value, 2),
            "products": sorted(obsolete_products, key=lambda x: x["total_value"], reverse=True)
        }

    columns = [
        {"key": "product_name", "header": "Producto"},
        {"key": "category", "header": "Categoría"},
        {"key": "current_stock", "header": "Stock"},
        {"key": "total_value", "header": "Valor Atrapado"},
        {"key": "last_movement_date", "header": "Último Mov."}
    ]
    
    filename = f"productos_obsoletos_{days_without_movement}dias"
    title = f"Productos sin Movimiento (> {days_without_movement} días)"

    summary = {
        "Total Productos": len(obsolete_products),
        "Capital Congelado": f"${total_value:,.2f}"
    }

    if format == "excel":
        buffer = ReportGenerator.generate_excel(obsolete_products, title, columns)
        return StreamingResponse(
            buffer, 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
    elif format == "pdf":
        buffer = ReportGenerator.generate_pdf(obsolete_products, title, columns, summary)
        return StreamingResponse(
            buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
            
    raise HTTPException(status_code=400, detail="Invalid format")