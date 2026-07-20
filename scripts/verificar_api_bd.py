"""
Verificación real API ↔ BD (sin falsos positivos).
Compara respuestas HTTP contra consultas SQLAlchemy directas
y prueba mutaciones (stock, carrito, pedido).
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _ok(msg: str) -> None:
    print(f"  PASS  {msg}")


def _fail(msg: str) -> None:
    print(f"  FAIL  {msg}")


def main() -> int:
    # Evitar UnicodeEncodeError en consola Windows (cp1252)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    fails = 0
    tmp = tempfile.TemporaryDirectory()
    db_path = Path(tmp.name) / "verify.db"
    db_uri = f"sqlite:///{db_path.as_posix()}"

    import os

    os.environ["DATABASE_URL"] = db_uri
    os.environ["SECRET_KEY"] = "verify-secret"
    os.environ["MP_ACCESS_TOKEN"] = "TEST-123456789-abcdef"
    os.environ["MP_PUBLIC_KEY"] = "TEST-public-key-abcdef"

    from app import create_app, db, _seed_data
    from app.models.producto import Producto
    from app.models.pedido import Pedido
    from app.models.carrito import Carrito, CarritoProducto
    from app.models.usuario import Usuario

    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        db.engine.dispose()
        db.session.remove()
        db.drop_all()
        db.create_all()
        _seed_data()

    client = app.test_client()

    print("=" * 70)
    print("1) API REST - solo LECTURA: conecta con la BD?")
    print("=" * 70)

    with app.app_context():
        productos_db = Producto.query.order_by(Producto.id).all()
        cats_db = sorted({p.categoria for p in productos_db})
        n_db = len(productos_db)
        print(f"  BD seed: {n_db} productos, {len(cats_db)} categorías")

    # GET /api/productos
    r = client.get("/api/productos")
    data = r.get_json()
    if r.status_code != 200:
        _fail(f"GET /api/productos → {r.status_code}")
        fails += 1
    elif not isinstance(data, list) or len(data) != n_db:
        _fail(f"GET /api/productos count {len(data) if data else None} != BD {n_db}")
        fails += 1
    else:
        with app.app_context():
            mismatch = False
            for item in data:
                p = Producto.query.get(item["id"])
                if not p or p.nombre != item["nombre"] or p.precio != item["precio"] or p.stock != item["stock"]:
                    mismatch = True
                    _fail(f"Producto id={item.get('id')} API≠BD")
                    fails += 1
                    break
            if not mismatch:
                _ok(f"GET /api/productos = {len(data)} items identicos a BD")

    # GET /api/productos/1
    r = client.get("/api/productos/1")
    d = r.get_json()
    with app.app_context():
        p1 = Producto.query.get(1)
        if r.status_code == 200 and p1 and d["nombre"] == p1.nombre and d["stock"] == p1.stock:
            _ok("GET /api/productos/1 coincide con BD")
        else:
            _fail("GET /api/productos/1 no coincide con BD")
            fails += 1

    # GET 404
    r = client.get("/api/productos/99999")
    if r.status_code == 404:
        _ok("GET /api/productos/99999 = 404")
    else:
        _fail(f"GET inexistente = {r.status_code} (esperado 404)")
        fails += 1

    # GET categorias
    r = client.get("/api/categorias")
    cats_api = r.get_json()
    if r.status_code == 200 and sorted(cats_api) == cats_db:
        _ok(f"GET /api/categorias = {len(cats_api)} = BD")
    else:
        _fail(f"categorias API {cats_api} != BD {cats_db}")
        fails += 1

    # GET categoria
    r = client.get("/api/productos/categoria/herramientas-manuales")
    with app.app_context():
        expected = Producto.query.filter(
            db.func.lower(Producto.categoria) == "herramientas manuales"
        ).count()
    if r.status_code == 200 and len(r.get_json()) == expected and expected > 0:
        _ok(f"GET categoria herramientas-manuales = {expected} (BD)")
    else:
        _fail("filtro categoria no cuadra con BD")
        fails += 1

    r = client.get("/api/productos/categoria/no-existe-xyz")
    if r.status_code == 404:
        _ok("categoria inexistente = 404")
    else:
        _fail(f"categoria inexistente = {r.status_code}")
        fails += 1

    # Divisas (externa o fallback)
    r = client.get("/api/divisas")
    div = r.get_json() or {}
    if r.status_code == 200 and "dolar" in div and "euro" in div:
        _ok(f"GET /api/divisas = dolar={div.get('dolar')} euro={div.get('euro')}")
    else:
        _fail("GET /api/divisas invalido")
        fails += 1

    # Conversion USD: no escribe BD
    with app.app_context():
        stock_pre_conv = Producto.query.get(1).stock
    r = client.get("/api/productos?convertir_a=USD")
    conv = r.get_json()
    with app.app_context():
        stock_post_conv = Producto.query.get(1).stock
    if (
        r.status_code == 200
        and conv
        and conv[0].get("moneda") == "USD"
        and "precio_original" in conv[0]
        and stock_pre_conv == stock_post_conv
    ):
        _ok("GET ?convertir_a=USD cambia moneda en JSON; stock BD intacto")
    else:
        _fail("conversion USD fallo o altero stock")
        fails += 1

    print()
    print("=" * 70)
    print("2) La API REST crea / modifica / elimina productos?")
    print("=" * 70)
    for method, path in [
        ("POST", "/api/productos"),
        ("PUT", "/api/productos/1"),
        ("PATCH", "/api/productos/1"),
        ("DELETE", "/api/productos/1"),
    ]:
        r = getattr(client, method.lower())(path, json={"nombre": "X", "precio": 1, "stock": 1})
        if r.status_code in (405, 404):
            _ok(f"{method} {path} = {r.status_code} (NO implementado; no muta BD)")
        else:
            _fail(f"{method} {path} = {r.status_code} inesperado")
            fails += 1

    with app.app_context():
        n_after = Producto.query.count()
    if n_after == n_db:
        _ok(f"Tras intentos CRUD API, count productos sigue = {n_db}")
    else:
        _fail(f"Count productos cambio {n_db} -> {n_after}")
        fails += 1

    print()
    print("=" * 70)
    print("3) Mutaciones REALES (carrito/vistas) — actualizan la BD?")
    print("=" * 70)

    r = client.post(
        "/login",
        data={"email": "cliente@ferramas.cl", "password": "cliente123"},
        follow_redirects=True,
    )
    if r.status_code != 200:
        _fail("login cliente fallo")
        fails += 1
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        print(f"\nTOTAL FAILS: {fails}")
        return 1
    _ok("login cliente@ferramas.cl")

    with app.app_context():
        stock_antes = Producto.query.get(1).stock

    r = client.post(
        "/carrito/agregar",
        json={"producto_id": 1, "cantidad": 2},
        content_type="application/json",
    )
    body = r.get_json() or {}
    with app.app_context():
        stock_despues = Producto.query.get(1).stock
        item = (
            CarritoProducto.query.join(Carrito)
            .join(Usuario)
            .filter(Usuario.email == "cliente@ferramas.cl", CarritoProducto.producto_id == 1)
            .first()
        )
    api_stock = client.get("/api/productos/1").get_json()["stock"]

    if r.status_code == 200 and body.get("ok") and stock_despues == stock_antes - 2:
        _ok(f"POST /carrito/agregar: stock BD {stock_antes} -> {stock_despues} (-2)")
    else:
        _fail(f"agregar: status={r.status_code} body={body} stock {stock_antes}->{stock_despues}")
        fails += 1

    if api_stock == stock_despues:
        _ok(f"API /api/productos/1 refleja stock BD ({api_stock})")
    else:
        _fail(f"API stock {api_stock} != BD {stock_despues} — DESYNC")
        fails += 1

    if item and item.cantidad >= 2:
        _ok(f"CarritoProducto en BD: producto_id=1 cantidad={item.cantidad}")
    else:
        _fail("no hay CarritoProducto en BD tras agregar")
        fails += 1

    with app.app_context():
        stock_mid = Producto.query.get(1).stock
        item = (
            CarritoProducto.query.join(Carrito)
            .join(Usuario)
            .filter(Usuario.email == "cliente@ferramas.cl", CarritoProducto.producto_id == 1)
            .first()
        )
        cant_ant = item.cantidad if item else 2

    r = client.post(
        "/carrito/actualizar",
        json={"producto_id": 1, "cantidad": cant_ant + 1, "cantidad_anterior": cant_ant},
        content_type="application/json",
    )
    with app.app_context():
        stock_upd = Producto.query.get(1).stock
        item = (
            CarritoProducto.query.join(Carrito)
            .join(Usuario)
            .filter(Usuario.email == "cliente@ferramas.cl", CarritoProducto.producto_id == 1)
            .first()
        )
    if r.status_code == 200 and item and item.cantidad == cant_ant + 1 and stock_upd == stock_mid - 1:
        _ok(f"POST /carrito/actualizar: cantidad {cant_ant}->{item.cantidad}, stock {stock_mid}->{stock_upd}")
    else:
        _fail(
            f"actualizar fallo status={r.status_code} "
            f"cant={getattr(item, 'cantidad', None)} stock={stock_upd}"
        )
        fails += 1

    with app.app_context():
        stock_pre_del = Producto.query.get(1).stock
        item = (
            CarritoProducto.query.join(Carrito)
            .join(Usuario)
            .filter(Usuario.email == "cliente@ferramas.cl", CarritoProducto.producto_id == 1)
            .first()
        )
        cant_del = item.cantidad if item else 0

    r = client.post(
        "/carrito/eliminar",
        json={"producto_id": 1},
        content_type="application/json",
    )
    with app.app_context():
        stock_post_del = Producto.query.get(1).stock
        item_gone = (
            CarritoProducto.query.join(Carrito)
            .join(Usuario)
            .filter(Usuario.email == "cliente@ferramas.cl", CarritoProducto.producto_id == 1)
            .first()
        )
    api_stock2 = client.get("/api/productos/1").get_json()["stock"]

    if r.status_code == 200 and item_gone is None and stock_post_del == stock_pre_del + cant_del:
        _ok(f"POST /carrito/eliminar: item borrado, stock {stock_pre_del}->{stock_post_del} (+{cant_del})")
    else:
        _fail(
            f"eliminar: item={item_gone} stock {stock_pre_del}->{stock_post_del} (esperaba +{cant_del})"
        )
        fails += 1

    if api_stock2 == stock_post_del:
        _ok(f"API refleja stock tras eliminar ({api_stock2})")
    else:
        _fail(f"API desync tras eliminar: {api_stock2} vs {stock_post_del}")
        fails += 1

    client.post("/carrito/agregar", json={"producto_id": 1, "cantidad": 1}, content_type="application/json")
    with app.app_context():
        stock_pre_co = Producto.query.get(1).stock
        pedidos_antes = Pedido.query.count()

    r = client.post(
        "/carrito/checkout",
        data={"modo_entrega": "retiro", "metodo_pago": "mercadopago"},
        follow_redirects=False,
    )
    with app.app_context():
        pedidos_despues = Pedido.query.count()
        ultimo = Pedido.query.order_by(Pedido.id.desc()).first()
        ultimo_id = ultimo.id if ultimo else None
        ultimo_estado = ultimo.estado if ultimo else None
        ultimo_total = ultimo.total if ultimo else None
        stock_post_co = Producto.query.get(1).stock

    if r.status_code in (302, 303) and pedidos_despues == pedidos_antes + 1:
        _ok(
            f"POST /carrito/checkout: Pedido id={ultimo_id} estado={ultimo_estado} "
            f"total={ultimo_total} (pedidos {pedidos_antes}->{pedidos_despues})"
        )
    else:
        _fail(f"checkout status={r.status_code} pedidos {pedidos_antes}->{pedidos_despues}")
        fails += 1

    if ultimo_estado in ("pendiente", "pendiente_transferencia"):
        _ok(f"Pedido persistido en BD con estado '{ultimo_estado}'")
    else:
        _fail(f"pedido estado inesperado: {ultimo_estado}")
        fails += 1

    if stock_post_co == stock_pre_co:
        _ok(f"Checkout NO altera stock de nuevo (se mantiene {stock_post_co}; ya descontado al agregar)")
    else:
        _fail(f"Checkout cambio stock {stock_pre_co}->{stock_post_co} (revisar logica)")
        fails += 1

    print()
    print("=" * 70)
    print("4) Webhook Mercado Pago (modo simulado)")
    print("=" * 70)
    r = client.post("/api/webhook/mercadopago", json={"action": "test"})
    body = r.get_json() or {}
    if r.status_code == 200 and body.get("status") in ("ok", "simulated_mode"):
        _ok(f"POST /api/webhook/mercadopago = {body} (modo simulado: NO confirma pago en BD)")
    else:
        _fail(f"webhook = {r.status_code} {body}")
        fails += 1

    with app.app_context():
        if ultimo_id:
            pedido_check = Pedido.query.get(ultimo_id)
            if pedido_check.estado == ultimo_estado:
                _ok(f"Pedido {pedido_check.id} sigue '{pedido_check.estado}' tras webhook simulado")
            else:
                _fail("webhook cambio estado en modo simulado (inesperado)")
                fails += 1

    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(
        """
CONCLUSION SOBRE LA BD Y LAS API:

* /api/productos, /api/categorias, /api/divisas, /api/productos/<id>
  = SOLO LECTURA. Leen de la misma BD (SQLAlchemy). NO crean, NO actualizan, NO borran.

* No existen POST/PUT/PATCH/DELETE de productos en la API REST.

* Quien SI modifica la BD:
  - POST /carrito/agregar     = descuenta stock + inserta/actualiza CarritoProducto
  - POST /carrito/actualizar  = ajusta cantidad y stock
  - POST /carrito/eliminar    = borra item y restituye stock
  - POST /carrito/checkout    = INSERT Pedido (+ lineas); stock ya venia descontado
  - Paneles vendedor/bodeguero = cambian estado del pedido
  - Webhook MP (solo con token REAL) = puede confirmar pago y cambiar pedido

* La API de lectura SI refleja cambios de stock hechos por el carrito
  (misma BD, mismo modelo Producto).
"""
    )
    with app.app_context():
        db.session.remove()
        db.engine.dispose()

    if fails:
        print(f"RESULTADO: {fails} fallos — hay inconsistencias reales.")
        return 1
    print("RESULTADO: 0 fallos — API<->BD coherente; mutaciones verificadas en SQLite.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
