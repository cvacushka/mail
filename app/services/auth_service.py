import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import verify_password, get_password_hash, create_access_token
from datetime import timedelta
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> User:
        """
        Регистрация нового пользователя
        
        Args:
            db: Сессия базы данных
            user_data: Данные для регистрации пользователя
            
        Returns:
            User: Созданный пользователь
            
        Raises:
            HTTPException: Если пользователь с таким username или email уже существует
        """
        # Проверка существования пользователя
        existing_user = db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()
        
        if existing_user:
            if existing_user.username == user_data.username:
                logger.warning(f"Registration failed: username '{user_data.username}' already exists")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered"
                )
            else:
                logger.warning(f"Registration failed: email '{user_data.email}' already exists")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        try:
            # Создание нового пользователя
            hashed_password = get_password_hash(user_data.password)
            db_user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            logger.info(f"User registered successfully: {db_user.username} (ID: {db_user.id})")
            return db_user
            
        except HTTPException:
            # Пробрасываем HTTPException (например, ошибка валидации пароля)
            db.rollback()
            raise
        except IntegrityError as e:
            # Обработка ошибок целостности БД (на случай race condition)
            db.rollback()
            logger.error(f"Database integrity error during registration: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username or email already exists"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error during user registration: {type(e).__name__}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during registration"
            )
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        return user
    
    @staticmethod
    def create_token_for_user(user: User) -> str:
        """Создание JWT токена для пользователя"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        return access_token

