"""
Criterios de aceptación (pruebas de aceptación automatizadas).

Cada test mapea a un caso CAxx del plan de pruebas Ferramas.
"""
import pytest

from app.models.producto import Producto


@pytest.mark.acceptance
class TestCriteriosAceptacion:
    """Historias de usuario / criterios Given-When-Then."""

    def test_CA01_cliente_ve_catalogo_con_precio_y_stock(self, client):
        """CA01: El cliente puede consultar productos con precio y stock."""
        r = client.get("/api/productos")
        assert r.status_code == 200
        producto = r.get_json()[0]
        assert producto["precio"] > 0
        assert producto["stock"] >= 0

    def test_CA02_cliente_filtra_por_categoria(self, client):
        """CA02: El catálogo filtra por categoría desde la URL."""
        r = client.get("/productos?categoria=fijaciones")
        assert r.status_code == 200
        assert b"Perno" in r.data or b"Tuerca" in r.data

    def test_CA03_cliente_agrega_producto_al_carrito(self, auth_client):
        """CA03: Usuario autenticado agrega ítem al carrito (API JSON)."""
        r = auth_client.post(
            "/carrito/agregar",
            json={"producto_id": 2, "cantidad": 1},
        )
        assert r.get_json()["ok"] is True

    def test_CA04_login_rechaza_credenciales_invalidas(self, client):
        """CA04: Sistema rechaza login con contraseña incorrecta."""
        r = client.post(
            "/login",
            data={"email": "cliente@ferramas.cl", "password": "wrong"},
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert b"incorrectos" in r.data.lower()

    def test_CA05_api_categorias_lista_todas_las_categorias(self, client, app):
        """CA05: API /api/categorias coincide con categorías en BD."""
        with app.app_context():
            bd_count = (
                Producto.query.with_entities(Producto.categoria).distinct().count()
            )
        api_cats = client.get("/api/categorias").get_json()
        assert len(api_cats) == bd_count

    def test_CA06_imagen_producto_accesible(self, client):
        """CA06: Imágenes de producto se sirven desde /static/."""
        r = client.get("/static/img/Productos/Martillo.jpg")
        assert r.status_code == 200
        assert r.mimetype.startswith("image")

    def test_CA07_webhook_mercadopago_acepta_test(self, client):
        """CA07: Endpoint webhook responde a notificación de prueba."""
        r = client.post(
            "/api/webhook/mercadopago",
            json={"action": "test"},
        )
        assert r.status_code == 200
        assert r.get_json().get("status") == "ok"
