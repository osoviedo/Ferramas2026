# Texto final para Word 3.2.4 — Ferramas

## 1.1 Resumen ejecutivo

Ferramas es un e-commerce de ferretería desarrollado en Flask con API REST, SQLite y frontend Jinja2. Este plan detallado define la estrategia de pruebas para la evaluación académica: validar API REST, flujo carrito–checkout–pedido, autenticación y rendimiento. Se ejecutan 30 pruebas automatizadas con pytest (unitarias, integración, mock, aceptación, carga y estrés). Criterio de éxito: 30 passed y cobertura ≥ 55%.

## 1.2.1 Elementos de pruebas

Listado de todos los módulos, componentes o elementos que se van a probar. Si es de alto nivel, se listan las áreas funcionales (módulos o procesos que cubre el Testing), por otro lado, si es de un nivel detallado se listan los programas, unidades o módulos.

Elementos de Ferramas (nivel detallado):

- API REST: `app/api/producto_api.py` (/api/productos, /api/categorias, /api/divisas)
- Vistas: `app/views/tienda.py`, `carrito.py`, `auth.py`
- Servicios: AuthService, DivisaService, PagoService
- Modelos: Producto, Usuario, Carrito, Pedido
- Tests: carpeta `tests/` (30 casos)

## 1.2.2 Pruebas funcionales (agregar)

Pruebas de caja negra sobre HTTP: datos normales (productos válidos), límite (carrito vacío), borde e ilegales (login incorrecto, categoría 404).

## 1.2.3 Riesgos (tabla)

| N° | Riesgo | Gravedad | Acción |
|----|--------|----------|--------|
| 1 | API mindicador.cl caída | Baja | Mock + valores por defecto |
| 2 | Token Mercado Pago inválido | Media | Modo simulado TEST |
| 3 | Conflicto BD prueba | Baja | SQLite temporal en pytest |

## 3.1.4 Herramientas

Python 3.14, Flask, pytest, pytest-cov, unittest.mock, SQLite, Flask test client.

## 6.1 Criterios

**Entrada:** `pip install -r requirements.txt`, pytest disponible.  
**Salida:** 30 tests passed, cobertura ≥ 55%.  
**Suspensión:** MP real falla → modo simulado.
