import mercadopago
from flask import current_app, url_for
from app import db
from app.models.pedido import Pago


class PagoService:

    # Token por defecto que indica entorno de desarrollo sin credenciales reales
    _DEFAULT_TEST_TOKEN = 'TEST-123456789-abcdef'

    @staticmethod
    def _es_modo_simulado():
        """True solo si NO hay credenciales reales configuradas."""
        token = current_app.config.get('MP_ACCESS_TOKEN', '')
        return (not token or token == PagoService._DEFAULT_TEST_TOKEN)

    @staticmethod
    def crear_preferencia(pedido):
        """Crea preferencia en Mercado Pago (o simulada). Solo crea la URL de pago.
        NO modifica el pedido ni el carrito — eso ocurre en /pago/exito."""
        if PagoService._es_modo_simulado():
            return PagoService._preferencia_simulada(pedido)

        sdk = mercadopago.SDK(access_token)
        items = []
        for pp in pedido.productos:
            items.append({
                'title': pp.producto.nombre,
                'quantity': pp.cantidad,
                'unit_price': float(pp.precio_unitario),
            })
        preference_data = {
            'items': items,
            'external_reference': str(pedido.id),
            'back_urls': {
                'success': url_for('tienda.pago_exito', pedido_id=pedido.id, _external=True),
                'failure': url_for('tienda.pago_error', pedido_id=pedido.id, _external=True),
                'pending': url_for('tienda.pago_error', pedido_id=pedido.id, _external=True),
            },
            'auto_return': 'approved',
        }
        try:
            preference_response = sdk.preference().create(preference_data)
            preference = preference_response['response']
            return {'init_point': preference['init_point']}
        except Exception:
            return PagoService._preferencia_simulada(pedido)

    @staticmethod
    def _preferencia_simulada(pedido):
        """Simula creación de preferencia sin credenciales reales."""
        return {
            'init_point': url_for('tienda.pago_exito', pedido_id=pedido.id),
            'simulado': True,
        }

    @staticmethod
    def confirmar_pago(pedido, transaccion_id=None):
        """Confirma el pago: crea registro Pago, cambia estado pedido, DESCUENTA stock,
        vacía carrito."""
        from app.models.carrito import Carrito, CarritoProducto
        from app.models.producto import Producto

        transaccion_id = transaccion_id or f'SIM-{pedido.id}-aprobado'
        pago = Pago.query.filter_by(pedido_id=pedido.id).first()
        if not pago:
            pago = Pago(
                pedido_id=pedido.id,
                metodo='mercadopago',
                estado='aprobado',
                transaccion_id=transaccion_id,
            )
            db.session.add(pago)
        else:
            pago.estado = 'aprobado'
            pago.transaccion_id = transaccion_id

        pedido.estado = 'aprobado'

        # Descontar stock de cada producto del pedido
        for pp in pedido.productos:
            producto = Producto.query.get(pp.producto_id)
            if producto:
                producto.stock = max(0, producto.stock - pp.cantidad)

        carrito = Carrito.query.filter_by(usuario_id=pedido.usuario_id).first()
        if carrito:
            CarritoProducto.query.filter_by(carrito_id=carrito.id).delete()

        db.session.commit()

    @staticmethod
    def cancelar_pedido(pedido):
        """Marca el pedido como cancelado sin vaciar el carrito."""
        pedido.estado = 'cancelado'
        pago = Pago.query.filter_by(pedido_id=pedido.id).first()
        if pago:
            pago.estado = 'rechazado'
        db.session.commit()

    @staticmethod
    def procesar_webhook(webhook_data):
        """Procesa notificación IPN de Mercado Pago."""
        pedido_id = webhook_data.get('external_reference')
        if not pedido_id:
            return False
        from app.models.pedido import Pedido
        pedido = Pedido.query.get(int(pedido_id))
        if pedido and pedido.estado == 'pendiente':
            PagoService.confirmar_pago(pedido, webhook_data.get('id', ''))
        return True
