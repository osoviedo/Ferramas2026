from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='cliente')
    rut = db.Column(db.String(20), default=None)
    sucursal_id = db.Column(db.Integer, default=None)
    descuento = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    carrito = db.relationship('Carrito', backref='usuario', lazy=True, uselist=False)
    pedidos = db.relationship('Pedido', backref='usuario', lazy=True)
    direcciones = db.relationship('Direccion', backref='usuario', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.rol == 'admin'

    def is_vendedor(self):
        return self.rol == 'vendedor'

    def is_bodeguero(self):
        return self.rol == 'bodeguero'


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
