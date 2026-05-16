import time
import requests
from flask import current_app


class DivisaService:
    _cache = {}
    _cache_time = 0

    def obtener_divisas(self):
        """Obtiene USD y EUR desde mindicador.cl con caché."""
        cache_segundos = current_app.config.get('DIVISA_CACHE_SEGUNDOS', 3600)
        ahora = time.time()
        if self._cache and (ahora - self._cache_time) < cache_segundos:
            return self._cache

        try:
            resp = requests.get('https://mindicador.cl/api', timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self._cache = {
                    'dolar': data.get('dolar', {}).get('valor', 950),
                    'euro': data.get('euro', {}).get('valor', 1050),
                }
                self._cache_time = ahora
                return self._cache
        except Exception:
            pass

        return {
            'dolar': 950,
            'euro': 1050,
        }
