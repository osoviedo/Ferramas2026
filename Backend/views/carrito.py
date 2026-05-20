import json
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from backend import db
from backend.models.producto import Producto
from backend.models.pedido import Pedido, PedidoProducto, Pago, Direccion
from backend.models.carrito import Carrito, CarritoProducto
from backend.services.pago_service import PagoService

carrito_bp = Blueprint('carrito', __name__, url_prefix='/carrito')


@carrito_bp.route('/')
def ver_carrito():
    return render_template('carrito.html')


@carrito_bp.route('/agregar', methods=['POST'])
def agregar():
    data = request.get_json()
    producto_id = data.get('producto_id')
    cantidad = data.get('cantidad', 1)
    producto = Producto.query.get_or_404(producto_id)

    if current_user.is_authenticated:
        carrito = Carrito.query.filter_by(usuario_id=current_user.id).first()
        if not carrito:
            carrito = Carrito(usuario_id=current_user.id)
            db.session.add(carrito)
            db.session.commit()
        item = CarritoProducto.query.filter_by(
            carrito_id=carrito.id, producto_id=producto_id
        ).first()
        if item:
            item.cantidad += cantidad
        else:
            item = CarritoProducto(
                carrito_id=carrito.id, producto_id=producto_id, cantidad=cantidad
            )
            db.session.add(item)
        db.session.commit()

    return jsonify({'ok': True, 'nombre': producto.nombre})


@carrito_bp.route('/eliminar', methods=['POST'])
def eliminar():
    data = request.get_json()
    producto_id = data.get('producto_id')
    if current_user.is_authenticated:
        carrito = Carrito.query.filter_by(usuario_id=current_user.id).first()
        if carrito:
            CarritoProducto.query.filter_by(
                carrito_id=carrito.id, producto_id=producto_id
            ).delete()
            db.session.commit()
    return jsonify({'ok': True})


@carrito_bp.route('/actualizar', methods=['POST'])
def actualizar():
    data = request.get_json()
    producto_id = data.get('producto_id')
    cantidad = data.get('cantidad', 1)
    if current_user.is_authenticated:
        carrito = Carrito.query.filter_by(usuario_id=current_user.id).first()
        if carrito:
            item = CarritoProducto.query.filter_by(
                carrito_id=carrito.id, producto_id=producto_id
            ).first()
            if item:
                item.cantidad = cantidad
                db.session.commit()
    return jsonify({'ok': True})


@carrito_bp.route('/sincronizar', methods=['POST'])
@login_required
def sincronizar():
    data = request.get_json()
    items = data.get('items', []) if data else []

    carrito = Carrito.query.filter_by(usuario_id=current_user.id).first()
    if not carrito:
        carrito = Carrito(usuario_id=current_user.id)
        db.session.add(carrito)
        db.session.commit()

    for item in items:
        producto_id = item.get('id')
        cantidad = item.get('cantidad', 1)
        cp = CarritoProducto.query.filter_by(
            carrito_id=carrito.id, producto_id=producto_id
        ).first()
        if cp:
            cp.cantidad = max(cp.cantidad, cantidad)
        else:
            cp = CarritoProducto(
                carrito_id=carrito.id, producto_id=producto_id, cantidad=cantidad
            )
            db.session.add(cp)
    db.session.commit()
    return jsonify({'ok': True})


@carrito_bp.route('/checkout', methods=['POST'])
@login_required
def procesar_checkout():
    modo_entrega = request.form.get('modo_entrega', 'retiro')
    metodo_pago = request.form.get('metodo_pago', 'mercadopago')
    direccion = request.form.get('direccion', '')
    comuna = request.form.get('comuna', '')
    region = request.form.get('region', '')
    sucursal = request.form.get('sucursal', 'Sucursal Central')

    carrito = Carrito.query.filter_by(usuario_id=current_user.id).first()

    if (not carrito or not carrito.productos):
        items_json = request.form.get('items_carrito', '[]')
        items = json.loads(items_json)
        if items:
            if not carrito:
                carrito = Carrito(usuario_id=current_user.id)
                db.session.add(carrito)
                db.session.commit()
            for item in items:
                producto = Producto.query.get(item.get('id'))
                if producto:
                    cp = CarritoProducto(
                        carrito_id=carrito.id,
                        producto_id=item['id'],
                        cantidad=item.get('cantidad', 1),
                    )
                    db.session.add(cp)
            db.session.commit()

    if not carrito or not carrito.productos:
        flash('El carrito está vacío.', 'danger')
        return redirect(url_for('carrito.ver_carrito'))

    subtotal = sum(
        cp.cantidad * cp.producto.precio for cp in carrito.productos
    )

    # Aplicar descuento del cliente
    descuento_pct = current_user.descuento or 0
    descuento_monto = round(subtotal * descuento_pct / 100)
    total = subtotal - descuento_monto

    estado_inicial = 'pendiente_transferencia' if metodo_pago == 'transferencia' else 'pendiente'

    pedido = Pedido(
        usuario_id=current_user.id,
        modo_entrega=modo_entrega,
        direccion_despacho=direccion if modo_entrega == 'despacho' else None,
        sucursal_retiro=sucursal if modo_entrega == 'retiro' else None,
        total=total,
        estado=estado_inicial,
    )
    db.session.add(pedido)
    db.session.commit()

    for cp in carrito.productos:
        pp = PedidoProducto(
            pedido_id=pedido.id,
            producto_id=cp.producto_id,
            cantidad=cp.cantidad,
            precio_unitario=cp.producto.precio,
        )
        db.session.add(pp)
    db.session.commit()

    if modo_entrega == 'despacho' and direccion:
        dir_obj = Direccion(
            usuario_id=current_user.id,
            direccion=direccion,
            comuna=comuna,
            region=region,
        )
        db.session.add(dir_obj)
        db.session.commit()

    if metodo_pago == 'transferencia':
        PagoService.confirmar_pago(pedido, f'TRANSF-{pedido.id}')
        flash(
            f'Pedido #{pedido.id} registrado. Envía tu comprobante a pagos@ferramas.cl.',
            'success'
        )
        return redirect(url_for('auth.perfil'))

    return redirect(url_for('tienda.pago_iniciar', pedido_id=pedido.id))
