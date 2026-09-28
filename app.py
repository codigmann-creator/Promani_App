from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

from datetime import datetime, date

from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)


# --------------------------------------------------
# CLAVE PARA MANEJAR LAS SESIONES
# --------------------------------------------------

app.secret_key = "promani_clave_temporal_2026"


# --------------------------------------------------
# FUNCIÓN PARA CONVERTIR CANTIDADES
# ACEPTA PUNTO O COMA DECIMAL
# --------------------------------------------------

def convertir_decimal(valor):

    if valor is None:
        raise ValueError("Valor vacío")

    valor = valor.strip()

    if not valor:
        raise ValueError("Valor vacío")

    valor = valor.replace(",", ".")

    return float(valor)


# --------------------------------------------------
# VALIDAR FECHA DE ENTREGA
# --------------------------------------------------

def validar_fecha(fecha_entrega):

    if not fecha_entrega:
        return True

    try:

        datetime.strptime(
            fecha_entrega,
            "%Y-%m-%d"
        )

        return True

    except ValueError:

        return False


# --------------------------------------------------
# PROTECCIÓN DEL SISTEMA
# --------------------------------------------------

@app.before_request
def proteger_sistema():

    rutas_publicas = [
        "login",
        "static"
    ]

    rutas_administrador = [
        "proveedores",
        "nuevo_proveedor",
        "nueva_compra",
        "compras",
        "usuarios",
        "nuevo_usuario",
        "editar_usuario",
        "eliminar_usuario",
        "restablecer_contrasena"
    ]

    if request.endpoint not in rutas_publicas:

        if "usuario_id" not in session:
            return redirect(url_for("login"))

    if request.endpoint in rutas_administrador:

        if session.get("rol") != "administrador":
            return redirect(url_for("inicio"))


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if "usuario_id" in session:
        return redirect(url_for("inicio"))

    if request.method == "POST":

        usuario = request.form["usuario"].strip()
        contrasena = request.form["contrasena"]

        conexion = sqlite3.connect("promani.db")
        conexion.row_factory = sqlite3.Row

        usuario_registrado = conexion.execute("""
            SELECT *
            FROM usuarios
            WHERE usuario = ?
        """, (usuario,)).fetchone()

        conexion.close()

        if usuario_registrado is not None:

            if check_password_hash(
                usuario_registrado["contrasena_hash"],
                contrasena
            ):

                session["usuario_id"] = usuario_registrado["id"]
                session["usuario"] = usuario_registrado["usuario"]
                session["rol"] = usuario_registrado["rol"]

                return redirect(url_for("inicio"))

        return "Usuario o contraseña incorrectos."

    return render_template("login.html")


# --------------------------------------------------
# CERRAR SESIÓN
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# --------------------------------------------------
# CAMBIAR MI CONTRASEÑA
# --------------------------------------------------

@app.route("/cambiar-contrasena", methods=["GET", "POST"])
def cambiar_contrasena():

    error = None

    if request.method == "POST":

        contrasena_actual = request.form["contrasena_actual"]
        nueva_contrasena = request.form["nueva_contrasena"]
        confirmar_contrasena = request.form["confirmar_contrasena"]

        if not contrasena_actual:

            error = "Debes ingresar tu contraseña actual."

        elif not nueva_contrasena:

            error = "Debes ingresar una nueva contraseña."

        elif len(nueva_contrasena) < 6:

            error = "La nueva contraseña debe tener al menos 6 caracteres."

        elif nueva_contrasena != confirmar_contrasena:

            error = "Las nuevas contraseñas no coinciden."

        else:

            conexion = sqlite3.connect("promani.db")
            conexion.row_factory = sqlite3.Row
            cursor = conexion.cursor()

            usuario = cursor.execute("""
                SELECT *
                FROM usuarios
                WHERE id = ?
            """, (
                session["usuario_id"],
            )).fetchone()

            if usuario is None:

                conexion.close()
                session.clear()

                return redirect(url_for("login"))

            if not check_password_hash(
                usuario["contrasena_hash"],
                contrasena_actual
            ):

                conexion.close()

                error = "La contraseña actual es incorrecta."

            else:

                nueva_hash = generate_password_hash(
                    nueva_contrasena
                )

                cursor.execute("""
                    UPDATE usuarios
                    SET contrasena_hash = ?
                    WHERE id = ?
                """, (
                    nueva_hash,
                    session["usuario_id"]
                ))

                conexion.commit()
                conexion.close()

                return redirect(
                    url_for(
                        "cambiar_contrasena",
                        exito="1"
                    )
                )

    return render_template(
        "cambiar_contrasena.html",
        error=error
    )


# --------------------------------------------------
# INICIO
# --------------------------------------------------

@app.route("/")
def inicio():

    conexion = sqlite3.connect("promani.db")

    pendientes = conexion.execute("""
        SELECT COUNT(*)
        FROM pedidos
        WHERE estado = 'Pendiente'
    """).fetchone()[0]

    en_produccion = conexion.execute("""
        SELECT COUNT(*)
        FROM pedidos
        WHERE estado = 'En producción'
    """).fetchone()[0]

    terminados = conexion.execute("""
        SELECT COUNT(*)
        FROM pedidos
        WHERE estado = 'Terminado'
    """).fetchone()[0]

    stock_bajo = conexion.execute("""
        SELECT COUNT(*)
        FROM materiales
        WHERE stock <= stock_minimo
    """).fetchone()[0]

    fecha_actual = date.today().isoformat()

    atrasados = conexion.execute("""
        SELECT COUNT(*)
        FROM pedidos
        WHERE fecha_entrega IS NOT NULL
        AND fecha_entrega != ''
        AND fecha_entrega < ?
        AND estado NOT IN ('Terminado', 'Entregado')
    """, (
        fecha_actual,
    )).fetchone()[0]

    conexion.close()

    return render_template(
        "inicio.html",
        pendientes=pendientes,
        en_produccion=en_produccion,
        terminados=terminados,
        stock_bajo=stock_bajo,
        atrasados=atrasados
    )


# --------------------------------------------------
# PEDIDOS
# --------------------------------------------------

@app.route("/pedidos")
def pedidos():

    conexion = sqlite3.connect("promani.db")
    conexion.row_factory = sqlite3.Row

    pedidos_registrados = conexion.execute("""
        SELECT *
        FROM pedidos
        ORDER BY id DESC
    """).fetchall()

    conexion.close()

    fecha_actual = date.today().isoformat()

    return render_template(
        "pedidos.html",
        pedidos=pedidos_registrados,
        hoy=fecha_actual
    )


# --------------------------------------------------
# NUEVO PEDIDO
# --------------------------------------------------

@app.route("/nuevo-pedido", methods=["GET", "POST"])
def nuevo_pedido():

    if request.method == "POST":

        cliente = request.form["cliente"].strip()
        descripcion = request.form["descripcion"].strip()
        medidas = request.form["medidas"].strip()
        estado = request.form["estado"]
        observaciones = request.form["observaciones"].strip()

        fecha_entrega = request.form.get(
            "fecha_entrega",
            ""
        ).strip()

        if not validar_fecha(fecha_entrega):

            return "La fecha de entrega ingresada no es válida."

        conexion = sqlite3.connect("promani.db")
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO pedidos (
                cliente,
                descripcion,
                medidas,
                estado,
                observaciones,
                fecha_entrega
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            cliente,
            descripcion,
            medidas,
            estado,
            observaciones,
            fecha_entrega
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("pedidos"))

    return render_template("nuevo_pedido.html")


# --------------------------------------------------
# EDITAR PEDIDO
# --------------------------------------------------

@app.route(
    "/editar-pedido/<int:pedido_id>",
    methods=["GET", "POST"]
)
def editar_pedido(pedido_id):

    conexion = sqlite3.connect("promani.db")
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    pedido = cursor.execute("""
        SELECT *
        FROM pedidos
        WHERE id = ?
    """, (
        pedido_id,
    )).fetchone()

    if pedido is None:

        conexion.close()

        return "El pedido no existe."

    if request.method == "POST":

        estado = request.form["estado"]

        fecha_entrega = request.form.get(
            "fecha_entrega",
            pedido["fecha_entrega"] or ""
        ).strip()

        medidas = request.form.get(
            "medidas",
            pedido["medidas"] or ""
        ).strip()

        if not validar_fecha(fecha_entrega):

            conexion.close()

            return "La fecha de entrega ingresada no es válida."

        cursor.execute("""
            UPDATE pedidos
            SET estado = ?,
                fecha_entrega = ?,
                medidas = ?
            WHERE id = ?
        """, (
            estado,
            fecha_entrega,
            medidas,
            pedido_id
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("pedidos"))

    conexion.close()

    return render_template(
        "editar_pedido.html",
        pedido=pedido
    )


# --------------------------------------------------
# INVENTARIO
# --------------------------------------------------

@app.route("/inventario")
def inventario():

    conexion = sqlite3.connect("promani.db")
    conexion.row_factory = sqlite3.Row

    materiales_registrados = conexion.execute("""
        SELECT *
        FROM materiales
        ORDER BY id DESC
    """).fetchall()

    conexion.close()

    return render_template(
        "inventario.html",
        materiales=materiales_registrados
    )


# --------------------------------------------------
# NUEVO MATERIAL
# --------------------------------------------------

@app.route("/nuevo-material", methods=["GET", "POST"])
def nuevo_material():

    if request.method == "POST":

        nombre = request.form["nombre"].strip()
        unidad = request.form["unidad"].strip()

        try:

            stock = convertir_decimal(
                request.form["stock"]
            )

            stock_minimo = convertir_decimal(
                request.form["stock_minimo"]
            )

        except ValueError:

            return (
                "El stock y el stock mínimo "
                "deben ser valores numéricos."
            )

        if stock < 0:

            return "El stock inicial no puede ser negativo."

        if stock_minimo < 0:

            return "El stock mínimo no puede ser negativo."

        conexion = sqlite3.connect("promani.db")
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO materiales (
                nombre,
                unidad,
                stock,
                stock_minimo
            )
            VALUES (?, ?, ?, ?)
        """, (
            nombre,
            unidad,
            stock,
            stock_minimo
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("inventario"))

    return render_template("nuevo_material.html")


# --------------------------------------------------
# NUEVO CONSUMO
# --------------------------------------------------

@app.route("/nuevo-consumo", methods=["GET", "POST"])
def nuevo_consumo():

    conexion = sqlite3.connect("promani.db")
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    if request.method == "POST":

        pedido_id = request.form["pedido_id"]
        material_id = request.form["material_id"]

        try:

            cantidad = convertir_decimal(
                request.form["cantidad"]
            )

        except ValueError:

            conexion.close()

            return "La cantidad ingresada no es válida."

        material = cursor.execute("""
            SELECT *
            FROM materiales
            WHERE id = ?
        """, (
            material_id,
        )).fetchone()

        if material is None:

            conexion.close()

            return "El material seleccionado no existe."

        if cantidad <= 0:

            conexion.close()

            return "La cantidad debe ser mayor que 0."

        if cantidad > material["stock"]:

            conexion.close()

            return (
                "No existe stock suficiente "
                "para registrar este consumo."
            )

        cursor.execute("""
            INSERT INTO consumos (
                pedido_id,
                material_id,
                cantidad
            )
            VALUES (?, ?, ?)
        """, (
            pedido_id,
            material_id,
            cantidad
        ))

        cursor.execute("""
            UPDATE materiales
            SET stock = stock - ?
            WHERE id = ?
        """, (
            cantidad,
            material_id
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("inventario"))

    pedidos_registrados = cursor.execute("""
        SELECT
            id,
            cliente,
            descripcion
        FROM pedidos
        ORDER BY id DESC
    """).fetchall()

    materiales_registrados = cursor.execute("""
        SELECT
            id,
            nombre,
            unidad,
            stock
        FROM materiales
        ORDER BY nombre
    """).fetchall()

    conexion.close()

    return render_template(
        "nuevo_consumo.html",
        pedidos=pedidos_registrados,
        materiales=materiales_registrados
    )


# --------------------------------------------------
# HISTORIAL DE CONSUMOS
# --------------------------------------------------

@app.route("/consumos")
def consumos():

    conexion = sqlite3.connect("promani.db")
    conexion.row_factory = sqlite3.Row

    consumos_registrados = conexion.execute("""
        SELECT
            c.id,
            c.pedido_id,
            p.cliente,
            p.descripcion,
            m.nombre AS material,
            m.unidad,
            c.cantidad,
            c.fecha

        FROM consumos c

        INNER JOIN pedidos p
        ON c.pedido_id = p.id

        INNER JOIN materiales m
        ON c.material_id = m.id

        ORDER BY c.id DESC
    """).fetchall()

    conexion.close()

    return render_template(
        "consumos.html",
        consumos=consumos_registrados
    )


# --------------------------------------------------
# PROVEEDORES
# SOLO ADMINISTRADOR
# --------------------------------------------------

@app.route("/proveedores")
def proveedores():

    conexion = sqlite3.connect("promani.db")
    conexion.row_factory = sqlite3.Row

    proveedores_registrados = conexion.execute("""
        SELECT *
        FROM proveedores
        ORDER BY id DESC
    """).fetchall()

    conexion.close()

    return render_template(
        "proveedores.html",
        proveedores=proveedores_registrados
    )


# --------------------------------------------------
# NUEVO PROVEEDOR
# SOLO ADMINISTRADOR
# --------------------------------------------------

@app.route(
    "/nuevo-proveedor",
    methods=["GET", "POST"]
)
def nuevo_proveedor():

    if request.method == "POST":

        nombre = request.form["nombre"]
        telefono = request.form["telefono"]
        correo = request.form["correo"]

        conexion = sqlite3.connect("promani.db")
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO proveedores (
                nombre,
                telefono,
                correo
            )
            VALUES (?, ?, ?)
        """, (
            nombre,
            telefono,
            correo
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("proveedores"))

    return render_template("nuevo_proveedor.html")


# --------------------------------------------------
# NUEVA COMPRA
# SOLO ADMINISTRADOR
# --------------------------------------------------

@app.route("/nueva-compra", methods=["GET", "POST"])
def nueva_compra():

    conexion = sqlite3.connect("promani.db")
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    if request.method == "POST":

        proveedor_id = request.form["proveedor_id"]
        material_id = request.form["material_id"]
        observaciones = request.form["observaciones"]

        try:

            cantidad = convertir_decimal(
                request.form["cantidad"]
            )

        except ValueError:

            conexion.close()

            return "La cantidad ingresada no es válida."

        fecha_compra = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        if cantidad <= 0:

            conexion.close()

            return "La cantidad debe ser mayor que 0."

        proveedor = cursor.execute("""
            SELECT *
            FROM proveedores
            WHERE id = ?
        """, (
            proveedor_id,
        )).fetchone()

        if proveedor is None:

            conexion.close()

            return "El proveedor seleccionado no existe."

        material = cursor.execute("""
            SELECT *
            FROM materiales
            WHERE id = ?
        """, (
            material_id,
        )).fetchone()

        if material is None:

            conexion.close()

            return "El material seleccionado no existe."

        cursor.execute("""
            INSERT INTO compras (
                proveedor_id,
                material_id,
                cantidad,
                fecha,
                observaciones
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            proveedor_id,
            material_id,
            cantidad,
            fecha_compra,
            observaciones
        ))

        cursor.execute("""
            UPDATE materiales
            SET stock = stock + ?
            WHERE id = ?
        """, (
            cantidad,
            material_id
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("inventario"))

    proveedores_registrados = cursor.execute("""
        SELECT
            id,
            nombre
        FROM proveedores
        ORDER BY nombre
    """).fetchall()

    materiales_registrados = cursor.execute("""
        SELECT
            id,
            nombre,
            unidad,
            stock
        FROM materiales
        ORDER BY nombre
    """).fetchall()

    conexion.close()

    return render_template(
        "nueva_compra.html",
        proveedores=proveedores_registrados,
        materiales=materiales_registrados
    )


# --------------------------------------------------
# HISTORIAL DE COMPRAS
# SOLO ADMINISTRADOR
# --------------------------------------------------

@app.route("/compras")
def compras():

    conexion = sqlite3.connect("promani.db")
    conexion.row_factory = sqlite3.Row

    compras_registradas = conexion.execute("""
        SELECT
            c.id,
            p.nombre AS proveedor,
            m.nombre AS material,
            m.unidad,
            c.cantidad,
            c.fecha,
            c.observaciones

        FROM compras c

        INNER JOIN proveedores p
        ON c.proveedor_id = p.id

        INNER JOIN materiales m
        ON c.material_id = m.id

        ORDER BY c.id DESC
    """).fetchall()

    conexion.close()

    return render_template(
        "historial_de_compras.html",
        compras=compras_registradas
    )


# --------------------------------------------------
# GESTIÓN DE USUARIOS
# SOLO ADMINISTRADOR
# --------------------------------------------------

@app.route("/usuarios")
def usuarios():

    conexion = sqlite3.connect("promani.db")
    conexion.row_factory = sqlite3.Row

    usuarios_registrados = conexion.execute("""
        SELECT
            id,
            usuario,
            rol
        FROM usuarios
        ORDER BY id ASC
    """).fetchall()

    conexion.close()

    return render_template(
        "usuarios.html",
        usuarios=usuarios_registrados
    )


# --------------------------------------------------
# NUEVO USUARIO
# SOLO ADMINISTRADOR
# --------------------------------------------------

@app.route("/nuevo-usuario", methods=["GET", "POST"])
def nuevo_usuario():

    if request.method == "POST":

        usuario = request.form["usuario"].strip()
        contrasena = request.form["contrasena"]
        rol = request.form["rol"]

        if not usuario:

            return "El nombre de usuario no puede estar vacío."

        if not contrasena:

            return "La contraseña no puede estar vacía."

        if len(contrasena) < 6:

            return "La contraseña debe tener al menos 6 caracteres."

        if rol not in [
            "administrador",
            "operario"
        ]:

            return "El rol seleccionado no es válido."

        contrasena_hash = generate_password_hash(
            contrasena
        )

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

        except sqlite3.IntegrityError:

            conexion.close()

            return "Ese nombre de usuario ya existe."

        conexion.close()

        return redirect(url_for("usuarios"))

    return render_template("nuevo_usuario.html")


# --------------------------------------------------
# EDITAR USUARIO
# SOLO ADMINISTRADOR
# --------------------------------------------------

@app.route(
    "/editar-usuario/<int:usuario_id>",
    methods=["GET", "POST"]
)
def editar_usuario(usuario_id):

    conexion = sqlite3.connect("promani.db")
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    usuario_registrado = cursor.execute("""
        SELECT
            id,
            usuario,
            rol
        FROM usuarios
        WHERE id = ?
    """, (
        usuario_id,
    )).fetchone()

    if usuario_registrado is None:

        conexion.close()

        return "El usuario no existe."

    if usuario_id == session.get("usuario_id"):

        conexion.close()

        return redirect(url_for("usuarios"))

    if request.method == "POST":

        rol = request.form["rol"]

        if rol not in [
            "administrador",
            "operario"
        ]:

            conexion.close()

            return "El rol seleccionado no es válido."

        cursor.execute("""
            UPDATE usuarios
            SET rol = ?
            WHERE id = ?
        """, (
            rol,
            usuario_id
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("usuarios"))

    conexion.close()

    return render_template(
        "editar_usuario.html",
        usuario=usuario_registrado
    )


# --------------------------------------------------
# RESTABLECER CONTRASEÑA
# SOLO ADMINISTRADOR
# --------------------------------------------------

@app.route(
    "/restablecer-contrasena/<int:usuario_id>",
    methods=["GET", "POST"]
)
def restablecer_contrasena(usuario_id):

    conexion = sqlite3.connect("promani.db")
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    usuario_registrado = cursor.execute("""
        SELECT
            id,
            usuario,
            rol
        FROM usuarios
        WHERE id = ?
    """, (
        usuario_id,
    )).fetchone()

    if usuario_registrado is None:

        conexion.close()

        return "El usuario no existe."

    if usuario_id == session.get("usuario_id"):

        conexion.close()

        return redirect(url_for("usuarios"))

    error = None

    if request.method == "POST":

        nueva_contrasena = request.form[
            "nueva_contrasena"
        ]

        confirmar_contrasena = request.form[
            "confirmar_contrasena"
        ]

        if not nueva_contrasena:

            error = "Debes ingresar una nueva contraseña."

        elif len(nueva_contrasena) < 6:

            error = (
                "La nueva contraseña debe tener "
                "al menos 6 caracteres."
            )

        elif nueva_contrasena != confirmar_contrasena:

            error = "Las contraseñas no coinciden."

        else:

            nueva_hash = generate_password_hash(
                nueva_contrasena
            )

            cursor.execute("""
                UPDATE usuarios
                SET contrasena_hash = ?
                WHERE id = ?
            """, (
                nueva_hash,
                usuario_id
            ))

            conexion.commit()
            conexion.close()

            return redirect(
                url_for(
                    "usuarios",
                    restablecido="1"
                )
            )

    conexion.close()

    return render_template(
        "restablecer_contrasena.html",
        usuario=usuario_registrado,
        error=error
    )


# --------------------------------------------------
# ELIMINAR USUARIO
# SOLO ADMINISTRADOR
# --------------------------------------------------

@app.route(
    "/eliminar-usuario/<int:usuario_id>",
    methods=["GET", "POST"]
)
def eliminar_usuario(usuario_id):

    conexion = sqlite3.connect("promani.db")
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    usuario_registrado = cursor.execute("""
        SELECT
            id,
            usuario,
            rol
        FROM usuarios
        WHERE id = ?
    """, (
        usuario_id,
    )).fetchone()

    if usuario_registrado is None:

        conexion.close()

        return "El usuario no existe."

    if usuario_id == session.get("usuario_id"):

        conexion.close()

        return redirect(url_for("usuarios"))

    if usuario_registrado["rol"] == "administrador":

        cantidad_administradores = cursor.execute("""
            SELECT COUNT(*)
            FROM usuarios
            WHERE rol = 'administrador'
        """).fetchone()[0]

        if cantidad_administradores <= 1:

            conexion.close()

            return (
                "No se puede eliminar al último "
                "administrador del sistema."
            )

    if request.method == "POST":

        cursor.execute("""
            DELETE FROM usuarios
            WHERE id = ?
        """, (
            usuario_id,
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("usuarios"))

    conexion.close()

    return render_template(
        "eliminar_usuario.html",
        usuario=usuario_registrado
    )


# --------------------------------------------------
# EJECUTAR APLICACIÓN
# --------------------------------------------------

if __name__ == "__main__":

    app.run(debug=True)