"""Pruebas unitarias: modelos y servicios sin HTTP."""
import pytest

from app.models.producto import Producto
from app.services.auth_service import AuthService


@pytest.mark.unit
class TestProductoModel:
    def test_to_dict_incluye_campos_requeridos(self, app):
        with app.app_context():
            p = Producto(
                nombre="Martillo",
                precio=8500,
                stock=10,
                categoria="herramientas manuales",
                imagen="Martillo.jpg",
            )
            d = p.to_dict()
            assert d["nombre"] == "Martillo"
            assert d["precio"] == 8500
            assert d["stock"] == 10
            assert d["categoria"] == "herramientas manuales"
            assert d["imagen"] == "Martillo.jpg"


@pytest.mark.unit
class TestAuthService:
    def test_login_exitoso_con_usuario_seed(self, app):
        with app.app_context():
            user, err = AuthService.login("cliente@ferramas.cl", "cliente123")
            assert err is None
            assert user is not None
            assert user.rol == "cliente"

    def test_login_falla_con_password_incorrecta(self, app):
        with app.app_context():
            user, err = AuthService.login("cliente@ferramas.cl", "mal-password")
            assert user is None
            assert "incorrectos" in err.lower()

    def test_registro_rechaza_email_duplicado(self, app):
        with app.app_context():
            user, err = AuthService.registrar("Otro", "cliente@ferramas.cl", "abc123")
            assert user is None
            assert "registrado" in err.lower()

    def test_registro_crea_usuario_y_carrito(self, app):
        with app.app_context():
            import uuid

            email = f"test_{uuid.uuid4().hex[:8]}@test.cl"
            user, err = AuthService.registrar("Nuevo Cliente", email, "pass12345")
            assert err is None
            assert user.carrito is not None
