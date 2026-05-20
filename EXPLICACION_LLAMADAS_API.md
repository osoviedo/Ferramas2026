# ¿Desde Dónde Se Llama a la URL de la API?

## 1. REGISTRO DE RUTAS (Dónde se definen)

### Paso 1: Crear Blueprint con Rutas
```python
# app/api/producto_api.py

from flask import Blueprint, jsonify, request
from app.models.producto import Producto

# ← CREAR Blueprint
api_bp = Blueprint('api', __name__)

# ← DEFINIR ruta en el blueprint
@api_bp.route('/api/productos')
def api_productos():
    """GET /api/productos retorna lista de productos"""
    productos = Producto.query.all()
    return jsonify([p.to_dict() for p in productos])

@api_bp.route('/api/categorias')
def api_categorias():
    """GET /api/categorias retorna categorías únicas"""
    categorias = Producto.query.with_entities(
        Producto.categoria
    ).distinct().all()
    lista = [c[0] for c in categorias]
    return jsonify(lista)

@api_bp.route('/api/webhook/mercadopago', methods=['POST'])
def webhook_mercadopago():
    """POST /api/webhook/mercadopago recibe notificaciones"""
    data = request.get_json()
    # ... procesar webhook
    return jsonify({'status': 'received'}), 200
```

**¿Qué pasó?**
- ✓ Se creó un Blueprint `api_bp`
- ✓ Se definieron 3 rutas (`/api/productos`, `/api/categorias`, `/api/webhook/...`)
- ✓ Pero aún **NO están activas en Flask**

---

### Paso 2: Registrar Blueprint en la App
```python
# app/__init__.py

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # ... configuración ...
    
    # ← IMPORTAR blueprint
    from app.api.producto_api import api_bp
    from app.views.auth import auth_bp
    from app.views.tienda import tienda_bp
    from app.views.carrito import carrito_bp
    
    # ← REGISTRAR blueprints (ahora las rutas están ACTIVAS)
    app.register_blueprint(api_bp)      # ✓ Rutas de API disponibles
    app.register_blueprint(auth_bp)     # ✓ Rutas de autenticación
    app.register_blueprint(tienda_bp)   # ✓ Rutas de tienda
    app.register_blueprint(carrito_bp)  # ✓ Rutas de carrito
    
    return app
```

**¿Qué pasó?**
- ✓ Flask **registra** el blueprint
- ✓ **Ahora están disponibles** las rutas:
  - `GET /api/productos`
  - `GET /api/categorias`
  - `POST /api/webhook/mercadopago`

---

## 2. LLAMAR LAS URLS (Desde dónde se usan)

### Opción A: Desde JavaScript/Frontend (HTML Template)

```html
<!-- app/templates/productos.html -->

<script>
// Selector de moneda: al cambiar, se llama a /api/productos con parámetro
document.getElementById("selector-moneda").addEventListener("change", function() {
    let moneda = this.value;
    
    // Construir URL con parámetro
    let url = "{{ url_for('tienda.productos') }}?categoria={{ categoria or '' }}&convertir_a=" + moneda;
    
    // Redirigir (que llama al backend)
    location.href = url;
});

// Agregar al carrito: Fetch POST a /carrito/agregar (no es API pero es similar)
function agregarAlCarrito(id, nombre, precio, btn) {
    let carrito = JSON.parse(localStorage.getItem("carrito")) || [];
    let existe = carrito.find(p => p.id === id);
    
    if (existe) {
        existe.cantidad++;
    } else {
        carrito.push({ id, nombre, precio, cantidad: 1 });
    }
    
    localStorage.setItem("carrito", JSON.stringify(carrito));
    
    // ← LLAMAR API: POST /carrito/agregar
    fetch("{{ url_for('carrito.agregar') }}", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            producto_id: id, 
            cantidad: 1 
        })
    })
    .then(r => r.json())
    .then(data => {
        console.log("✓ Producto agregado:", data.nombre);
    })
    .catch(err => console.error("Error:", err));
}
</script>
```

**Flujo:**
```
Usuario hace click "Cambiar moneda a USD"
    ↓
JavaScript: location.href = "...&convertir_a=USD"
    ↓
Navegador: GET /productos?convertir_a=USD
    ↓
Flask (@tienda_bp.route('/productos')): 
    - Obtiene parámetro ?convertir_a=USD
    - LLAMA A /api/productos internamente (para datos)
    - Renderiza template productos.html con datos convertidos
    ↓
Usuario ve precios en USD
```

---

### Opción B: Desde Python/Backend (Servicios)

```python
# app/services/divisa_service.py

import requests

class DivisaService:
    
    @staticmethod
    def obtener_divisas():
        """Obtiene tasas de cambio desde API externa"""
        
        try:
            # ← LLAMAR API EXTERNA
            response = requests.get('https://mindicador.cl/api/dolar')
            
            # Procesar respuesta
            if response.status_code == 200:
                data = response.json()
                dolar = data['serie'][0]['valor']
                return {'dolar': dolar}
        
        except Exception as e:
            print(f"Error obteniendo divisas: {e}")
            return {'dolar': 1000}  # Valor default
```

**Uso en otra función:**
```python
# app/api/producto_api.py

@api_bp.route('/api/productos')
def api_productos():
    """Convertir precios a otra moneda"""
    
    convert_to = request.args.get('convertir_a', '').upper()
    
    if convert_to == 'USD':
        # ← LLAMAR SERVICIO (que internamente llama API externa)
        ds = DivisaService()
        divisas = ds.obtener_divisas()
        tasa = divisas.get('dolar')
        
        # Convertir cada precio
        for p in productos:
            p.precio = round(p.precio / tasa)
    
    return jsonify(productos)
```

---

### Opción C: Desde Cliente Externo (Postman, curl, aplicaciones móviles)

#### Con curl (línea de comandos)
```bash
# GET /api/productos
curl http://localhost:5000/api/productos

# GET /api/productos?convertir_a=USD
curl "http://localhost:5000/api/productos?convertir_a=USD"

# GET /api/categorias
curl http://localhost:5000/api/categorias

# POST /api/webhook/mercadopago
curl -X POST http://localhost:5000/api/webhook/mercadopago \
  -H "Content-Type: application/json" \
  -d '{"action": "payment.approved", "data": {"id": "123"}}'
```

#### Con Postman (GUI)
1. Crear request GET a `http://localhost:5000/api/productos`
2. Click "Send"
3. Ver respuesta JSON

#### Desde aplicación móvil (Android/iOS)
```java
// Android (Java)
OkHttpClient client = new OkHttpClient();

Request request = new Request.Builder()
    .url("http://localhost:5000/api/productos")
    .build();

client.newCall(request).enqueue(new Callback() {
    @Override
    public void onResponse(Call call, Response response) {
        String json = response.body().string();
        // Parsear JSON
    }
});
```

---

## 3. DIAGRAMA: FLUJO COMPLETO

```
┌──────────────────────────────────────────────────────────────┐
│                    USUARIO EN NAVEGADOR                      │
│                   http://localhost:5000                      │
└──────────────────────────┬───────────────────────────────────┘
                           │
                    (1) Click "USD"
                           │
                           ▼
         ┌─────────────────────────────────────┐
         │   FRONTEND (JavaScript)             │
         │   selector-moneda.addEventListener  │
         │   → location.href = "...?convertir_ │
         │     a=USD"                          │
         └──────────────┬──────────────────────┘
                        │ GET /productos?convertir_a=USD
                        │
                        ▼
    ┌───────────────────────────────────────────────────┐
    │     BACKEND - ROUTE HANDLER                       │
    │     @tienda_bp.route('/productos')                │
    │     def productos():                              │
    │         convert_to = request.args.get('conve     │
    │                      rtir_a')  # = 'USD'         │
    └──────────────┬──────────────────────────┬────────┘
                   │                          │
         (2) Llamar API interna    (3) Obtener divisas
                   │                          │
                   ▼                          ▼
      ┌────────────────────────┐  ┌──────────────────────┐
      │  @api_bp.route         │  │  DivisaService()     │
      │  ('/api/productos')    │  │  → requests.get()    │
      │  → Retorna JSON        │  │  → mindicador.cl API │
      │                        │  │  → dolar: 1000       │
      └────────────┬───────────┘  └─────────┬────────────┘
                   │                        │
                   └────────────┬───────────┘
                                │ Procesar datos
                                │
                                ▼
              ┌─────────────────────────────────┐
              │  Renderizar Template            │
              │  (productos.html con Jinja2)    │
              │  - Productos: [...]             │
              │  - Precios en USD               │
              │  - Categorías: [...]            │
              └──────────────┬──────────────────┘
                             │ HTML generado
                             ▼
              ┌─────────────────────────────────┐
              │  RESPUESTA HTTP 200             │
              │  Content-Type: text/html        │
              │  (página con precios en USD)    │
              └──────────────┬──────────────────┘
                             │
                             ▼
              ┌─────────────────────────────────┐
              │  NAVEGADOR                      │
              │  Renderiza HTML                 │
              │  Usuario ve: $30.000 USD        │
              └─────────────────────────────────┘
```

---

## 4. PUNTOS CLAVE

### ¿Dónde se DEFINEN las rutas?
📍 `app/api/producto_api.py` — Aquí se crean con `@api_bp.route()`

### ¿Dónde se REGISTRAN en Flask?
📍 `app/__init__.py` — Aquí se hace `app.register_blueprint(api_bp)`

### ¿Desde dónde se LLAMAN?
1. **Frontend (JavaScript/HTML):** `fetch()`, `location.href`, selectores
2. **Backend (Python):** Servicios, otras rutas
3. **Cliente externo:** Postman, curl, apps móviles, etc.

### ¿Cómo viaja la solicitud?
```
Cliente
  ↓ HTTP REQUEST (GET /api/productos)
Servidor Flask
  ↓ Busca ruta en blueprints registrados
Encuentra @api_bp.route('/api/productos')
  ↓ Ejecuta función: api_productos()
  ↓ Consulta BD (Producto.query.all())
  ↓ Convierte a JSON (jsonify())
  ↓ HTTP RESPONSE 200 OK + JSON
Cliente recibe datos
  ↓ JavaScript procesa/renderiza
Usuario ve resultado
```

---

## 5. EJEMPLO PRÁCTICO: Agregar al Carrito

### 1️⃣ Usuario hace click "Agregar al carrito"
```html
<button onclick="agregarAlCarrito(1, 'Martillo', 8500, this)">
  Agregar al carrito
</button>
```

### 2️⃣ JavaScript ejecuta función
```javascript
function agregarAlCarrito(id, nombre, precio, btn) {
    // Guardar en localStorage (cliente)
    let carrito = JSON.parse(localStorage.getItem("carrito")) || [];
    carrito.push({ id, nombre, precio, cantidad: 1 });
    localStorage.setItem("carrito", JSON.stringify(carrito));
    
    // LLAMAR API backend: POST /carrito/agregar
    fetch("{{ url_for('carrito.agregar') }}", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ producto_id: 1, cantidad: 1 })
    })
    .then(r => r.json())
    .then(data => console.log("✓ Agregado:", data.nombre));
}
```

### 3️⃣ POST llega al backend
```python
# app/views/carrito.py

@carrito_bp.route('/carrito/agregar', methods=['POST'])
def agregar():
    """Recibe POST /carrito/agregar"""
    data = request.get_json()  # {"producto_id": 1, "cantidad": 1}
    
    producto = Producto.query.get_or_404(data['producto_id'])
    
    carrito = Carrito.query.filter_by(
        usuario_id=current_user.id
    ).first()
    
    # Agregar a BD
    item = CarritoProducto(
        carrito_id=carrito.id,
        producto_id=data['producto_id'],
        cantidad=data['cantidad']
    )
    db.session.add(item)
    db.session.commit()
    
    # Retornar respuesta
    return jsonify({'ok': True, 'nombre': producto.nombre})
```

### 4️⃣ Frontend recibe respuesta
```javascript
// .then(r => r.json())
// .then(data => console.log("✓ Agregado:", data.nombre));
// Resultado: ✓ Agregado: Martillo
```

---

## 6. RESUMEN

| Pregunta | Respuesta |
|----------|-----------|
| **¿Dónde se definen las URLs?** | `app/api/producto_api.py` con `@api_bp.route()` |
| **¿Dónde se activan en Flask?** | `app/__init__.py` con `app.register_blueprint()` |
| **¿Quién las llama?** | JavaScript, Python, clientes externos |
| **¿Cómo se llaman?** | `fetch()`, `location.href`, `requests`, curl, Postman |
| **¿Qué retornan?** | JSON (para APIs) o HTML (para vistas) |
| **¿Cómo llega al usuario?** | Navegador renderiza respuesta HTML o JS procesa JSON |

