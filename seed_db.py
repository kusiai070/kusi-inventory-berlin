#!/usr/bin/env python3
"""
Script para insertar datos de demostración
Seed database with demo data for testing
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from backend.models.database import (
    Base, Restaurant, User, Category, Provider, Product, 
    StockMovement, Invoice, InvoiceItem, PhysicalCount, 
    PhysicalCountItem, WasteLog, Alert
)
from werkzeug.security import generate_password_hash

def seed_database():
    """Insertar datos de demostración"""
    
    # Conectar a base de datos
    db_path = os.path.join(os.path.dirname(__file__), "database", "inventory.db")
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("🌱 Insertando datos de demostración...")
    
    try:
        # Crear usuarios de ejemplo
        print("👤 Creando usuarios de ejemplo...")
        restaurants = session.query(Restaurant).all()
        
        for restaurant in restaurants:
            # Admin user
            admin = User(
                email=f"admin@{restaurant.name.lower().replace(' ', '')}.com",
                hashed_password=generate_password_hash("admin123"),
                full_name=f"Administrador {restaurant.name}",
                role="admin",
                restaurant_id=restaurant.id
            )
            session.add(admin)
            
            # Manager user
            manager = User(
                email=f"manager@{restaurant.name.lower().replace(' ', '')}.com",
                hashed_password=generate_password_hash("manager123"),
                full_name=f"Gerente {restaurant.name}",
                role="manager",
                restaurant_id=restaurant.id
            )
            session.add(manager)
            
            # Staff user
            staff = User(
                email=f"staff@{restaurant.name.lower().replace(' ', '')}.com",
                hashed_password=generate_password_hash("staff123"),
                full_name=f"Personal {restaurant.name}",
                role="staff",
                restaurant_id=restaurant.id
            )
            session.add(staff)
        
        session.commit()
        print("✅ Usuarios creados")
        
        # Crear productos de ejemplo para cada restaurante
        print("📦 Creando productos de ejemplo...")
        categories = session.query(Category).all()
        providers = session.query(Provider).all()
        
        product_names = {
            'food': [
                'Filete de Res', 'Pollo Entero', 'Salmón Fresco', 'Pasta Italiana',
                'Tomates Roma', 'Cebolla Blanca', 'Lechuga Iceberg', 'Queso Mozzarella',
                'Pan Baguette', 'Aceite de Oliva', 'Sal Marina', 'Pimienta Negra'
            ],
            'beverage': [
                'Cerveza Nacional', 'Vino Tinto', 'Vino Blanco', 'Agua Mineral',
                'Refresco Cola', 'Jugo de Naranja', 'Energética', 'Whisky Premium'
            ],
            'cleaning': [
                'Detergente Multiusos', 'Desinfectante', 'Jabón Líquido', 'Papel Higiénico',
                'Toallas de Papel', 'Guantes de Nitrilo', 'Basureros', 'Escobas'
            ]
        }
        
        for restaurant in restaurants:
            for category in categories:
                if category.type in product_names:
                    for i, product_name in enumerate(product_names[category.type][:4]):
                        provider = providers[i % len(providers)]
                        
                        product = Product(
                            name=f"{product_name} - {restaurant.name}",
                            description=f"{product_name} de alta calidad",
                            barcode=f"BAR-{restaurant.id}-{category.id}-{i:03d}",
                            unit=['kg', 'lit', 'unit', 'package'][i % 4],
                            current_stock=float(20 + i * 5),
                            min_stock=float(5 + i * 2),
                            max_stock=float(50 + i * 10),
                            cost_price=float(5.0 + i * 1.5),
                            selling_price=float(8.0 + i * 2.5),
                            category_id=category.id,
                            provider_id=provider.id,
                            restaurant_id=restaurant.id,
                            last_purchase_date=datetime.now().date() - timedelta(days=i)
                        )
                        session.add(product)
        
        session.commit()
        print("✅ Productos creados")
        
        # Crear movimientos de stock
        print("📊 Creando movimientos de stock...")
        products = session.query(Product).all()
        users = session.query(User).all()
        
        for product in products[:5]:
            # Movimiento de entrada (compra)
            movement_in = StockMovement(
                product_id=product.id,
                movement_type="IN",
                quantity=10.0,
                previous_stock=product.current_stock - 10.0,
                new_stock=product.current_stock,
                reason="Compra inicial",
                reference_id=f"INV-{datetime.now().strftime('%Y%m%d')}-001",
                user_id=users[0].id,
                restaurant_id=product.restaurant_id
            )
            session.add(movement_in)
            
            # Movimiento de salida (consumo)
            movement_out = StockMovement(
                product_id=product.id,
                movement_type="OUT",
                quantity=2.0,
                previous_stock=product.current_stock,
                new_stock=product.current_stock - 2.0,
                reason="Consumo del día",
                reference_id=f"CONS-{datetime.now().strftime('%Y%m%d')}-001",
                user_id=users[1].id,
                restaurant_id=product.restaurant_id
            )
            session.add(movement_out)
        
        session.commit()
        print("✅ Movimientos de stock creados")
        
        # Crear facturas de ejemplo
        print("📄 Creando facturas de ejemplo...")
        for restaurant in restaurants:
            provider = providers[0]
            
            invoice = Invoice(
                invoice_number=f"FAC-{restaurant.id}-{datetime.now().strftime('%Y%m%d')}-001",
                invoice_date=datetime.now().date(),
                provider_id=provider.id,
                restaurant_id=restaurant.id,
                subtotal=150.0,
                tax=15.0,
                total=165.0,
                ocr_text="Factura de ejemplo procesada por OCR",
                ocr_confidence=0.95,
                status="processed",
                processed_by=users[0].id,
                processed_at=datetime.now()
            )
            session.add(invoice)
            session.flush()
            
            # Items de la factura
            products_restaurant = session.query(Product).filter_by(restaurant_id=restaurant.id).limit(3).all()
            for i, product in enumerate(products_restaurant):
                item = InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=product.id,
                    product_name=product.name,
                    quantity=10.0,
                    unit_price=product.cost_price,
                    total_price=10.0 * product.cost_price,
                    stock_updated=True
                )
                session.add(item)
        
        session.commit()
        print("✅ Facturas creadas")
        
        # Crear mermas de ejemplo
        print("⚠️ Creando registros de merma...")
        for product in products[:3]:
            waste = WasteLog(
                product_id=product.id,
                restaurant_id=product.restaurant_id,
                quantity=1.5,
                waste_type="preparation",
                reason="Preparación excesiva",
                cost=1.5 * product.cost_price,
                user_id=users[0].id
            )
            session.add(waste)
        
        session.commit()
        print("✅ Mermas registradas")
        
        # Crear alertas de ejemplo
        print("🚨 Creando alertas del sistema...")
        for restaurant in restaurants:
            # Alerta de stock bajo
            alert_low_stock = Alert(
                restaurant_id=restaurant.id,
                alert_type="low_stock",
                severity="medium",
                title="Stock bajo detectado",
                message="Algunos productos están por debajo del stock mínimo",
                entity_type="product",
                entity_id=1
            )
            session.add(alert_low_stock)
            
            # Alerta de conteo pendiente
            alert_count = Alert(
                restaurant_id=restaurant.id,
                alert_type="count_pending",
                severity="low",
                title="Conteo pendiente",
                message="Se recomienda realizar conteo físico semanal",
                entity_type="count",
                entity_id=1
            )
            session.add(alert_count)
        
        session.commit()
        print("✅ Alertas creadas")
        
        print("\n🎉 Datos de demostración insertados exitosamente!")
        print("\nCredenciales de prueba:")
        for restaurant in restaurants:
            domain = restaurant.name.lower().replace(' ', '')
            print(f"\n🏪 {restaurant.name}:")
            print(f"   Admin: admin@{domain}.com / admin123")
            print(f"   Manager: manager@{domain}.com / manager123")
            print(f"   Staff: staff@{domain}.com / staff123")
        
    except Exception as e:
        print(f"❌ Error insertando datos: {e}")
        session.rollback()
        raise
    
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()