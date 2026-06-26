"""Fixtures compartidas para la suite de pruebas Ferramas."""
import pytest


@pytest.fixture
def app(tmp_path, monkeypatch):
    """App Flask con SQLite temporal aislado por test."""
    db_file = tmp_path / "test.db"
    db_uri = f"sqlite:///{db_file.as_posix()}"

    monkeypatch.setenv("DATABASE_URL", db_uri)
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("MP_ACCESS_TOKEN", "TEST-123456789-abcdef")
    monkeypatch.setenv("MP_PUBLIC_KEY", "TEST-public-key-abcdef")

    from app import create_app, db
    from app import _seed_data

    application = create_app()
    application.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    application.config["TESTING"] = True

    with application.app_context():
        db.engine.dispose()
        db.session.remove()
        db.drop_all()
        db.create_all()
        _seed_data()

    yield application

    with application.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Cliente con sesión iniciada como cliente demo."""
    client.post(
        "/login",
        data={"email": "cliente@ferramas.cl", "password": "cliente123"},
        follow_redirects=True,
    )
    return client
