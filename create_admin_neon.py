import os
import bcrypt
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Database URL desde .env o environment
DATABASE_URL = "postgresql://neondb_owner:npg_eszRZgG14BtS@ep-twilight-paper-abvrqqpo-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require"

# Crear engine con SSL
engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"},
    pool_pre_ping=True
)

# Hashear password
password = "admin123"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
hashed_str = hashed.decode('utf-8')

print(f"Hash generado: {hashed_str}")

# Insertar o actualizar usuario
with engine.connect() as conn:
    # Primero verificar si existe
    result = conn.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": "admin@RestauranteElSol.com"}
    )
    user = result.fetchone()
    
    if user:
        # Actualizar password
        conn.execute(
            text("UPDATE users SET hashed_password = :pwd WHERE email = :email"),
            {"pwd": hashed_str, "email": "admin@RestauranteElSol.com"}
        )
        conn.commit()
        print("✅ Usuario admin actualizado")
    else:
        # Crear usuario
        conn.execute(
            text("""
                INSERT INTO users (email, hashed_password, full_name, role, is_active)
                VALUES (:email, :pwd, :name, :role, true)
            """),
            {
                "email": "admin@RestauranteElSol.com",
                "pwd": hashed_str,
                "name": "Admin User",
                "role": "admin"
            }
        )
        conn.commit()
        print("✅ Usuario admin creado")

print("Done!")