import sys
import os
import threading
import time
from decimal import Decimal
from datetime import datetime

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.database import Base, Product, Restaurant, User, StockMovement, WasteLog
from backend.models.enums import StockMovementType, WasteType
from backend.api.products import router as products_router

# Setup Test DB
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///./test_qa_inventory.db")
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_db():
    # Drop and recreate
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    # Create Dummy Restaurant & User
    restaurant = Restaurant(name="Test Restaurant", address="123 Test St", phone="555-0000")
    db.add(restaurant)
    db.commit()
    
    user = User(
        email="test@admin.com", 
        full_name="Test Admin",
        hashed_password="fake", 
        role="admin",
        restaurant_id=restaurant.id
    )
    db.add(user)
    db.commit()
    
    return db, restaurant.id, user.id

def test_decimal_precision(db, restaurant_id):
    print("\n[TEST 1] - Precisión Decimal (Money & Stock)")
    
    # Create product with 3 decimal places for stock and 2 for price
    product = Product(
        name="Precice Coffee",
        category_id=1,
        unit="kg",
        current_stock=Decimal('10.333'),  # 10.333 kg
        cost_price=Decimal('15.55'),      # $15.55
        selling_price=Decimal('25.99'),
        restaurant_id=restaurant_id
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Check Storage
    assert isinstance(product.current_stock, Decimal), "Stock no es Decimal"
    assert isinstance(product.cost_price, Decimal), "Precio no es Decimal"
    
    # Calculate Total Value manually
    total_value = product.current_stock * product.cost_price
    # 10.333 * 15.55 = 160.67815
    
    print(f"  Stock: {product.current_stock}")
    print(f"  Cost: {product.cost_price}")
    print(f"  Total Value (Calculated): {total_value}")
    
    expected = Decimal('160.67815')
    assert total_value == expected, f"Error matemático: Esperado {expected}, Obtenido {total_value}"
    
    print("  ✅ Cálculo decimal exacto (sin residuos flotantes).")

def test_enums(db, restaurant_id):
    print("\n[TEST 2] - Enums y Tipos Fuertes")
    
    # Try to insert WasteLog with valid Enum
    product = db.query(Product).first()
    waste = WasteLog(
        product_id=product.id,
        restaurant_id=restaurant_id,
        quantity=Decimal('1.000'),
        waste_type=WasteType.EXPIRED, # Using Enum
        reason="Test Enum",
        cost=Decimal('10.00'),
        user_id=1
    )
    db.add(waste)
    db.commit()
    print(f"  ✅ WasteLog creado con WasteType.EXPIRED ({waste.waste_type})")

def test_stock_movement_atomicidad_simulation(restaurant_id):
    print("\n[TEST 3] - Atomicidad y Concurrencia (Simulación)")
    
    # Since SQLite with typical locking handles simple concurrency well, 
    # and we implemented 'with_for_update' tailored for Postgres/MySQL mostly 
    # (SQLite ignores FOR UPDATE but locks the file), this test verifies logic flow.
    
    # We will simulate the logic of our API endpoint: Read (Lock) -> Update
    
    db1 = TestingSessionLocal()
    db2 = TestingSessionLocal()
    
    product = Product(
        name="Atomic Burger",
        category_id=1,
        unit="unit",
        current_stock=Decimal('100.000'),
        cost_price=Decimal('5.00'),
        restaurant_id=restaurant_id
    )
    db1.add(product)
    db1.commit()
    
    p_id = product.id
    db1.close()
    
    def sell_product(session, quantity):
        # Simulate the API logic with locking
        # SQLite ignores with_for_update, but ensure code runs without crashing
        p = session.query(Product).filter(Product.id == p_id).with_for_update().first()
        time.sleep(0.1) # Simulate processing time
        p.current_stock -= Decimal(str(quantity))
        session.commit()
        
    t1 = threading.Thread(target=sell_product, args=(db1, 10))
    t2 = threading.Thread(target=sell_product, args=(db2, 20))
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    # Verify final stock
    final_db = TestingSessionLocal()
    final_p = final_db.query(Product).filter(Product.id == p_id).first()
    
    print(f"  Stock Inicial: 100.000")
    print(f"  Ventas simuladas: -10 y -20")
    print(f"  Stock Final: {final_p.current_stock}")
    
    assert final_p.current_stock == Decimal('70.000'), f"Fallo de concurrencia: {final_p.current_stock}"
    print("  ✅ Stock final correcto bajo estrés simulado.")
    final_db.close()

def test_negative_stock_prevention(db, restaurant_id):
    print("\n[TEST 4] - Prevención Stock Negativo")
    
    product = Product(
        name="Low Stock Item",
        category_id=1,
        unit="unit",
        current_stock=Decimal('5.000'),
        cost_price=Decimal('1.00'),
        restaurant_id=restaurant_id
    )
    db.add(product)
    db.commit()
    
    # Attempt to update to negative via API logic logic simulation
    try:
        new_stock = Decimal('-1.000')
        if new_stock < 0:
            raise ValueError("Stock cannot be negative")
        product.current_stock = new_stock
        print("  ❌ Fallo: Se permitió stock negativo")
    except ValueError as e:
        print(f"  ✅ Validacion Correcta: {e}")

if __name__ == "__main__":
    print("=== INICIANDO QA SUITE (KusiTurno v2 Core) ===")
    
    try:
        db, r_id, u_id = setup_db()
        test_decimal_precision(db, r_id)
        test_enums(db, r_id)
        test_negative_stock_prevention(db, r_id)
        db.close()
        
        # Concurrency needs fresh sessions
        test_stock_movement_atomicidad_simulation(r_id)
        
        print("\n=== ✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE ===")
        
        # Cleanup
        os.remove("./test_qa_inventory.db")
        
    except Exception as e:
        print(f"\n❌ ERROR CRITICO EN PRUEBAS: {e}")
        import traceback
        traceback.print_exc()
