from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.pedido import Pedido
from app.services.email_service import EmailService

vendedor_bp = Blueprint('vendedor', __name__, url_prefix='/vendedor')


def vendedor_required():
    if not current_user.is_authenticated or current_user.rol not in ('vendedor', 'admin'):
        flash('Acceso restringido a vendedores.', 'danger')
        return False
    return True


@vendedor_bp.route('/')
@login_required
def panel():
    if not vendedor_required():
        return redirect(url_for('tienda.index'))
    pedidos = Pedido.query.filter_by(estado='pendiente').order_by(
        Pedido.created_at.desc()
    ).all()
    return render_template('vendedor.html', pedidos=pedidos)


@vendedor_bp.route('/aprobar/<int:pedido_id>', methods=['POST'])
@login_required
def aprobar(pedido_id):
    if not vendedor_required():
        return redirect(url_for('tienda.index'))
    pedido = Pedido.query.get_or_404(pedido_id)
    pedido.estado = 'preparando'
    db.session.commit()
    EmailService.enviar_cambio_estado(pedido.usuario, pedido, 'aprobado')
    flash(f'Pedido #{pedido.id} aprobado.', 'success')
    return redirect(url_for('vendedor.panel'))


@vendedor_bp.route('/rechazar/<int:pedido_id>', methods=['POST'])
@login_required
def rechazar(pedido_id):
    if not vendedor_required():
        return redirect(url_for('tienda.index'))
    pedido = Pedido.query.get_or_404(pedido_id)
    pedido.estado = 'rechazado'
    db.session.commit()
    EmailService.enviar_cambio_estado(pedido.usuario, pedido, 'rechazado')
    flash(f'Pedido #{pedido.id} rechazado.', 'warning')
    return redirect(url_for('vendedor.panel'))
