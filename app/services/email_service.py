import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


class EmailService:

    @staticmethod
    def _enviar_real(destinatario, asunto, cuerpo_html):
        """Envía un correo real vía SMTP. Retorna True si se envió, False si no."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = asunto
            msg['From'] = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@ferramas.cl')
            msg['To'] = destinatario
            msg.attach(MIMEText(cuerpo_html, 'html', 'utf-8'))

            server = smtplib.SMTP(
                current_app.config.get('MAIL_SERVER', 'smtp.gmail.com'),
                current_app.config.get('MAIL_PORT', 587),
                timeout=10,
            )
            server.ehlo()
            if current_app.config.get('MAIL_USE_TLS', True):
                server.starttls()
                server.ehlo()
            username = current_app.config.get('MAIL_USERNAME', '')
            password = current_app.config.get('MAIL_PASSWORD', '')
            if username and password:
                server.login(username, password)
            server.sendmail(msg['From'], [destinatario], msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f'[EMAIL ERROR] {e}')
            return False

    @staticmethod
    def _tiene_credenciales():
        return bool(
            current_app.config.get('MAIL_USERNAME', '') and
            current_app.config.get('MAIL_PASSWORD', '')
        )

    @staticmethod
    def enviar_bienvenida(usuario):
        """Envía correo de bienvenida tras registro."""
        asunto = '¡Bienvenido a Ferramas!'
        cuerpo = f'''
        <div style="background:#2c1a0e; color:#fff; padding:32px; font-family:sans-serif; border-radius:12px;">
            <h1 style="color:#e8601a;">¡Bienvenido a Ferramas, {usuario.nombre}!</h1>
            <p>Tu cuenta ha sido creada exitosamente.</p>
            <p>Empieza a comprar las mejores herramientas y materiales de ferretería.</p>
            <a href="http://localhost:5000" style="display:inline-block; background:#e8601a; color:#fff; padding:10px 24px; border-radius:8px; text-decoration:none; margin-top:12px;">
                Ir a la tienda
            </a>
            <p style="margin-top:24px; color:rgba(255,255,255,0.5); font-size:12px;">
                Ferramas — Tu ferretería de confianza
            </p>
        </div>
        '''
        if EmailService._tiene_credenciales():
            ok = EmailService._enviar_real(usuario.email, asunto, cuerpo)
            if ok:
                return True
        print(f'[EMAIL SIMULADO] Para: {usuario.email}')
        print(f'[EMAIL SIMULADO] Asunto: {asunto}')
        return True

    @staticmethod
    def enviar_confirmacion_pedido(usuario, pedido):
        asunto = f'Pedido #{pedido.id} confirmado — Ferramas'
        cuerpo = f'''
        <div style="background:#2c1a0e; color:#fff; padding:32px; font-family:sans-serif; border-radius:12px;">
            <h1 style="color:#1d9e75;">¡Pedido confirmado!</h1>
            <p>Hola {usuario.nombre}, tu pedido <strong>#{pedido.id}</strong> ha sido confirmado.</p>
            <p style="font-size:20px; color:#e8601a;">Total: ${pedido.total}</p>
            <p style="margin-top:16px; color:rgba(255,255,255,0.6);">
                Estado: <span style="color:#1d9e75;">{pedido.estado}</span><br>
                Entrega: {pedido.modo_entrega}
            </p>
        </div>
        '''
        if EmailService._tiene_credenciales():
            ok = EmailService._enviar_real(usuario.email, asunto, cuerpo)
            if ok:
                return True
        print(f'[EMAIL SIMULADO] Para: {usuario.email}')
        print(f'[EMAIL SIMULADO] Asunto: {asunto}')
        print(f'[EMAIL SIMULADO] Total: ${pedido.total}')
        return True

    @staticmethod
    def enviar_cambio_estado(usuario, pedido, nuevo_estado):
        asunto = f'Pedido #{pedido.id} — {nuevo_estado}'
        cuerpo = f'''
        <div style="background:#2c1a0e; color:#fff; padding:32px; font-family:sans-serif; border-radius:12px;">
            <h1 style="color:#378add;">Actualización de pedido</h1>
            <p>Hola {usuario.nombre}, tu pedido <strong>#{pedido.id}</strong> ha cambiado a:</p>
            <p style="font-size:18px; color:#e8601a; text-transform:capitalize;">{nuevo_estado}</p>
        </div>
        '''
        if EmailService._tiene_credenciales():
            ok = EmailService._enviar_real(usuario.email, asunto, cuerpo)
            if ok:
                return True
        print(f'[EMAIL SIMULADO] Para: {usuario.email}')
        print(f'[EMAIL SIMULADO] Asunto: {asunto}')
        return True
