# Guía demo exposición Ferramas (~5 minutos)

**Equipo:** Jose Larenas / Oscar Oviedo  
**Proyecto:** Ferramas — e-commerce Flask  
**URL base:** http://127.0.0.1:5000

Esta guía complementa `python -m pytest -v` con una demo **visual** en navegador (F12).  
Cada paso indica qué decir y a qué test automatizado corresponde.

---

## Antes de entrar al aula (2 minutos)

Abre **dos terminales** en la carpeta del proyecto:

```powershell
cd C:\Users\Jose\Desktop\Ferramas2026-main
```

**Terminal 1 — pruebas (opcional, si el docente pide evidencia):**

```powershell
python -m pytest -v
```

Debe mostrar **30 passed**.

**Terminal 2 — servidor (obligatorio para la demo):**

```powershell
python run.py
```

Espera el mensaje `Running on http://127.0.0.1:5000`.

Abre Chrome o Edge y deja **F12** listo (pestaña **Network / Red**).

---

## Guión minuto a minuto

### Min 0:00 — Intro (15 s)

**Decir:**  
*"Ferramas es un e-commerce en Flask con API REST, SQLite y Mercado Pago sandbox. Tenemos 30 pruebas automatizadas con pytest y ahora mostramos el mismo comportamiento en vivo con el navegador y las herramientas de desarrollador."*

---

### Min 0:15 — CA01 + API (1 min)

**Hacer:**

1. Nueva pestaña → `http://127.0.0.1:5000/api/productos`
2. El navegador muestra JSON con productos (id, nombre, precio, stock, categoria).

**Decir:**  
*"CA01: el cliente consulta el catálogo. La API devuelve HTTP 200 y cada producto tiene precio y stock. Esto lo valida el test `test_CA01_cliente_ve_catalogo_con_precio_y_stock`."*

**Extra visual (Consola F12):**

1. Ir a `http://127.0.0.1:5000/productos`
2. F12 → pestaña **Console**
3. Pegar y Enter:

```javascript
fetch('/api/productos').then(r => r.json()).then(d => console.table(d.slice(0, 5)))
```

**Decir:**  
*"Misma API que consume el frontend; la tabla en consola es la prueba de integración CA-INT-01 en vivo."*

---

### Min 1:15 — CA02 filtro categoría (45 s)

**Hacer:**

1. Ir a `http://127.0.0.1:5000/productos?categoria=fijaciones`
2. Mostrar que solo aparecen productos de esa categoría (Perno, Tuerca, etc.).

**Decir:**  
*"CA02: filtro por categoría desde la URL. El test `test_CA02_cliente_filtra_por_categoria` verifica que la página responde 200 y muestra productos de fijaciones."*

---

### Min 2:00 — CA05 divisas + Network (1 min)

**Hacer:**

1. Ir a `http://127.0.0.1:5000/productos`
2. F12 → **Network** → marcar **Preserve log**
3. En el selector de moneda de la página, elegir **USD**
4. En Network, buscar la petición a `productos?convertir_a=USD` o recargar con  
   `http://127.0.0.1:5000/productos?convertir_a=USD`
5. Clic en la petición → pestaña **Response** → mostrar precios convertidos.

**Decir:**  
*"Integración con mindicador.cl vía DivisaService. En pruebas usamos mock; aquí la conversión es real o con caché. CA-INT-03 y la API con `?convertir_a=USD` lo cubren en pytest."*

**Atajo API (segunda pestaña):**

`http://127.0.0.1:5000/api/productos?convertir_a=USD`  
Mostrar campo `"moneda": "USD"` en el JSON.

---

### Min 3:00 — CA03 carrito + Network (1 min 30 s)

**Hacer:**

1. En `/productos`, clic **Agregar al carrito** en cualquier producto.
2. F12 → **Network** → filtrar **Fetch/XHR**
3. Clic en `agregar` → mostrar:
   - **Status:** 200
   - **Response:** `{"ok": true}` (o similar)

4. F12 → **Application** → **Local Storage** → `http://127.0.0.1:5000`
5. Mostrar la clave del carrito en localStorage.

**Decir:**  
*"CA03: el carrito es híbrido — localStorage en el navegador y persistencia en SQLite cuando el usuario está logueado. El POST a `/carrito/agregar` es lo que prueba `test_CA03_cliente_agrega_producto_al_carrito`."*

6. Clic en **Carrito** en el navbar → verificar que el producto aparece.

---

### Min 4:30 — CA04 login + cierre (30 s)

**Hacer:**

1. Ir a `http://127.0.0.1:5000/login`
2. Intentar login con contraseña **incorrecta** (ej. `wrong`)
3. Mostrar mensaje de error en pantalla.

**Decir:**  
*"CA04: credenciales inválidas son rechazadas. Test `test_CA04_login_rechaza_credenciales_invalidas`."*

4. Login correcto: `cliente@ferramas.cl` / `cliente123`
5. (Opcional 10 s) Ir a checkout si hay tiempo.

**Decir cierre:**  
*"Además tenemos CA05 categorías, CA06 imágenes estáticas y CA07 webhook Mercado Pago — los 30 tests pasan con `pytest -v`. Los informes 3.1.4 a 3.4.4 documentan integración, plan, defectos e implantación."*

---

## Bonus si preguntan (30 s cada uno)

### CA05 — Categorías API

Abrir: `http://127.0.0.1:5000/api/categorias`  
**Decir:** *"Lista alineada con la base de datos; test CA05."*

### CA06 — Imagen estática

Abrir: `http://127.0.0.1:5000/static/img/Productos/Martillo.jpg`  
**Decir:** *"Assets servidos por Flask; test CA06."*

### CA07 — Webhook (Consola, con servidor corriendo)

F12 → Console:

```javascript
fetch('/api/webhook/mercadopago', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({action: 'test'})
}).then(r => r.json()).then(console.log)
```

Esperado: `{status: "ok"}`  
**Decir:** *"Endpoint de integración Mercado Pago; test CA07."*

### Reporte HTML de pytest

```powershell
python -m pytest -v --html=docs/reporte_pruebas.html --self-contained-html
```

Abrir `docs\reporte_pruebas.html` en el navegador.

### Cobertura visual

```powershell
python -m pytest --cov=app --cov-report=html
```

Abrir `htmlcov\index.html`.

---

## Qué mirar en F12 (cheat sheet)

| Pestaña | Cuándo usarla | Qué mostrar |
|---------|---------------|-------------|
| **Network** | Agregar carrito, cambiar moneda | POST/GET, status 200, JSON |
| **Console** | API rápida | `fetch(...)` + `console.table` |
| **Application** | Carrito | Local Storage |
| **Elements** | UI | Precios cambiados al seleccionar USD |

**Tip:** en Network, activa **Preserve log** para que no se borren las peticiones al cambiar de página.

---

## Errores comunes en la demo

| Problema | Causa | Solución |
|----------|-------|----------|
| Página en blanco / fetch failed | No hay servidor | `python run.py` en terminal 2 |
| Abriste HTML suelto (`file://`) | Sin Flask | Usar siempre `http://127.0.0.1:5000` |
| Network vacío | F12 abierto después del clic | Recargar página o repetir acción con F12 abierto |
| Mercado Pago falla | `.env` sin token | Usar transferencia en checkout o verificar `.env` |

---

## Usuarios de prueba

| Rol | Email | Contraseña |
|-----|-------|------------|
| Cliente | cliente@ferramas.cl | cliente123 |
| Admin | admin@ferramas.cl | admin123 |
| Vendedor | vendedor@ferramas.cl | vendedor123 |
| Bodeguero | bodeguero@ferramas.cl | bodeguero123 |

---

## Checklist el día D

- [ ] `.env` presente (MP sandbox)
- [ ] `pip install -r requirements.txt`
- [ ] Terminal 1: `python -m pytest -v` → 30 passed
- [ ] Terminal 2: `python run.py`
- [ ] 4 informes en `Desktop\test\`
- [ ] Navegador en `127.0.0.1:5000` (no archivos sueltos)
- [ ] F12 → Network + Preserve log
