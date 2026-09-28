import sqlite3


# --------------------------------------------------
# ACTUALIZACIÓN DE LA BASE DE DATOS
# Agrega fecha_entrega a la tabla pedidos
# --------------------------------------------------

conexion = sqlite3.connect("promani.db")

cursor = conexion.cursor()


# Obtener las columnas actuales de la tabla pedidos
columnas = cursor.execute("""
    PRAGMA table_info(pedidos)
""").fetchall()


nombres_columnas = [
    columna[1]
    for columna in columnas
]


# Verificar si fecha_entrega ya existe
if "fecha_entrega" not in nombres_columnas:

    cursor.execute("""
        ALTER TABLE pedidos
        ADD COLUMN fecha_entrega TEXT
    """)

    conexion.commit()

    print("Columna fecha_entrega agregada correctamente.")

else:

    print("La columna fecha_entrega ya existe.")


conexion.close()