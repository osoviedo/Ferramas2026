from backend import db


class Carrito(db.Model):
    __tablename__ = 'carrito'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    productos = db.relationship('CarritoProducto', backref='carrito', lazy=True)


class CarritoProducto(db.Model):
    __tablename__ = 'carrito_productos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    carrito_id = db.Column(db.Integer, db.ForeignKey('carrito.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)

    producto = db.relationship('Producto', lazy=True)
