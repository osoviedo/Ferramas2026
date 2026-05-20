"""
Script para probar el flujo de pago y verificar que el error NameError se ha corregido.
"""
import requests
import json

BASE_URL = 'http://127.0.0.1:5000'

# 1. Login (usuario ya existe en seed data)
login_data = {
    'email': 'cliente@ferramas.cl',
    'password': 'cliente123'
}
session = requests.Session()
r = session.post(f'{BASE_URL}/login', data=login_data)
print(f"Login: {r.status_code}")
if r.status_code != 200 and r.status_code != 302:
    print(f"  Error: {r.text[:500]}")

# 2. Agregar producto al carrito
carrito_data = {'producto_id': 1, 'cantidad': 1}
r = session.post(f'{BASE_URL}/carrito/agregar', json=carrito_data)
print(f"Agregar carrito: {r.status_code}")
if r.status_code != 200:
    print(f"  Error: {r.text[:500]}")

# 3. Crear checkout (crear pedido)
checkout_data = {
    'nombre_retiro': 'Test User',
    'email_retiro': 'test@test.com',
    'opcion_entrega': 'retiro'
}
r = session.post(f'{BASE_URL}/carrito/checkout', data=checkout_data)
print(f"Checkout: {r.status_code}")
if r.status_code in [302, 303]:  # Redirección a pago
    location = r.headers.get('location', '')
    print(f"  Redirected to: {location}")
    pedido_id = location.split('/')[-1]  # Extraer pedido_id de URL
    
    # 4. Intentar iniciar pago (aquí es donde ocurría el error)
    r = session.get(f'{BASE_URL}/pago/iniciar/{pedido_id}')
    print(f"Pago iniciar: {r.status_code}")
    if r.status_code == 200:
        print("  ✓ Pago iniciado exitosamente (sin NameError)")
    elif r.status_code == 500:
        print(f"  Error 500: {r.text[:1000]}")
    else:
        print(f"  Respuesta: {r.text[:500]}")
else:
    print(f"  Error: {r.text[:500]}")
    print(f"  Status: {r.status_code}")
