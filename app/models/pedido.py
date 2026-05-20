from app import db


class Pedido(db.Model):
    __tablename__ = 'pedidos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='pendiente')
    direccion_despacho = db.Column(db.String(255), default=None)
    sucursal_retiro = db.Column(db.String(100), default=None)
    modo_entrega = db.Column(db.String(20), nullable=False, default='retiro')
    total = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    productos = db.relationship('PedidoProducto', backref='pedido', lazy=True)
    pago = db.relationship('Pago', backref='pedido', lazy=True, uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'estado': self.estado,
            'modo_entrega': self.modo_entrega,
            'total': self.total,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class PedidoProducto(db.Model):
    __tablename__ = 'pedido_productos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Integer, nullable=False)

    producto = db.relationship('Producto', lazy=True)


class Pago(db.Model):
    __tablename__ = 'pagos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    metodo = db.Column(db.String(50), nullable=False, default='mercadopago')
    estado = db.Column(db.String(20), nullable=False, default='pendiente')
    transaccion_id = db.Column(db.String(255), default=None)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())


class Direccion(db.Model):
    __tablename__ = 'direcciones'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    direccion = db.Column(db.String(255), nullable=False)
    comuna = db.Column(db.String(100), default=None)
    region = db.Column(db.String(100), default=None)
