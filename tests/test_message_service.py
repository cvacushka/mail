"""
Unit тесты для MessageService
"""
import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from decimal import Decimal

from app.services.message_service import MessageService
from app.schemas.message import MessageCreate, AttachmentCreate
from app.models.message import Message
from app.models.user import User


def test_create_message_success(db, test_user, test_user2):
    """Тест успешного создания сообщения"""
    message_data = MessageCreate(
        recipient_id=test_user2.id,
        subject="Test Subject",
        body="Test Body"
    )
    
    message = MessageService.create_message(db, message_data, test_user.id)
    
    assert message.id is not None
    assert message.sender_id == test_user.id
    assert message.recipient_id == test_user2.id
    assert message.subject == "Test Subject"
    assert message.body == "Test Body"
    assert message.is_read is False


def test_create_message_with_attachments(db, test_user, test_user2):
    """Тест создания сообщения с вложениями"""
    attachments = [
        AttachmentCreate(
            attachment_type="item",
            item_id=123,
            item_name="Test Item",
            quantity=Decimal("1.0"),
            attachment_data={"rarity": "epic"}
        ),
        AttachmentCreate(
            attachment_type="gold",
            quantity=Decimal("100.0")
        )
    ]
    
    message_data = MessageCreate(
        recipient_id=test_user2.id,
        subject="Test Subject",
        body="Test Body",
        attachments=attachments
    )
    
    message = MessageService.create_message(db, message_data, test_user.id)
    
    assert message.id is not None
    assert len(message.attachments) == 2
    assert message.attachments[0].attachment_type == "item"
    assert message.attachments[1].attachment_type == "gold"


def test_create_message_recipient_not_found(db, test_user):
    """Тест создания сообщения несуществующему получателю"""
    message_data = MessageCreate(
        recipient_id=99999,
        subject="Test Subject",
        body="Test Body"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        MessageService.create_message(db, message_data, test_user.id)
    
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Recipient not found" in exc_info.value.detail


def test_create_message_inactive_recipient(db, test_user, inactive_user):
    """Тест создания сообщения неактивному получателю"""
    message_data = MessageCreate(
        recipient_id=inactive_user.id,
        subject="Test Subject",
        body="Test Body"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        MessageService.create_message(db, message_data, test_user.id)
    
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot send message to inactive user" in exc_info.value.detail


def test_create_message_to_self(db, test_user):
    """Тест отправки сообщения самому себе"""
    message_data = MessageCreate(
        recipient_id=test_user.id,
        subject="Test Subject",
        body="Test Body"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        MessageService.create_message(db, message_data, test_user.id)
    
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot send message to yourself" in exc_info.value.detail


def test_create_message_spam_limit_per_minute(db, test_user, test_user2):
    """Тест защиты от спама - лимит сообщений в минуту"""
    from app.core.config import settings
    
    # Создаем сообщения напрямую в БД в пределах одной минуты
    # чтобы проверить лимит сообщений
    base_time = datetime.utcnow() - timedelta(seconds=30)
    for i in range(settings.MAX_MESSAGES_PER_MINUTE):
        msg = Message(
            sender_id=test_user.id,
            recipient_id=test_user2.id,
            subject=f"Test Subject {i}",
            body=f"Test Body {i}",
            created_at=base_time + timedelta(seconds=i * 3)  # По 3 секунды между сообщениями
        )
        db.add(msg)
    db.commit()
    
    # Теперь попытка создать через сервис должна проверить лимит
    message_data = MessageCreate(
        recipient_id=test_user2.id,
        subject="Spam",
        body="Spam"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        MessageService.create_message(db, message_data, test_user.id)
    
    assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Too many messages" in exc_info.value.detail
    assert "per minute" in exc_info.value.detail.lower()


def test_create_message_spam_limit_per_hour(db, test_user, test_user2):
    """Тест защиты от спама - лимит сообщений в час"""
    from app.core.config import settings
    import time
    
    # Удаляем все существующие сообщения от этого пользователя для чистоты теста
    db.query(Message).filter(Message.sender_id == test_user.id).delete()
    db.commit()
    
    # Создаем сообщения напрямую в БД в пределах одного часа
    # НО не в пределах последней минуты, чтобы не сработал лимит в минуту
    # Распределяем сообщения так: первые 50 сообщений созданы между 2 и 61 минутами назад
    # Таким образом они будут в пределах часа, но не в пределах последней минуты
    base_time = datetime.utcnow() - timedelta(minutes=61)  # 61 минута назад
    for i in range(settings.MAX_MESSAGES_PER_HOUR):
        # Создаем сообщения начиная с 2 минут назад (чтобы не попасть в последнюю минуту)
        msg_time = base_time + timedelta(minutes=2 + i)  # От 2 до 51 минуты назад
        msg = Message(
            sender_id=test_user.id,
            recipient_id=test_user2.id,
            subject=f"Test Subject {i}",
            body=f"Test Body {i}",
            created_at=msg_time
        )
        db.add(msg)
    db.commit()
    
    # Ждем чтобы последнее сообщение было точно вне минимального интервала
    time.sleep(4)
    
    # Теперь попытка создать через сервис должна проверить лимит в час
    message_data = MessageCreate(
        recipient_id=test_user2.id,
        subject="Spam Hour",
        body="Spam Hour"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        MessageService.create_message(db, message_data, test_user.id)
    
    assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Too many messages" in exc_info.value.detail
    assert "per hour" in exc_info.value.detail.lower()


def test_create_message_min_interval_protection(db, test_user, test_user2):
    """Тест защиты от спама - минимальный интервал между сообщениями"""
    from app.core.config import settings
    
    # Создаем сообщение через сервис (это успешно)
    message_data1 = MessageCreate(
        recipient_id=test_user2.id,
        subject="First Message",
        body="First Body"
    )
    MessageService.create_message(db, message_data1, test_user.id)
    
    # Сразу пытаемся отправить второе (должно быть заблокировано)
    message_data2 = MessageCreate(
        recipient_id=test_user2.id,
        subject="Second Message",
        body="Second Body"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        MessageService.create_message(db, message_data2, test_user.id)
    
    assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "wait" in exc_info.value.detail.lower() or "seconds" in exc_info.value.detail.lower()


def test_create_message_duplicate_prevention(db, test_user, test_user2):
    """Тест защиты от дубликатов сообщений"""
    # Создаем первое сообщение через сервис (успешно)
    message_data = MessageCreate(
        recipient_id=test_user2.id,
        subject="Test Subject",
        body="Test Body"
    )
    MessageService.create_message(db, message_data, test_user.id)
    
    # Ждем минимальный интервал, но не ждем до истечения окна дубликатов
    import time
    time.sleep(4)  # Больше чем MIN_SECONDS_BETWEEN_MESSAGES (3 сек), но в пределах DUPLICATE_WINDOW
    
    # Теперь попытка создать дубликат через сервис должна быть заблокирована
    message_data2 = MessageCreate(
        recipient_id=test_user2.id,
        subject="Test Subject",
        body="Test Body"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        MessageService.create_message(db, message_data2, test_user.id)
    
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "identical message" in exc_info.value.detail.lower()


def test_get_inbox_messages(db, test_user, test_user2):
    """Тест получения входящих сообщений"""
    import time
    # Создаем несколько сообщений с задержкой, чтобы обойти минимальный интервал
    for i in range(3):
        message_data = MessageCreate(
            recipient_id=test_user.id,
            subject=f"Subject {i}",
            body=f"Body {i}"
        )
        MessageService.create_message(db, message_data, test_user2.id)
        if i < 2:  # Не ждем после последнего
            time.sleep(4)  # Больше MIN_SECONDS_BETWEEN_MESSAGES
    
    messages = MessageService.get_inbox_messages(db, test_user.id)
    
    assert len(messages) == 3
    assert all(msg.recipient_id == test_user.id for msg in messages)


def test_get_inbox_messages_unread_only(db, test_user, test_user2):
    """Тест получения только непрочитанных сообщений"""
    import time
    # Создаем сообщения с задержкой
    message_ids = []
    for i in range(5):
        message_data = MessageCreate(
            recipient_id=test_user.id,
            subject=f"Subject {i}",
            body=f"Body {i}"
        )
        msg = MessageService.create_message(db, message_data, test_user2.id)
        message_ids.append(msg.id)
        if i < 4:  # Не ждем после последнего
            time.sleep(4)  # Больше MIN_SECONDS_BETWEEN_MESSAGES
    
    # Отмечаем первые 2 как прочитанные
    for msg_id in message_ids[:2]:
        MessageService.mark_as_read(db, msg_id, test_user.id)
    
    unread_messages = MessageService.get_inbox_messages(
        db, test_user.id, unread_only=True
    )
    
    assert len(unread_messages) == 3
    assert all(not msg.is_read for msg in unread_messages)


def test_get_sent_messages(db, test_user, test_user2):
    """Тест получения отправленных сообщений"""
    import time
    # Создаем несколько сообщений с задержкой
    for i in range(3):
        message_data = MessageCreate(
            recipient_id=test_user2.id,
            subject=f"Subject {i}",
            body=f"Body {i}"
        )
        MessageService.create_message(db, message_data, test_user.id)
        if i < 2:  # Не ждем после последнего
            time.sleep(4)  # Больше MIN_SECONDS_BETWEEN_MESSAGES
    
    messages = MessageService.get_sent_messages(db, test_user.id)
    
    assert len(messages) == 3
    assert all(msg.sender_id == test_user.id for msg in messages)


def test_get_message_by_id_success(db, test_user, test_user2):
    """Тест получения сообщения по ID"""
    message_data = MessageCreate(
        recipient_id=test_user2.id,
        subject="Test Subject",
        body="Test Body"
    )
    message = MessageService.create_message(db, message_data, test_user.id)
    
    retrieved = MessageService.get_message_by_id(db, message.id, test_user.id)
    
    assert retrieved.id == message.id
    assert retrieved.subject == "Test Subject"


def test_get_message_by_id_unauthorized(db, test_user, test_user2):
    """Тест получения чужого сообщения"""
    message_data = MessageCreate(
        recipient_id=test_user2.id,
        subject="Test Subject",
        body="Test Body"
    )
    message = MessageService.create_message(db, message_data, test_user.id)
    
    # Создаем третьего пользователя
    user3 = User(
        username="user3",
        email="user3@example.com",
        hashed_password="hash",
        is_active=True
    )
    db.add(user3)
    db.commit()
    db.refresh(user3)
    
    with pytest.raises(HTTPException) as exc_info:
        MessageService.get_message_by_id(db, message.id, user3.id)
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


def test_mark_as_read_success(db, test_user, test_user2):
    """Тест отметки сообщения как прочитанного"""
    message_data = MessageCreate(
        recipient_id=test_user.id,
        subject="Test Subject",
        body="Test Body"
    )
    message = MessageService.create_message(db, message_data, test_user2.id)
    
    assert message.is_read is False
    
    updated = MessageService.mark_as_read(db, message.id, test_user.id)
    
    assert updated.is_read is True
    assert updated.read_at is not None


def test_mark_as_read_only_recipient(db, test_user, test_user2):
    """Тест что только получатель может отметить как прочитанное"""
    message_data = MessageCreate(
        recipient_id=test_user.id,
        subject="Test Subject",
        body="Test Body"
    )
    message = MessageService.create_message(db, message_data, test_user2.id)
    
    # Отправитель не может отметить
    with pytest.raises(HTTPException) as exc_info:
        MessageService.mark_as_read(db, message.id, test_user2.id)
    
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


def test_delete_message_by_sender(db, test_user, test_user2):
    """Тест мягкого удаления сообщения отправителем"""
    message_data = MessageCreate(
        recipient_id=test_user2.id,
        subject="Test Subject",
        body="Test Body"
    )
    message = MessageService.create_message(db, message_data, test_user.id)
    
    MessageService.delete_message(db, message.id, test_user.id)
    
    db.refresh(message)
    assert message.is_deleted_by_sender is True
    assert message.is_deleted_by_recipient is False
    
    # Получатель все еще видит сообщение
    retrieved = MessageService.get_message_by_id(db, message.id, test_user2.id)
    assert retrieved is not None


def test_delete_message_by_recipient(db, test_user, test_user2):
    """Тест мягкого удаления сообщения получателем"""
    message_data = MessageCreate(
        recipient_id=test_user.id,
        subject="Test Subject",
        body="Test Body"
    )
    message = MessageService.create_message(db, message_data, test_user2.id)
    
    MessageService.delete_message(db, message.id, test_user.id)
    
    db.refresh(message)
    assert message.is_deleted_by_recipient is True
    assert message.is_deleted_by_sender is False
    
    # Отправитель все еще видит сообщение
    retrieved = MessageService.get_message_by_id(db, message.id, test_user2.id)
    assert retrieved is not None

