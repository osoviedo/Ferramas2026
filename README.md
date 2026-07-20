# 🛠️ Ferramas — E-commerce de Ferretería

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple.svg)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Sistema e-commerce completo para una ferretería, construido con **Flask** + **SQLAlchemy** + **Bootstrap 5**. Incluye catálogo de productos, carrito de compras, pasarela de pago con **Mercado Pago**, panel de administración por roles, API REST y despliegue en **Render**.

---

## ✨ Funcionalidades

- 🏪 **Catálogo de productos** — 18 productos organizados en 6 categorías (herramientas manuales, equipos de seguridad, fijaciones, materiales básicos, tornillos y anclaje, equipos de medición)
- 🛒 **Carrito de compras** — localStorage en frontend + sincronización con base de datos al iniciar sesión
- 💳 **Pago con Mercado Pago** — integración completa con SDK oficial; modo simulado automático sin credenciales reales
- 👥 **Cuatro roles de usuario**: cliente, vendedor, bodeguero y administrador
- 📦 **Flujo de pedidos** — pendiente → aprobado → preparado → entregado
- 🔐 **Autenticación** — registro, login, hash de contraseñas (werkzeug), sesiones con Flask-Login
- 🌐 **API REST** — endpoints públicos para productos, categorías y divisas
- 💱 **Conversión de divisas** — tasas USD/EUR desde el Banco Central de Chile (mindicador.cl)
- 📧 **Notificaciones por email** — confirmación de pedidos vía SMTP
- 📊 **Panel de administración** — gestión de usuarios, reportes y pedidos
- 🚀 **Despliegue en Render** — configurado con `render.yaml`

---

## 🏗️ Estructura del proyecto

```
Ferramas2026/
├── app/
│   ├── __init__.py              # Factory pattern (create_app), Flask-Login, seed data
│   ├── config.py                # Configuración desde variables de entorno
│   ├── api/
│   │   └── producto_api.py      # API REST: /api/productos, /api/categorias, /api/divisas
│   ├── models/
│   │   ├── producto.py          # Modelo Producto
│   │   ├── usuario.py           # Modelo Usuario (con hash de contraseñas)
│   │   ├── pedido.py            # Pedido, PedidoProducto, Pago, Direccion
│   │   ├── carrito.py           # Carrito, CarritoProducto
│   │   └── suscriptor.py        # Suscripciones al newsletter
│   ├── services/
│   │   ├── auth_service.py      # Lógica de autenticación
│   │   ├── pago_service.py      # Integración Mercado Pago (SDK oficial)
│   │   ├── divisa_service.py    # Conversión CLP ↔ USD/EUR
│   │   └── email_service.py     # Envío de emails (SMTP)
│   ├── views/
│   │   ├── auth.py              # Login, registro, perfil
│   │   ├── tienda.py            # Landing, productos, checkout, pago
│   │   ├── carrito.py           # Gestión del carrito
│   │   ├── vendedor.py          # Panel de vendedor
│   │   ├── bodeguero.py         # Panel de bodeguero
│   │   └── admin.py             # Panel de administrador
│   ├── static/
│   │   ├── styles.css           # Estilos personalizados
│   │   └── img/Productos/       # Imágenes de los 18 productos
│   └── templates/               # Plantillas Jinja2 (Bootstrap 5)
│       ├── base.html            # Layout base con navbar
│       ├── index.html           # Landing page
│       ├── productos.html       # Catálogo con filtros
│       ├── checkout.html        # Checkout y confirmación de pago
│       ├── pago_sandbox.html    # Demo de pago con credenciales test MP
│       ├── auth/                # Login, registro, perfil
│       ├── admin.html           # Panel administrador
│       ├── vendedor.html        # Panel vendedor
│       └── bodeguero.html       # Panel bodeguero
├── docs/
│   └── CASOS_PRUEBA_FERRAMAS.md # Documentación de casos de prueba
├── scripts/
│   └── demo_pago_mp.ps1         # Script PowerShell para demo de pago
├── tests/                       # Pruebas unitarias, integración, aceptación
├── requirements.txt             # Dependencias Python
├── run.py                       # Punto de entrada: python run.py
├── render.yaml                  # Configuración de despliegue en Render
├── pytest.ini                   # Configuración de pytest
├── .env.example                 # Plantilla de variables de entorno
└── README.md
```

---

## 🚀 Instalación rápida

### Requisitos previos

- **Python 3.9+**
- (Opcional) Cuenta de [Mercado Pago](https://www.mercadopago.cl/developers/panel/app) para pagos reales

### Paso a paso

```bash
# 1. Clonar el repositorio
git clone https://github.com/osoviedo/Ferramas2026
cd Ferramas2026

# 2. Crear entorno virtual (recomendado)
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores (ver tabla de configuración más abajo)

# 5. Ejecutar la aplicación
python run.py
```

La app se inicia en **http://127.0.0.1:5000** y crea automáticamente:
- La base de datos `ferramas.db` (SQLite)
- 18 productos de ferretería de prueba
- 4 usuarios con roles predefinidos

---

## 👥 Usuarios de prueba

| Rol | Email | Contraseña |
|---|---|---|
| Administrador | `admin@ferramas.cl` | `admin123` |
| Vendedor | `vendedor@ferramas.cl` | `vendedor123` |
| Bodeguero | `bodeguero@ferramas.cl` | `bodeguero123` |
| Cliente | `cliente@ferramas.cl` | `cliente123` |

---

## ⚙️ Configuración

Copia `.env.example` a `.env` y configura las siguientes variables:

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `SECRET_KEY` | Llave secreta para sesiones Flask | `dev-key-ferramas-2026` |
| `MP_ACCESS_TOKEN` | Access token de Mercado Pago (sandbox). El valor `TEST-123456789-abcdef` activa modo simulado. | `TEST-123456789-abcdef` |
| `MP_PUBLIC_KEY` | Public key de Mercado Pago | `TEST-public-key-abcdef` |
| `DATABASE_URL` | URL de conexión a base de datos | `sqlite:///ferramas.db` |
| `DIVISA_CACHE_SEGUNDOS` | Tiempo de caché para tasas de cambio | `3600` |
| `PUBLIC_BASE_URL` | URL pública de la app (necesaria para callbacks de Mercado Pago) | `http://127.0.0.1:5000` |
| `BCENTRAL_USER` | Usuario API Banco Central (opcional) | *(vacío)* |
| `BCENTRAL_PASS` | Contraseña API Banco Central (opcional) | *(vacío)* |
| `DEV_AUTO_LOGIN` | Auto-login demo en desarrollo | `false` |
| `DEV_LOGIN_EMAIL` | Email para auto-login | `cliente@ferramas.cl` |
| `DEV_LOGIN_PASSWORD` | Contraseña para auto-login | `cliente123` |
| `MP_TEST_BUYER_USER` | Usuario comprador test de Mercado Pago | *(vacío)* |
| `MP_TEST_BUYER_PASSWORD` | Contraseña comprador test de Mercado Pago | *(vacío)* |
| `MAIL_SERVER` | Servidor SMTP | `smtp.gmail.com` |
| `MAIL_PORT` | Puerto SMTP | `587` |
| `MAIL_USE_TLS` | Usar TLS | `true` |
| `MAIL_USERNAME` | Usuario SMTP | *(vacío)* |
| `MAIL_PASSWORD` | Contraseña SMTP | *(vacío)* |
| `MAIL_DEFAULT_SENDER` | Remitente por defecto | `noreply@ferramas.cl` |

### 💡 Modo demo local con Mercado Pago Sandbox

Para probar el flujo completo de pago con credenciales de prueba de Mercado Pago:

```bash
# 1. Usar ngrok para exponer localhost
ngrok http 5000

# 2. En .env:
PUBLIC_BASE_URL=https://xxxx.ngrok-free.app
MP_ACCESS_TOKEN=APP_USR-tu-access-token-sandbox
MP_PUBLIC_KEY=APP_USR-tu-public-key-sandbox
DEV_AUTO_LOGIN=true
MP_TEST_BUYER_USER=tu-usuario-comprador-test
MP_TEST_BUYER_PASSWORD=tu-contraseña-comprador-test
```

Para demo rápida sin ngrok, ejecuta `scripts/demo_pago_mp.ps1`.

---

## 📡 API REST

La API es pública y no requiere autenticación.

### Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/productos` | Lista todos los productos |
| `GET` | `/api/productos?convertir_a=USD` | Productos con precio convertido a USD |
| `GET` | `/api/productos?convertir_a=EUR` | Productos con precio convertido a EUR |
| `GET` | `/api/productos/<id>` | Detalle de un producto |
| `GET` | `/api/productos/categoria/<nombre>` | Productos por categoría |
| `GET` | `/api/categorias` | Lista de categorías únicas |
| `GET` | `/api/divisas` | Tasas de cambio USD/EUR |
| `POST` | `/api/webhook/mercadopago` | Webhook para notificaciones de pago |

### Ejemplos de respuesta

**`GET /api/productos`**
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
  }
]
```

**`GET /api/divisas`**
```json
{
  "dolar": 950.5,
  "euro": 1020.3,
  "fecha": "2026-07-19"
}
```

---

## 🔄 Flujo de pedidos

```
Cliente agrega productos al carrito
        ↓
Crea pedido (estado: pendiente)
        ↓
Pago con Mercado Pago (simulado o real)
        ↓
Vendedor revisa → aprueba pedido
        ↓
Bodeguero prepara → marca como preparado
        ↓
Bodeguero entrega → marca como entregado
```

---

## 👤 Roles de usuario

| Rol | Permisos |
|---|---|
| **cliente** | Explorar catálogo, agregar al carrito, comprar, ver historial de pedidos |
| **vendedor** | Ver pedidos pendientes, aprobar o rechazar pedidos |
| **bodeguero** | Ver pedidos aprobados, preparar y entregar pedidos |
| **contador** | Definido en el modelo (vistas futuras) |
| **admin** | Gestión completa de usuarios, productos y reportes; acceso a todos los paneles |

---

## 🧪 Pruebas

```bash
# Instalar dependencias de prueba
pip install -r requirements.txt

# Ejecutar todos los tests
python -m pytest -v

# Por tipo de prueba
python -m pytest -m unit -v            # Unitarias
python -m pytest -m integration -v     # Integración
python -m pytest -m mock -v            # Con mocks de servicios externos
python -m pytest -m acceptance -v      # Criterios de aceptación
python -m pytest -m load -v            # Carga
python -m pytest -m stress -v          # Estrés

# Con cobertura
python -m pytest --cov=app --cov-report=html
```

Los casos de prueba detallados (CA01–CA07) están documentados en `docs/CASOS_PRUEBA_FERRAMAS.md`.

---

## 🚀 Despliegue

### Render (configuración incluida)

El proyecto incluye `render.yaml` listo para despliegue en [Render](https://render.com):

1. Conecta tu repositorio de GitHub a Render
2. Render detecta automáticamente `render.yaml`
3. Configura las variables de entorno con `sync: false` (secrets)
4. La app se despliega en `https://ferramas-xxxx.onrender.com`

### Variables de entorno requeridas en producción

- `SECRET_KEY` — usar un valor seguro y único
- `MP_ACCESS_TOKEN` — token de producción de Mercado Pago
- `MP_PUBLIC_KEY` — public key de producción
- `PUBLIC_BASE_URL` — URL HTTPS de la app en producción
- `MAIL_USERNAME` / `MAIL_PASSWORD` — credenciales SMTP para notificaciones

---

## 🛠️ Tecnologías

| Capa | Tecnología |
|---|---|
| **Backend** | Flask 3.x, Python 3.9+ |
| **ORM** | SQLAlchemy (Flask-SQLAlchemy) |
| **Base de datos** | SQLite (desarrollo) / MySQL (producción vía `DATABASE_URL`) |
| **Autenticación** | Flask-Login, werkzeug (hash de contraseñas) |
| **Frontend** | Bootstrap 5, Jinja2, JavaScript vanilla |
| **Pagos** | Mercado Pago SDK (modo simulado + real) |
| **Divisas** | mindicador.cl (Banco Central de Chile) |
| **Email** | SMTP (Gmail o cualquier servidor) |
| **Testing** | pytest, pytest-cov, pytest-mock, responses |
| **Despliegue** | Render |

---

## 📝 Notas

- El carrito usa **localStorage** en el frontend y se sincroniza con la base de datos cuando el usuario inicia sesión
- Si no se configuran credenciales reales de Mercado Pago (`MP_ACCESS_TOKEN=TEST-123456789-abcdef`), los pagos se **simulan automáticamente** — ideal para desarrollo
- Las contraseñas se almacenan con **hash seguro** usando `werkzeug.security`
- La base de datos se crea automáticamente al iniciar la app (`db.create_all()` en `create_app`)
- Para desarrollo local con Mercado Pago real, se recomienda usar **ngrok** para exponer `localhost` con HTTPS
- En producción (Render), la app detecta automáticamente el proxy y configura HTTPS

---

## 📄 Licencia

MIT — ver archivo [LICENSE](LICENSE) para más detalles.
