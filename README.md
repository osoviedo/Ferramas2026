# Ferramas — E-commerce de Ferretería

Sistema e-commerce completo construido con Flask, SQLAlchemy, Bootstrap 5 y MariaDB.

## Estructura del proyecto

```
Ferramas2026/
├── backend/
│   ├── __init__.py          # Factory pattern, Flask-Login, SQLAlchemy
│   ├── config.py            # Variables de entorno y configuración
│   ├── models/
│   │   ├── usuario.py       # Usuario (UserMixin), roles: cliente/admin/vendedor/bodeguero/contador
│   │   ├── producto.py      # Producto (mapea tabla existente)
│   │   ├── pedido.py        # Pedido, PedidoProducto, Pago, Direccion
│   │   └── carrito.py       # Carrito, CarritoProducto
│   ├── services/
│   │   ├── auth_service.py  # Registro, login, hash de contraseñas
│   │   ├── pago_service.py  # Mercado Pago (real + simulado)
│   │   ├── divisa_service.py # mindicador.cl para USD/EUR con caché
│   │   └── email_service.py # Placeholder de notificaciones
│   ├── api/
│   │   └── producto_api.py  # API REST: /api/productos, /api/categorias, etc.
│   └── views/
│       ├── auth.py          # Login, registro, logout, perfil
│       ├── tienda.py        # Index, productos, checkout
│       ├── carrito.py       # Carrito CRUD, checkout → pedido
│       ├── vendedor.py      # Panel vendedor: aprobar/rechazar pedidos
│       ├── bodeguero.py     # Panel bodeguero: preparar/entregar pedidos
│       └── admin.py         # Panel admin: gestión de usuarios, reportes
├── frontend/
│   ├── static/
│   │   ├── styles.css       # Tema oscuro café #2c1a0e
│   │   └── img/Productos/   # Imágenes de productos
│   └── templates/
│       ├── base.html        # Layout con navbar, footer, flash messages
│       ├── index.html       # Hero + grid de 6 categorías
│       ├── productos.html   # Cards de productos, filtro por categoría, selector moneda
│       ├── carrito.html     # Tabla carrito localStorage, cantidades, total
│       ├── checkout.html    # Retiro/despacho, resumen, botón Mercado Pago
│       ├── login.html       # Formulario email + password
│       ├── registro.html    # Formulario nombre + email + password
│       ├── perfil.html      # Datos usuario + historial pedidos
│       ├── vendedor.html    # Tabla pedidos pendientes, aprobar/rechazar
│       ├── bodeguero.html   # Tabla órdenes, preparar/entregar
│       └── admin.html       # Stats, gestión usuarios, pedidos recientes
├── database/
│   └── schema.sql           # Tablas nuevas (usuarios, carrito, pedidos, etc.)
├── docs/
│   └── postman_collection.json  # Colección Postman v2.1
├── requirements.txt
├── run.py
├── .env.example
└── README.md
```

## Requisitos

- Python 3.9+
- MariaDB con base de datos `ferramas` y tabla `productos` ya poblada
- (Opcional) Cuenta de Mercado Pago para pagos reales

## Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/osoviedo/Ferramas2026
cd Ferramas2026

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores reales

# 4. Ejecutar schema.sql en MariaDB
# En MySQL/MariaDB CLI:
#   USE ferramas;
#   SOURCE database/schema.sql;

# 5. Ejecutar la aplicación
python run.py
```

## Configuración

Copiar `.env.example` a `.env` y editar:

| Variable | Descripción |
|---|---|
| `SECRET_KEY` | Llave secreta para sesiones Flask |
| `MP_ACCESS_TOKEN` | Access token de Mercado Pago (o dejar TEST para modo simulado) |
| `MP_PUBLIC_KEY` | Public key de Mercado Pago |
| `DATABASE_URL` | URL de conexión MariaDB |
| `DIVISA_CACHE_SEGUNDOS` | Tiempo de caché para tasas de cambio (default: 3600) |

## Endpoints principales

### API REST (pública)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/productos` | Lista todos los productos (query: `?convertir_a=USD`) |
| GET | `/api/productos/<id>` | Detalle de producto |
| GET | `/api/productos/categoria/<nombre>` | Productos por categoría |
| GET | `/api/categorias` | Lista de categorías únicas |

### Vistas web

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Landing page con grid de categorías |
| GET | `/productos` | Catálogo con filtros |
| GET/POST | `/login` | Inicio de sesión |
| GET/POST | `/registro` | Registro de cliente |
| GET | `/perfil` | Perfil e historial (requiere sesión) |
| GET/POST | `/carrito` | Gestión del carrito |
| GET/POST | `/checkout` | Checkout y pago |
| GET | `/vendedor` | Panel vendedor (rol: vendedor/admin) |
| GET | `/bodeguero` | Panel bodeguero (rol: bodeguero/admin) |
| GET | `/admin` | Panel administrador (rol: admin) |

## Roles

- **cliente**: Compra productos, ve su historial
- **vendedor**: Aprueba o rechaza pedidos pendientes
- **bodeguero**: Prepara y entrega pedidos aprobados
- **contador**: (definido en modelo, vistas futuras)
- **admin**: Gestión completa de usuarios y reportes

## Integraciones

1. **API REST propia** — endpoints de productos
2. **Mercado Pago** — pasarela de pago (SDK oficial, modo prueba automático sin credenciales)
3. **mindicador.cl** — API de cambio de divisas Banco Central para USD/EUR

## Notas

- El carrito usa localStorage en frontend + sincronización con BD cuando hay sesión
- Si no se configuran credenciales reales de Mercado Pago, los pagos se simulan automáticamente
- Las contraseñas se almacenan con hash (werkzeug.security)
- Los endpoints originales (`/productos`, `/categorias`) ahora están bajo `/api/` y usan SQLAlchemy
