from app import db
from app.models.usuario import Usuario
from app.models.carrito import Carrito


class AuthService:

    @staticmethod
    def registrar(nombre, email, password, rol='cliente', rut=None):
        if Usuario.query.filter_by(email=email).first():
            return None, 'El email ya está registrado.'
        user = Usuario(nombre=nombre, email=email, rol=rol, rut=rut)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        carrito = Carrito(usuario_id=user.id)
        db.session.add(carrito)
        db.session.commit()
        return user, None

    @staticmethod
    def login(email, password):
        user = Usuario.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return None, 'Email o contraseña incorrectos.'
        return user, None

    @staticmethod
    def cambiar_password(user, current_password, new_password):
        if not user.check_password(current_password):
            return False, 'Contraseña actual incorrecta.'
        user.set_password(new_password)
        db.session.commit()
        return True, None
