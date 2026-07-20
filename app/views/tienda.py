from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db, login_manager
from app.models.producto import Producto
from app.models.pedido import Pedido
from app.services.divisa_service import DivisaService
from app.services.pago_service import PagoService

tienda_bp = Blueprint('tienda', __name__, url_prefix='')


@tienda_bp.route('/')
def index():
    return render_template('index.html')


@tienda_bp.route('/suscribirse', methods=['POST'])
def suscribirse():
    from app.models.suscriptor import Suscriptor
    email = request.form.get('email', '').strip().lower()
    if not email or '@' not in email:
        flash('Ingresa un correo válido.', 'danger')
        return redirect(url_for('tienda.index'))
    if Suscriptor.query.filter_by(email=email).first():
        flash('Ya estás suscrito.', 'info')
        return redirect(url_for('tienda.index'))
    db.session.add(Suscriptor(email=email))
    db.session.commit()
    flash('¡Suscripción exitosa! Recibirás nuestras ofertas.', 'success')
    return redirect(url_for('tienda.index'))


@tienda_bp.route('/productos')
def productos():
    categoria = request.args.get('categoria', '')
    productos_q = Producto.query
    if categoria:
        categoria_clean = categoria.replace('-', ' ')
        productos_q = productos_q.filter(
            db.func.lower(Producto.categoria) == db.func.lower(categoria_clean)
        )
    productos_lista = productos_q.all()

    convert_to = request.args.get('convertir_a', '').upper()
    ds = DivisaService()
    divisas = ds.obtener_divisas()

    return render_template(
        'productos.html',
        productos=productos_lista,
        categoria=categoria,
        convert_to=convert_to,
        divisas=divisas,
    )


@tienda_bp.route('/checkout')
def checkout():
    return render_template('checkout.html')


@tienda_bp.route('/pago/iniciar/<int:pedido_id>')
@login_required
def pago_iniciar(pedido_id):
    """Crea la preferencia de Mercado Pago y redirige a la URL de pago."""
    pedido = Pedido.query.get_or_404(pedido_id)

    if pedido.usuario_id != current_user.id:
        flash('No tienes permiso para pagar este pedido.', 'danger')
        return redirect(url_for('tienda.index'))

    if pedido.estado != 'pendiente':
        flash('Este pedido ya fue procesado.', 'info')
        return redirect(url_for('auth.perfil'))

    result = PagoService.crear_preferencia(pedido)
    init_point = result.get('init_point')
    if not init_point:
        error_mp = result.get('error', 'No se pudo iniciar el pago en Mercado Pago.')
        flash(f'No se pudo iniciar el pago en Mercado Pago. Detalle: {error_mp}', 'danger')
        return redirect(url_for('tienda.checkout'))

    from flask import current_app
    if (
        current_app.config.get('DEV_AUTO_LOGIN')
        and current_app.config.get('MP_TEST_BUYER_USER')
    ):
        return render_template(
            'pago_sandbox.html',
            init_point=init_point,
            pedido_id=pedido_id,
            local_dev=result.get('local_dev', False),
            url_confirmar=url_for('tienda.pago_exito', pedido_id=pedido_id),
        )
    return redirect(init_point)


@tienda_bp.route('/pago/exito')
def pago_exito():
    """Pago: intenta confirmar de forma verificable (SDK/webhook) y muestra estado."""
    pedido_id = request.args.get('pedido_id')
    payment_id = request.args.get('payment_id') or request.args.get('collection_id')
    status = (
        request.args.get('status', '')
        or request.args.get('collection_status', '')
        or request.args.get('payment_status', '')
    ).lower()

    if not pedido_id:
        return render_template('checkout.html', error_pago=True)

    pedido = Pedido.query.get(int(pedido_id))
    if not pedido:
        return render_template('checkout.html', error_pago=True)

    # Modo simulado: mantener flujo rápido para demo local.
    if PagoService._es_modo_simulado():
        if pedido.estado == 'pendiente':
            PagoService.confirmar_pago(pedido, f"SIM-{pedido.id}-callback")
        return render_template('checkout.html', exito=True, pedido_id=pedido_id, payment_id='SIMULADO')

    # Si ya fue procesado por webhook, solo mostramos el estado.
    if pedido.estado != 'pendiente':
        if pedido.estado == 'aprobado':
            return render_template('checkout.html', exito=True, pedido_id=pedido_id)
        return render_template('checkout.html', error_pago=True)

    payment_data = PagoService.verificar_pago(payment_id) if payment_id else None
    if not payment_data:
        payment_data = PagoService.buscar_pago_aprobado(pedido.id)
    if payment_data:
        mp_status = (payment_data.get('status') or '').lower()
        external_ref = str(payment_data.get('external_reference') or '')
        if mp_status == 'approved' and external_ref == str(pedido.id):
            PagoService.confirmar_pago(pedido, str(payment_data.get('id')))
            return render_template(
                'checkout.html',
                exito=True,
                pedido_id=pedido_id,
                payment_id=payment_data.get('id'),
            )
        if mp_status in ('pending', 'in_process'):
            return render_template(
                'checkout.html',
                pending_verificacion=True,
                pedido_id=pedido_id,
                payment_id=payment_data.get('id'),
            )

    # Sin payment_id en el redirect (típico en localhost): consultar MP antes de cancelar.
    if status == 'approved' or not payment_id:
        return render_template(
            'checkout.html',
            pending_verificacion=True,
            pedido_id=pedido_id,
            payment_id=payment_id,
        )

    if pedido.estado == 'pendiente':
        PagoService.cancelar_pedido(pedido)
    return render_template('checkout.html', error_pago=True)


@tienda_bp.route('/pago/error')
def pago_error():
    """Maneja retorno de error/fallo y evita falsos negativos por pendientes."""
    pedido_id = request.args.get('pedido_id')
    payment_id = request.args.get('payment_id') or request.args.get('collection_id')
    status = (
        request.args.get('status', '')
        or request.args.get('collection_status', '')
        or request.args.get('payment_status', '')
    ).lower()

    if not pedido_id:
        return render_template('checkout.html', error_pago=True)

    pedido = Pedido.query.get(int(pedido_id))
    if not pedido:
        return render_template('checkout.html', error_pago=True)

    if PagoService._es_modo_simulado():
        if pedido.estado == 'pendiente':
            PagoService.cancelar_pedido(pedido)
        return render_template('checkout.html', error_pago=True)

    if pedido.estado == 'aprobado':
        return render_template('checkout.html', exito=True, pedido_id=pedido_id, payment_id=payment_id)

    payment_data = PagoService.verificar_pago(payment_id) if payment_id else None
    if not payment_data:
        payment_data = PagoService.buscar_pago_aprobado(pedido.id)
    if payment_data:
        mp_status = (payment_data.get('status') or '').lower()
        external_ref = str(payment_data.get('external_reference') or '')
        if mp_status == 'approved' and external_ref == str(pedido.id):
            if pedido.estado == 'pendiente':
                PagoService.confirmar_pago(pedido, str(payment_data.get('id')))
            return render_template('checkout.html', exito=True, pedido_id=pedido_id, payment_id=payment_data.get('id'))
        if mp_status in ('pending', 'in_process'):
            return render_template('checkout.html', pending_verificacion=True, pedido_id=pedido_id, payment_id=payment_id)

    if status in ('pending', 'in_process', 'approved'):
        return render_template('checkout.html', pending_verificacion=True, pedido_id=pedido_id, payment_id=payment_id)

    if pedido.estado == 'pendiente':
        PagoService.cancelar_pedido(pedido)
    return render_template('checkout.html', error_pago=True)
