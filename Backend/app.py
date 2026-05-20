from flask import Flask, jsonify
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app)

# ── CONEXION MARIADB ──
def get_conexion():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="1234",
        database="ferramas"
    )

# ── RUTA PRINCIPAL ──
@app.route("/")
def inicio():
    return "Ferramas API funcionando"

# ── TODOS LOS PRODUCTOS ──
@app.route("/productos")
def productos():
    conexion = get_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM productos")
    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    productos_lista = []
    for fila in resultados:
        producto = {
            "id":        fila[0],
            "nombre":    fila[1],
            "precio":    fila[2],
            "stock":     fila[3],
            "categoria": fila[4],
            "imagen":    fila[5]
        }
        productos_lista.append(producto)

    return jsonify(productos_lista)

# ── PRODUCTOS POR CATEGORÍA ──
@app.route("/productos/categoria/<nombre_categoria>")
def productos_por_categoria(nombre_categoria):
    conexion = get_conexion()
    cursor = conexion.cursor()

    categoria_buscar = nombre_categoria.replace("-", " ")

    sql = "SELECT * FROM productos WHERE LOWER(categoria) = LOWER(%s)"
    cursor.execute(sql, (categoria_buscar,))
    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    if not resultados:
        return jsonify({"error": "Categoría no encontrada"}), 404

    productos_lista = []
    for fila in resultados:
        producto = {
            "id":        fila[0],
            "nombre":    fila[1],
            "precio":    fila[2],
            "stock":     fila[3],
            "categoria": fila[4],
            "imagen":    fila[5]
        }
        productos_lista.append(producto)

    return jsonify(productos_lista)

# ── CATEGORÍAS DISPONIBLES ──
@app.route("/categorias")
def categorias():
    conexion = get_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT DISTINCT categoria FROM productos ORDER BY categoria")
    resultados = cursor.fetchall()

    cursor.close()
    conexion.close()

    lista = [fila[0] for fila in resultados]
    return jsonify(lista)

if __name__ == "__main__":
    app.run(debug=True)