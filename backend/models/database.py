"""
Modelos de base de datos para Sistema Enterprise de Inventarios
Enterprise Restaurant Inventory System - Database Models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Date, Numeric, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
from sqlalchemy import Enum as SQLEnum
from backend.models.enums import StockMovementType, WasteType, CountType, CountStatus, InvoiceStatus
from backend.config import settings

# Database Configuration
# Configurar SSL para PostgreSQL/Neon
connect_args = {}
if settings.DATABASE_URL and "postgresql" in settings.DATABASE_URL:
    connect_args = {
        "sslmode": "require",
        "connect_timeout": 10
    }

# Crear engine con configuración SSL
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base = declarative_base()

class Restaurant(Base):
    """Modelo para restaurantes (multi-tenant)"""
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255))
    currency = Column(String(3), default="USD")
    timezone = Column(String(50), default="UTC")
    phone = Column(String(20))
    email = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relaciones
    products = relationship("Product", back_populates="restaurant")
    users = relationship("User", back_populates="restaurant")
    invoices = relationship("Invoice", back_populates="restaurant")
    counts = relationship("PhysicalCount", back_populates="restaurant")
    waste_logs = relationship("WasteLog", back_populates="restaurant")


class User(Base):
    """Modelo para usuarios del sistema"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), default="staff")  # admin, manager, staff
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relaciones
    restaurant = relationship("Restaurant", back_populates="users")


class Category(Base):
    """Modelo para categorías de productos"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255))
    type = Column(String(20), nullable=False)  # food, beverage, cleaning
    icon = Column(String(50))
    is_active = Column(Boolean, default=True)
    
    # Relaciones
    products = relationship("Product", back_populates="category")


class Provider(Base):
    """Modelo para proveedores"""
    __tablename__ = "providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    contact_person = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(String(255))
    tax_id = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relaciones
    products = relationship("Product", back_populates="provider")
    invoices = relationship("Invoice", back_populates="provider")


class Product(Base):
    """Modelo principal para productos del inventario"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    barcode = Column(String(50), unique=True)
    
    # Unidad de medida
    unit = Column(String(20), nullable=False)  # kg, lit, unit, package
    
    # Stock levels
    # Stock levels
    current_stock = Column(Numeric(12, 3), default=0.0)
    min_stock = Column(Numeric(12, 3), default=0.0)
    max_stock = Column(Numeric(12, 3), default=100.0)
    
    # Precios
    cost_price = Column(Numeric(10, 2), default=0.0)
    selling_price = Column(Numeric(10, 2), default=0.0)
    
    # Relaciones
    category_id = Column(Integer, ForeignKey("categories.id"))
    provider_id = Column(Integer, ForeignKey("providers.id"))
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    
    # Tracking
    last_purchase_date = Column(Date)
    last_count_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relaciones
    category = relationship("Category", back_populates="products")
    provider = relationship("Provider", back_populates="products")
    restaurant = relationship("Restaurant", back_populates="products")
    stock_movements = relationship("StockMovement", back_populates="product")
    waste_logs = relationship("WasteLog", back_populates="product")


class StockMovement(Base):
    """Modelo para tracking de movimientos de stock"""
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    movement_type = Column(SQLEnum(StockMovementType), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    previous_stock = Column(Numeric(12, 3), nullable=False)
    new_stock = Column(Numeric(12, 3), nullable=False)
    reason = Column(String(100))
    reference_id = Column(String(50))  # ID de factura o conteo
    user_id = Column(Integer, ForeignKey("users.id"))
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    created_at = Column(DateTime, server_default=func.now())
    
    # Relaciones
    product = relationship("Product", back_populates="stock_movements")


class Invoice(Base):
    """Modelo para facturas procesadas por OCR"""
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), nullable=False)
    invoice_date = Column(Date, nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"))
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    
    # Totales
    subtotal = Column(Numeric(10, 2), default=0.0)
    tax = Column(Numeric(10, 2), default=0.0)
    total = Column(Numeric(10, 2), default=0.0)
    
    # Metadata OCR
    ocr_text = Column(Text)  # Texto raw del OCR
    ocr_confidence = Column(Float)  # Confianza del OCR
    
    # Estado
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.PENDING)
    processed_by = Column(Integer, ForeignKey("users.id"))
    processed_at = Column(DateTime)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relaciones
    provider = relationship("Provider", back_populates="invoices")
    restaurant = relationship("Restaurant", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice")


class InvoiceItem(Base):
    """Items individuales de una factura"""
    __tablename__ = "invoice_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    
    # Info del producto en la factura
    product_name = Column(String(100), nullable=False)  # Como aparece en la factura
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # Tracking
    stock_updated = Column(Boolean, default=False)  # Si ya se actualizó el inventario
    
    # Relaciones
    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product")


class PhysicalCount(Base):
    """Modelo para conteos físicos de inventario"""
    __tablename__ = "physical_counts"
    
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    count_type = Column(SQLEnum(CountType), nullable=False)
    status = Column(SQLEnum(CountStatus), default=CountStatus.IN_PROGRESS)
    
    # Quién realizó el conteo
    started_by = Column(Integer, ForeignKey("users.id"))
    completed_by = Column(Integer, ForeignKey("users.id"))
    
    # Fechas
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    
    # Relaciones
    restaurant = relationship("Restaurant", back_populates="counts")
    items = relationship("PhysicalCountItem", back_populates="count")


class PhysicalCountItem(Base):
    """Items individuales de un conteo físico"""
    __tablename__ = "physical_count_items"
    
    id = Column(Integer, primary_key=True, index=True)
    count_id = Column(Integer, ForeignKey("physical_counts.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    
    # Valores
    system_stock = Column(Numeric(12, 3), nullable=False)  # Stock según sistema
    physical_count = Column(Numeric(12, 3), nullable=False)  # Conteo físico real
    difference = Column(Numeric(12, 3))  # Diferencia calculada
    
    # Ajuste realizado
    adjustment_made = Column(Boolean, default=False)
    
    # Relaciones
    count = relationship("PhysicalCount", back_populates="items")
    product = relationship("Product")


class WasteLog(Base):
    """Modelo para registro de mermas"""
    __tablename__ = "waste_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    
    # Info de la merma
    quantity = Column(Numeric(12, 3), nullable=False)
    waste_type = Column(SQLEnum(WasteType), nullable=False)
    reason = Column(String(255))
    cost = Column(Numeric(10, 2))  # Calculado automáticamente
    
    # Quién registró
    user_id = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relaciones
    product = relationship("Product", back_populates="waste_logs")
    restaurant = relationship("Restaurant", back_populates="waste_logs")


class PriceHistory(Base):
    """Historial de cambios de precios"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    old_price = Column(Numeric(10, 2), nullable=False)
    new_price = Column(Numeric(10, 2), nullable=False)
    change_reason = Column(String(100))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())


class Alert(Base):
    """Modelo para alertas del sistema"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"))
    alert_type = Column(String(30), nullable=False)  # low_stock, expiration, count_pending
    severity = Column(String(10), default="medium")  # low, medium, high, critical
    
    # Contenido
    title = Column(String(100), nullable=False)
    message = Column(Text)
    
    # Estado
    is_active = Column(Boolean, default=True)
    dismissed_by = Column(Integer, ForeignKey("users.id"))
    dismissed_at = Column(DateTime)
    
    # Metadata
    entity_type = Column(String(20))  # product, count, etc
    entity_id = Column(Integer)  # ID del objeto relacionado
    
    created_at = Column(DateTime, server_default=func.now())