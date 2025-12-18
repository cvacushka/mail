"""
Интеграционные тесты для API эндпоинтов сообщений
"""
import pytest
import time
from datetime import datetime, timedelta
from app.models.message import Message
from app.models.user import User
from app.core.security import decode_access_token
from app.core.config import settings


def test_create_message_success(client, auth_headers, test_user2):
    """Тест успешного создания сообщения"""
    response = client.post(
        "/api/messages",
        headers=auth_headers,
        json={
            "recipient_id": test_user2.id,
            "subject": "Test Subject",
            "body": "Test Body"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["subject"] == "Test Subject"
    assert data["body"] == "Test Body"
    assert data["recipient_id"] == test_user2.id
    assert "id" in data


def test_create_message_with_attachments(client, auth_headers, test_user2):
    """Тест создания сообщения с вложениями"""
    response = client.post(
        "/api/messages",
        headers=auth_headers,
        json={
            "recipient_id": test_user2.id,
            "subject": "Test Subject",
            "body": "Test Body",
            "attachments": [
                {
                    "attachment_type": "item",
                    "item_id": 123,
                    "item_name": "Test Item",
                    "quantity": "1.0",
                    "attachment_data": {"rarity": "epic"}
                },
                {
                    "attachment_type": "gold",
                    "quantity": "100.0"
                }
            ]
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert len(data["attachments"]) == 2
    assert data["attachments"][0]["attachment_type"] == "item"
    assert data["attachments"][1]["attachment_type"] == "gold"


def test_create_message_unauthorized(client, test_user2):
    """Тест создания сообщения без авторизации"""
    response = client.post(
        "/api/messages",
        json={
            "recipient_id": test_user2.id,
            "subject": "Test Subject",
            "body": "Test Body"
        }
    )
    
    assert response.status_code == 401


def test_create_message_recipient_not_found(client, auth_headers):
    """Тест создания сообщения несуществующему получателю"""
    response = client.post(
        "/api/messages",
        headers=auth_headers,
        json={
            "recipient_id": 99999,
            "subject": "Test Subject",
            "body": "Test Body"
        }
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_message_to_self(client, auth_headers, test_user):
    """Тест отправки сообщения самому себе"""
    response = client.post(
        "/api/messages",
        headers=auth_headers,
        json={
            "recipient_id": test_user.id,
            "subject": "Test Subject",
            "body": "Test Body"
        }
    )
    
    assert response.status_code == 400
    assert "yourself" in response.json()["detail"].lower()


def test_create_message_spam_protection_min_interval(client, auth_headers, test_user2):
    """Тест защиты от спама - минимальный интервал между сообщениями"""
    # Отправляем первое сообщение
    response1 = client.post(
        "/api/messages",
        headers=auth_headers,
        json={
            "recipient_id": test_user2.id,
            "subject": "First Message",
            "body": "First Body"
        }
    )
    assert response1.status_code == 201
    
    # Сразу пытаемся отправить второе (должно быть заблокировано)
    response2 = client.post(
        "/api/messages",
        headers=auth_headers,
        json={
            "recipient_id": test_user2.id,
            "subject": "Second Message",
            "body": "Second Body"
        }
    )
    
    assert response2.status_code == 429
    assert "too many" in response2.json()["detail"].lower() or "wait" in response2.json()["detail"].lower()


def test_create_message_spam_protection_limit_per_minute(client, auth_headers, test_user2, db):
    """Тест защиты от спама - лимит сообщений в минуту"""
    # Получаем ID пользователя из токена
    token = auth_headers["Authorization"].replace("Bearer ", "")
    payload = decode_access_token(token)
    user = db.query(User).filter(User.username == payload["sub"]).first()
    
    # Удаляем все существующие сообщения от этого пользователя для чистоты теста
    db.query(Message).filter(Message.sender_id == user.id).delete()
    db.commit()
    
    # Создаем сообщения напрямую в БД в пределах одной минуты
    # Но с интервалами больше минимального, чтобы не сработала проверка интервала
    # Последнее сообщение должно быть достаточно давно, чтобы не сработал минимальный интервал
    base_time = datetime.utcnow() - timedelta(seconds=55)  # Почти минута назад
    for i in range(settings.MAX_MESSAGES_PER_MINUTE):
        msg = Message(
            sender_id=user.id,
            recipient_id=test_user2.id,
            subject=f"Test Subject {i}",
            body=f"Test Body {i}",
            created_at=base_time + timedelta(seconds=i * 5)  # По 5 секунд между сообщениями
        )
        db.add(msg)
    db.commit()
    
    # Ждем чтобы последнее сообщение было точно вне минимального интервала (3 сек)
    time.sleep(4)
    
    # Попытка отправить еще одно должно вызвать ошибку лимита в минуту
    response = client.post(
        "/api/messages",
        headers=auth_headers,
        json={
            "recipient_id": test_user2.id,
            "subject": "Spam",
            "body": "Spam"
        }
    )
    
    assert response.status_code == 429
    detail = response.json()["detail"].lower()
    assert "too many" in detail or "per minute" in detail


def test_create_message_duplicate_prevention(client, auth_headers, test_user2):
    """Тест защиты от дубликатов"""
    message_data = {
        "recipient_id": test_user2.id,
        "subject": "Test Subject",
        "body": "Test Body"
    }
    
    # Первое сообщение
    response = client.post(
        "/api/messages",
        headers=auth_headers,
        json=message_data
    )
    assert response.status_code == 201
    
    # Попытка отправить дубликат
    response = client.post(
        "/api/messages",
        headers=auth_headers,
        json=message_data
    )
    
    assert response.status_code == 400
    assert "identical" in response.json()["detail"].lower()


def test_get_inbox_messages(client, auth_headers, test_user, test_user2):
    """Тест получения входящих сообщений"""
    # Создаем сообщение от test_user2 к test_user
    # Сначала получаем токен для test_user2
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": test_user2.username,
            "password": "testpassword123"
        }
    )
    user2_token = login_response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    
    # Отправляем сообщение
    client.post(
        "/api/messages",
        headers=user2_headers,
        json={
            "recipient_id": test_user.id,
            "subject": "Test Subject",
            "body": "Test Body"
        }
    )
    
    # Получаем входящие сообщения
    response = client.get(
        "/api/messages",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["subject"] == "Test Subject"


def test_get_inbox_messages_unread_only(client, auth_headers, test_user, test_user2):
    """Тест получения только непрочитанных сообщений"""
    # Получаем токен для test_user2
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": test_user2.username,
            "password": "testpassword123"
        }
    )
    user2_token = login_response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    
    # Создаем 3 сообщения с задержкой
    message_ids = []
    for i in range(3):
        response = client.post(
            "/api/messages",
            headers=user2_headers,
            json={
                "recipient_id": test_user.id,
                "subject": f"Subject {i}",
                "body": f"Body {i}"
            }
        )
        assert response.status_code in [201, 429]  # Может быть 429 если слишком быстро
        if response.status_code == 201:
            message_ids.append(response.json()["id"])
        if i < 2:  # Не ждем после последнего
            time.sleep(4)  # Больше MIN_SECONDS_BETWEEN_MESSAGES
    
    # Отмечаем первое как прочитанное (если создалось)
    if message_ids:
        client.patch(
            f"/api/messages/{message_ids[0]}/read",
            headers=auth_headers
        )
    
    # Получаем только непрочитанные
    response = client.get(
        "/api/messages?unread_only=true",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    # Проверяем что есть непрочитанные сообщения
    assert len(data) >= 1
    assert all(not msg["is_read"] for msg in data)


def test_get_sent_messages(client, auth_headers, test_user2):
    """Тест получения отправленных сообщений"""
    # Отправляем сообщение
    client.post(
        "/api/messages",
        headers=auth_headers,
        json={
            "recipient_id": test_user2.id,
            "subject": "Test Subject",
            "body": "Test Body"
        }
    )
    
    # Получаем отправленные сообщения
    response = client.get(
        "/api/messages/sent",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["subject"] == "Test Subject"


def test_get_message_by_id(client, auth_headers, test_user2):
    """Тест получения конкретного сообщения"""
    # Создаем сообщение
    create_response = client.post(
        "/api/messages",
        headers=auth_headers,
        json={
            "recipient_id": test_user2.id,
            "subject": "Test Subject",
            "body": "Test Body"
        }
    )
    message_id = create_response.json()["id"]
    
    # Получаем сообщение
    response = client.get(
        f"/api/messages/{message_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == message_id
    assert data["subject"] == "Test Subject"


def test_get_message_unauthorized(client, auth_headers, test_user, test_user2):
    """Тест получения чужого сообщения"""
    # Получаем токен для test_user2
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": test_user2.username,
            "password": "testpassword123"
        }
    )
    user2_token = login_response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    
    # test_user2 отправляет сообщение test_user
    create_response = client.post(
        "/api/messages",
        headers=user2_headers,
        json={
            "recipient_id": test_user.id,
            "subject": "Test Subject",
            "body": "Test Body"
        }
    )
    message_id = create_response.json()["id"]
    
    # test_user получает сообщение (это нормально, он получатель)
    response = client.get(
        f"/api/messages/{message_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # Создаем третьего пользователя и пытаемся получить сообщение
    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "user3",
            "email": "user3@example.com",
            "password": "password123"
        }
    )
    assert register_response.status_code == 201
    
    # Логинимся для получения токена
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "user3",
            "password": "password123"
        }
    )
    assert login_response.status_code == 200
    user3_token = login_response.json()["access_token"]
    user3_headers = {"Authorization": f"Bearer {user3_token}"}
    
    # user3 не должен иметь доступа
    response = client.get(
        f"/api/messages/{message_id}",
        headers=user3_headers
    )
    assert response.status_code == 403


def test_mark_message_as_read(client, auth_headers, test_user, test_user2):
    """Тест отметки сообщения как прочитанного"""
    # Получаем токен для test_user2
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": test_user2.username,
            "password": "testpassword123"
        }
    )
    user2_token = login_response.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    
    # test_user2 отправляет сообщение test_user
    create_response = client.post(
        "/api/messages",
        headers=user2_headers,
        json={
            "recipient_id": test_user.id,
            "subject": "Test Subject",
            "body": "Test Body"
        }
    )
    message_id = create_response.json()["id"]
    
    # test_user отмечает как прочитанное
    response = client.patch(
        f"/api/messages/{message_id}/read",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_read"] is True
    assert data["read_at"] is not None


def test_mark_message_as_read_only_recipient(client, auth_headers, test_user2):
    """Тест что только получатель может отметить как прочитанное"""
    # Создаем сообщение
    create_response = client.post(
        "/api/messages",
        headers=auth_headers,
        json={
            "recipient_id": test_user2.id,
            "subject": "Test Subject",
            "body": "Test Body"
        }
    )
    message_id = create_response.json()["id"]
    
    # Отправитель не может отметить как прочитанное
    response = client.patch(
        f"/api/messages/{message_id}/read",
        headers=auth_headers
    )
    
    assert response.status_code == 403


def test_delete_message(client, auth_headers, test_user2):
    """Тест удаления сообщения"""
    # Создаем сообщение
    create_response = client.post(
        "/api/messages",
        headers=auth_headers,
        json={
            "recipient_id": test_user2.id,
            "subject": "Test Subject",
            "body": "Test Body"
        }
    )
    message_id = create_response.json()["id"]
    
    # Удаляем сообщение
    response = client.delete(
        f"/api/messages/{message_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    # Сообщение должно быть удалено для отправителя
    response = client.get(
        "/api/messages/sent",
        headers=auth_headers
    )
    data = response.json()
    assert not any(msg["id"] == message_id for msg in data)

