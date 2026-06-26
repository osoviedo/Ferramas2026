# Explicacion del Codigo - Ferramas

Este documento resume como funciona el proyecto Flask en 4 bloques clave para presentacion: backend, frontend/UI, conversor de moneda y API de pago (Mercado Pago).

## 1) Backend (Flask + SQLAlchemy + logica de negocio)

**Archivo base:** `app/__init__.py`

- La app se crea con `create_app()`, carga configuracion y registra blueprints.
- Se inicializan `SQLAlchemy`, `LoginManager` y `CORS`.
- En Render se aplica `ProxyFix` para que las URLs externas usen `https` correctamente.
- Al iniciar, se crean tablas y se siembran datos iniciales (productos y usuarios demo).

**Flujo de carrito a pedido:** `app/views/carrito.py`

- El carrito se sincroniza entre frontend (localStorage) y BD (`Carrito`, `CarritoProducto`).
- En `POST /carrito/checkout` se:
  - valida carrito,
  - calcula subtotal y descuento del usuario,
  - crea `Pedido` y `PedidoProducto`,
  - deriva a transferencia o Mercado Pago.
- Si es Mercado Pago, redirige a `tienda.pago_iniciar`.

## 2) Frontend y UI (Jinja + JS vanilla + Bootstrap)

**Vista principal de pago:** `app/templates/checkout.html`

- Es una plantilla Jinja que muestra:
  - metodo de entrega (retiro/despacho),
  - metodo de pago (Mercado Pago/transferencia),
  - resumen del carrito.
- La UI usa Bootstrap + estilos custom del proyecto.
- El JS del template:
  - lee carrito desde `localStorage`,
  - recalcula subtotales y total en pantalla,
  - sincroniza items como `hidden input` antes de enviar el formulario.
- Estados visuales en la misma vista:
  - `exito`,
  - `pending_verificacion`,
  - `error_pago`.

## 3) Conversor de dinero (solo visual)

**Servicio de tasa:** `app/services/divisa_service.py`  
**Endpoint:** `GET /api/divisas` en `app/api/producto_api.py`  
**Consumo UI:** `checkout.html`

- El backend obtiene USD/EUR desde `mindicador.cl` con cache.
- Si falla la API externa, usa valores de respaldo (`dolar=950`, `euro=1050`).
- En checkout hay selector CLP/USD/EUR.
- Importante: la conversion es visual.  
  El cobro real y el pedido siguen en CLP.

## 4) API de pago (Mercado Pago) y retorno

**Servicio pago:** `app/services/pago_service.py`  
**Controlador web:** `app/views/tienda.py`  
**Webhook:** `POST /api/webhook/mercadopago` en `app/api/producto_api.py`

### Creacion de preferencia

- `PagoService.crear_preferencia(pedido)` construye:
  - `items`,
  - `external_reference` (id del pedido),
  - `back_urls` (success/failure/pending),
  - `notification_url` (webhook),
  - `auto_return = approved`.
- Para entorno de prueba prioriza `sandbox_init_point`.
- Si no hay link de pago, retorna error explicito para diagnostico.

### Redireccion y confirmacion

- `GET /pago/iniciar/<pedido_id>` redirige al `init_point`.
- `GET /pago/exito` y `GET /pago/error` intentan verificar estado real del pago.
- Si hay `payment_id`, se consulta a MP (`verificar_pago`) y:
  - si esta aprobado, confirma pedido,
  - si esta pendiente, muestra "procesando",
  - si falla/rechaza, muestra error.

### Webhook

- `POST /api/webhook/mercadopago` recibe notificaciones de MP.
- Verifica pago y confirma pedido cuando estado sea `approved`.
- Esto evita depender solo del redirect del navegador.

---

## Resumen rapido para exposicion

1. **Backend Flask** maneja autenticacion, carrito, pedidos y estados.
2. **Frontend/UI** usa Jinja + JS para experiencia de compra y resumen en tiempo real.
3. **Conversor** muestra CLP/USD/EUR solo visualmente, sin alterar el cobro real.
4. **Mercado Pago** se integra con preferencia, redirect de checkout y webhook de confirmacion.

