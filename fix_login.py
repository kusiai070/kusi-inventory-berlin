"""
Script directo SQL para resetear contraseña
"""
import sqlite3
import bcrypt

# Conectar a la BD
conn = sqlite3.connect('enterprise_local.db')
cursor = conn.cursor()

# Listar usuarios
cursor.execute("SELECT id, email, full_name, role FROM users WHERE role='admin' LIMIT 1")
user = cursor.fetchone()

if user:
    user_id, email, name, role = user
    print(f"Usuario encontrado: {email} ({name})")
    
    # Crear hash simple de contraseña "123"
    password = "123"
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Actualizar en BD
    cursor.execute("UPDATE users SET hashed_password = ?, is_active = 1 WHERE id = ?", 
                   (hashed.decode('utf-8'), user_id))
    conn.commit()
    
    print("\n" + "="*60)
    print("✅ CREDENCIALES LISTAS:")
    print("="*60)
    print(f"Email:    {email}")
    print(f"Password: {password}")
    print("="*60)
    print(f"\n🌐 Abre: http://localhost:8000")
else:
    print("❌ No se encontró usuario admin")

conn.close()
