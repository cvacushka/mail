import logging
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    # Убираем max_length из Field, так как ограничение должно быть в байтах, а не символах
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters and not exceed 72 bytes")
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        """
        Валидация длины пароля в байтах (bcrypt ограничение: 72 байта).
        Проверяем длину в UTF-8 кодировке, так как именно её использует bcrypt.
        """
        if not v:
            raise ValueError("Password cannot be empty")
        
        # Проверяем минимальную длину в символах
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        # Кодируем в UTF-8 и проверяем длину в байтах
        try:
            password_bytes = v.encode('utf-8')
            byte_length = len(password_bytes)
            char_length = len(v)
            
            # Логируем для отладки
            logger.debug(f"Password validation: {char_length} chars, {byte_length} bytes")
            
            if byte_length > 72:
                error_msg = (
                    f"Password is too long. Maximum length is 72 bytes in UTF-8 encoding. "
                    f"Your password is {byte_length} bytes ({char_length} characters). "
                    f"Note: Some Unicode characters (like emoji or special symbols) use multiple bytes."
                )
                logger.warning(f"Password too long: {char_length} chars = {byte_length} bytes")
                raise ValueError(error_msg)
            
            # Дополнительная проверка: убеждаемся, что пароль не пустой после кодирования
            if byte_length == 0:
                raise ValueError("Password cannot be empty")
                
        except UnicodeEncodeError as e:
            raise ValueError(f"Password contains invalid characters: {e}")
        
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

