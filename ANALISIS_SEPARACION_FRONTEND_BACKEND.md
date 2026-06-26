# Análisis de Separación Front-End / Back-End
## Proyecto Ferramas E-commerce

**Fecha de análisis:** 15 de Mayo, 2026  
**Arquitectura:** Monolítica con componentes separados  
**Estado actual:** Corriendo localmente en `http://127.0.0.1:5000`

---

## 1. Estructura del Proyecto

```
Ferramas2026/
├── app/                          # Paquete principal (backend + frontend)
│   ├── __init__.py              # Factory Flask, SQLAlchemy init
│   ├── config.py                # Variables de entorno
│   ├── models/                  # Modelos ORM
│   │   ├── usuario.py
│   │   ├── producto.py
│   │   ├── pedido.py
│   │   └── carrito.py
│   ├── services/                # Lógica de negocio
│   │   ├── auth_service.py
│   │   ├── pago_service.py
│   │   ├── divisa_service.py
│   │   └── email_service.py
│   ├── api/                     # Endpoints REST
│   │   └── producto_api.py      # GET /api/productos, /api/categorias
│   ├── views/                   # Rutas y lógica de presentación
│   │   ├── tienda.py           # GET /, /productos, /checkout
│   │   ├── carrito.py          # POST /carrito/*, GET /carrito
│   │   ├── auth.py             # POST /login, /registro
│   │   ├── vendedor.py         # Panel vendedor
│   │   ├── bodeguero.py        # Panel bodeguero
│   │   └── admin.py            # Panel admin
│   ├── static/                  # CSS, imágenes (frontend)
│   │   ├── styles.css
│   │   └── img/Productos/
│   └── templates/               # Templates HTML (frontend)
│       ├── base.html
│       ├── index.html
│       ├── productos.html
│       ├── carrito.html
│       ├── checkout.html
│       ├── login.html
│       └── ...
└── run.py                       # Punto de entrada
```

---

## 2. Evaluación de Separación

### ✓ **Aspectos Bien Separados**

#### a) **Separación Lógica en Carpetas**
- **Modelos** (`app/models/`) → Define la lógica de datos (ORM SQLAlchemy)
- **Servicios** (`app/services/`) → Lógica de negocio desacoplada
- **Vistas** (`app/views/`) → Rutas HTTP y presentación
- **API** (`app/api/`) → Endpoints REST públicos

**Ejemplo:** El servicio `PagoService` es independiente y reutilizable:
```python
# app/services/pago_service.py
class PagoService:
    @staticmethod
    def crear_preferencia(pedido):
        """Crea preferencia en Mercado Pago"""
```
Se puede llamar desde vistas web o APIs, manteniendo lógica centralizada.

#### b) **API REST Disponible**
```
GET  /api/productos                          # Lista de productos (JSON)
GET  /api/productos/<id>                     # Detalle de producto (JSON)
GET  /api/productos/categoria/<nombre>       # Productos por categoría (JSON)
GET  /api/categorias                         # Categorías únicas (JSON)
POST /api/webhook/mercadopago                # Webhook de pagos
```

Permite que un frontend SPA o móvil consuma datos sin vistas HTML.

#### c) **Blueprints para Organización Modular**
```python
# app/__init__.py
app.register_blueprint(api_bp)      # API REST
app.register_blueprint(auth_bp)     # Autenticación
app.register_blueprint(tienda_bp)   # Tienda
app.register_blueprint(carrito_bp)  # Carrito
```

---

### ✗ **Limitaciones en la Separación**

#### a) **Backend sirve el frontend en el mismo proceso**

En `app/__init__.py` Flask usa las rutas por defecto (`app/templates/`, `app/static/`):

```python
app = Flask(__name__)
```

**Implicación:**
- No hay separación de procesos (1 servidor Flask para todo)
- El backend está acoplado al frontend HTML
- Cambiar frontend requiere reiniciar backend
- No hay CORS configurado para frontends remotos (aunque está instalado)

#### b) **Vistas HTML Renderizadas en el Servidor**
```python
# app/views/tienda.py
@tienda_bp.route('/')
def index():
    return render_template('index.html')  # ← Server-side rendering
```

**Implicación:**
- Frontend depende de Jinja2 templates del backend
- Lógica de presentación mezclada con lógica de ruta
- Difícil de testear sin Flask

#### c) **Rutas Mixtas (HTML + JSON)**
```python
# Misma ruta sirve HTML y JSON
GET /productos               → HTML (vista)
GET /api/productos          → JSON (API)
```

Genera duplicidad: dos endpoints para lo mismo.

---

## 3. Flujo de Datos

### Frontend → Backend

```
[Navegador / HTML]
    ↓
GET /productos (vista HTML, servidor renderiza)
    ↓
[Flask - app/views/tienda.py]
    ↓
[SQLAlchemy - app/models/producto.py]
    ↓
[Base de datos - SQLite/MariaDB]
    ↓
[Jinja2 template - app/templates/productos.html]
    ↓
[Respuesta HTML al navegador]
```

### API REST (Alternativa)

```
[Cliente (SPA/Móvil)]
    ↓
GET /api/productos (JSON)
    ↓
[Flask - app/api/producto_api.py]
    ↓
[SQLAlchemy - app/models/producto.py]
    ↓
[Base de datos]
    ↓
[JSON serializado]
    ↓
[Respuesta JSON]
```

---

## 4. Pruebas Realizadas

| Endpoint | Método | Status | Resultado |
|----------|--------|--------|-----------|
| `/` | GET | 200 | HTML landing page |
| `/productos` | GET | 200 | HTML con productos |
| `/api/productos` | GET | 200 | JSON array |
| `/api/categorias` | GET | 200 | JSON array |
| `/login` | GET | 200 | Formulario login |
| `/carrito/agregar` | POST | 200 | Producto añadido |
| `/carrito/checkout` | POST | 302 | Redirección a pago |
| `/pago/iniciar/<id>` | GET | 302 | URL Mercado Pago generada |

**Estado de Pago:** ✓ Funcional (error NameError corregido)

---

## 5. Conclusiones

### Tipo de Arquitectura Actual
**Monolítica con capas lógicas separadas, pero no completamente desacoplada.**

- ✓ Hay separación **lógica** en componentes (Models, Services, Views, API)
- ✓ API REST disponible para consumo externo
- ✗ Backend y frontend operan en el **mismo proceso**
- ✗ No hay independencia de deployment

### Para una Tarea Universitaria

**Puntos a Mencionar:**

1. **Lo que está bien:** Estructura modular con blueprints, separación de responsabilidades en capas, uso de ORM (SQLAlchemy), servicios reutilizables.

2. **Lo que falta:** Separación física de frontend/backend, independencia de procesos, test unitarios sin Flask, documentación OpenAPI.

3. **Clasificación en Patrones:**
   - **Arquitectura MVC:** Sí (Models, Views Controllers en app/)
   - **Arquitectura REST API-first:** Parcialmente (API disponible pero no es el foco)
   - **Separación N-tier completa:** No (frontend y backend en mismo proceso)

---

## 6. Recomendaciones de Mejora

### Para una Separación Más Estricta:

1. **Convertir a Backend API-only:**
   ```python
   # Remover template_folder y static_folder
   app = Flask(__name__)  # Sin vistas HTML
   ```

2. **Mover Frontend a SPA (React/Vue/Angular):**
   - Carpeta `/frontend` con Node.js + Webpack
   - Consume solo endpoints `/api/*`
   - Deploy independiente

3. **Documentar API con OpenAPI/Swagger:**
   ```python
   from flask_swagger_ui import get_swaggerui_blueprint
   ```

4. **Agregar CORS más restrictivo:**
   ```python
   cors = CORS(app, resources={
       r"/api/*": {"origins": ["https://frontend.com"]}
   })
   ```

5. **Testear backend sin Flask:**
   - Usar pytest + coverage
   - Mock de servicios

---

## 7. Resumen Ejecutivo

| Aspecto | Estado | Calificación |
|--------|--------|--------------|
| Separación lógica | Implementada | 8/10 |
| Separación física | Incompleta | 4/10 |
| API disponible | Sí | 8/10 |
| Documentación | Básica | 5/10 |
| Testabilidad | Moderada | 6/10 |
| **Calificación General** | **Monolito modular** | **6.2/10** |

**Veredicto:** El proyecto tiene buena arquitectura interna (capas bien definidas) pero está limitado a una arquitectura monolítica. Para una tarea universitaria sobre separación front/backend, es un ejemplo útil de **lo que está bien** (separación lógica) y **lo que falta** (separación física).

---

*Análisis generado automáticamente. Código funcional verificado localmente.*
