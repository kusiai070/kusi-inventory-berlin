-- Database initialization script for Enterprise Restaurant Inventory System
-- Script de inicialización para Sistema de Inventarios Enterprise

-- Insertar categorías predeterminadas
INSERT INTO categories (name, description, type, icon) VALUES 
('Carnes y Pescados', 'Productos cárnicos y mariscos frescos', 'food', '🥩'),
('Lácteos y Huevos', 'Productos lácteos y huevos', 'food', '🥛'),
('Verduras y Frutas', 'Productos frescos de temporada', 'food', '🥬'),
('Panadería', 'Productos de panadería y repostería', 'food', '🍞'),
('Granos y Cereales', 'Arroz, legumbres, cereales', 'food', '🌾'),
('Bebidas Alcohólicas', 'Cervezas, vinos y licores', 'beverage', '🍺'),
('Bebidas Sin Alcohol', 'Refrescos, jugos y aguas', 'beverage', '🥤'),
('Suministros de Limpieza', 'Productos de limpieza e higiene', 'cleaning', '🧽'),
('Utensilios y Desechables', 'Utensilios, platos y productos desechables', 'cleaning', '🍽️'),
('Condimentos y Salsas', 'Especias, condimentos y salsas', 'food', '🧂');

-- Insertar proveedores de ejemplo
INSERT INTO providers (name, contact_person, phone, email, address, tax_id) VALUES 
('Distribuidora Central', 'Juan Pérez', '555-0101', 'juan@central.com', 'Av. Principal 123', '123456789'),
('Productores Frescos S.A.', 'María García', '555-0202', 'maria@frescos.com', 'Calle Mercado 456', '987654321'),
('Bebidas Premium', 'Carlos López', '555-0303', 'carlos@premium.com', 'Zona Industrial Norte', '456789123'),
('Limpieza Express', 'Ana Martínez', '555-0404', 'ana@express.com', 'Centro Comercial Sur', '789123456');

-- Insertar restaurantes de ejemplo (máximo 3)
INSERT INTO restaurants (name, address, currency, timezone, phone, email) VALUES 
('Restaurante El Sol', 'Plaza Mayor 789, Ciudad', 'USD', 'America/New_York', '555-1001', 'info@elsol.com'),
('Bistró Luna', 'Avenida Gourmet 321, Ciudad', 'USD', 'America/New_York', '555-2002', 'contacto@bistroluna.com'),
('Café Estrella', 'Centro Comercial Central, Local 15', 'USD', 'America/New_York', '555-3003', 'hola@cafeestrella.com');