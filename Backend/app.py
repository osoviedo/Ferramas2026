from flask import Flask, jsonify
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app)

# CONEXION MARIADB
conexion = pymysql.connect(
    host="localhost",
    user="root",
    password="1234",
    database="ferramas"
)

@app.route("/")
def inicio():
    return "Ferramas API funcionando"

@app.route("/productos")
def productos():

    cursor = conexion.cursor()

    sql = "SELECT * FROM productos"
    cursor.execute(sql)

    resultados = cursor.fetchall()

    productos_lista = []

    for fila in resultados:
        producto = {
            "id": fila[0],
            "nombre": fila[1],
            "precio": fila[2],
            "stock": fila[3]
        }

        productos_lista.append(producto)

    return jsonify(productos_lista)

if __name__ == "__main__":
    app.run(debug=True)