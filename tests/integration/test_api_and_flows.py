"""Pruebas de integración: API REST + flujos entre módulos."""
import pytest

from app.models.producto import Producto


@pytest.mark.integration
class TestApiProductos:
    def test_get_api_productos_retorna_lista_json(self, client):
        r = client.get("/api/productos")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "nombre" in data[0]
        assert "precio" in data[0]

    def test_get_api_productos_por_categoria(self, client):
        r = client.get("/api/productos/categoria/herramientas-manuales")
        assert r.status_code == 200
        data = r.get_json()
        assert all("herramientas manuales" in p["categoria"].lower() for p in data)

    def test_get_api_categorias_distintas(self, client):
        r = client.get("/api/categorias")
        assert r.status_code == 200
        categorias = r.get_json()
        assert len(categorias) == len(set(categorias))

    def test_categoria_inexistente_retorna_404(self, client):
        r = client.get("/api/productos/categoria/categoria-falsa-xyz")
        assert r.status_code == 404

    @pytest.mark.mock
    def test_api_productos_conversion_usd(self, mocker, client):
        mock_ds_class = mocker.patch("app.api.producto_api.DivisaService")
        mock_ds_class.return_value.obtener_divisas.return_value = {
            "dolar": 1000,
            "euro": 1100,
        }
        r = client.get("/api/productos?convertir_a=USD")
        assert r.status_code == 200
        item = r.get_json()[0]
        assert item["moneda"] == "USD"
        assert "precio_original" in item


@pytest.mark.integration
class TestFlujoCarrito:
    def test_agregar_producto_al_carrito_json(self, auth_client, app):
        with app.app_context():
            stock_inicial = Producto.query.get(1).stock
        r = auth_client.post(
            "/carrito/agregar",
            json={"producto_id": 1, "cantidad": 1},
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data["ok"] is True
        assert data["nombre"] == "Martillo"
        assert data["stock"] == stock_inicial - 1
        with app.app_context():
            assert Producto.query.get(1).stock == stock_inicial - 1

    def test_checkout_crea_pedido_pendiente(self, auth_client, app):
        auth_client.post("/carrito/agregar", json={"producto_id": 1, "cantidad": 2})
        r = auth_client.post(
            "/carrito/checkout",
            data={
                "modo_entrega": "retiro",
                "metodo_pago": "mercadopago",
                "sucursal": "Sucursal Central",
            },
            follow_redirects=False,
        )
        assert r.status_code in (302, 303)
        assert "/pago/iniciar/" in r.headers.get("Location", "")

        with app.app_context():
            from app.models.pedido import Pedido

            pedido = Pedido.query.order_by(Pedido.id.desc()).first()
            assert pedido.estado == "pendiente"
            assert pedido.total > 0


@pytest.mark.integration
class TestVistasTienda:
    def test_home_responde_200(self, client):
        assert client.get("/").status_code == 200

    def test_productos_por_categoria_html(self, client):
        r = client.get("/productos?categoria=herramientas-manuales")
        assert r.status_code == 200
        assert b"Martillo" in r.data

    def test_login_post_credenciales_validas(self, client):
        r = client.post(
            "/login",
            data={"email": "cliente@ferramas.cl", "password": "cliente123"},
            follow_redirects=False,
        )
        assert r.status_code in (302, 303)
