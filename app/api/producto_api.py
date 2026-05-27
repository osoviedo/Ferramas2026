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
    """Recibe notificaciones IPN de Mercado Pago."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'invalid data'}), 400

    action = data.get('action', '')
    if action == 'payment.created' or action == 'payment.updated':
        payment_id = data.get('data', {}).get('id', '')
        if payment_id and not PagoService._es_modo_simulado():
            # En modo real, verificar el pago contra la API de MP
            import mercadopago
            access_token = current_app.config.get('MP_ACCESS_TOKEN', '')
            sdk = mercadopago.SDK(access_token)
            payment_info = sdk.payment().get(payment_id)
            status = payment_info.get('response', {}).get('status', '')
            external_ref = payment_info.get('response', {}).get('external_reference', '')
            if status == 'approved' and external_ref:
                pedido = Pedido.query.get(int(external_ref))
                if pedido and pedido.estado == 'pendiente':
                    PagoService.confirmar_pago(pedido, payment_id)
        else:
            # Modo simulado: buscar por external_reference
            ext_ref = data.get('external_reference', data.get('data', {}).get('id', ''))
    elif action == 'test':
        return jsonify({'status': 'ok'}), 200
    else:
        # Para otros tipos de notificación, procesar genéricamente
        PagoService.procesar_webhook(data)

    return jsonify({'status': 'received'}), 200
