"""Pruebas unitarias con mock de APIs externas."""
import responses
import pytest

from app.services.divisa_service import DivisaService
from app.services.pago_service import PagoService


@pytest.mark.unit
@pytest.mark.mock
class TestDivisaServiceMock:
    @responses.activate
    def test_obtener_divisas_desde_api_externa(self, app):
        responses.add(
            responses.GET,
            "https://mindicador.cl/api",
            json={"dolar": {"valor": 900}, "euro": {"valor": 1000}},
            status=200,
        )

        with app.app_context():
            DivisaService._cache = {}
            DivisaService._cache_time = 0
            divisas = DivisaService().obtener_divisas()

        assert divisas["dolar"] == 900
        assert divisas["euro"] == 1000
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == "https://mindicador.cl/api"

    @responses.activate
    def test_obtener_divisas_usa_valores_por_defecto_si_falla_api(self, app):
        responses.add(
            responses.GET,
            "https://mindicador.cl/api",
            body=ConnectionError("sin red"),
        )

        with app.app_context():
            DivisaService._cache = {}
            DivisaService._cache_time = 0
            divisas = DivisaService().obtener_divisas()

        assert divisas["dolar"] == 950
        assert divisas["euro"] == 1050


@pytest.mark.unit
@pytest.mark.mock
class TestPagoServiceMock:
    def test_modo_simulado_sin_token_real(self, app):
        with app.app_context():
            app.config["MP_ACCESS_TOKEN"] = "TEST-123456789-abcdef"
            assert PagoService._es_modo_simulado() is True

    def test_crear_preferencia_real_usa_sdk(self, mocker, app):
        mock_sdk_class = mocker.patch("app.services.pago_service.mercadopago.SDK")
        mock_sdk = mocker.MagicMock()
        mock_sdk.preference.return_value.create.return_value = {
            "response": {
                "sandbox_init_point": "https://sandbox.mercadopago.cl/checkout",
            }
        }
        mock_sdk_class.return_value = mock_sdk

        with app.app_context():
            app.config["MP_ACCESS_TOKEN"] = "APP_USR-token-real-de-prueba"
            from app.models.pedido import Pedido, PedidoProducto
            from app.models.producto import Producto
            from app import db

            producto = Producto.query.first()
            pedido = Pedido(usuario_id=1, total=8500, estado="pendiente")
            db.session.add(pedido)
            db.session.commit()
            db.session.add(
                PedidoProducto(
                    pedido_id=pedido.id,
                    producto_id=producto.id,
                    cantidad=1,
                    precio_unitario=producto.precio,
                )
            )
            db.session.commit()

            result = PagoService.crear_preferencia(pedido)

        assert "init_point" in result
        mock_sdk_class.assert_called_once()
