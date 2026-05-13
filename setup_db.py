"""Ejecuta schema.sql directamente vía PyMySQL — no requiere mysql CLI."""
import pymysql
import os

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')

HOST = 'localhost'
USER = 'root'
PASSWORD = '1234'
DB = 'ferramas'

with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
    sql = f.read()

try:
    conn = pymysql.connect(host=HOST, user=USER, password=PASSWORD, database=DB)
    cursor = conn.cursor()
    # Ejecutar cada statement por separado (separados por ;)
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    for stmt in statements:
        try:
            cursor.execute(stmt)
            print(f'OK: {stmt.split()[0]} {stmt.split()[1]} ...')
        except pymysql.err.OperationalError as e:
            if 'already exists' in str(e).lower() or e.args[0] == 1050:
                print(f'SKIP (ya existe): {stmt.split()[1]} {stmt.split()[2] if len(stmt.split()) > 2 else ""}')
            else:
                print(f'ERROR: {str(e)[:100]}')
    conn.commit()
    cursor.close()
    conn.close()
    print('\nSchema ejecutado correctamente.')
except pymysql.err.OperationalError as e:
    print(f'ERROR de conexión: {e}')
    print('Asegúrate de que MariaDB esté corriendo en localhost:3306 con la BD "ferramas".')
