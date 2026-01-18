"""
Script para restaurar usuarios hardcodeados para pruebas locales
"""
import sys
import bcrypt
import sqlite3

# Conectar a la BD
conn = sqlite3.connect('enterprise_local.db')
cursor = conn.cursor()

users = [
    {
        "email": "admin@restauranteelsol.com",
        "name": "Administrador Restaurante El Sol",
        "role": "admin",
        "pass": "admin123"
    },
    {
        "email": "manager@restauranteelsol.com",
        "name": "Gerente Restaurante El Sol",
        "role": "manager",
        "pass": "manager123"
    },
    {
        "email": "staff@restauranteelsol.com",
        "name": "Personal Restaurante El Sol",
        "role": "staff",
        "pass": "staff123"
    }
]

print("Restaurando usuarios...")

for u in users:
    # Hash password with bcrypt
    hashed = bcrypt.hashpw(u["pass"].encode('utf-8'), bcrypt.gensalt())
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (u["email"],))
    existing = cursor.fetchone()
    
    if existing:
        print(f"Actualizando {u['email']}...")
        cursor.execute("""
            UPDATE users 
            SET hashed_password = ?, full_name = ?, role = ?, is_active = 1 
            WHERE email = ?
        """, (hashed.decode('utf-8'), u["name"], u["role"], u["email"]))
    else:
        print(f"Creando {u['email']}...")
        # Get restaurant ID (assume 1)
        cursor.execute("INSERT INTO users (email, hashed_password, full_name, role, restaurant_id, is_active, created_at) VALUES (?, ?, ?, ?, 1, 1, date('now'))",
                      (u["email"], hashed.decode('utf-8'), u["name"], u["role"]))

conn.commit()
conn.close()

print("\n" + "="*60)
print("✅ USUARIOS RESTAURADOS:")
print("="*60)
for u in users:
    print(f"User: {u['email']:<30} | Pass: {u['pass']}")
print("="*60)
