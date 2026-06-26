# Casos de prueba Ferramas — Guía para plantillas del curso

Proyecto: **Ferramas** | Autor: Fitzroyal | Fecha: 26/06/2026

Este documento complementa las plantillas de `Desktop/TEST/` con casos reales del proyecto.
Los tests automatizados están en `tests/` y se ejecutan con `python -m pytest`.

---

## 1. Resumen por tipo de prueba

| Tipo | Carpeta | Herramienta | Comando |
|------|---------|-------------|---------|
| Unitarios | `tests/unit/` | pytest | `python -m pytest -m unit` |
| Integración | `tests/integration/` | pytest + Flask test client | `python -m pytest -m integration` |
| Mock | `tests/unit/test_services_mock.py` | unittest.mock | `python -m pytest -m mock` |
| Criterios aceptación | `tests/acceptance/` | pytest (CA01–CA07) | `python -m pytest -m acceptance` |
| Carga | `tests/load/` | pytest | `python -m pytest -m load` |
| Estrés | `tests/stress/` | pytest | `python -m pytest -m stress` |
| **Todos** | `tests/` | pytest | `python -m pytest -v` |

---

## 2. Casos de integración (plantilla 3.1.4)

Copiar en Excel **3.1.4 Plantilla Casos de prueba Integracion.xlsx**:

### CA-INT-01 — API productos ↔ Base de datos

| Campo | Valor |
|-------|-------|
| Componente | API REST — SQLAlchemy |
| Descripción | GET /api/productos devuelve JSON desde SQLite |
| Prerrequisitos | `python run.py` o pytest con fixture `client` |

| Paso | Descripción | Entrada | Salida esperada | OK |
|------|-------------|---------|-----------------|-----|
| 1 | Ejecutar test | `pytest tests/integration/test_api_and_flows.py::TestApiProductos::test_get_api_productos_retorna_lista_json` | HTTP 200, lista JSON | |
| 2 | Verificar campos | — | id, nombre, precio, stock, categoria | |

### CA-INT-02 — Carrito ↔ Checkout ↔ Pedido

| Campo | Valor |
|-------|-------|
| Componente | views/carrito — models/pedido |
| Descripción | Usuario logueado agrega producto y crea pedido pendiente |

| Paso | Descripción | Entrada | Salida esperada | OK |
|------|-------------|---------|-----------------|-----|
| 1 | Login | cliente@ferramas.cl / cliente123 | Sesión activa | |
| 2 | POST /carrito/agregar | `{"producto_id":1,"cantidad":2}` | `{"ok":true}` | |
| 3 | POST /carrito/checkout | modo_entrega=retiro | Redirect /pago/iniciar/{id} | |
| 4 | Verificar BD | pedido último | estado=pendiente, total>0 | |

### CA-INT-03 — API divisas ↔ mindicador.cl (mock)

| Campo | Valor |
|-------|-------|
| Componente | DivisaService — API externa |
| Descripción | Conversión USD con tasas mockeadas |

| Paso | Descripción | Entrada | Salida esperada | OK |
|------|-------------|---------|-----------------|-----|
| 1 | Mock requests.get | dolar=1000 | — | |
| 2 | GET /api/productos?convertir_a=USD | — | moneda=USD, precio convertido | |

---

## 3. Criterios de aceptación (CA01–CA07)

| ID | Criterio | Test automatizado |
|----|----------|-------------------|
| CA01 | Cliente ve catálogo con precio y stock | `test_CA01_cliente_ve_catalogo_con_precio_y_stock` |
| CA02 | Filtro por categoría en web | `test_CA02_cliente_filtra_por_categoria` |
| CA03 | Agregar al carrito autenticado | `test_CA03_cliente_agrega_producto_al_carrito` |
| CA04 | Rechazo login inválido | `test_CA04_login_rechaza_credenciales_invalidas` |
| CA05 | API categorías = BD | `test_CA05_api_categorias_lista_todas_las_categorias` |
| CA06 | Imágenes en /static/ | `test_CA06_imagen_producto_accesible` |
| CA07 | Webhook MP acepta test | `test_CA07_webhook_mercadopago_acepta_test` |

---

## 4. Plan de pruebas (plantilla 3.2.4) — extracto Ferramas

### 3.1 Tipos de pruebas aplicados

- **Funcionales (caja negra):** acceptance + integration
- **Unitarias:** models, AuthService, servicios aislados
- **Mock:** mindicador.cl y Mercado Pago SDK sin red real
- **Rendimiento:** 50 req secuenciales (`load`)
- **Estrés:** 200 req + 90 consultas por categoría (`stress`)

### Ambiente

- Python 3.9+, Flask, SQLite de prueba (fixture `tmp_path`)
- Variables: `SECRET_KEY`, `MP_ACCESS_TOKEN=TEST-...` (modo simulado)

### Herramientas

- pytest, pytest-cov
- unittest.mock
- Flask test client

---

## 5. Registro de defectos (plantilla 3.3.4) — ejemplo

| ID | Caso | Módulo | Descripción | Tipo | Severidad | Estado |
|----|------|--------|-------------|------|-----------|--------|
| — | — | — | Sin defectos abiertos tras suite 26/06/2026 | — | — | Cerrado |

*(Completar si falla un test manual en evaluación.)*

---

## 6. Ejecución rápida para la evaluación

```bash
pip install -r requirements.txt
python -m pytest -v --tb=short
python -m pytest -v --cov=app --cov-report=term-missing
```

Demostración en vivo:

1. `python run.py` → http://127.0.0.1:5000
2. Postman: GET `/api/productos`
3. Terminal: `python -m pytest -m acceptance -v`
