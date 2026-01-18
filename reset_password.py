"""
Script simple para resetear contraseña de admin
"""
import sys
sys.path.append('.')

from backend.models.database import SessionLocal, User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

try:
    # Buscar primer admin
    admin = db.query(User).filter(User.role == "admin").first()
    
    if admin:
        print(f"Usuario encontrado: {admin.email}")
        # Contraseña simple
        simple_password = "123"
        admin.hashed_password = pwd_context.hash(simple_password[:72])  # Truncar a 72 bytes
        admin.is_active = True
        db.commit()
        
        print("\n" + "="*60)
        print("✅ CREDENCIALES ACTUALIZADAS:")
        print("="*60)
        print(f"Email:    {admin.email}")
        print(f"Password: {simple_password}")
        print("="*60)
    else:
        print("❌ No se encontró usuario admin")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
