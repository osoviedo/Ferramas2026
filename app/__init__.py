from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Debes iniciar sesión para acceder.'


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    CORS(app)

    login_manager.init_app(app)

    from app.models.usuario import Usuario
    from app.models.producto import Producto
    from app.models.pedido import Pedido, PedidoProducto, Pago, Direccion
    from app.models.carrito import Carrito, CarritoProducto
    from app.models.suscriptor import Suscriptor

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    from app.api.producto_api import api_bp
    from app.views.auth import auth_bp
    from app.views.tienda import tienda_bp
    from app.views.carrito import carrito_bp
    from app.views.vendedor import vendedor_bp
    from app.views.bodeguero import bodeguero_bp
    from app.views.admin import admin_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tienda_bp)
    app.register_blueprint(carrito_bp)
    app.register_blueprint(vendedor_bp)
    app.register_blueprint(bodeguero_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        _seed_data()

    return app


def _seed_data():
    """Puebla productos y usuarios por defecto si las tablas están vacías."""
    from app.models.producto import Producto
    from app.models.usuario import Usuario

    if Producto.query.count() == 0:
        productos_data = [
            ('Martillo', 8500, 50, 'herramientas manuales', 'Martillo.jpg'),
            ('Llave', 6200, 40, 'herramientas manuales', 'Llave.jpg'),
            ('Destornillador', 3500, 60, 'herramientas manuales', 'Destornillador.jpg'),
            ('Casco', 12000, 30, 'equipos de seguridad', 'Casco.jpg'),
            ('Guantes', 4500, 45, 'equipos de seguridad', 'Guantes.jpg'),
            ('Arnes', 28000, 15, 'equipos de seguridad', 'Arnes.jpg'),
            ('Perno', 1500, 100, 'fijaciones', 'Perno.jpg'),
            ('Tuerca', 800, 120, 'fijaciones', 'Tuerca.jpg'),
            ('Clavo', 600, 200, 'fijaciones', 'Clavo.jpg'),
            ('Cemento', 5500, 80, 'materiales basicos', 'Cemento.jpg'),
            ('Arena', 3200, 90, 'materiales basicos', 'Arena.jpg'),
            ('Yeso', 4000, 70, 'materiales basicos', 'Yeso.jpg'),
            ('Tornillo', 1200, 150, 'tornillos y anclaje', 'Tornillo.jpg'),
            ('Taco', 900, 130, 'tornillos y anclaje', 'Taco.jpg'),
            ('Esparrago', 2500, 55, 'tornillos y anclaje', 'Esparrago.jpg'),
            ('Nivel', 9500, 25, 'equipos de medicion', 'Nivel.jpg'),
            ('Metro', 3800, 35, 'equipos de medicion', 'Metro.jpg'),
            ('Escuadra', 4200, 40, 'equipos de medicion', 'Escuadra.jpg'),
        ]
        for nombre, precio, stock, categoria, imagen in productos_data:
            db.session.add(Producto(
                nombre=nombre, precio=precio, stock=stock,
                categoria=categoria, imagen=imagen
            ))
        db.session.commit()

    if Usuario.query.count() == 0:
        roles = [
            ('Admin', 'admin@ferramas.cl', 'admin123', 'admin', 0),
            ('Vendedor', 'vendedor@ferramas.cl', 'vendedor123', 'vendedor', 0),
            ('Bodeguero', 'bodeguero@ferramas.cl', 'bodeguero123', 'bodeguero', 0),
            ('Cliente Demo', 'cliente@ferramas.cl', 'cliente123', 'cliente', 10),
        ]
        for nombre, email, password, rol, descuento in roles:
            user = Usuario(nombre=nombre, email=email, rol=rol, descuento=descuento)
            user.set_password(password)
            db.session.add(user)
        db.session.commit()
