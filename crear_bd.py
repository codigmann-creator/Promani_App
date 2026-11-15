import sqlite3


# CREACIÓN Y ACTUALIZACIÓN DE LA BASE DE DATOS

def crear_base_de_datos():
    conexion = sqlite3.connect('promani.db')
    try:
        conexion.executescript('''
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                medidas TEXT,
                estado TEXT NOT NULL,
                observaciones TEXT,
                fecha_entrega TEXT
            );

            CREATE TABLE IF NOT EXISTS materiales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                unidad TEXT NOT NULL,
                stock REAL NOT NULL DEFAULT 0,
                stock_minimo REAL NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS consumos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER NOT NULL,
                material_id INTEGER NOT NULL,
                cantidad REAL NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
                FOREIGN KEY (material_id) REFERENCES materiales(id)
            );

            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT,
                correo TEXT
            );

            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor_id INTEGER NOT NULL,
                material_id INTEGER NOT NULL,
                cantidad REAL NOT NULL,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                observaciones TEXT,
                FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
                FOREIGN KEY (material_id) REFERENCES materiales(id)
            );

            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                contrasena_hash TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'operario'
            );
        ''')

        # Compatibilidad con bases antiguas que no tienen fecha_entrega.
        columnas = {columna[1] for columna in conexion.execute('PRAGMA table_info(pedidos)')}
        if 'fecha_entrega' not in columnas:
            conexion.execute('ALTER TABLE pedidos ADD COLUMN fecha_entrega TEXT')

        conexion.commit()
        print('Base de datos y tablas verificadas correctamente.')
    finally:
        conexion.close()


if __name__ == '__main__':
    crear_base_de_datos()
