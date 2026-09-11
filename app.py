from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)


@app.route("/")
def inicio():

    conexion = sqlite3.connect("promani.db")

    pendientes = conexion.execute("""
        SELECT COUNT(*) FROM pedidos
        WHERE estado = 'Pendiente'
    """).fetchone()[0]

    en_produccion = conexion.execute("""
        SELECT COUNT(*) FROM pedidos
        WHERE estado = 'En producción'
    """).fetchone()[0]

    terminados = conexion.execute("""
        SELECT COUNT(*) FROM pedidos
        WHERE estado = 'Terminado'
    """).fetchone()[0]

    stock_bajo = conexion.execute("""
        SELECT COUNT(*) FROM materiales
        WHERE stock <= stock_minimo
    """).fetchone()[0]

    conexion.close()

    return render_template(
        "inicio.html",
        pendientes=pendientes,
        en_produccion=en_produccion,
        terminados=terminados,
        stock_bajo=stock_bajo
    )


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

    return render_template(
        "pedidos.html",
        pedidos=pedidos_registrados
    )


@app.route("/nuevo-pedido", methods=["GET", "POST"])
def nuevo_pedido():

    if request.method == "POST":

        cliente = request.form["cliente"]
        descripcion = request.form["descripcion"]
        medidas = request.form["medidas"]
        estado = request.form["estado"]
        observaciones = request.form["observaciones"]

        conexion = sqlite3.connect("promani.db")
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO pedidos (
                cliente,
                descripcion,
                medidas,
                estado,
                observaciones
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            cliente,
            descripcion,
            medidas,
            estado,
            observaciones
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("pedidos"))

    return render_template("nuevo_pedido.html")


@app.route("/editar-pedido/<int:pedido_id>", methods=["GET", "POST"])
def editar_pedido(pedido_id):

    conexion = sqlite3.connect("promani.db")
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    pedido = cursor.execute("""
        SELECT *
        FROM pedidos
        WHERE id = ?
    """, (pedido_id,)).fetchone()

    if pedido is None:
        conexion.close()
        return "El pedido no existe."

    if request.method == "POST":

        estado = request.form["estado"]

        cursor.execute("""
            UPDATE pedidos
            SET estado = ?
            WHERE id = ?
        """, (
            estado,
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


@app.route("/nuevo-material", methods=["GET", "POST"])
def nuevo_material():

    if request.method == "POST":

        nombre = request.form["nombre"]
        unidad = request.form["unidad"]
        stock = request.form["stock"]
        stock_minimo = request.form["stock_minimo"]

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


@app.route("/nuevo-consumo", methods=["GET", "POST"])
def nuevo_consumo():

    conexion = sqlite3.connect("promani.db")
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()

    if request.method == "POST":

        pedido_id = request.form["pedido_id"]
        material_id = request.form["material_id"]
        cantidad = float(request.form["cantidad"])

        material = cursor.execute("""
            SELECT *
            FROM materiales
            WHERE id = ?
        """, (material_id,)).fetchone()

        if material is None:
            conexion.close()
            return "El material seleccionado no existe."

        if cantidad <= 0:
            conexion.close()
            return "La cantidad debe ser mayor que 0."

        if cantidad > material["stock"]:
            conexion.close()
            return "No existe stock suficiente para registrar este consumo."

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
        SELECT id, cliente, descripcion
        FROM pedidos
        ORDER BY id DESC
    """).fetchall()

    materiales_registrados = cursor.execute("""
        SELECT id, nombre, unidad, stock
        FROM materiales
        ORDER BY nombre
    """).fetchall()

    conexion.close()

    return render_template(
        "nuevo_consumo.html",
        pedidos=pedidos_registrados,
        materiales=materiales_registrados
    )


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


@app.route("/nuevo-proveedor", methods=["GET", "POST"])
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


if __name__ == "__main__":
    app.run(debug=True)