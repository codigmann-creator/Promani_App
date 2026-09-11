import sqlite3

conexion = sqlite3.connect("promani.db")
cursor = conexion.cursor()


# Tabla de pedidos
cursor.execute("""
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    medidas TEXT,
    estado TEXT NOT NULL,
    observaciones TEXT
)
""")


# Tabla de materiales
cursor.execute("""
CREATE TABLE IF NOT EXISTS materiales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    unidad TEXT NOT NULL,
    stock REAL NOT NULL DEFAULT 0,
    stock_minimo REAL NOT NULL DEFAULT 0
)
""")


# Tabla de consumos
cursor.execute("""
CREATE TABLE IF NOT EXISTS consumos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    cantidad REAL NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
    FOREIGN KEY (material_id) REFERENCES materiales(id)
)
""")


# Tabla de proveedores
cursor.execute("""
CREATE TABLE IF NOT EXISTS proveedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    telefono TEXT,
    correo TEXT
)
""")


# Tabla de compras
cursor.execute("""
CREATE TABLE IF NOT EXISTS compras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proveedor_id INTEGER NOT NULL,
    material_id INTEGER NOT NULL,
    cantidad REAL NOT NULL,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    observaciones TEXT,

    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
    FOREIGN KEY (material_id) REFERENCES materiales(id)
)
""")


conexion.commit()
conexion.close()

print("Base de datos y tablas creadas correctamente.")