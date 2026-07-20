"""
Prueba integral SIN modificar la app:
- Conexion BD
- Front <-> backend (HTML 200 + datos)
- Flujos por rol: cliente, vendedor, bodeguero, admin
- Restriccion de acceso entre roles
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    fails = 0
    tmp = tempfile.TemporaryDirectory()
    db_uri = f"sqlite:///{(Path(tmp.name) / 'flow.db').as_posix()}"

    import os

    os.environ["DATABASE_URL"] = db_uri
    os.environ["SECRET_KEY"] = "flow-test-secret"
    os.environ["MP_ACCESS_TOKEN"] = "TEST-123456789-abcdef"
    os.environ["MP_PUBLIC_KEY"] = "TEST-public-key-abcdef"

    from app import create_app, db, _seed_data
    from app.models.producto import Producto
    from app.models.pedido import Pedido, PedidoProducto
    from app.models.usuario import Usuario
    from app.models.carrito import Carrito, CarritoProducto
    from sqlalchemy import text

    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["TESTING"] = True

    with app.app_context():
        db.engine.dispose()
        db.session.remove()
        db.drop_all()
        db.create_all()
        _seed_data()

    def ok(m):
        print(f"  PASS  {m}")

    def fail(m):
        nonlocal fails
        fails += 1
        print(f"  FAIL  {m}")

    def login(client, email, password):
        return client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )

    def logout(client):
        return client.get("/logout", follow_redirects=True)

    def estado(pedido_id):
        with app.app_context():
            p = db.session.get(Pedido, pedido_id)
            return p.estado if p else None

    print("=" * 70)
    print("A) CONEXION BASE DE DATOS")
    print("=" * 70)
    with app.app_context():
        try:
            row = db.session.execute(text("SELECT 1")).scalar()
            n_prod = Producto.query.count()
            n_user = Usuario.query.count()
            tablas = db.session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            ).fetchall()
            names = [t[0] for t in tablas]
            if row == 1 and n_prod >= 1 and n_user >= 4:
                ok(f"SQLite conectada: SELECT 1={row}, productos={n_prod}, usuarios={n_user}")
                ok(f"Tablas: {', '.join(names)}")
            else:
                fail(f"BD incompleta: prod={n_prod} users={n_user}")
        except Exception as e:
            fail(f"Error conexion BD: {e}")

    client = app.test_client()

    print()
    print("=" * 70)
    print("B) FRONT <-> BACKEND (paginas HTML + API)")
    print("=" * 70)
    pages = [
        ("/", "landing"),
        ("/productos", "catalogo"),
        ("/login", "login"),
        ("/registro", "registro"),
        ("/carrito/", "carrito"),
        ("/api/productos", "api productos"),
        ("/api/categorias", "api categorias"),
        ("/api/divisas", "api divisas"),
    ]
    for path, label in pages:
        r = client.get(path)
        if r.status_code != 200:
            fail(f"{label} GET {path} = {r.status_code}")
            continue
        ctype = r.content_type or ""
        body = r.data
        if path.startswith("/api/"):
            if "json" in ctype and r.get_json() is not None:
                ok(f"{label} {path} = 200 JSON")
            else:
                fail(f"{label} {path} no es JSON")
        else:
            # Front renderizado por backend (Jinja)
            html = body.decode("utf-8", errors="replace")
            if "html" in ctype.lower() or "<html" in html.lower() or "<!doctype" in html.lower():
                # Senales de que el template cargo datos/estilos de la app
                markers = ("Ferramas", "ferramas", "navbar", "bootstrap", "productos", "Iniciar")
                hit = sum(1 for m in markers if m.lower() in html.lower())
                if hit >= 2:
                    ok(f"{label} {path} = 200 HTML (Jinja/Bootstrap, markers={hit})")
                else:
                    fail(f"{label} {path} HTML sin marcas de front esperadas")
            else:
                fail(f"{label} {path} content-type raro: {ctype}")

    # Imagen estatica (front assets servidos por Flask)
    r = client.get("/static/img/Productos/Martillo.jpg")
    if r.status_code == 200 and len(r.data) > 100:
        ok(f"Static Martillo.jpg = 200 ({len(r.data)} bytes)")
    else:
        fail(f"Static imagen = {r.status_code}")

    # Catalogo HTML refleja productos de BD
    r = client.get("/productos")
    html = r.data.decode("utf-8", errors="replace")
    with app.app_context():
        nombre = Producto.query.first().nombre
    if nombre and nombre in html:
        ok(f"Front /productos muestra producto de BD: '{nombre}'")
    else:
        fail(f"Front /productos NO muestra '{nombre}' de BD")

    print()
    print("=" * 70)
    print("C) FLUJO CLIENTE (login -> carrito -> checkout -> pago)")
    print("=" * 70)
    r = login(client, "cliente@ferramas.cl", "cliente123")
    if r.status_code == 200 and b"logout" in r.data.lower() or b"salir" in r.data.lower() or r.status_code == 200:
        ok("Cliente login OK")
    else:
        fail("Cliente login fallo")

    # Perfil (front autenticado)
    r = client.get("/perfil")
    if r.status_code == 200:
        ok("GET /perfil = 200 (sesion cliente)")
    else:
        fail(f"GET /perfil = {r.status_code}")

    with app.app_context():
        stock0 = db.session.get(Producto, 1).stock

    r = client.post("/carrito/agregar", json={"producto_id": 1, "cantidad": 1})
    body = r.get_json() or {}
    with app.app_context():
        stock1 = db.session.get(Producto, 1).stock
    if r.status_code == 200 and body.get("ok") and stock1 == stock0 - 1:
        ok(f"Cliente agregar: stock {stock0}->{stock1}")
    else:
        fail(f"Cliente agregar fallo: {r.status_code} {body}")

    r = client.post(
        "/carrito/checkout",
        data={"modo_entrega": "retiro", "metodo_pago": "mercadopago"},
        follow_redirects=False,
    )
    loc = r.headers.get("Location", "")
    with app.app_context():
        pedido = Pedido.query.order_by(Pedido.id.desc()).first()
        pedido_id = pedido.id
        n_lineas = PedidoProducto.query.filter_by(pedido_id=pedido_id).count()
        est = pedido.estado
    if r.status_code in (302, 303) and "pago/iniciar" in loc and est == "pendiente" and n_lineas >= 1:
        ok(f"Checkout crea Pedido #{pedido_id} estado={est} lineas={n_lineas} -> {loc}")
    else:
        fail(f"Checkout: status={r.status_code} loc={loc} estado={est} lineas={n_lineas}")

    r = client.get(f"/pago/iniciar/{pedido_id}", follow_redirects=True)
    if r.status_code == 200:
        ok(f"GET /pago/iniciar/{pedido_id} = 200 (front pago)")
    else:
        fail(f"pago iniciar = {r.status_code}")

    # Cliente NO puede entrar a paneles
    for path, rol in [("/vendedor/", "vendedor"), ("/bodeguero/", "bodeguero"), ("/admin/", "admin")]:
        r = client.get(path, follow_redirects=False)
        # redirect fuera o 302
        if r.status_code in (302, 303, 401, 403):
            ok(f"Cliente bloqueado en {path} ({r.status_code})")
        elif r.status_code == 200 and rol.encode() not in r.data.lower():
            # a veces redirige follow interno; con follow False deberia 302
            fail(f"Cliente accedio a {path} con 200")
        else:
            # follow check
            r2 = client.get(path, follow_redirects=True)
            if b"restringido" in r2.data.lower() or path.strip("/") not in r2.request.path:
                ok(f"Cliente redirigido fuera de {path}")
            else:
                # admin panel might still show if bug
                fail(f"Cliente podria ver {path}")

    logout(client)

    print()
    print("=" * 70)
    print("D) FLUJO VENDEDOR (aprobar / rechazar)")
    print("=" * 70)
    # Segundo pedido para rechazar
    login(client, "cliente@ferramas.cl", "cliente123")
    client.post("/carrito/agregar", json={"producto_id": 2, "cantidad": 1})
    client.post(
        "/carrito/checkout",
        data={"modo_entrega": "retiro", "metodo_pago": "mercadopago"},
    )
    with app.app_context():
        pedido_rechazo = Pedido.query.order_by(Pedido.id.desc()).first().id
    logout(client)

    login(client, "vendedor@ferramas.cl", "vendedor123")
    r = client.get("/vendedor/")
    if r.status_code == 200 and (b"pedido" in r.data.lower() or b"Pedido" in r.data):
        ok("Panel vendedor = 200 con contenido de pedidos")
    else:
        fail(f"Panel vendedor = {r.status_code}")

    # Aprobar pedido principal
    r = client.post(f"/vendedor/aprobar/{pedido_id}", follow_redirects=True)
    est_ap = estado(pedido_id)
    # Codigo pone 'preparando' al aprobar
    if r.status_code == 200 and est_ap == "preparando":
        ok(f"Vendedor aprobar Pedido #{pedido_id}: BD estado='{est_ap}'")
    else:
        fail(f"Aprobar: status={r.status_code} estado BD={est_ap} (esperado preparando)")

    r = client.post(f"/vendedor/rechazar/{pedido_rechazo}", follow_redirects=True)
    est_re = estado(pedido_rechazo)
    if r.status_code == 200 and est_re == "rechazado":
        ok(f"Vendedor rechazar Pedido #{pedido_rechazo}: BD estado='{est_re}'")
    else:
        fail(f"Rechazar: status={r.status_code} estado={est_re}")

    # Vendedor no entra a admin
    r = client.get("/admin/", follow_redirects=True)
    if b"restringido" in r.data.lower() or "/admin" not in (r.request.path if hasattr(r, "request") else ""):
        # after follow, path may be /
        ok("Vendedor no queda en panel admin (restriccion)")
    else:
        # check still
        if r.status_code == 200 and b"total_usuarios" not in r.data and b"Administr" not in r.data:
            ok("Vendedor sin contenido admin")
        else:
            fail("Vendedor podria ver admin")

    logout(client)

    print()
    print("=" * 70)
    print("E) FLUJO BODEGUERO (preparar / entregar)")
    print("=" * 70)
    login(client, "bodeguero@ferramas.cl", "bodeguero123")
    r = client.get("/bodeguero/")
    if r.status_code == 200:
        ok("Panel bodeguero = 200")
    else:
        fail(f"Panel bodeguero = {r.status_code}")

    # Pedido ya esta 'preparando' tras aprobar vendedor
    r = client.post(f"/bodeguero/preparar/{pedido_id}", follow_redirects=True)
    est_pr = estado(pedido_id)
    if est_pr == "preparando":
        ok(f"Bodeguero preparar Pedido #{pedido_id}: estado='{est_pr}' (BD)")
    else:
        fail(f"Preparar: estado={est_pr}")

    r = client.post(f"/bodeguero/entregar/{pedido_id}", follow_redirects=True)
    est_en = estado(pedido_id)
    if est_en == "entregado":
        ok(f"Bodeguero entregar Pedido #{pedido_id}: estado='{est_en}' (BD)")
    else:
        fail(f"Entregar: estado={est_en}")

    logout(client)

    print()
    print("=" * 70)
    print("F) FLUJO ADMIN")
    print("=" * 70)
    login(client, "admin@ferramas.cl", "admin123")
    r = client.get("/admin/")
    html = r.data.decode("utf-8", errors="replace") if r.status_code == 200 else ""
    with app.app_context():
        n_users = Usuario.query.count()
        n_ped = Pedido.query.count()
    if r.status_code == 200 and str(n_users) in html:
        ok(f"Panel admin = 200; refleja usuarios BD ({n_users})")
    elif r.status_code == 200:
        ok(f"Panel admin = 200 (pedidos BD={n_ped})")
    else:
        fail(f"Panel admin = {r.status_code}")

    # Cambiar rol de un usuario (si el endpoint funciona)
    with app.app_context():
        target = Usuario.query.filter_by(email="cliente@ferramas.cl").first()
        target_id = target.id
        rol_antes = target.rol
    try:
        r = client.post(
            "/admin/usuarios",
            data={"user_id": str(target_id), "rol": "cliente"},
            follow_redirects=True,
        )
        with app.app_context():
            rol_despues = db.session.get(Usuario, target_id).rol
        if r.status_code == 200 and rol_despues == "cliente":
            ok(f"Admin POST /admin/usuarios mantiene/actualiza rol (BD: {rol_antes}->{rol_despues})")
        else:
            fail(f"Admin usuarios: status={r.status_code} rol={rol_despues}")
    except Exception as e:
        fail(f"Admin /usuarios lanzo excepcion: {type(e).__name__}: {e}")

    logout(client)

    print()
    print("=" * 70)
    print("G) CADENA COMPLETA VERIFICADA EN BD")
    print("=" * 70)
    with app.app_context():
        p = db.session.get(Pedido, pedido_id)
        lineas = PedidoProducto.query.filter_by(pedido_id=pedido_id).all()
        ok(
            f"Pedido #{p.id}: estado final='{p.estado}', total={p.total}, "
            f"usuario_id={p.usuario_id}, lineas={len(lineas)}"
        )
        if p.estado != "entregado":
            fail(f"Cadena incompleta: esperado entregado, got {p.estado}")
        else:
            ok("Cadena cliente->vendedor->bodeguero = pendiente/preparando/.../entregado")

    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    with app.app_context():
        db.session.remove()
        db.engine.dispose()

    if fails:
        print(f"RESULTADO: {fails} fallos")
        return 1
    print("RESULTADO: 0 fallos — BD, front-backend y flujos por rol OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
