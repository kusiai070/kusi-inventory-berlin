from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Adjust path if needed
db_path = os.path.join("backend", "database", "inventory.db")
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    # Try alternate path
    db_path = os.path.join("database", "inventory.db")

print(f"Checking DB at: {db_path}")

engine = create_engine(f"sqlite:///{db_path}")
Session = sessionmaker(bind=engine)
session = Session()

try:
    result = session.execute(text("SELECT id, email, role, is_active FROM users"))
    users = result.fetchall()
    print("\n--- USERS IN DB ---")
    for u in users:
        print(f"ID: {u[0]}, Email: {u[1]}, Role: {u[2]}, Active: {u[3]}")
except Exception as e:
    print(f"Error reading DB: {e}")
finally:
    session.close()
