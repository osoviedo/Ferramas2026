# Plan de Pruebas — Ferramas (copiar a Word 3.2.4)

**Proyecto:** Ferramas E-commerce | **Fecha:** 26/06/2026 | **Versión:** 1.0

## 1. Introducción

Ferramas es un e-commerce Flask con API REST y SQLite. Este plan cubre pruebas unitarias, integración, mock, aceptación, carga y estrés antes de la evaluación.

**Alcance:** API (`/api/productos`, `/api/categorias`), carrito, checkout, auth, servicios DivisaService y PagoService.

## 3. Estrategia — Tipos de pruebas

| Tipo | Carpeta | Comando |
|------|---------|---------|
| Unitarias | tests/unit/ | python -m pytest -m unit -v |
| Integración | tests/integration/ | python -m pytest -m integration -v |
| Mock | tests/unit/test_services_mock.py | python -m pytest -m mock -v |
| Aceptación CA01–CA07 | tests/acceptance/ | python -m pytest -m acceptance -v |
| Carga | tests/load/ | python -m pytest -m load -v |
| Estrés | tests/stress/ | python -m pytest -m stress -v |

**Herramientas:** pytest, pytest-cov, Flask test client, unittest.mock. Postman es opcional.

**Criterio de salida:** 30 tests passed, cobertura ~56%.

## Demo API sin Postman

Navegador: http://127.0.0.1:5000/api/productos

PowerShell: `Invoke-RestMethod http://127.0.0.1:5000/api/productos`
