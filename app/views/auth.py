import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)


def _sync_carrito_items(usuario_id, items):
    """Sincroniza items de localStorage al carrito BD del usuario."""
    from app.models.carrito import Carrito, CarritoProducto
    from app.models.producto import Producto
    carrito = Carrito.query.filter_by(usuario_id=usuario_id).first()
    if not carrito:
        carrito = Carrito(usuario_id=usuario_id)
        db.session.add(carrito)
        db.session.commit()
    for item_data in items:
        pid = item_data.get('id')
        cant = item_data.get('cantidad', 1)
        producto = Producto.query.get(pid)
        if not producto:
            continue
        cp = CarritoProducto.query.filter_by(
            carrito_id=carrito.id, producto_id=pid
        ).first()
        if cp:
            cp.cantidad = max(cp.cantidad, cant)
        else:
            db.session.add(CarritoProducto(
                carrito_id=carrito.id, producto_id=pid, cantidad=cant
            ))
    db.session.commit()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        user, error = AuthService.login(email, password)
        if error:
            flash(error, 'danger')
            return render_template('login.html')
        login_user(user)

        # Sincronizar carrito localStorage → BD al iniciar sesión
        items_json = request.form.get('items_carrito', '[]')
        try:
            items = json.loads(items_json)
            if items:
                _sync_carrito_items(user.id, items)
        except (json.JSONDecodeError, ValueError):
            pass

        flash('Inicio de sesión exitoso.', 'success')
        if user.rol == 'admin':
            return redirect(url_for('admin.panel'))
        elif user.rol == 'vendedor':
            return redirect(url_for('vendedor.panel'))
        elif user.rol == 'bodeguero':
            return redirect(url_for('bodeguero.panel'))
        return redirect(url_for('tienda.index'))
    return render_template('login.html')


@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        confirmar = request.form.get('confirmar', '')
        if password != confirmar:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('registro.html')
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
            return render_template('registro.html')
        user, error = AuthService.registrar(nombre, email, password)
        if error:
            flash(error, 'danger')
            return render_template('registro.html')
        login_user(user)
        from app.services.email_service import EmailService
        EmailService.enviar_bienvenida(user)
        flash('Registro exitoso.', 'success')
        return redirect(url_for('tienda.index'))
    return render_template('registro.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('tienda.index'))


@auth_bp.route('/perfil')
@login_required
def perfil():
    from app.models.pedido import Pedido
    pedidos = Pedido.query.filter_by(usuario_id=current_user.id).order_by(
        Pedido.created_at.desc()
    ).all()
    return render_template('perfil.html', pedidos=pedidos)
