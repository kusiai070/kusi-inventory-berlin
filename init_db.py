#!/usr/bin/env python3
"""
Script para inicializar la base de datos SQLite
Database initialization script for Enterprise Restaurant Inventory System
"""

import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.database import Base

def init_database():
    """Inicializar base de datos SQLite con todas las tablas"""
    
    # Crear directorio de base de datos si no existe
    db_dir = os.path.join(os.path.dirname(__file__), "database")
    os.makedirs(db_dir, exist_ok=True)
    
    # Ruta de la base de datos
    db_path = os.path.join(db_dir, "inventory.db")
    
    # Crear engine de SQLAlchemy
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    
    # Crear todas las tablas
    print("🗄️ Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente")
    
    # Ejecutar script de inicialización
    print("📊 Insertando datos iniciales...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Leer y ejecutar script SQL
        script_path = os.path.join(db_dir, "init.sql")
        with open(script_path, 'r', encoding='utf-8') as f:
            script = f.read()
            cursor.executescript(script)
        
        conn.commit()
        print("✅ Datos iniciales insertados")
        
    except Exception as e:
        print(f"❌ Error insertando datos iniciales: {e}")
        conn.rollback()
    
    finally:
        conn.close()
    
    print(f"🎯 Base de datos inicializada en: {db_path}")
    return db_path

if __name__ == "__main__":
    init_database()