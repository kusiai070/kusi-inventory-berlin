import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.models.database import Base, Restaurant, User, Category, Provider

# Setup DB
DATABASE_URL = "sqlite:///" + os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "database", "inventory.db")
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tenants():
    db = SessionLocal()
    
    tenants = [
        {"name": "Cafetería Central", "type": "cafe"},
        {"name": "Pizzería Centro", "type": "pizza"},
        {"name": "Pizzería Norte", "type": "pizza"}
    ]
    
    print("🏢 Creando Restaurantes y Administradores...\n")
    
    for tenant in tenants:
        # Check if exists
        existing = db.query(Restaurant).filter(Restaurant.name == tenant["name"]).first()
        if existing:
            print(f"⚠️ {tenant['name']} ya existe. Saltando...")
            continue
            
        # Create Restaurant
        restaurant = Restaurant(
            name=tenant["name"],
            address="Dirección pendiente",
            currency="USD",
            phone="555-0000"
        )
        db.add(restaurant)
        db.commit() # Commit to get ID
        
        # Create Admin User
        username = tenant["name"].lower().replace(' ', '_').replace('í', 'i').replace('é', 'e')
        email = f"admin@{username}.com"
        
        admin = User(
            email=email,
            hashed_password=generate_password_hash("admin123"),
            full_name=f"Admin {tenant['name']}",
            role="admin",
            restaurant_id=restaurant.id
        )
        db.add(admin)
        
        print(f"✅ Creado: {tenant['name']}")
        print(f"   └── User: {email} / Pass: admin123")
        
    db.commit()
    db.close()
    print("\n✨ Proceso completado.")

if __name__ == "__main__":
    create_tenants()
