"""Prueba de estrés: pico alto de peticiones al API."""
import pytest


@pytest.mark.stress
class TestEstres:
    def test_estres_200_peticiones_api_productos(self, client):
        """200 peticiones consecutivas — el servidor no debe caer."""
        ok = 0
        for _ in range(200):
            if client.get("/api/productos").status_code == 200:
                ok += 1
        assert ok == 200

    def test_estres_consultas_por_categoria(self, client):
        categorias = [
            "herramientas-manuales",
            "fijaciones",
            "equipos-de-seguridad",
        ]
        for _ in range(30):
            for cat in categorias:
                r = client.get(f"/api/productos/categoria/{cat}")
                assert r.status_code == 200
