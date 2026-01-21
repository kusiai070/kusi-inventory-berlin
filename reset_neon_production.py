"""
Reset completo de Neon DB para mes de prueba en Berlín
ADVERTENCIA: Borra TODOS los datos
"""
import os
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Neon connection
DATABASE_URL = "postgresql://neondb_owner:npg_eszRZgG14BtS@ep-twilight-paper-abvrqqpo-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"},
    pool_pre_ping=True
)

SessionLocal = sessionmaker(bind=engine)

def reset_database():
    """Borra todas las tablas y las recrea"""
    with engine.connect() as conn:
        # Listar todas las tablas
        result = conn.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        """))
        tables = [row[0] for row in result]
        
        print(f"📋 Tablas encontradas: {tables}")
        
        # Borrar todas las tablas
        for table in tables:
            print(f"🗑️  Borrando tabla: {table}")
            conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
        
        conn.commit()
        print("✅ Todas las tablas borradas")

def create_tables():
    """Recrea todas las tablas"""
    from backend.models.database import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas recreadas")

def create_admin():
    """Crea restaurante y usuario admin"""
    db = SessionLocal()
    
    # 1. CREAR RESTAURANTE
    restaurant_result = db.execute(text("""
        INSERT INTO restaurants (name, address, email, is_active)
        VALUES (:name, :address, :email, true)
        RETURNING id
    """), {
        "name": "Restaurante El Sol - Berlín",
        "address": "Berlín, Alemania",
        "email": "admin@RestauranteElSol.com"
    })
    restaurant_id = restaurant_result.fetchone()[0]
    db.commit()
    
    # 2. CREAR ADMIN con restaurant_id
    password = "admin123"
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    hashed_str = hashed.decode('utf-8')
    
    db.execute(text("""
        INSERT INTO users (email, hashed_password, full_name, role, is_active, restaurant_id)
        VALUES (:email, :pwd, :name, :role, true, :restaurant_id)
    """), {
        "email": "admin@RestauranteElSol.com",
        "pwd": hashed_str,
        "name": "Administrador",
        "role": "admin",
        "restaurant_id": restaurant_id
    })
    
    db.commit()
    db.close()
    print(f"✅ Restaurante creado: ID {restaurant_id}")
    print("✅ Admin creado y asignado al restaurante")

def seed_initial_data():
    """Inserta categorías iniciales"""
    db = SessionLocal()
    
    # CATEGORÍAS (10 Básicas)
    categories = [
        ('Carnes', 'Carnes y proteínas', 'food', '🥩'),
        ('Lácteos', 'Leche, quesos y derivados', 'food', '🥛'),
        ('Verduras', 'Vegetales y frutas', 'food', '🥬'),
        ('Panadería', 'Panes y harinas', 'food', '🍞'),
        ('Granos', 'Arroz, menestras y cereales', 'food', '🌾'),
        ('Bebidas Alcohólicas', 'Cervezas, vinos y licores', 'beverage', '🍺'),
        ('Bebidas Sin Alcohol', 'Agua, gaseosas y jugos', 'beverage', '🥤'),
        ('Limpieza', 'Detergentes y aseo', 'cleaning', '🧽'),
        ('Utensilios', 'Cubiertos y vajilla', 'reusable', '🍽️'),
        ('Condimentos', 'Especias y aderezos', 'food', '🧂')
    ]
    
    print(f"🌱 Creando {len(categories)} categorías...")
    
    for name, desc, cat_type, icon in categories:
        db.execute(text("""
            INSERT INTO categories (name, description, type, icon, is_active)
            VALUES (:name, :desc, :type, :icon, true)
        """), {"name": name, "desc": desc, "type": cat_type, "icon": icon})
    
    db.commit()
    db.close()
    print(f"✅ Categorías creadas correctamente (Sin proveedores)")


if __name__ == "__main__":
    print("⚠️  RESET COMPLETO DE NEON DB")
    print("⚠️  Se borrarán TODOS los datos")
    confirm = input("¿Continuar? (escribe 'SI'): ")
    
    if confirm == "SI":
        reset_database()
        create_tables()
        seed_initial_data()
        create_admin()
        print("🎉 Base de datos reseteada - Lista para Berlín")
    else:
        print("❌ Cancelado")
