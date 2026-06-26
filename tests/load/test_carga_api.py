"""Prueba de carga: volumen sostenido de peticiones al API."""
import time

import pytest


@pytest.mark.load
class TestCarga:
    def test_carga_50_peticiones_secuenciales_api(self, client):
        """50 lecturas seguidas a /api/productos en menos de 15 segundos."""
        t0 = time.perf_counter()
        for _ in range(50):
            r = client.get("/api/productos")
            assert r.status_code == 200
        elapsed = time.perf_counter() - t0
        assert elapsed < 15.0, f"50 peticiones tardaron {elapsed:.1f}s"

    def test_carga_endpoints_criticos(self, client):
        """Round-robin entre rutas principales sin errores."""
        paths = ["/api/productos", "/api/categorias", "/", "/api/divisas"]
        for i in range(40):
            assert client.get(paths[i % len(paths)]).status_code == 200
