"""
Unit тесты для AuthService
"""
import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.services.auth_service import AuthService
from app.schemas.user import UserCreate
from app.models.user import User


def test_register_user_success(db):
    """Тест успешной регистрации пользователя"""
    user_data = UserCreate(
        username="newuser",
        email="newuser@example.com",
        password="securepassword123"
    )
    
    user = AuthService.register_user(db, user_data)
    
    assert user.id is not None
    assert user.username == "newuser"
    assert user.email == "newuser@example.com"
    assert user.hashed_password != "securepassword123"  # Должен быть захеширован
    assert user.is_active is True


def test_register_user_duplicate_username(db, test_user):
    """Тест регистрации с дублирующимся username"""
    user_data = UserCreate(
        username=test_user.username,
        email="different@example.com",
        password="password123"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        AuthService.register_user(db, user_data)
    
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username already registered" in exc_info.value.detail


def test_register_user_duplicate_email(db, test_user):
    """Тест регистрации с дублирующимся email"""
    user_data = UserCreate(
        username="differentuser",
        email=test_user.email,
        password="password123"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        AuthService.register_user(db, user_data)
    
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email already registered" in exc_info.value.detail


def test_authenticate_user_success(db, test_user):
    """Тест успешной аутентификации"""
    user = AuthService.authenticate_user(db, "testuser", "testpassword123")
    
    assert user is not None
    assert user.id == test_user.id
    assert user.username == "testuser"


def test_authenticate_user_wrong_username(db):
    """Тест аутентификации с неверным username"""
    user = AuthService.authenticate_user(db, "nonexistent", "password123")
    
    assert user is None


def test_authenticate_user_wrong_password(db, test_user):
    """Тест аутентификации с неверным паролем"""
    user = AuthService.authenticate_user(db, "testuser", "wrongpassword")
    
    assert user is None


def test_authenticate_user_inactive(db, inactive_user):
    """Тест аутентификации неактивного пользователя"""
    with pytest.raises(HTTPException) as exc_info:
        AuthService.authenticate_user(db, "inactive", "testpassword123")
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Inactive user" in exc_info.value.detail


def test_create_token_for_user(test_user):
    """Тест создания JWT токена"""
    token = AuthService.create_token_for_user(test_user)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0

