from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal


class AttachmentCreate(BaseModel):
    attachment_type: str = Field(..., description="Тип вложения: 'item', 'currency', 'gold' и т.д.")
    item_id: Optional[int] = None
    item_name: Optional[str] = None
    quantity: Decimal = Field(default=Decimal("1.0"), ge=0)
    attachment_data: Optional[Dict[str, Any]] = None


class AttachmentResponse(BaseModel):
    id: int
    attachment_type: str
    item_id: Optional[int]
    item_name: Optional[str]
    quantity: Decimal
    attachment_data: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    recipient_id: int


class MessageCreate(MessageBase):
    attachments: Optional[List[AttachmentCreate]] = None


class MessageUpdate(BaseModel):
    is_read: Optional[bool] = None


class MessageResponse(MessageBase):
    id: int
    sender_id: int
    is_read: bool
    is_deleted_by_sender: bool
    is_deleted_by_recipient: bool
    created_at: datetime
    read_at: Optional[datetime]
    attachments: List[AttachmentResponse] = []
    
    class Config:
        from_attributes = True

