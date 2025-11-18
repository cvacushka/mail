import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token as TokenSchema
from app.services.auth_service import AuthService
from app.models.user import User

logger = logging.getLogger(__name__)

# Убираем префикс /api, так как он добавляется в main.py
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Регистрация нового пользователя
    
    - **username**: уникальное имя пользователя (3-50 символов)
    - **email**: валидный email адрес
    - **password**: пароль (минимум 6 символов, максимум 72 байта в UTF-8)
    
    Возвращает данные созданного пользователя (без пароля).
    """
    try:
        logger.info(f"Registration attempt for username: {user_data.username}, email: {user_data.email}")
        user = AuthService.register_user(db, user_data)
        logger.info(f"User registered successfully: {user.username} (ID: {user.id})")
        return user
    except HTTPException:
        # Пробрасываем HTTPException как есть (например, пользователь уже существует)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration. Please try again."
        )


@router.post("/login", response_model=TokenSchema)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Вход в систему и получение JWT токена
    
    - **username**: имя пользователя
    - **password**: пароль
    
    Возвращает access_token для использования в заголовке Authorization: Bearer <token>
    """
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = AuthService.create_token_for_user(user)
    
    return {"access_token": access_token, "token_type": "bearer"}

