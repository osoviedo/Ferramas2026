import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(basedir), '.env'))


class Config:
    # URL pública HTTPS (Render inyecta RENDER_EXTERNAL_URL automáticamente)
    PUBLIC_BASE_URL = (
        os.environ.get('PUBLIC_BASE_URL')
        or os.environ.get('RENDER_EXTERNAL_URL')
        or 'http://127.0.0.1:5000'
    ).rstrip('/')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-ferramas-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'sqlite:///' + os.path.join(os.path.dirname(basedir), 'ferramas.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MP_ACCESS_TOKEN = os.environ.get('MP_ACCESS_TOKEN', 'TEST-123456789-abcdef')
    MP_PUBLIC_KEY = os.environ.get('MP_PUBLIC_KEY', 'TEST-public-key-abcdef')
    DIVISA_CACHE_SEGUNDOS = int(os.environ.get('DIVISA_CACHE_SEGUNDOS', 3600))
    # Email (SMTP)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@ferramas.cl')

    # Demo local: auto-login Ferramas + credenciales comprador MP sandbox
    DEV_AUTO_LOGIN = os.environ.get('DEV_AUTO_LOGIN', 'false').lower() == 'true'
    DEV_LOGIN_EMAIL = os.environ.get('DEV_LOGIN_EMAIL', 'cliente@ferramas.cl')
    DEV_LOGIN_PASSWORD = os.environ.get('DEV_LOGIN_PASSWORD', 'cliente123')
    MP_TEST_BUYER_USER = os.environ.get('MP_TEST_BUYER_USER', '')
    MP_TEST_BUYER_PASSWORD = os.environ.get('MP_TEST_BUYER_PASSWORD', '')
