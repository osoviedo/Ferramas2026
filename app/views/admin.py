from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.usuario import Usuario
from app.models.pedido import Pedido

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required():
    if not current_user.is_authenticated or current_user.rol != 'admin':
        flash('Acceso restringido a administradores.', 'danger')
        return False
    return True


@admin_bp.route('/')
@login_required
def panel():
    if not admin_required():
        return redirect(url_for('tienda.index'))
    usuarios = Usuario.query.all()
    pedidos = Pedido.query.order_by(Pedido.created_at.desc()).all()
    total_usuarios = Usuario.query.count()
    total_pedidos = Pedido.query.count()
    total_ventas = db.session.query(db.func.sum(Pedido.total)).filter(
        Pedido.estado.in_(['entregado', 'preparando'])
    ).scalar() or 0
    return render_template(
        'admin.html',
        usuarios=usuarios,
        pedidos=pedidos,
        total_usuarios=total_usuarios,
        total_pedidos=total_pedidos,
        total_ventas=total_ventas,
    )


@admin_bp.route('/usuarios', methods=['GET', 'POST'])
@login_required
def usuarios():
    if not admin_required():
        return redirect(url_for('tienda.index'))
    if request.method == 'POST':
        from flask import request
        user_id = request.form.get('user_id')
        nuevo_rol = request.form.get('rol')
        user = Usuario.query.get_or_404(int(user_id))
        user.rol = nuevo_rol
        db.session.commit()
        flash(f'Rol de {user.nombre} actualizado a {nuevo_rol}.', 'success')
    return redirect(url_for('admin.panel'))
