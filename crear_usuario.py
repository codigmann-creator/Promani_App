import sqlite3
from getpass import getpass
from werkzeug.security import generate_password_hash


usuario = input("Nombre de usuario: ").strip()
contrasena = getpass("Contraseña: ").strip()

print("")
print("Roles disponibles:")
print("1 - Administrador")
print("2 - Operario")

opcion_rol = input("Seleccione el rol (1 o 2): ").strip()


if not usuario:
    print("El nombre de usuario no puede estar vacío.")
    exit()


if not contrasena:
    print("La contraseña no puede estar vacía.")
    exit()


if opcion_rol == "1":
    rol = "administrador"

elif opcion_rol == "2":
    rol = "operario"

else:
    print("Rol no válido.")
    exit()


contrasena_hash = generate_password_hash(contrasena)


conexion = sqlite3.connect("promani.db")
cursor = conexion.cursor()


try:

    cursor.execute("""
        INSERT INTO usuarios (
            usuario,
            contrasena_hash,
            rol
        )
        VALUES (?, ?, ?)
    """, (
        usuario,
        contrasena_hash,
        rol
    ))

    conexion.commit()

    print("")
    print("Usuario creado correctamente.")
    print("Usuario:", usuario)
    print("Rol:", rol)


except sqlite3.IntegrityError:

    print("Ese nombre de usuario ya existe.")


finally:

    conexion.close()