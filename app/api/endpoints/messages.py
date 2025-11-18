from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_active_user
from app.schemas.message import MessageCreate, MessageResponse, MessageUpdate
from app.services.message_service import MessageService

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.get("", response_model=List[MessageResponse])
def get_inbox_messages(
    skip: int = Query(0, ge=0, description="Количество пропущенных записей"),
    limit: int = Query(50, ge=1, le=100, description="Максимальное количество записей"),
    unread_only: bool = Query(False, description="Показать только непрочитанные"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получение списка входящих сообщений
    
    - **skip**: количество пропущенных записей (для пагинации)
    - **limit**: максимальное количество записей (1-100)
    - **unread_only**: показать только непрочитанные сообщения
    """
    return MessageService.get_inbox_messages(
        db, current_user.id, skip=skip, limit=limit, unread_only=unread_only
    )


@router.get("/sent", response_model=List[MessageResponse])
def get_sent_messages(
    skip: int = Query(0, ge=0, description="Количество пропущенных записей"),
    limit: int = Query(50, ge=1, le=100, description="Максимальное количество записей"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получение списка отправленных сообщений
    
    - **skip**: количество пропущенных записей (для пагинации)
    - **limit**: максимальное количество записей (1-100)
    """
    return MessageService.get_sent_messages(db, current_user.id, skip=skip, limit=limit)


@router.get("/{message_id}", response_model=MessageResponse)
def get_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получение конкретного сообщения по ID
    
    - **message_id**: ID сообщения
    """
    return MessageService.get_message_by_id(db, message_id, current_user.id)


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Отправка нового сообщения
    
    - **recipient_id**: ID получателя
    - **subject**: тема сообщения (1-200 символов)
    - **body**: текст сообщения
    - **attachments**: список вложений (опционально)
    """
    return MessageService.create_message(db, message_data, current_user.id)


@router.patch("/{message_id}/read", response_model=MessageResponse)
def mark_message_as_read(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Отметка сообщения как прочитанного
    
    - **message_id**: ID сообщения
    
    Только получатель может отметить сообщение как прочитанное.
    """
    return MessageService.mark_as_read(db, message_id, current_user.id)


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Удаление сообщения (мягкое удаление)
    
    - **message_id**: ID сообщения
    
    Сообщение будет скрыто для текущего пользователя, но останется доступным для другого участника переписки.
    """
    MessageService.delete_message(db, message_id, current_user.id)
    return None

