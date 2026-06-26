import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(basedir), '.env'), override=True)


class Config:
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
