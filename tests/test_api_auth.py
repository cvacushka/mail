"""
Интеграционные тесты для API эндпоинтов аутентификации
"""
import pytest


def test_register_success(client):
    """Тест успешной регистрации"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "password" not in data  # Пароль не должен быть в ответе


def test_register_duplicate_username(client, test_user):
    """Тест регистрации с дублирующимся username"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": test_user.username,
            "email": "different@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_register_duplicate_email(client, test_user):
    """Тест регистрации с дублирующимся email"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "differentuser",
            "email": test_user.email,
            "password": "password123"
        }
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_register_validation_error(client):
    """Тест валидации данных при регистрации"""
    # Слишком короткий username
    response = client.post(
        "/api/auth/register",
        json={
            "username": "ab",
            "email": "test@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 422


def test_register_invalid_email(client):
    """Тест регистрации с невалидным email"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123"
        }
    )
    
    assert response.status_code == 422


def test_register_short_password(client):
    """Тест регистрации с коротким паролем"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "12345"  # Меньше 6 символов
        }
    )
    
    assert response.status_code == 422


def test_login_success(client, test_user):
    """Тест успешного входа"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user.username,
            "password": "testpassword123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_login_wrong_username(client):
    """Тест входа с неверным username"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "nonexistent",
            "password": "password123"
        }
    )
    
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_wrong_password(client, test_user):
    """Тест входа с неверным паролем"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user.username,
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()


def test_login_inactive_user(client, inactive_user):
    """Тест входа неактивного пользователя"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": inactive_user.username,
            "password": "testpassword123"
        }
    )
    
    assert response.status_code == 403

