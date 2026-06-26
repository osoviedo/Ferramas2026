from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from backend import db
from backend.models.pedido import Pedido
from backend.services.email_service import EmailService

bodeguero_bp = Blueprint('bodeguero', __name__, url_prefix='/bodeguero')


def bodeguero_required():
    if not current_user.is_authenticated or current_user.rol not in ('bodeguero', 'admin'):
        flash('Acceso restringido a bodegueros.', 'danger')
        return False
    return True


@bodeguero_bp.route('/')
@login_required
def panel():
    if not bodeguero_required():
        return redirect(url_for('tienda.index'))
    pedidos = Pedido.query.filter(
        Pedido.estado.in_(['preparando', 'aprobado'])
    ).order_by(Pedido.created_at.desc()).all()
    return render_template('bodeguero.html', pedidos=pedidos)


@bodeguero_bp.route('/preparar/<int:pedido_id>', methods=['POST'])
@login_required
def preparar(pedido_id):
    if not bodeguero_required():
        return redirect(url_for('tienda.index'))
    pedido = Pedido.query.get_or_404(pedido_id)
    pedido.estado = 'preparando'
    db.session.commit()
    EmailService.enviar_cambio_estado(pedido.usuario, pedido, 'preparando')
    flash(f'Pedido #{pedido.id} en preparación.', 'info')
    return redirect(url_for('bodeguero.panel'))


@bodeguero_bp.route('/entregar/<int:pedido_id>', methods=['POST'])
@login_required
def entregar(pedido_id):
    if not bodeguero_required():
        return redirect(url_for('tienda.index'))
    pedido = Pedido.query.get_or_404(pedido_id)
    pedido.estado = 'entregado'
    db.session.commit()
    EmailService.enviar_cambio_estado(pedido.usuario, pedido, 'entregado')
    flash(f'Pedido #{pedido.id} entregado.', 'success')
    return redirect(url_for('bodeguero.panel'))
