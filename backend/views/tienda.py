from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from backend import db, login_manager
from backend.models.producto import Producto
from backend.models.pedido import Pedido
from backend.services.divisa_service import DivisaService
from backend.services.pago_service import PagoService

tienda_bp = Blueprint('tienda', __name__, url_prefix='')


@tienda_bp.route('/')
def index():
    return render_template('index.html')


@tienda_bp.route('/suscribirse', methods=['POST'])
def suscribirse():
    from backend.models.suscriptor import Suscriptor
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
    return redirect(result['init_point'])


@tienda_bp.route('/pago/exito')
def pago_exito():
    """Pago confirmado: actualiza pedido, vacía carrito BD, muestra éxito."""
    pedido_id = request.args.get('pedido_id')
    if pedido_id:
        pedido = Pedido.query.get(int(pedido_id))
        if pedido and pedido.estado == 'pendiente':
            PagoService.confirmar_pago(pedido)
    return render_template('checkout.html', exito=True, pedido_id=pedido_id)


@tienda_bp.route('/pago/error')
def pago_error():
    """Pago fallido o cancelado: cancela el pedido, mantiene el carrito."""
    pedido_id = request.args.get('pedido_id')
    if pedido_id:
        pedido = Pedido.query.get(int(pedido_id))
        if pedido and pedido.estado == 'pendiente':
            PagoService.cancelar_pedido(pedido)
    return render_template('checkout.html', error_pago=True)
