from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.message import Message
from app.models.attachment import Attachment
from app.models.user import User
from app.schemas.message import MessageCreate, AttachmentCreate
from app.core.config import settings


class MessageService:
    @staticmethod
    def _check_spam_protection(
        db: Session,
        sender_id: int,
        recipient_id: int,
        subject: str,
        body: str
    ) -> None:
        """Проверка защиты от спама"""
        now = datetime.utcnow()
        
        # 1. Проверка на дубликаты (проверяем первым, так как это более специфичная проверка)
        duplicate_window_ago = now - timedelta(seconds=settings.DUPLICATE_MESSAGE_WINDOW_SECONDS)
        duplicate_message = db.query(Message).filter(
            and_(
                Message.sender_id == sender_id,
                Message.recipient_id == recipient_id,
                Message.subject == subject,
                Message.body == body,
                Message.created_at >= duplicate_window_ago
            )
        ).first()
        
        if duplicate_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have recently sent an identical message to this recipient. Please wait before sending duplicates."
            )
        
        # 2. Проверка минимального интервала между сообщениями
        min_interval_ago = now - timedelta(seconds=settings.MIN_SECONDS_BETWEEN_MESSAGES)
        recent_message = db.query(Message).filter(
            and_(
                Message.sender_id == sender_id,
                Message.created_at >= min_interval_ago
            )
        ).order_by(Message.created_at.desc()).first()
        
        if recent_message:
            seconds_ago = (now - recent_message.created_at).total_seconds()
            # Проверяем что сообщение действительно недавнее (не отрицательное время)
            if seconds_ago >= 0 and seconds_ago < settings.MIN_SECONDS_BETWEEN_MESSAGES:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Please wait {settings.MIN_SECONDS_BETWEEN_MESSAGES} seconds between messages. Last message was sent {int(seconds_ago)} seconds ago."
                )
        
        # 3. Проверка лимита сообщений в минуту
        one_minute_ago = now - timedelta(minutes=1)
        messages_last_minute = db.query(func.count(Message.id)).filter(
            and_(
                Message.sender_id == sender_id,
                Message.created_at >= one_minute_ago
            )
        ).scalar()
        
        if messages_last_minute >= settings.MAX_MESSAGES_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many messages sent. Maximum {settings.MAX_MESSAGES_PER_MINUTE} messages per minute allowed."
            )
        
        # 4. Проверка лимита сообщений в час
        one_hour_ago = now - timedelta(hours=1)
        messages_last_hour = db.query(func.count(Message.id)).filter(
            and_(
                Message.sender_id == sender_id,
                Message.created_at >= one_hour_ago
            )
        ).scalar()
        
        if messages_last_hour >= settings.MAX_MESSAGES_PER_HOUR:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many messages sent. Maximum {settings.MAX_MESSAGES_PER_HOUR} messages per hour allowed."
            )
    
    @staticmethod
    def create_message(
        db: Session,
        message_data: MessageCreate,
        sender_id: int
    ) -> Message:
        """Создание нового сообщения с защитой от спама"""
        # Проверка существования получателя
        recipient = db.query(User).filter(User.id == message_data.recipient_id).first()
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient not found"
            )
        
        if not recipient.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send message to inactive user"
            )
        
        # Проверка, что пользователь не отправляет сообщение самому себе
        if sender_id == message_data.recipient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot send message to yourself"
            )
        
        # Проверка защиты от спама
        MessageService._check_spam_protection(
            db, sender_id, message_data.recipient_id, message_data.subject, message_data.body
        )
        
        # Создание сообщения
        db_message = Message(
            sender_id=sender_id,
            recipient_id=message_data.recipient_id,
            subject=message_data.subject,
            body=message_data.body
        )
        
        db.add(db_message)
        db.flush()  # Получаем ID сообщения
        
        # Создание вложений
        if message_data.attachments:
            for attachment_data in message_data.attachments:
                db_attachment = Attachment(
                    message_id=db_message.id,
                    attachment_type=attachment_data.attachment_type,
                    item_id=attachment_data.item_id,
                    item_name=attachment_data.item_name,
                    quantity=attachment_data.quantity,
                    attachment_data=attachment_data.attachment_data
                )
                db.add(db_attachment)
        
        db.commit()
        db.refresh(db_message)
        
        return db_message
    
    @staticmethod
    def get_inbox_messages(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Message]:
        """Получение входящих сообщений"""
        query = db.query(Message).filter(
            and_(
                Message.recipient_id == user_id,
                Message.is_deleted_by_recipient == False
            )
        )
        
        if unread_only:
            query = query.filter(Message.is_read == False)
        
        return query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_sent_messages(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[Message]:
        """Получение отправленных сообщений"""
        return db.query(Message).filter(
            and_(
                Message.sender_id == user_id,
                Message.is_deleted_by_sender == False
            )
        ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_message_by_id(
        db: Session,
        message_id: int,
        user_id: int
    ) -> Message:
        """Получение сообщения по ID с проверкой прав доступа"""
        message = db.query(Message).filter(Message.id == message_id).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Проверка прав доступа
        if message.sender_id != user_id and message.recipient_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Проверка удаления
        if message.sender_id == user_id and message.is_deleted_by_sender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        if message.recipient_id == user_id and message.is_deleted_by_recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        return message
    
    @staticmethod
    def mark_as_read(
        db: Session,
        message_id: int,
        user_id: int
    ) -> Message:
        """Отметка сообщения как прочитанного"""
        message = MessageService.get_message_by_id(db, message_id, user_id)
        
        # Только получатель может отметить как прочитанное
        if message.recipient_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only recipient can mark message as read"
            )
        
        if not message.is_read:
            message.is_read = True
            message.read_at = datetime.utcnow()
            db.commit()
            db.refresh(message)
        
        return message
    
    @staticmethod
    def delete_message(
        db: Session,
        message_id: int,
        user_id: int
    ) -> None:
        """Удаление сообщения (мягкое удаление)"""
        message = MessageService.get_message_by_id(db, message_id, user_id)
        
        if message.sender_id == user_id:
            message.is_deleted_by_sender = True
        elif message.recipient_id == user_id:
            message.is_deleted_by_recipient = True
        
        db.commit()

