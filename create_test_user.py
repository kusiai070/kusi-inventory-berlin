"""
Script para crear usuario de prueba funcional
"""
import sys
sys.path.append('.')

from backend.models.database import SessionLocal, engine, Base, User, Restaurant
from passlib.context import CryptContext

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

# Configurar hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()

try:
    # Verificar si existe restaurante
    restaurant = db.query(Restaurant).first()
    if not restaurant:
        print("Creando restaurante de prueba...")
        restaurant = Restaurant(
            name="Restaurante Berlin",
            address="Berlin, Germany",
            currency="EUR",
            timezone="Europe/Berlin",
            phone="+49123456789",
            email="info@berlin-restaurant.com",
            is_active=True
        )
        db.add(restaurant)
        db.commit()
        db.refresh(restaurant)
        print(f"✅ Restaurante creado: ID {restaurant.id}")
    else:
        print(f"✅ Restaurante existente: {restaurant.name} (ID: {restaurant.id})")
    
    # Verificar usuarios existentes
    users = db.query(User).all()
    print(f"\n📋 USUARIOS EXISTENTES ({len(users)}):")
    for u in users:
        print(f"  - Email: {u.email} | Nombre: {u.full_name} | Role: {u.role} | Activo: {u.is_active}")
    
    # Crear usuario admin de prueba
    admin_email = "admin@berlin.com"
    admin = db.query(User).filter(User.email == admin_email).first()
    
    if not admin:
        print(f"\n🔧 Creando usuario admin...")
        hashed_password = pwd_context.hash("admin123")
        admin = User(
            email=admin_email,
            hashed_password=hashed_password,
            full_name="Admin Berlin",
            role="admin",
            restaurant_id=restaurant.id,
            is_active=True
        )
        db.add(admin)
        db.commit()
        print(f"✅ Usuario admin creado")
    else:
        print(f"\n🔧 Actualizando contraseña del admin existente...")
        admin.hashed_password = pwd_context.hash("admin123")
        admin.is_active = True
        db.commit()
        print(f"✅ Contraseña actualizada")
    
    print("\n" + "="*60)
    print("✅ CREDENCIALES DE ACCESO:")
    print("="*60)
    print(f"Email:    admin@berlin.com")
    print(f"Password: admin123")
    print("="*60)
    
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()
