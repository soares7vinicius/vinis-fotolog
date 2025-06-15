from sqlmodel import Session
from src.db import get_db
from src.models.models import User


def create_user(engine, username="john", password="secret"):
    with Session(engine) as session:
        user = User(username=username, password=User.hash_password(password))
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def test_login_success(client, engine):
    create_user(engine, "alice", "wonderland")
    response = client.post(
        "/login", json={"username": "alice", "password": "wonderland"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Success"
    assert "user_id" in data


def test_login_invalid_credentials(client, engine):
    create_user(engine, "bob", "builder")
    response = client.post("/login", json={"username": "bob", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_logout(client, engine):
    create_user(engine, "charlie", "chocolate")
    login_resp = client.post(
        "/login", json={"username": "charlie", "password": "chocolate"}
    )
    assert login_resp.status_code == 200
    assert client.cookies.get("session") is not None

    logout_resp = client.post("/logout")
    assert logout_resp.status_code == 200
