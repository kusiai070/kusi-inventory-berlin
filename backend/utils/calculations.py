"""
Business calculations module
Módulo de cálculos de negocio
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP

class ReportCalculator:
    """Calculator for business reports and analysis"""
    
    def __init__(self, db: Session, restaurant_id: int):
        self.db = db
        self.restaurant_id = restaurant_id
    
    def calculate_inventory_value(self) -> Dict[str, any]:
        """Calculate total inventory value using weighted average cost"""
        
        from backend.models.database import Product, PriceHistory
        
        total_value = 0.0
        products_data = []
        
        products = self.db.query(Product).filter(
            Product.restaurant_id == self.restaurant_id
        ).all()
        
        for product in products:
            # Use current cost price or calculate weighted average
            avg_cost = self._get_average_product_cost(product.id)
            item_value = product.current_stock * avg_cost
            total_value += item_value
            
            products_data.append({
                "product_id": product.id,
                "name": product.name,
                "current_stock": product.current_stock,
                "avg_cost": avg_cost,
                "total_value": item_value
            })
        
        return {
            "total_value": round(total_value, 2),
            "products": products_data,
            "product_count": len(products_data)
        }
    
    def _get_average_product_cost(self, product_id: int) -> float:
        """Calculate weighted average cost for a product"""
        
        from backend.models.database import PriceHistory, InvoiceItem
        
        # Get recent price history
        prices = self.db.query(PriceHistory).filter(
            PriceHistory.product_id == product_id
        ).order_by(PriceHistory.created_at.desc()).limit(5).all()
        
        if prices:
            avg_price = sum(p.new_price for p in prices) / len(prices)
            return avg_price
        
        # Fallback to invoice prices
        invoice_prices = self.db.query(InvoiceItem).filter(
            InvoiceItem.product_id == product_id
        ).order_by(InvoiceItem.id.desc()).limit(3).all()
        
        if invoice_prices:
            avg_price = sum(p.unit_price for p in invoice_prices) / len(invoice_prices)
            return avg_price
        
        # Default to current cost price
        product = self.db.query(Product).filter(Product.id == product_id).first()
        return product.cost_price if product else 0.0
    
    def calculate_theoretical_vs_actual(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """Calculate theoretical vs actual consumption variance"""
        
        from backend.models.database import StockMovement, Product, WasteLog
        
        # Calculate theoretical consumption
        # Theoretical = Stock_initial + Purchases - Stock_final
        
        # Stock at beginning of period
        stock_initial = self._get_stock_at_date(start_date - timedelta(days=1))
        
        # Purchases during period
        purchases = self._get_purchases_in_period(start_date, end_date)
        
        # Stock at end of period
        stock_final = self._get_stock_at_date(end_date)
        
        # Theoretical consumption
        theoretical = stock_initial + purchases - stock_final
        
        # Actual consumption (OUT movements + waste)
        out_movements = self.db.query(func.sum(StockMovement.quantity)).filter(
            StockMovement.restaurant_id == self.restaurant_id,
            StockMovement.movement_type == "OUT",
            StockMovement.created_at >= start_date,
            StockMovement.created_at <= end_date
        ).scalar() or 0.0
        
        waste_quantity = self.db.query(func.sum(WasteLog.quantity)).filter(
            WasteLog.restaurant_id == self.restaurant_id,
            WasteLog.created_at >= start_date,
            WasteLog.created_at <= end_date
        ).scalar() or 0.0
        
        actual = out_movements + waste_quantity
        
        # Calculate variance
        variance = actual - theoretical
        variance_percentage = (variance / theoretical * 100) if theoretical > 0 else 0
        
        return {
            "theoretical": float(theoretical),
            "actual": float(actual),
            "variance": float(variance),
            "variance_percentage": float(variance_percentage),
            "is_abnormal": abs(variance_percentage) > 5.0
        }
    
    def _get_stock_at_date(self, target_date: datetime) -> float:
        """Get total stock value at a specific date"""
        
        from backend.models.database import StockMovement, Product
        
        products = self.db.query(Product).filter(
            Product.restaurant_id == self.restaurant_id
        ).all()
        
        total_stock = 0.0
        
        for product in products:
            # Get last movement before target date
            last_movement = self.db.query(StockMovement).filter(
                StockMovement.product_id == product.id,
                StockMovement.created_at <= target_date
            ).order_by(StockMovement.created_at.desc()).first()
            
            if last_movement:
                stock_quantity = last_movement.new_stock
            else:
                # No movements before target date, use current stock
                stock_quantity = product.current_stock
            
            total_stock += stock_quantity * product.cost_price
        
        return total_stock
    
    def _get_purchases_in_period(self, start_date: datetime, end_date: datetime) -> float:
        """Get total purchases value in a period"""
        
        from backend.models.database import StockMovement
        
        purchases = self.db.query(func.sum(StockMovement.quantity)).filter(
            StockMovement.restaurant_id == self.restaurant_id,
            StockMovement.movement_type == "IN",
            StockMovement.created_at >= start_date,
            StockMovement.created_at <= end_date
        ).scalar() or 0.0
        
        # Convert to value (approximation using current prices)
        return purchases
    
    def calculate_waste_percentage(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate waste percentage vs consumption"""
        
        from backend.models.database import WasteLog, StockMovement
        
        # Total waste cost
        total_waste = self.db.query(func.sum(WasteLog.cost)).filter(
            WasteLog.restaurant_id == self.restaurant_id,
            WasteLog.created_at >= start_date,
            WasteLog.created_at <= end_date
        ).scalar() or 0.0
        
        # Total consumption value (OUT movements)
        consumption_movements = self.db.query(StockMovement).filter(
            StockMovement.restaurant_id == self.restaurant_id,
            StockMovement.movement_type == "OUT",
            StockMovement.created_at >= start_date,
            StockMovement.created_at <= end_date
        ).all()
        
        total_consumption_value = 0.0
        for movement in consumption_movements:
            product = self.db.query(Product).filter(Product.id == movement.product_id).first()
            if product:
                total_consumption_value += movement.quantity * product.cost_price
        
        # Calculate percentage
        if total_consumption_value > 0:
            waste_percentage = (total_waste / total_consumption_value) * 100
        else:
            waste_percentage = 0.0
        
        return float(waste_percentage)
    
    def calculate_rotation_rate(self, product_id: int, days: int = 30) -> float:
        """Calculate product rotation rate"""
        
        from backend.models.database import StockMovement, Product
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get product
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return 0.0
        
        # Get movements
        movements = self.db.query(StockMovement).filter(
            StockMovement.product_id == product_id,
            StockMovement.created_at >= start_date,
            StockMovement.created_at <= end_date
        ).all()
        
        # Calculate average stock using recorded new_stock values (more reliable)
        if movements:
            stock_history = [float(m.new_stock) for m in movements]
            avg_stock = sum(stock_history) / len(stock_history)
        else:
            avg_stock = float(product.current_stock)
        
        # Calculate total consumption
        total_consumed = sum(float(m.quantity) for m in movements if m.movement_type == "OUT")
        
        # Rotation rate = Total consumed / Average stock
        if avg_stock > 0:
            rotation_rate = total_consumed / avg_stock
        else:
            rotation_rate = 0.0
        
        return float(rotation_rate)
    
    def calculate_eoq(self, product_id: int) -> Dict[str, float]:
        """Calculate Economic Order Quantity (EOQ)"""
        
        from backend.models.database import Product, StockMovement
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"error": "Product not found"}
        
        # Get annual demand (consumption in last year)
        year_ago = datetime.utcnow() - timedelta(days=365)
        
        annual_consumption = self.db.query(func.sum(StockMovement.quantity)).filter(
            StockMovement.product_id == product_id,
            StockMovement.movement_type == "OUT",
            StockMovement.created_at >= year_ago
        ).scalar() or 0.0
        
        # Assume ordering cost (can be configured)
        ordering_cost = 50.0  # Cost per order
        
        # Calculate EOQ: sqrt((2 * D * S) / H)
        # D = Annual demand, S = Ordering cost, H = Holding cost
        holding_cost = product.cost_price * 0.25  # 25% of unit cost
        
        if holding_cost > 0:
            eoq = ((2 * annual_consumption * ordering_cost) / holding_cost) ** 0.5
        else:
            eoq = 0.0
        
        return {
            "annual_demand": float(annual_consumption),
            "ordering_cost": ordering_cost,
            "holding_cost": float(holding_cost),
            "economic_order_quantity": float(eoq),
            "current_stock": float(product.current_stock),
            "reorder_point": float(product.min_stock)
        }
    
    def calculate_reorder_point(self, product_id: int, lead_time_days: int = 7) -> float:
        """Calculate reorder point with safety stock"""
        
        from backend.models.database import Product, StockMovement
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return 0.0
        
        # Calculate average daily consumption
        last_month = datetime.utcnow() - timedelta(days=30)
        
        monthly_consumption = self.db.query(func.sum(StockMovement.quantity)).filter(
            StockMovement.product_id == product_id,
            StockMovement.movement_type == "OUT",
            StockMovement.created_at >= last_month
        ).scalar() or 0.0
        
        avg_daily_consumption = monthly_consumption / 30
        
        # Safety stock (can be configured)
        safety_stock = avg_daily_consumption * 3  # 3 days safety
        
        # Reorder point = (Daily consumption * Lead time) + Safety stock
        reorder_point = (avg_daily_consumption * lead_time_days) + safety_stock
        
        return float(reorder_point)
    
    def generate_alerts(self) -> List[Dict[str, any]]:
        """Generate system alerts"""
        
        from backend.models.database import Product, Alert
        
        alerts = []
        
        # Low stock alerts
        low_stock_products = self.db.query(Product).filter(
            Product.restaurant_id == self.restaurant_id,
            Product.current_stock <= Product.min_stock
        ).all()
        
        for product in low_stock_products:
            alerts.append({
                "type": "low_stock",
                "severity": "high" if product.current_stock == 0 else "medium",
                "title": f"Stock bajo: {product.name}",
                "message": f"Stock actual: {product.current_stock} {product.unit}. Mínimo: {product.min_stock} {product.unit}",
                "entity_type": "product",
                "entity_id": product.id
            })
        
        # Expiration alerts (if tracking expiration dates)
        # This would require additional date tracking fields
        
        # Count pending alerts (weekly reminder)
        last_week = datetime.utcnow() - timedelta(days=7)
        recent_count = self.db.query(Product).filter(
            Product.restaurant_id == self.restaurant_id,
            Product.last_count_date >= last_week.date()
        ).count()
        
        if recent_count == 0:
            alerts.append({
                "type": "count_pending",
                "severity": "low",
                "title": "Conteo pendiente",
                "message": "Se recomienda realizar conteo físico semanal",
                "entity_type": "count",
                "entity_id": None
            })
        
        # Waste alerts
        recent_waste = self.db.query(Product).filter(
            Product.restaurant_id == self.restaurant_id,
            Product.waste_logs.any(
                Product.created_at >= last_week
            )
        ).count()
        
        if recent_waste > 10:  # More than 10 products with waste
            alerts.append({
                "type": "high_waste",
                "severity": "medium",
                "title": "Merma elevada detectada",
                "message": f"Se han registrado mermas en {recent_waste} productos esta semana",
                "entity_type": "waste",
                "entity_id": None
            })
        
        return alerts