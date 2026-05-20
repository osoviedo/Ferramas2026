# Guía: Cómo Funciona Mercado Pago en Ferramas

## 1. ¿Qué es Mercado Pago?

**Mercado Pago** es una plataforma de pagos digital de Mercado Libre que permite:
- Procesar pagos de tarjetas de crédito/débito
- Transferencias bancarias
- Billeteras digitales
- Funciona en Argentina, Brasil, Chile, Colombia, México, Perú, Uruguay, Venezuela

En tu proyecto, Mercado Pago es la **pasarela de pago** que maneja las transacciones monetarias.

---

## 2. Conceptos Clave

### **A. Access Token (Credencial)**
Es una clave secreta que identifica tu cuenta de Mercado Pago.

Ubicación en tu proyecto:
```bash
.env
├── MP_ACCESS_TOKEN=APP_USR-756277913881318...  # Token real (producción)
└── MP_PUBLIC_KEY=APP_USR-3966ff91-0170...      # Clave pública
```

El SDK de Mercado Pago se inicializa con este token:
```python
# En app/services/pago_service.py línea 25
sdk = mercadopago.SDK(current_app.config.get('MP_ACCESS_TOKEN', ''))
```

### **B. Preferencia**
Es un "carrito de compra" que Mercado Pago reconoce. Contiene:
- Lista de productos (nombre, cantidad, precio)
- Referencia externa (tu ID de pedido)
- URLs de retorno (qué hacer después del pago)

### **C. init_point**
Es la URL de pago que genera Mercado Pago. El usuario es redirigido a esta URL para pagar.

Ejemplo:
```
https://www.mercadopago.com/checkout/v1/redirect?preference-id=12345678
```

---

## 3. Flujo Completo de Pago en Ferramas

```
┌─────────────────────────────────────────────────────────────────────┐
│ FLUJO DE COMPRA Y PAGO EN FERRAMAS                                   │
└─────────────────────────────────────────────────────────────────────┘

1. USUARIO EN TIENDA
   ┌──────────────┐
   │ Navega por   │
   │ productos    │
   │ en localhost │
   └──────────────┘
          ↓
   (GET /productos)
   
   
2. AGREGA AL CARRITO
   ┌──────────────────────┐
   │ POST /carrito/agregar│
   │ {producto_id, cant}  │
   └──────────────────────┘
          ↓
   Almacena en BD (tabla CarritoProducto)


3. VA AL CHECKOUT
   ┌──────────────┐
   │ GET /checkout│
   └──────────────┘
          ↓
   Muestra resumen del carrito


4. CONFIRMA COMPRA
   ┌────────────────────────┐
   │ POST /carrito/checkout │
   │ (nombre, email, opción)│
   └────────────────────────┘
          ↓
   Flask CREA UN PEDIDO en BD
   (tabla Pedido con estado='pendiente')


5. INICIA PAGO → ⭐ MERCADO PAGO ENTRA EN ACCIÓN ⭐
   ┌─────────────────────────────┐
   │ GET /pago/iniciar/<pedido_id>│
   └─────────────────────────────┘
          ↓
   Flask LLAMA A: PagoService.crear_preferencia()
          ↓
   
   ┌────────────────────────────────────────────────────┐
   │ Python SDK de Mercado Pago se ejecuta:              │
   │ sdk = mercadopago.SDK(MP_ACCESS_TOKEN)              │
   │ sdk.preference().create(preference_data)            │
   └────────────────────────────────────────────────────┘
          ↓
   Mercado Pago RETORNA: init_point (URL de pago)
          ↓
   Flask REDIRIGE al usuario a esa URL:
   >>> redirect('https://www.mercadopago.com/...')
   

6. USUARIO PAGA EN MERCADO PAGO
   ┌──────────────────────────────────┐
   │ Usuario en www.mercadopago.com   │
   │ Ingresa tarjeta / datos           │
   │ ✓ Pago APROBADO                   │
   └──────────────────────────────────┘
   
   Mercado Pago internamente:
   ├─ Procesa la transacción
   ├─ Valida tarjeta
   ├─ Cobra dinero
   └─ Si TODO OK → redirección


7. MERCADO PAGO REDIRIGE DE VUELTA
   ┌──────────────────────────────────────────────┐
   │ Mercado Pago redirige a la URL de éxito que  │
   │ configuramos en la preferencia:               │
   │                                               │
   │ back_urls: {                                 │
   │   'success': '/pago/exito?pedido_id=14'     │
   │   'failure': '/pago/error?pedido_id=14'     │
   │ }                                             │
   └──────────────────────────────────────────────┘
          ↓
   Flask RECIBE en: GET /pago/exito?pedido_id=14


8. CONFIRMACIÓN LOCAL EN FERRAMAS
   ┌────────────────────────────────────┐
   │ PagoService.confirmar_pago(pedido)  │
   │ ├─ Crea registro Pago en BD         │
   │ ├─ Marca Pedido como 'aprobado'    │
   │ ├─ DESCUENTA STOCK de productos    │
   │ └─ Vacía carrito del usuario        │
   └────────────────────────────────────┘
   
   ✓ Pago procesado completamente


9. USUARIO VE CONFIRMACIÓN
   ┌────────────────────────────────┐
   │ Página de éxito con datos del   │
   │ pedido (número, total, detalles)│
   └────────────────────────────────┘
```

---

## 4. Código Detallado: Paso a Paso

### **Paso 5: Crear Preferencia**

```python
# app/services/pago_service.py - líneas 18-47

@staticmethod
def crear_preferencia(pedido):
    """Crea preferencia en Mercado Pago (o simulada)."""
    
    # ✓ Verificar si estamos en modo TEST (sin credenciales reales)
    if PagoService._es_modo_simulado():
        return PagoService._preferencia_simulada(pedido)
    
    # INICIALIZAR SDK DE MERCADO PAGO
    sdk = mercadopago.SDK(current_app.config.get('MP_ACCESS_TOKEN', ''))
    # ↑ Pasa el token de autenticación
    
    
    # CONSTRUIR LISTA DE ITEMS (productos del pedido)
    items = []
    for pp in pedido.productos:  # pp = PedidoProducto
        items.append({
            'title': pp.producto.nombre,        # ej: "Martillo"
            'quantity': pp.cantidad,            # ej: 2
            'unit_price': float(pp.precio_unitario),  # ej: 8500.00
        })
    
    # items = [
    #   {'title': 'Martillo', 'quantity': 2, 'unit_price': 8500.0},
    #   {'title': 'Casco', 'quantity': 1, 'unit_price': 12000.0}
    # ]
    
    
    # CONSTRUIR PREFERENCIA
    preference_data = {
        'items': items,                                    # ↑ Productos
        'external_reference': str(pedido.id),  # ej: "14" (ID tuyo)
        
        # URLs DE RETORNO (qué hacer después del pago)
        'back_urls': {
            'success': url_for('tienda.pago_exito', 
                               pedido_id=pedido.id, 
                               _external=True),
            # Ej: http://localhost:5000/pago/exito?pedido_id=14
            
            'failure': url_for('tienda.pago_error', 
                               pedido_id=pedido.id, 
                               _external=True),
            # Ej: http://localhost:5000/pago/error?pedido_id=14
            
            'pending': url_for('tienda.pago_error', 
                               pedido_id=pedido.id, 
                               _external=True),
            # Pago pendiente (transferencia, etc)
        },
        'auto_return': 'approved',  # Redirigir automáticamente si aprobado
    }
    
    # ENVIAR A MERCADO PAGO
    try:
        preference_response = sdk.preference().create(preference_data)
        # ↑ Llamada HTTP: POST https://api.mercadopago.com/checkout/preferences
        
        preference = preference_response['response']
        
        # Mercado Pago retorna algo como:
        # {
        #   'id': '12345678-1234-...',
        #   'init_point': 'https://www.mercadopago.com/checkout/v1/redirect?...',
        #   ...
        # }
        
        return {'init_point': preference['init_point']}
        
    except Exception:
        # Si falla → modo simulado como fallback
        return PagoService._preferencia_simulada(pedido)
```

---

## 5. ¿Cómo Funciona en Modo Simulado vs Real?

### **MODO SIMULADO** (SIN credenciales reales)

```python
# Cuando no hay token válido, redirige directamente a /pago/exito

@staticmethod
def _preferencia_simulada(pedido):
    return {
        'init_point': url_for('tienda.pago_exito', 
                               pedido_id=pedido.id),
        # NO va a Mercado Pago, 
        # va directo a tu localhost /pago/exito
        'simulado': True,
    }
```

**Uso:** Desarrollo local sin tener que procesar pagos reales.

---

### **MODO REAL** (CON credenciales válidas)

```python
# Cuando tienes MP_ACCESS_TOKEN real:
# 1. Envía datos a API Mercado Pago
# 2. Mercado Pago genera URL de pago
# 3. Usuario paga REALMENTE con tarjeta
# 4. Mercado Pago te notifica via webhook o redirige
```

---

## 6. Configuración: Variables de Entorno

```bash
# .env (archivo que ya existe en tu proyecto)

# Token de acceso (credencial de tu cuenta Mercado Pago)
MP_ACCESS_TOKEN=APP_USR-756277913881318-051316-...

# Clave pública (para JavaScript en frontend, si lo necesitas)
MP_PUBLIC_KEY=APP_USR-3966ff91-0170-...

# Base de datos
DATABASE_URL=sqlite:///ferramas.db
```

### **Cómo obtener tus propias credenciales:**

1. Ir a [https://www.mercadopago.com.ar/developers/panel](https://www.mercadopago.com.ar/developers/panel)
2. Crear una cuenta de desarrollador (es gratis)
3. Ir a "Credenciales"
4. Copiar **Access Token** (producción o prueba)
5. Pegarlo en tu `.env` como `MP_ACCESS_TOKEN=...`

---

## 7. Webhook (Notificación de Pago)

Mercado Pago **también puede notificar** a tu servidor cuando ocurre un pago (por si el usuario nunca vuelve de la redirección).

```python
# app/api/producto_api.py - líneas 67-104

@api_bp.route('/api/webhook/mercadopago', methods=['POST'])
def webhook_mercadopago():
    """Mercado Pago nos envía JSON cuando hay un pago."""
    data = request.get_json()
    
    # Mercado Pago envía algo como:
    # {
    #   'action': 'payment.created' o 'payment.updated',
    #   'data': {
    #     'id': 'ID_TRANSACCION',
    #   },
    #   'external_reference': 'ID_PEDIDO'
    # }
    
    if data.get('action') == 'payment.approved':
        # → Procesar pago confirmado
        PagoService.procesar_webhook(data)
    
    return jsonify({'status': 'received'}), 200
```

**Uso:** Si quieres procesar pagos sin redirecciones, puedes habilitar webhooks.

---

## 8. Tabla de Estados del Pago

| Estado | Significado | Acción |
|--------|------------|--------|
| `pendiente` | Pedido creado, esperando pago | Usuario en checkout |
| `aprobado` | Pago procesado OK | Descontar stock, vaciar carrito |
| `cancelado` | Usuario canceló o pago falló | Mantener carrito para reintentar |
| `rechazado` | Tarjeta rechazada o error | Mostrar error, carrito intacto |

---

## 9. Diagrama de Bases de Datos

```
Tabla: pedidos
┌─────────────────────────────┐
│ id | usuario_id | estado    │
├─────────────────────────────┤
│ 14 | 5          | aprobado  │ ← Cambió de 'pendiente' a 'aprobado'
└─────────────────────────────┘

Tabla: pagos (se crea al confirmar)
┌─────────────────────────────────────────┐
│ id | pedido_id | metodo | estado        │
├─────────────────────────────────────────┤
│ 3  | 14        | mercadopago | aprobado │
│    │           |        | transaccion_id│
│    │           │       │ SIM-14-aprobado│
└─────────────────────────────────────────┘

Tabla: productos (STOCK SE DESCUENTA)
┌──────────────────────────┐
│ id | nombre | stock      │
├──────────────────────────┤
│ 1  | Martillo | 48 ← 50 - 2 │
│ 5  | Casco    | 29 ← 30 - 1 │
└──────────────────────────┘

Tabla: carrito_productos (SE VACÍA)
┌─────────────────────┐
│ id | carrito_id | ... │
├─────────────────────┤
│ (vacío)             │ ← Se elimina
└─────────────────────┘
```

---

## 10. Ejemplo Real: Flujo Completo

### **Inicio**
- Usuario: José
- Carrito: 2 Martillos ($8,500 c/u) + 1 Casco ($12,000)
- Total: $29,000 CLP

### **Acciones**
1. **GET /checkout** → Ve resumen
2. **POST /carrito/checkout** → Se crea Pedido(id=14, estado='pendiente')
3. **GET /pago/iniciar/14** → 
   - Llama a `PagoService.crear_preferencia(pedido14)`
   - SDK envía a Mercado Pago:
     ```json
     {
       "items": [
         {"title": "Martillo", "quantity": 2, "unit_price": 8500},
         {"title": "Casco", "quantity": 1, "unit_price": 12000}
       ],
       "external_reference": "14",
       "back_urls": {
         "success": "http://localhost:5000/pago/exito?pedido_id=14"
       }
     }
     ```
   - Mercado Pago retorna `init_point`: `https://www.mercadopago.com/checkout/v1/redirect?preference-id=98765432`
   - Redirige a José a esa URL
4. **José paga en Mercado Pago** → ✓ Aprobado
5. **Mercado Pago redirige de vuelta** → GET `/pago/exito?pedido_id=14`
6. **Backend procesa confirmación**:
   - Crea registro `Pago(pedido_id=14, estado='aprobado')`
   - Actualiza `Pedido(estado='aprobado')`
   - **Descuenta stock**:
     - Martillo: 50 → 48
     - Casco: 30 → 29
   - **Vacía carrito**
7. **José ve** → ✓ "¡Pago procesado! Tu pedido #14 está confirmado"
8. **Backend notifica** → Vendedor puede ver pedido nuevo en panel

---

## 11. Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `NameError: access_token is not defined` | Código antiguo | ✓ Ya está arreglado en tu proyecto |
| `Mercado Pago API error 401` | Token inválido | Verificar `.env` con token real |
| `TypeError: cannot access...` | Token vacío | Usar modo simulado o agregar token |
| `Webhook no se ejecuta` | URL no registrada en MP | Configurar webhook URL en panel MP |

---

## 12. Código Clave en Tu Proyecto

| Archivo | Función | Qué hace |
|---------|---------|----------|
| `app/services/pago_service.py` | `crear_preferencia()` | Genera URL de pago |
| `app/services/pago_service.py` | `confirmar_pago()` | Procesa pago confirmado |
| `app/views/tienda.py` | `pago_iniciar()` | Inicia el flujo (línea 65) |
| `app/views/tienda.py` | `pago_exito()` | Maneja retorno exitoso |
| `app/views/tienda.py` | `pago_error()` | Maneja error o cancelación |
| `app/api/producto_api.py` | `webhook_mercadopago()` | Recibe notificaciones MP |

---

## 13. Resumen Rápido

**¿Cómo funciona Mercado Pago en Ferramas?**

1. **Usuario compra** → Se crea Pedido con estado='pendiente'
2. **Pasa a pago** → Tu backend llama SDK Mercado Pago
3. **SDK genera URL** → Mercado Pago crea sesión de pago
4. **Usuario redirigido** → Va a www.mercadopago.com
5. **Usuario paga** → Ingresa tarjeta/transferencia
6. **MP redirige de vuelta** → A tu `back_urls['success']`
7. **Backend confirma** → Descuenta stock, vacía carrito, cambia estado
8. **Usuario ve éxito** → Recibe confirmación con número de pedido

**En desarrollo (modo simulado):** Se salta Mercado Pago y va directo a /pago/exito.

---

*Guía creada: 15 de Mayo, 2026*
