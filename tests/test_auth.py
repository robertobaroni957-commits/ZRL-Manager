import pytest
from newZRL import db
from newZRL.models.user import User
from werkzeug.security import generate_password_hash
from flask import session

def test_root_redirect_to_login(client):
    """Testa che la root reindirizzi alla pagina di login."""
    response = client.get("/")
    assert response.status_code == 302
    assert "/auth/login" in response.location

def test_login_page_loads(client):
    """Testa che la pagina di login si carichi correttamente."""
    response = client.get("/auth/login")
    assert response.status_code == 200
    assert b"Email" in response.data
    assert b"Password" in response.data

def test_successful_login_and_redirect(client, app):
    """Testa un login corretto e il reindirizzamento alla dashboard corretta."""
    with app.app_context():
        hashed_password = generate_password_hash("a_strong_password", method="pbkdf2:sha256")
        # Using a unique profile_id to avoid conflicts
        test_user = User(profile_id=1001, email="admin1@test.com", password=hashed_password, role="admin")
        db.session.add(test_user)
        db.session.commit()

    response = client.post("/auth/login", data={
        "email": "admin1@test.com",
        "password": "a_strong_password"
    }, follow_redirects=False)

    assert response.status_code == 302
    assert "/admin/dashboard" in response.location

    # Test that the session is set correctly
    with client.session_transaction() as sess:
        assert sess["user_id"] == 1001
        assert sess["user_role"] == "admin"

def test_login_wrong_password(client, app):
    """Testa un login con password errata."""
    with app.app_context():
        hashed_password = generate_password_hash("a_strong_password", method="pbkdf2:sha256")
        test_user = User(profile_id=1002, email="admin2@test.com", password=hashed_password, role="admin")
        db.session.add(test_user)
        db.session.commit()

    response = client.post("/auth/login", data={
        "email": "admin2@test.com",
        "password": "wrong_password"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert response.request.path == "/auth/login"
    assert b"Credenziali non valide" in response.data

def test_login_nonexistent_user(client):
    """Testa un login con un utente che non esiste."""
    response = client.post("/auth/login", data={
        "email": "nonexistent@example.com",
        "password": "some_password"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert response.request.path == "/auth/login"
    assert b"Credenziali non valide" in response.data

def test_logout(client, app):
    """Testa il logout."""
    with app.app_context():
        hashed_password = generate_password_hash("a_strong_password", method="pbkdf2:sha256")
        test_user = User(profile_id=1003, email="admin3@test.com", password=hashed_password, role="admin")
        db.session.add(test_user)
        db.session.commit()
    
    # Login first
    client.post("/auth/login", data={"email": "admin3@test.com", "password": "a_strong_password"})
    
    # Then logout
    response = client.get("/auth/logout", follow_redirects=True)
    assert response.status_code == 200
    assert response.request.path == "/auth/login"
    assert b"Logout effettuato con successo" in response.data