import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Максимальная длина пароля для bcrypt (72 байта)
MAX_PASSWORD_LENGTH = 72


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Хеширование пароля с использованием bcrypt.
    
    Bcrypt имеет ограничение в 72 байта для пароля в UTF-8 кодировке.
    Валидация длины должна происходить на уровне Pydantic схемы.
    """
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot be empty"
        )
    
    try:
        # Проверяем длину для логирования и дополнительной защиты
        password_bytes = password.encode('utf-8')
        byte_length = len(password_bytes)
        char_length = len(password)
        
        logger.debug(f"get_password_hash: {char_length} chars, {byte_length} bytes")
        
        # Дополнительная проверка на случай, если валидация Pydantic была пропущена
        if byte_length > MAX_PASSWORD_LENGTH:
            logger.warning(f"Password too long (bypassed validation): {char_length} chars = {byte_length} bytes")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password is too long. Maximum length is {MAX_PASSWORD_LENGTH} bytes in UTF-8 encoding. "
                       f"Your password is {byte_length} bytes ({char_length} characters)."
            )
        
        # Хеширование пароля через passlib
        # Passlib автоматически обрабатывает кодировку UTF-8
        hashed = pwd_context.hash(password)
        return hashed
        
    except HTTPException:
        # Пробрасываем HTTPException как есть
        raise
    except UnicodeEncodeError as e:
        logger.error(f"Unicode encoding error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password contains invalid characters"
        )
    except ValueError as e:
        # Обработка ошибок от bcrypt/passlib
        error_msg = str(e)
        error_msg_lower = error_msg.lower()
        
        # Проверяем длину пароля для логирования
        try:
            password_bytes_check = password.encode('utf-8')
            byte_length_check = len(password_bytes_check)
            char_length_check = len(password)
        except:
            byte_length_check = None
            char_length_check = "unknown"
        
        logger.error(
            f"ValueError in get_password_hash: {error_msg}, "
            f"password: {char_length_check} chars, {byte_length_check if byte_length_check is not None else 'unknown'} bytes, "
            f"repr: {repr(password)}"
        )
        
        if ("longer than 72 bytes" in error_msg_lower or "password cannot be longer" in error_msg_lower) and byte_length_check is not None and byte_length_check > MAX_PASSWORD_LENGTH:
            # Ошибка от bcrypt - пароль слишком длинный (только если действительно длинный)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password is too long. Maximum length is {MAX_PASSWORD_LENGTH} bytes in UTF-8 encoding. "
                       f"Your password is {byte_length_check} bytes ({char_length_check} characters)."
            )
        # Другие ValueError
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid password format: {error_msg}"
        )
    except Exception as e:
        logger.error(f"Unexpected error hashing password: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing password. Please try again."
        )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Декодирование JWT токена"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

