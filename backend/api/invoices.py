"""
Invoice OCR module
Módulo de procesamiento de facturas con OCR
"""

from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.models.database import (
    Invoice, InvoiceItem, Product, Provider, User, StockMovement, get_db
)
from backend.models.enums import InvoiceStatus, StockMovementType
from backend.api.auth import get_current_user, SessionLocal
from backend.utils.ocr_parser import OCRParser
from backend.config import settings

# Router
router = APIRouter()

# Pydantic models
class InvoiceItemCreate(BaseModel):
    product_name: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal

class InvoiceCreate(BaseModel):
    invoice_number: str
    invoice_date: str
    provider_id: int
    items: List[InvoiceItemCreate]
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    ocr_text: str
    ocr_confidence: float

class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    invoice_date: str
    provider_name: str
    subtotal: float
    tax: float
    total: float
    status: str
    item_count: int
    created_at: str

class OCRResult(BaseModel):
    success: bool
    invoice_number: Optional[str]
    invoice_date: Optional[str]
    provider_name: Optional[str]
    items: List[dict]
    subtotal: Optional[Decimal]
    tax: Optional[Decimal]
    total: Optional[Decimal]
    confidence: float
    raw_text: str
    suggestions: List[dict]

@router.post("/ocr/process", response_model=OCRResult)
async def process_invoice_with_ocr(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process invoice image/PDF with OCR"""
    
    # Validate file type
    if file.content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
        )
    
    # Read file contents
    contents = await file.read()
    
    # Validate file size (prevent DoS attacks)
    file_size_mb = len(contents) / (1024 * 1024)
    if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    try:
        # Initialize OCR parser
        ocr_parser = OCRParser()
        
        # Perform OCR
        result = ocr_parser.process_invoice(contents, file.content_type)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail="OCR processing failed")
        
        # Find provider suggestions
        suggestions = []
        if result['provider_name']:
            providers = db.query(Provider).filter(
                Provider.name.ilike(f"%{result['provider_name'][:20]}%")
            ).limit(3).all()
            
            for provider in providers:
                suggestions.append({
                    "type": "provider",
                    "id": provider.id,
                    "name": provider.name,
                    "match": result['provider_name']
                })
        
        # Find product suggestions
        for item in result['items']:
            products = db.query(Product).filter(
                Product.restaurant_id == current_user.restaurant_id,
                Product.name.ilike(f"%{item['product_name'][:15]}%")
            ).limit(2).all()
            
            for product in products:
                suggestions.append({
                    "type": "product",
                    "id": product.id,
                    "name": product.name,
                    "match": item['product_name']
                })
        
        result['suggestions'] = suggestions
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing error: {str(e)}")

@router.post("/", response_model=dict)
async def create_invoice(
    invoice_data: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create invoice from OCR results"""
    
    try:
        # Parse JSON data
        data = json.loads(invoice_data)
        
        # Create invoice
        invoice = Invoice(
            invoice_number=data['invoice_number'],
            invoice_date=datetime.strptime(data['invoice_date'], '%Y-%m-%d').date(),
            provider_id=data['provider_id'],
            restaurant_id=current_user.restaurant_id,

            subtotal=Decimal(str(data['subtotal'])),
            tax=Decimal(str(data.get('tax', 0.0))),
            total=Decimal(str(data['total'])),
            ocr_text=data.get('ocr_text', ''),
            ocr_confidence=data.get('ocr_confidence', 0.0),
            status=InvoiceStatus.PROCESSED,
            processed_by=current_user.id,
            processed_at=datetime.utcnow()
        )
        
        db.add(invoice)
        db.flush()
        
        # Create invoice items and update stock
        discrepancies = []
        for item_data in data['items']:
            # Try to find existing product (with lock)
            product = db.query(Product).filter(
                Product.restaurant_id == current_user.restaurant_id,
                Product.id == item_data.get('product_id')
            ).with_for_update().first()
            
            if product:
                # Update stock
                old_stock = product.current_stock
                product.current_stock += Decimal(str(item_data['quantity']))
                
                # Create stock movement
                movement = StockMovement(
                    product_id=product.id,
                    movement_type=StockMovementType.IN,
                    quantity=item_data['quantity'],
                    previous_stock=old_stock,
                    new_stock=product.current_stock,
                    reason=f"Invoice {invoice.invoice_number}",
                    reference_id=str(invoice.id),
                    user_id=current_user.id,
                    restaurant_id=current_user.restaurant_id
                )
                db.add(movement)
                
                stock_updated = True
            else:
                stock_updated = False
                discrepancies.append({
                    'product_name': item_data['product_name'],
                    'quantity': item_data['quantity'],
                    'unit_price': item_data['unit_price'],
                    'action': 'CREATE_NEW'
                })
            
            # Create invoice item
            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=item_data.get('product_id'),
                product_name=item_data['product_name'],
                quantity=Decimal(str(item_data['quantity'])),
                unit_price=Decimal(str(item_data['unit_price'])),
                total_price=Decimal(str(item_data['total_price'])),
                stock_updated=stock_updated
            )
            db.add(invoice_item)
        
        db.commit()
        
        return {
            "message": "Invoice processed successfully",
            "invoice_id": invoice.id,
            "discrepancies": discrepancies,
            "items_processed": len(data['items']),
            "stock_updated": len(data['items']) - len(discrepancies)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating invoice: {str(e)}")

@router.get("/", response_model=List[InvoiceResponse])
async def get_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: Optional[InvoiceStatus] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all invoices for current restaurant"""
    
    query = db.query(Invoice).filter(Invoice.restaurant_id == current_user.restaurant_id)
    
    # Apply filters
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    
    if date_from:
        query = query.filter(Invoice.invoice_date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    
    if date_to:
        query = query.filter(Invoice.invoice_date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    invoices = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for invoice in invoices:
        provider = db.query(Provider).filter(Provider.id == invoice.provider_id).first()
        item_count = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice.id).count()
        
        result.append(InvoiceResponse(
            id=invoice.id,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date.isoformat(),
            provider_name=provider.name if provider else "Unknown",
            subtotal=invoice.subtotal,
            tax=invoice.tax,
            total=invoice.total,
            status=invoice.status,
            item_count=item_count,
            created_at=invoice.created_at.isoformat() if invoice.created_at else None
        ))
    
    return result

@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get invoice details"""
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this invoice")
    
    provider = db.query(Provider).filter(Provider.id == invoice.provider_id).first()
    items = db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice.id).all()
    
    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date.isoformat(),
        "provider": {
            "id": provider.id if provider else None,
            "name": provider.name if provider else "Unknown"
        },
        "subtotal": invoice.subtotal,
        "tax": invoice.tax,
        "total": invoice.total,
        "status": invoice.status,
        "ocr_confidence": invoice.ocr_confidence,
        "items": [{
            "id": item.id,
            "product_name": item.product_name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
            "stock_updated": item.stock_updated
        } for item in items],
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
        "processed_at": invoice.processed_at.isoformat() if invoice.processed_at else None
    }

@router.post("/{invoice_id}/update-stock")
async def update_stock_from_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update stock for items that weren't automatically processed"""
    
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.restaurant_id != current_user.restaurant_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    items = db.query(InvoiceItem).filter(
        InvoiceItem.invoice_id == invoice_id,
        InvoiceItem.stock_updated == False
    ).all()
    
    updated_count = 0
    for item in items:
        # Try to find product by name
        product = db.query(Product).filter(
            Product.restaurant_id == current_user.restaurant_id,
            func.lower(Product.name) == func.lower(item.product_name)
        ).with_for_update().first()
        
        if not product:
            # Try fuzzy match
            product = db.query(Product).filter(
                Product.restaurant_id == current_user.restaurant_id,
                Product.name.ilike(f"%{item.product_name[:10]}%")
            ).with_for_update().first()
        
        if product:
            # Update stock
            old_stock = product.current_stock
            product.current_stock += item.quantity
            
            # Create stock movement
            movement = StockMovement(
                product_id=product.id,
                movement_type=StockMovementType.IN,
                quantity=item.quantity,
                previous_stock=old_stock,
                new_stock=product.current_stock,
                reason=f"Invoice update {invoice.invoice_number}",
                reference_id=str(invoice.id),
                user_id=current_user.id,
                restaurant_id=current_user.restaurant_id
            )
            db.add(movement)
            
            # Mark item as processed
            item.stock_updated = True
            updated_count += 1
    
    db.commit()
    
    return {
        "message": f"Stock updated for {updated_count} items",
        "updated_count": updated_count
    }