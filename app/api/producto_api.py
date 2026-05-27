from flask import Blueprint, jsonify, request, current_app
from app import db
from app.models.producto import Producto
from app.models.pedido import Pedido
from app.services.divisa_service import DivisaService
from app.services.pago_service import PagoService

api_bp = Blueprint('api', __name__)


@api_bp.route('/api/productos')
def api_productos():
    productos = Producto.query.all()
    convert_to = request.args.get('convertir_a', '').upper()
    tasa = None
    if convert_to in ('USD', 'EUR'):
        ds = DivisaService()
        divisas = ds.obtener_divisas()
        if convert_to == 'USD':
            tasa = divisas.get('dolar', None)
        elif convert_to == 'EUR':
            tasa = divisas.get('euro', None)

    productos_lista = []
    for p in productos:
        d = p.to_dict()
        if tasa:
            d['precio_original'] = d['precio']
            d['precio'] = round(d['precio'] / tasa)
            d['moneda'] = convert_to
        else:
            d['moneda'] = 'CLP'
        productos_lista.append(d)
    return jsonify(productos_lista)


@api_bp.route('/api/productos/<int:producto_id>')
def api_producto_detail(producto_id):
    p = Producto.query.get_or_404(producto_id)
    return jsonify(p.to_dict())


@api_bp.route('/api/productos/categoria/<nombre_categoria>')
def api_productos_categoria(nombre_categoria):
    categoria_buscar = nombre_categoria.replace('-', ' ')
    productos = Producto.query.filter(
        db.func.lower(Producto.categoria) == db.func.lower(categoria_buscar)
    ).all()

    if not productos:
        return jsonify({'error': 'Categoría no encontrada'}), 404

    return jsonify([p.to_dict() for p in productos])


@api_bp.route('/api/categorias')
def api_categorias():
    categorias = Producto.query.with_entities(
        Producto.categoria
    ).distinct().order_by(Producto.categoria).all()
    lista = [c[0] for c in categorias]
    return jsonify(lista)


@api_bp.route('/api/divisas')
def api_divisas():
    """Retorna tasas de cambio CLP para USD/EUR."""
    ds = DivisaService()
    return jsonify(ds.obtener_divisas())


@api_bp.route('/api/webhook/mercadopago', methods=['POST'])
def webhook_mercadopago():
    """Recibe notificaciones de Mercado Pago y confirma pagos aprobados."""
    if PagoService._es_modo_simulado():
        return jsonify({'status': 'simulated_mode'}), 200

    # MP puede enviar JSON o query params (topic/type + id/data.id).
    data = request.get_json(silent=True) or {}
    topic = (
        request.args.get('topic')
        or request.args.get('type')
        or data.get('type')
        or data.get('topic')
        or ''
    )

    payment_id = (
        request.args.get('id')
        or data.get('data', {}).get('id')
        or data.get('id')
        or ''
    )

    if topic == 'test' or data.get('action') == 'test':
        return jsonify({'status': 'ok'}), 200

    if topic and topic != 'payment':
        return jsonify({'status': 'ignored_topic'}), 200

    if not payment_id:
        return jsonify({'status': 'ignored_no_payment_id'}), 200

    payment_data = PagoService.verificar_pago(str(payment_id))
    if not payment_data:
        return jsonify({'status': 'verification_failed'}), 200

    mp_status = (payment_data.get('status') or '').lower()
    external_ref = str(payment_data.get('external_reference') or '')
    if mp_status == 'approved' and external_ref.isdigit():
        pedido = Pedido.query.get(int(external_ref))
        if pedido and pedido.estado == 'pendiente':
            PagoService.confirmar_pago(pedido, str(payment_data.get('id') or payment_id))

    return jsonify({'status': 'received'}), 200
