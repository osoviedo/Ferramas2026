# Ferramas — E-commerce de Ferretería

Sistema e-commerce completo construido con Flask, SQLAlchemy, Bootstrap 5 y SQLite.

## Estructura del proyecto

```
Ferramas2026/
├── app/
│   ├── __init__.py          # Factory pattern, Flask-Login, SQLAlchemy
│   ├── config.py            # Variables de entorno y configuración
│   ├── models/              # Usuario, Producto, Pedido, Carrito, etc.
│   ├── services/            # Auth, pagos (Mercado Pago), divisas, email
│   ├── api/
│   │   └── producto_api.py  # API REST: /api/productos, /api/categorias, etc.
│   ├── views/               # Rutas web: tienda, carrito, auth, paneles
│   ├── static/
│   │   ├── styles.css
│   │   └── img/Productos/   # Imágenes de productos
│   └── templates/           # HTML Jinja2 (index, productos, checkout, ...)
├── database/
│   └── schema.sql
├── docs/
│   └── postman_collection.json
├── requirements.txt
├── run.py                   # Punto de entrada: python run.py
├── .env.example
└── README.md
```

## Requisitos

- Python 3.9+
- (Opcional) Cuenta de Mercado Pago sandbox para pagos de prueba

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

# 4. Ejecutar la aplicación (crea ferramas.db y datos de prueba automáticamente)
python run.py
```

## Configuración

Copiar `.env.example` a `.env` y editar:

| Variable | Descripción |
|---|---|
| `SECRET_KEY` | Llave secreta para sesiones Flask |
| `MP_ACCESS_TOKEN` | Access token de Mercado Pago (o dejar TEST para modo simulado) |
| `MP_PUBLIC_KEY` | Public key de Mercado Pago |
| `DATABASE_URL` | URL de conexión (default: `sqlite:///ferramas.db`) |
| `DIVISA_CACHE_SEGUNDOS` | Tiempo de caché para tasas de cambio (default: 3600) |

## Endpoints principales

### API REST (pública)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/productos` | Lista todos los productos (query: `?convertir_a=USD`) |
| GET | `/api/productos/<id>` | Detalle de producto |
| GET | `/api/productos/categoria/<nombre>` | Productos por categoría |
| GET | `/api/categorias` | Lista de categorías únicas |
| GET | `/api/divisas` | Tasas USD/EUR (mindicador.cl) |

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

## Pruebas (evaluación)

```bash
pip install -r requirements.txt
python -m pytest -v                    # todos los tests
python -m pytest -m unit -v            # unitarios
python -m pytest -m integration -v     # integración
python -m pytest -m mock -v            # con mocks
python -m pytest -m acceptance -v      # criterios de aceptación
python -m pytest -m load -v            # carga
python -m pytest -m stress -v          # estrés
```

Detalle de casos CA01–CA07 y plantillas del curso: `docs/CASOS_PRUEBA_FERRAMAS.md`
