import sqlite3
from getpass import getpass
from werkzeug.security import generate_password_hash


# CREAR USUARIO DESDE LA TERMINAL

def crear_usuario():
    usuario = input("Nombre de usuario: ").strip()
    contrasena = getpass("Contraseña: ")
    print("\nRoles disponibles: 1 - Administrador | 2 - Operario")
    rol = {"1": "administrador", "2": "operario"}.get(
        input("Seleccione el rol (1 o 2): ").strip()
    )

    if not usuario:
        print("El nombre de usuario no puede estar vacío.")
        return
    if not contrasena:
        print("La contraseña no puede estar vacía.")
        return
    if rol is None:
        print("Rol no válido.")
        return

    conexion = sqlite3.connect("promani.db")
    try:
        conexion.execute(
            "INSERT INTO usuarios (usuario, contrasena_hash, rol) VALUES (?, ?, ?)",
            (usuario, generate_password_hash(contrasena), rol)
        )
        conexion.commit()
        print(f"\nUsuario creado correctamente.\nUsuario: {usuario}\nRol: {rol}")
    except sqlite3.IntegrityError:
        print("No se pudo crear el usuario: el nombre ya existe o hay datos no válidos.")
    finally:
        conexion.close()


if __name__ == "__main__":
    crear_usuario()
