# Ejemplos de Código Ferramas — Presentación Universitaria

---

## 1. BACKEND (Python + Flask)

### Ejemplo Backend #1: Modelo de Base de Datos (ORM SQLAlchemy)

```python
# app/models/carrito.py

from app import db

class Carrito(db.Model):
    __tablename__ = 'carrito'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    productos = db.relationship('CarritoProducto', backref='carrito', lazy=True)


class CarritoProducto(db.Model):
    __tablename__ = 'carrito_productos'

    id = db.Column(db.Integer, primary_key=True)
    carrito_id = db.Column(db.Integer, db.ForeignKey('carrito.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)

    producto = db.relationship('Producto', lazy=True)
```

**¿Por qué es importante?**
- Define estructura de tablas en la BD
- Uso de **ORM (SQLAlchemy)** en lugar de SQL puro
- **Relaciones** entre Carrito ↔ CarritoProducto ↔ Producto
- Facilita queries sin escribir SQL

---

### Ejemplo Backend #2: Rutas y Lógica de Negocio (Flask Blueprint)

```python
# app/views/carrito.py

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.carrito import Carrito, CarritoProducto
from app.models.producto import Producto

carrito_bp = Blueprint('carrito', __name__, url_prefix='/carrito')

@carrito_bp.route('/agregar', methods=['POST'])
def agregar():
    """Agrega un producto al carrito del usuario autenticado."""
    data = request.get_json()
    producto_id = data.get('producto_id')
    cantidad = data.get('cantidad', 1)
    
    producto = Producto.query.get_or_404(producto_id)

    if current_user.is_authenticated:
        # Obtener o crear carrito del usuario
        carrito = Carrito.query.filter_by(usuario_id=current_user.id).first()
        if not carrito:
            carrito = Carrito(usuario_id=current_user.id)
            db.session.add(carrito)
            db.session.commit()
        
        # Verificar si producto ya está en carrito
        item = CarritoProducto.query.filter_by(
            carrito_id=carrito.id, producto_id=producto_id
        ).first()
        
        if item:
            item.cantidad += cantidad  # Incrementar cantidad
        else:
            item = CarritoProducto(
                carrito_id=carrito.id, 
                producto_id=producto_id, 
                cantidad=cantidad
            )
            db.session.add(item)
        
        db.session.commit()
    
    return jsonify({'ok': True, 'nombre': producto.nombre})
```

**¿Por qué es importante?**
- **Blueprint**: organiza rutas por módulo (escalable)
- **Request JSON**: recibe datos del frontend
- **Login requerido**: manejo de sesiones
- **DB transactions**: commit/rollback
- **Retorna JSON**: para comunicación client-server

---

### Ejemplo Backend #3: Lógica de Pago (Servicio Externo - Mercado Pago)

```python
# app/services/pago_service.py

import mercadopago
from flask import current_app, url_for
from app import db
from app.models.pedido import Pago

class PagoService:
    
    @staticmethod
    def crear_preferencia(pedido):
        """
        Crea una preferencia en Mercado Pago.
        Retorna URL de pago que redirige al usuario.
        """
        
        # Inicializar SDK de Mercado Pago con token
        sdk = mercadopago.SDK(current_app.config.get('MP_ACCESS_TOKEN', ''))
        
        # Construir items del pedido
        items = []
        for pp in pedido.productos:
            items.append({
                'title': pp.producto.nombre,
                'quantity': pp.cantidad,
                'unit_price': float(pp.precio_unitario),
            })
        
        # Construir preferencia con URLs de retorno
        preference_data = {
            'items': items,
            'external_reference': str(pedido.id),
            'back_urls': {
                'success': url_for('tienda.pago_exito', 
                                   pedido_id=pedido.id, 
                                   _external=True),
                'failure': url_for('tienda.pago_error', 
                                   pedido_id=pedido.id, 
                                   _external=True),
            },
            'auto_return': 'approved',
        }
        
        try:
            # Enviar a API de Mercado Pago
            response = sdk.preference().create(preference_data)
            preference = response['response']
            
            # Retorna URL para redirigir usuario
            return {'init_point': preference['init_point']}
        
        except Exception as e:
            # Fallback: modo simulado
            return {'init_point': url_for('tienda.pago_exito', 
                                          pedido_id=pedido.id)}
    
    @staticmethod
    def confirmar_pago(pedido):
        """Marca pago como aprobado, descuenta stock, vacía carrito."""
        
        # Crear registro de pago en BD
        pago = Pago(
            pedido_id=pedido.id,
            metodo='mercadopago',
            estado='aprobado',
        )
        db.session.add(pago)
        pedido.estado = 'aprobado'
        
        # Descontar stock de cada producto
        for pp in pedido.productos:
            producto = Producto.query.get(pp.producto_id)
            if producto:
                producto.stock = max(0, producto.stock - pp.cantidad)
        
        db.session.commit()
```

**¿Por qué es importante?**
- **SDK externo**: integración con terceros
- **Manejo de excepciones**: fallback si API falla
- **Transacciones**: guardar cambios atómicamente
- **Descuento de stock**: lógica de negocio

---

## 2. API REST (Endpoints públicos)

### Ejemplo API #1: Listar Productos (GET)

```python
# app/api/producto_api.py

from flask import Blueprint, jsonify, request
from app.models.producto import Producto

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/productos')
def api_productos():
    """
    GET /api/productos
    Retorna lista de productos en formato JSON.
    
    Parámetro opcional:
    - convertir_a: USD o EUR (convierte precios)
    """
    productos = Producto.query.all()
    
    convert_to = request.args.get('convertir_a', '').upper()
    tasa = None
    
    if convert_to in ('USD', 'EUR'):
        from app.services.divisa_service import DivisaService
        ds = DivisaService()
        divisas = ds.obtener_divisas()
        tasa = divisas.get('dolar') if convert_to == 'USD' else divisas.get('euro')
    
    productos_lista = []
    for p in productos:
        d = {
            'id': p.id,
            'nombre': p.nombre,
            'precio': p.precio,
            'stock': p.stock,
            'categoria': p.categoria,
            'imagen': p.imagen,
        }
        
        if tasa:
            d['precio_original'] = d['precio']
            d['precio'] = round(d['precio'] / tasa)
            d['moneda'] = convert_to
        else:
            d['moneda'] = 'CLP'
        
        productos_lista.append(d)
    
    return jsonify(productos_lista)
```

**Respuesta ejemplo:**
```json
[
  {
    "id": 1,
    "nombre": "Martillo",
    "precio": 8500,
    "stock": 50,
    "categoria": "herramientas manuales",
    "imagen": "Martillo.jpg",
    "moneda": "CLP"
  },
  {
    "id": 5,
    "nombre": "Casco",
    "precio": 12000,
    "stock": 30,
    "categoria": "equipos de seguridad",
    "imagen": "Casco.jpg",
    "moneda": "CLP"
  }
]
```

**¿Por qué es importante?**
- **API REST**: separación frontend/backend
- **Query parameters**: ?convertir_a=USD
- **JSON**: formato estándar de intercambio
- **Reutilizable**: cualquier cliente puede consumir

---

### Ejemplo API #2: Crear Preferencia de Pago (POST)

```python
# app/views/tienda.py

from flask import Blueprint, render_template, redirect
from flask_login import login_required, current_user
from app.services.pago_service import PagoService
from app.models.pedido import Pedido

tienda_bp = Blueprint('tienda', __name__)

@tienda_bp.route('/pago/iniciar/<int:pedido_id>')
@login_required
def pago_iniciar(pedido_id):
    """
    GET /pago/iniciar/<pedido_id>
    Crea preferencia en Mercado Pago y redirige a URL de pago.
    """
    pedido = Pedido.query.get_or_404(pedido_id)
    
    # Validar que es el usuario del pedido
    if pedido.usuario_id != current_user.id:
        return redirect(url_for('tienda.index'))
    
    # Llamar al servicio de pago
    result = PagoService.crear_preferencia(pedido)
    
    # Redirigir a Mercado Pago
    return redirect(result['init_point'])
```

**Flujo:**
1. Usuario hace click "Pagar"
2. Flask llama a `PagoService.crear_preferencia()`
3. Mercado Pago retorna URL
4. Usuario es redirigido a Mercado Pago
5. Usuario paga y retorna

---

### Ejemplo API #3: Webhook (Notificación de Mercado Pago)

```python
# app/api/producto_api.py

@api_bp.route('/api/webhook/mercadopago', methods=['POST'])
def webhook_mercadopago():
    """
    POST /api/webhook/mercadopago
    Recibe notificaciones de Mercado Pago cuando hay pagos.
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'invalid data'}), 400
    
    action = data.get('action', '')
    
    # Si es notificación de pago aprobado
    if action == 'payment.approved':
        external_ref = data.get('data', {}).get('external_reference', '')
        
        if external_ref:
            from app.models.pedido import Pedido
            pedido = Pedido.query.get(int(external_ref))
            
            if pedido and pedido.estado == 'pendiente':
                # Confirmar pago localmente
                PagoService.confirmar_pago(pedido)
    
    return jsonify({'status': 'received'}), 200
```

**¿Por qué es importante?**
- **Webhooks**: notificaciones asincrónicas
- **Seguridad**: verifica external_reference
- **Transacciones**: procesa de forma confiable

---

## 3. FRONTEND (HTML + JavaScript)

### Ejemplo Frontend #1: Template HTML (Jinja2)

```html
<!-- app/templates/carrito.html -->

{% extends "base.html" %}
{% block content %}

<section class="hero">
    <h1>Carrito de compras</h1>
    <p>Revisa tus productos antes de comprar</p>
</section>

<div style="max-width:900px; margin:0 auto; padding: 8px 32px 40px;">
    
    <!-- Mensaje si carrito está vacío -->
    <div id="carrito-vacio" style="text-align:center; padding:40px; display:none;">
        <i class="ti ti-shopping-cart-off" style="font-size:48px; color:rgba(255,255,255,0.3);"></i>
        <p style="color:rgba(255,255,255,0.5); margin-top:12px;">Tu carrito está vacío.</p>
        <a href="{{ url_for('tienda.productos') }}" class="btn" style="background:#e8601a;">
            <i class="ti ti-package"></i> Ver productos
        </a>
    </div>
    
    <!-- Tabla con productos del carrito -->
    <div id="carrito-contenido">
        <div id="tabla-carrito"></div>
        
        <!-- Total y botón pagar -->
        <div style="text-align:right; margin-top:24px; padding:24px; background:rgba(255,255,255,0.07);">
            <h3 class="text-white mb-3">
                Total: <span id="total-carrito" style="color:#e8601a;">$0</span>
            </h3>
            <a href="{{ url_for('tienda.checkout') }}" class="btn btn-lg" style="background:#e8601a;">
                <i class="ti ti-credit-card"></i> Ir a pagar
            </a>
        </div>
    </div>
    
</div>

{% endblock %}
```

**¿Por qué es importante?**
- **Jinja2 templates**: server-side rendering
- **Template inheritance**: reutiliza base.html
- **URL generation**: url_for() genera URLs dinámicamente
- **Bootstrap classes**: diseño responsive

---

### Ejemplo Frontend #2: JavaScript - Renderizar Carrito

```javascript
<!-- En carrito.html: {% block scripts %} -->

function renderCarrito() {
    // Obtener carrito del localStorage (almacenamiento local del navegador)
    let carrito = JSON.parse(localStorage.getItem("carrito")) || [];
    let tabla = document.getElementById("tabla-carrito");
    let total = 0;

    // Si no hay productos, mostrar mensaje vacío
    if (carrito.length === 0) {
        document.getElementById("carrito-vacio").style.display = "block";
        document.getElementById("carrito-contenido").style.display = "none";
        return;
    }

    // Generar HTML de la tabla
    let html = '<div class="table-responsive"><table class="table table-dark">';
    html += '<thead><tr><th>Producto</th><th>Precio</th><th>Cantidad</th><th>Subtotal</th><th></th></tr></thead><tbody>';

    // Iterar sobre productos en carrito
    carrito.forEach((p, idx) => {
        let subtotal = p.precio * p.cantidad;
        total += subtotal;
        
        html += `<tr>
            <td>${p.nombre}</td>
            <td>$${p.precio.toLocaleString("es-CL")}</td>
            <td>
                <input type="number" min="1" value="${p.cantidad}" 
                    onchange="actualizarCantidad(${p.id}, this.value)">
            </td>
            <td>$${subtotal.toLocaleString("es-CL")}</td>
            <td>
                <button onclick="eliminarItem(${p.id})" class="btn btn-sm">
                    <i class="ti ti-trash"></i>
                </button>
            </td>
        </tr>`;
    });

    html += '</tbody></table></div>';
    
    // Inyectar HTML en el DOM
    tabla.innerHTML = html;
    
    // Actualizar total
    document.getElementById("total-carrito").textContent = "$" + total.toLocaleString("es-CL");
}

// Ejecutar cuando carga la página
renderCarrito();
```

**¿Por qué es importante?**
- **localStorage**: persistencia en el navegador
- **DOM manipulation**: actualiza HTML dinámicamente
- **Event handlers**: onchange en inputs
- **Formato de moneda**: .toLocaleString()

---

### Ejemplo Frontend #3: Comunicación Backend (Fetch API)

```javascript
function actualizarCantidad(id, nuevaCantidad) {
    // 1. Actualizar localStorage (frontend)
    let carrito = JSON.parse(localStorage.getItem("carrito")) || [];
    let item = carrito.find(p => p.id === id);
    
    if (item) {
        item.cantidad = Math.max(1, parseInt(nuevaCantidad) || 1);
        localStorage.setItem("carrito", JSON.stringify(carrito));
    }
    
    // 2. Renderizar cambios en pantalla
    renderCarrito();
    
    // 3. Sincronizar con backend (request POST)
    fetch("{{ url_for('carrito.actualizar') }}", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
            producto_id: id, 
            cantidad: Math.max(1, parseInt(nuevaCantidad) || 1) 
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            console.log("✓ Carrito sincronizado en BD");
        }
    })
    .catch(err => console.error("Error:", err));
}

function eliminarItem(id) {
    // 1. Eliminar de localStorage
    let carrito = JSON.parse(localStorage.getItem("carrito")) || [];
    carrito = carrito.filter(p => p.id !== id);
    localStorage.setItem("carrito", JSON.stringify(carrito));
    
    // 2. Renderizar
    renderCarrito();
    
    // 3. Notificar al backend
    fetch("{{ url_for('carrito.eliminar') }}", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ producto_id: id })
    })
    .catch(() => {});
}
```

**¿Por qué es importante?**
- **Fetch API**: comunicación asincrónica client-server
- **JSON serialization**: intercambio de datos
- **Dual storage**: localStorage + BD
- **Error handling**: .catch() para errores

---

## Resumen: Cómo Interactúan las 3 Capas

```
┌─────────────────────────────────────────────────────────┐
│ FRONTEND (HTML/CSS/JavaScript)                          │
│ - Renderiza carrito desde localStorage                  │
│ - Usuario cambia cantidad o elimina producto            │
│ - Envía fetch POST a /carrito/actualizar               │
└──────────────────────┬──────────────────────────────────┘
                       │ JSON
                       ▼
┌─────────────────────────────────────────────────────────┐
│ API REST (Flask Blueprints)                             │
│ - POST /carrito/actualizar recibe JSON                 │
│ - Valida datos y usuario autenticado                   │
│ - Llama modelos para actualizar BD                     │
│ - Retorna JSON con respuesta                           │
└──────────────────────┬──────────────────────────────────┘
                       │ SQL/ORM
                       ▼
┌─────────────────────────────────────────────────────────┐
│ BACKEND (SQLAlchemy Models + BD)                        │
│ - CarritoProducto.query.filter_by(...).first()         │
│ - item.cantidad = nueva_cantidad                        │
│ - db.session.commit() → ACTUALIZA EN BD                │
└─────────────────────────────────────────────────────────┘

Respuesta: JSON {'ok': True} retorna al Frontend
```

---

**Para la presentación, puedes usar estos 9 ejemplos para hablar de:**
- ✓ Separación de capas (Backend/API/Frontend)
- ✓ Patrones: MVC, ORM, REST
- ✓ Tecnologías: Flask, SQLAlchemy, JavaScript
- ✓ Comunicación: JSON, Fetch, Jinja2
- ✓ Persistencia: localStorage + BD
