# Ferramas — Documento de Exposición del Código

> **Proyecto:** Sistema e-commerce de ferretería  
> **Stack:** Flask + SQLAlchemy + SQLite + Mercado Pago + mindicador.cl  
> **Equipo:** Grupo Ferramas — Integración de Plataformas  

---

## 1. Arquitectura General

El proyecto sigue el **patrón fábrica (Factory Pattern)** de Flask, organizado en módulos independientes:

```
Cliente (Navegador)
       │
       ▼
┌─────────────────────────────────────────────┐
│  Flask App (run.py → create_app())          │
│  ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │ Blueprints│ │ Services │ │    Models    │ │
│  │ (rutas)   │ │(lógica)  │ │  (SQLAlchemy)│ │
│  └──────────┘ └──────────┘ └─────────────┘ │
│         │            │            │          │
│         ▼            ▼            ▼          │
│  ┌──────────────────────────────────────┐   │
│  │        SQLite (ferramas.db)           │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
       │                    │
       ▼                    ▼
┌──────────────┐   ┌──────────────────┐
│ Mercado Pago │   │  mindicador.cl   │
│  (pagos)     │   │ (divisas USD/EUR) │
└──────────────┘   └──────────────────┘
```

**Principios clave:**
- Separación de responsabilidades: modelos (datos), servicios (lógica), vistas (rutas HTTP), templates (UI)
- Blueprints de Flask para modularizar rutas por dominio
- SQLAlchemy ORM con SQLite (sin dependencia de MariaDB/MySQL externo)
- Autenticación con Flask-Login + werkzeug (hash de contraseñas)
- Carrito híbrido: localStorage (navegador) + base de datos (servidor)

---

## 2. Estructura del Proyecto

```
FerramasEV2/
├── run.py                      # Punto de entrada
├── requirements.txt            # Dependencias
├── ferramas.db                 # Base de datos SQLite (autogenerada)
├── .env                        # Variables de entorno (opcional)
├── app/
│   ├── __init__.py             # Fábrica create_app() + seed data
│   ├── config.py               # Configuración desde .env
│   │
│   ├── models/                 # Capa de datos (SQLAlchemy)
│   │   ├── usuario.py          # Usuario (5 roles)
│   │   ├── producto.py         # Producto (catálogo)
│   │   ├── pedido.py           # Pedido, PedidoProducto, Pago, Direccion
│   │   ├── carrito.py          # Carrito, CarritoProducto
│   │   └── suscriptor.py       # Suscriptor (newsletter)
│   │
│   ├── services/               # Capa de lógica de negocio
│   │   ├── auth_service.py     # Registro, login, cambio password
│   │   ├── pago_service.py     # Mercado Pago + flujo simulado
│   │   ├── divisa_service.py   # mindicador.cl con caché
│   │   └── email_service.py    # SMTP real + fallback simulado
│   │
│   ├── views/                  # Blueprints (rutas HTTP)
│   │   ├── auth.py             # /login, /registro, /logout, /perfil
│   │   ├── tienda.py           # /, /productos, /checkout, /pago/*
│   │   ├── carrito.py          # /carrito/* (CRUD + checkout)
│   │   ├── vendedor.py         # /vendedor (aprobar/rechazar pedidos)
│   │   ├── bodeguero.py        # /bodeguero (preparar/entregar pedidos)
│   │   └── admin.py            # /admin (dashboard + gestión usuarios)
│   │
│   ├── api/                    # API REST
│   │   └── producto_api.py     # /api/productos, divisas, webhook MP
│   │
│   ├── templates/              # Vistas Jinja2 (11 templates)
│   │   ├── base.html           # Layout base (navbar, footer, flash)
│   │   ├── index.html          # Homepage (categorías + suscripción)
│   │   ├── productos.html      # Catálogo con grid + selector moneda
│   │   ├── carrito.html        # Carrito (tabla dinámica con JS)
│   │   ├── checkout.html       # Checkout (entrega, pago, descuento)
│   │   ├── login.html          # Login con sync carrito
│   │   ├── registro.html       # Registro de cliente
│   │   ├── perfil.html         # Perfil cliente + historial pedidos
│   │   ├── vendedor.html       # Panel vendedor
│   │   ├── bodeguero.html      # Panel bodeguero
│   │   └── admin.html          # Panel admin (dashboard + roles)
│   │
│   └── static/
│       ├── styles.css          # Estilos globales (tema oscuro #2c1a0e)
│       └── img/Productos/      # Imágenes de productos
```

---

## 3. Configuración y Arranque

### 3.1 Punto de entrada (`run.py`)

```python
from app import create_app
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
```

Llama a la fábrica `create_app()` que construye toda la aplicación.

### 3.2 Fábrica (`app/__init__.py`)

La función `create_app()` ejecuta en orden:

1. **Crear instancia Flask** y cargar configuración desde `Config`
2. **Inicializar extensiones**: SQLAlchemy, Flask-CORS, Flask-Login
3. **Importar modelos** y configurar `@login_manager.user_loader`
4. **Registrar 7 Blueprints** (api, auth, tienda, carrito, vendedor, bodeguero, admin)
5. **Crear tablas** con `db.create_all()` si no existen
6. **Ejecutar `_seed_data()`** que inserta 18 productos en 6 categorías y 4 usuarios (admin, vendedor, bodeguero, cliente demo con 10% descuento) si las tablas están vacías

### 3.3 Configuración (`app/config.py`)

Usa `python-dotenv` para cargar variables desde `.env`. Valores principales:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `SECRET_KEY` | `dev-key-ferramas-2026` | Clave de sesiones Flask |
| `DATABASE_URL` | `sqlite:///ferramas.db` | Conexión BD |
| `MP_ACCESS_TOKEN` | `TEST-123...` | Token Mercado Pago |
| `MAIL_SERVER` | `smtp.gmail.com` | Servidor SMTP |
| `MAIL_PORT` | `587` | Puerto SMTP |
| `DIVISA_CACHE_SEGUNDOS` | `3600` | Caché de divisas |

---

## 4. Modelos de Datos

### 4.1 Usuario (`app/models/usuario.py`)

```python
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id            # PK autoincremental
    nombre        # String(100)
    email         # String(150) único
    password_hash # String(255) — hash werkzeug
    rol           # String(20): cliente, admin, vendedor, bodeguero, contador
    rut           # String(20) opcional
    sucursal_id   # Integer opcional
    descuento     # Integer — porcentaje de descuento (0-100)
    created_at    # DateTime
```

**Relaciones:** 1:1 con Carrito, 1:N con Pedido, 1:N con Direccion  
**Seguridad:** `set_password()` y `check_password()` usan `werkzeug.security`  
**Roles:** Métodos helper `is_admin()`, `is_vendedor()`, `is_bodeguero()`

### 4.2 Producto (`app/models/producto.py`)

```python
class Producto(db.Model):
    id, nombre, precio (Integer), stock (Integer),
    categoria (String), imagen (String)
```

Método `to_dict()` para serialización JSON en la API.

### 4.3 Pedido y asociados (`app/models/pedido.py`)

**Pedido:** `id, usuario_id, estado, direccion_despacho, sucursal_retiro, modo_entrega (retiro/despacho), total, created_at`

**Estados del pedido (máquina de estados):**
```
pendiente → aprobado → preparando → entregado
                ↓
           rechazado / cancelado
```

**PedidoProducto:** Tabla pivote con `pedido_id, producto_id, cantidad, precio_unitario` (guarda el precio al momento de la compra)

**Pago:** `pedido_id, metodo, estado, transaccion_id` — registro de transacción

**Direccion:** `usuario_id, direccion, comuna, region`

### 4.4 Carrito (`app/models/carrito.py`)

**Carrito:** `id, usuario_id` (1:1 con Usuario)  
**CarritoProducto:** `carrito_id, producto_id, cantidad` (relación N:M con Producto)

### 4.5 Suscriptor (`app/models/suscriptor.py`)

```python
class Suscriptor(db.Model):
    id, email (único), created_at
```

Para la funcionalidad de newsletter en la homepage.

### Diagrama Entidad-Relación

```
Usuario ──1:1── Carrito ──1:N── CarritoProducto ──N:1── Producto
   │
   ├──1:N── Pedido ──1:N── PedidoProducto ──N:1── Producto
   │            │
   │            └──1:1── Pago
   │
   └──1:N── Direccion

Suscriptor (independiente)
```

---

## 5. Servicios (Lógica de Negocio)

### 5.1 AuthService (`app/services/auth_service.py`)

- **`registrar(nombre, email, password, rol, rut)`**: Crea usuario con hash de contraseña, crea carrito vacío asociado. Retorna `(user, error)`.
- **`login(email, password)`**: Busca por email, verifica hash. Retorna `(user, error)`.
- **`cambiar_password(user, current, new)`**: Verifica contraseña actual, actualiza hash.

### 5.2 PagoService (`app/services/pago_service.py`)

El servicio más complejo. Maneja dos modos:

**Modo simulado** (sin token real de MP):
- `_es_modo_simulado()`: Detecta si el token es el default `TEST-123456789-abcdef`
- `_preferencia_simulada()`: Retorna URL directa a `/pago/exito`

**Modo real** (con credenciales de Mercado Pago):
- `crear_preferencia(pedido)`: Usa SDK `mercadopago`, crea preferencia con items, back_urls y auto_return. Si falla, cae a simulado.

**Flujo de confirmación:**
- `confirmar_pago(pedido, transaccion_id)`: 
  1. Crea/actualiza registro Pago
  2. Cambia pedido.estado a `'aprobado'`
  3. **Descuenta stock**: `producto.stock = max(0, producto.stock - cantidad)`
  4. **Vacía carrito** del usuario
  5. `db.session.commit()`

- `cancelar_pedido(pedido)`: Marca como `'cancelado'`, NO vacía carrito
- `procesar_webhook(data)`: Recibe IPN de Mercado Pago y confirma pago

### 5.3 DivisaService (`app/services/divisa_service.py`)

- Consulta `https://mindicador.cl/api` para obtener USD y EUR
- **Caché en memoria** con TTL configurable (`DIVISA_CACHE_SEGUNDOS`, default 1 hora)
- Fallback a valores fijos (USD=950, EUR=1050) si la API falla

### 5.4 EmailService (`app/services/email_service.py`)

- `_enviar_real(destinatario, asunto, cuerpo_html)`: Usa `smtplib` + `MIMEMultipart` para enviar correos HTML con TLS
- `_tiene_credenciales()`: Verifica si hay MAIL_USERNAME y MAIL_PASSWORD configurados
- Si no hay credenciales → imprime en consola `[EMAIL SIMULADO]` y retorna True
- Tres métodos públicos:
  - `enviar_bienvenida(usuario)` — email tras registro
  - `enviar_confirmacion_pedido(usuario, pedido)` — al confirmar pedido
  - `enviar_cambio_estado(usuario, pedido, nuevo_estado)` — en cada cambio de estado

---

## 6. Vistas y Rutas (Blueprints)

### 6.1 Auth (`app/views/auth.py`) — Sin prefijo

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/login` | GET/POST | Login + sincronización carrito localStorage→BD |
| `/registro` | GET/POST | Registro cliente + email bienvenida |
| `/logout` | GET | Cerrar sesión |
| `/perfil` | GET | Perfil + historial de pedidos |

**Detalle clave — Sincronización de carrito en login:**
Al enviar el formulario de login, JavaScript serializa el carrito de `localStorage` a un campo oculto `items_carrito`. El backend llama a `_sync_carrito_items()` que fusiona los items con el carrito existente en BD (usa `max(cantidad_existente, cantidad_localstorage)`).

**Detalle clave — Email en registro:**
```python
EmailService.enviar_bienvenida(user)
```
Se llama inmediatamente después de `login_user(user)`. Si no hay SMTP configurado, imprime en consola `[EMAIL SIMULADO]`.

### 6.2 Tienda (`app/views/tienda.py`) — Sin prefijo

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/` | GET | Homepage con categorías y suscripción |
| `/suscribirse` | POST | Suscripción newsletter |
| `/productos` | GET | Catálogo con filtro categoría y conversión moneda |
| `/checkout` | GET | Página de checkout |
| `/pago/iniciar/<id>` | GET | Crea preferencia MP y redirige |
| `/pago/exito` | GET | Confirma pago, descuenta stock, vacía carrito |
| `/pago/error` | GET | Cancela pedido, mantiene carrito |

**Detalle — Conversión de moneda:**
El parámetro `?convertir_a=USD` o `?convertir_a=EUR` consulta la API mindicador.cl y divide los precios por el valor de la divisa. Los precios originales en CLP se guardan en `data-precio-clp` para el frontend.

### 6.3 Carrito (`app/views/carrito.py`) — Prefijo `/carrito`

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/carrito/` | GET | Vista del carrito |
| `/carrito/agregar` | POST | Agregar producto (JSON) |
| `/carrito/eliminar` | POST | Eliminar producto (JSON) |
| `/carrito/actualizar` | POST | Cambiar cantidad (JSON) |
| `/carrito/sincronizar` | POST | Sincronizar localStorage→BD |
| `/carrito/checkout` | POST | **Procesar checkout** |

**Detalle — Flujo de checkout:**
1. Recibe `modo_entrega`, `metodo_pago`, `direccion`, `comuna`, `region`
2. Si el carrito BD está vacío, sincroniza desde `items_carrito` (hidden field)
3. Calcula `subtotal`, aplica `descuento_pct` del usuario, calcula `total`
4. Crea `Pedido` con estado `'pendiente'` (MP) o `'pendiente_transferencia'` (transferencia)
5. Crea registros `PedidoProducto` y opcionalmente `Direccion`
6. Si es transferencia → confirma pago inmediatamente y redirige a perfil
7. Si es Mercado Pago → redirige a `/pago/iniciar/<pedido_id>`

### 6.4 Vendedor (`app/views/vendedor.py`) — Prefijo `/vendedor`

Control de acceso: solo `vendedor` o `admin`.

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/vendedor/` | GET | Panel: pedidos pendientes |
| `/vendedor/aprobar/<id>` | POST | Aprueba pedido → estado `preparando` + email |
| `/vendedor/rechazar/<id>` | POST | Rechaza pedido → estado `rechazado` + email |

### 6.5 Bodeguero (`app/views/bodeguero.py`) — Prefijo `/bodeguero`

Control de acceso: solo `bodeguero` o `admin`.

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/bodeguero/` | GET | Panel: pedidos aprobados/preparando |
| `/bodeguero/preparar/<id>` | POST | Marca como `preparando` + email |
| `/bodeguero/entregar/<id>` | POST | Marca como `entregado` + email |

### 6.6 Admin (`app/views/admin.py`) — Prefijo `/admin`

Control de acceso: solo `admin`.

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/admin/` | GET | Dashboard: stats + usuarios + pedidos |
| `/admin/usuarios` | POST | Cambiar rol de un usuario |

---

## 7. API REST (`app/api/producto_api.py`)

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/productos` | GET | Lista productos. `?convertir_a=USD\|EUR` para divisa |
| `/api/productos/<id>` | GET | Detalle de un producto |
| `/api/productos/categoria/<nombre>` | GET | Productos por categoría |
| `/api/categorias` | GET | Lista de categorías distintas |
| `/api/webhook/mercadopago` | POST | Webhook IPN de Mercado Pago |

**Detalle — Conversión de divisa en API:**
Cuando se pasa `?convertir_a=USD`, cada producto incluye:
```json
{
  "precio": 9,           // convertido
  "precio_original": 8500,
  "moneda": "USD"
}
```

**Detalle — Webhook MP:**
Soporta dos modos:
- **Real:** Recibe `payment.created`/`payment.updated`, consulta el estado del pago al SDK de MP, y si está `approved` confirma el pedido
- **Simulado:** Procesa mediante `PagoService.procesar_webhook()`

---

## 8. Integraciones Externas

### 8.1 Mercado Pago (API de pago)

**SDK:** `mercadopago` (instalado vía pip)  
**Modos:** Real (con token de vendedor) y Simulado (desarrollo)

**Flujo completo:**
```
1. Cliente hace checkout → POST /carrito/checkout
2. Se crea Pedido con estado "pendiente"
3. Redirige a /pago/iniciar/<pedido_id>
4. PagoService.crear_preferencia() → init_point de MP
5. Cliente paga en Mercado Pago (o simulado)
6. MP redirige a /pago/exito?pedido_id=X
7. PagoService.confirmar_pago():
   - Crea Pago (aprobado)
   - Cambia pedido.estado = "aprobado"
   - Descuenta stock de cada producto
   - Vacía carrito del usuario
```

**Configuración necesaria en .env:**
```
MP_ACCESS_TOKEN=TEST-123456789-abcdef
MP_PUBLIC_KEY=TEST-public-key-abcdef
```

### 8.2 mindicador.cl (API de divisas)

**Endpoint:** `https://mindicador.cl/api`  
**Uso:** Conversión CLP ↔ USD/EUR en tiempo real  
**Caché:** 1 hora por defecto (configurable)  
**Fallback:** Si la API no responde, usa valores fijos

### 8.3 SMTP (envío de correos)

**Protocolo:** SMTP con TLS (puerto 587)  
**Configuración:** MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD  
**Fallback:** Sin credenciales imprime en consola `[EMAIL SIMULADO]`

---

## 9. Frontend (Templates y Estilos)

### 9.1 Tema visual

- **Color fondo:** `#2c1a0e` (café oscuro) en todo el sitio
- **Color acento:** `#e8601a` (naranja) para botones, precios, links
- **Colores semánticos:** `#1d9e75` (éxito), `#e24b4a` (error), `#378add` (info), `#ef9f27` (warning)
- **Librerías CDN:** Bootstrap 5.3.3 + Tabler Icons
- **Efectos:** backdrop-filter blur, bordes semitransparentes, transiciones

### 9.2 Layout base (`base.html`)

Define la estructura común:
- **Navbar:** Logo + links (Productos, Carrito con contador, Usuario/Login/Registro)
- **Dropdown usuario:** Perfil, Panel Admin/Vendedor/Bodeguero (según rol), Logout
- **Flash messages:** Alertas Bootstrap con colores por categoría
- **Footer:** Links + redes sociales
- **Contador carrito:** `actualizarContador()` lee localStorage y actualiza badge

### 9.3 Carrito híbrido (localStorage + BD)

El carrito funciona en dos capas:

1. **localStorage (navegador):** Array JSON con `[{id, nombre, precio, cantidad}]`. Permite agregar productos sin estar logueado.
2. **Base de datos (servidor):** Tablas `carrito` y `carrito_productos`. Persiste el carrito entre sesiones.

**Sincronización:**
- Al hacer login: se envía el localStorage como hidden field → backend fusiona con BD
- Al agregar/eliminar/actualizar: se modifica localStorage + se envía fetch al backend
- Al hacer checkout: si BD está vacía, se reconstruye desde el hidden field `items_carrito`

### 9.4 Páginas principales

**Homepage (`index.html`):** Grid de 6 categorías con iconos + sección de suscripción newsletter

**Checkout (`checkout.html`):**
- Selector de entrega: retiro en sucursal / despacho a domicilio
- Dirección de despacho (condicional)
- Selector de pago: Mercado Pago / Transferencia bancaria
- Datos bancarios para transferencia (Banco Santander, cuenta, RUT, email)
- Resumen dinámico desde localStorage con cálculo de descuento
- Botón de pago (cambia texto según método seleccionado)

**Productos (`productos.html`):** Grid de cards con imagen, nombre, precio, stock, botón agregar + selector de moneda

---

## 10. Flujos Principales

### 10.1 Flujo de compra completo

```
1. Cliente navega catálogo (/productos)
2. Agrega productos al carrito (localStorage + fetch a /carrito/agregar)
3. Va al carrito (/carrito) → revisa items
4. Click "Ir a pagar" → /checkout
5. Elige modo de entrega (retiro/despacho) y método de pago (MP/transferencia)
6. POST /carrito/checkout:
   - Se crea Pedido y PedidoProductos
   - Si transferencia → confirmación inmediata, redirect a /perfil
   - Si MP → redirect a /pago/iniciar/<id>
7. /pago/iniciar crea preferencia MP y redirige a Mercado Pago
8. Cliente paga → MP redirige a /pago/exito
9. /pago/exito confirma pago, descuenta stock, vacía carrito
10. Cliente ve pantalla de éxito
```

### 10.2 Flujo de trabajo interno (workflow staff)

```
Cliente compra → Pedido "pendiente"
    ↓
Vendedor revisa → Aprueba: "aprobado" / Rechaza: "rechazado"
    ↓
Bodeguero ve "aprobado" → Prepara: "preparando"
    ↓
Bodeguero entrega → "entregado"

Cada cambio de estado envía email al cliente.
```

### 10.3 Flujo de autenticación

```
Registro:
  GET /registro → formulario
  POST /registro → AuthService.registrar() → login_user() → EmailService.enviar_bienvenida()

Login:
  GET /login → formulario
  POST /login → AuthService.login() → login_user() → sync localStorage→BD → redirect según rol
```

---

## 11. Dependencias (requirements.txt)

| Paquete | Uso |
|---------|-----|
| `flask` | Framework web |
| `flask-cors` | CORS para API |
| `flask-sqlalchemy` | ORM para SQLite |
| `flask-login` | Sesiones y autenticación |
| `werkzeug` | Hash de contraseñas |
| `mercadopago` | SDK Mercado Pago |
| `requests` | Cliente HTTP (mindicador.cl) |
| `python-dotenv` | Variables de entorno |

---

## 12. Puntos Clave para la Exposición

1. **Arquitectura limpia:** Factory pattern + Blueprints + Services. Cada responsabilidad en su capa.

2. **Adaptabilidad de BD:** Originalmente diseñado para MariaDB, migrado a SQLite sin cambiar lógica de negocio — solo cambió `DATABASE_URL`. Demuestra portabilidad del ORM.

3. **Mercado Pago dual:** El sistema detecta automáticamente si usar MP real o simulado según el token configurado. No hay código diferente para desarrollo vs producción.

4. **Carrito híbrido:** La combinación localStorage + BD permite agregar productos sin login y no perder el carrito al iniciar sesión. Es una solución práctica para e-commerce.

5. **Máquina de estados:** El pedido transita por 6 estados con reglas claras y cada transición notifica al cliente por email.

6. **Seguridad:** Contraseñas hasheadas con werkzeug, roles con verificaciones explícitas en cada blueprint, protección CSRF implícita en formularios POST.

7. **API REST propia:** Endpoints para productos, categorías y webhook que pueden ser consumidos por un frontend mobile o terceros.

8. **Integración de divisas:** Consulta en tiempo real a mindicador.cl con caché para no sobrecargar la API externa.

---

> **Servidor:** `python run.py` → http://127.0.0.1:5000  
> **Usuarios de prueba:** admin@ferramas.cl / cliente@ferramas.cl / vendedor@ferramas.cl / bodeguero@ferramas.cl  
> **Contraseña común:** `admin123` / `cliente123` / `vendedor123` / `bodeguero123`
