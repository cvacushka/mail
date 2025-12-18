from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Game Mail API"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/game_mail_db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Anti-spam settings
    MAX_MESSAGES_PER_HOUR: int = 50  # Максимум сообщений в час от одного пользователя
    MAX_MESSAGES_PER_MINUTE: int = 10  # Максимум сообщений в минуту от одного пользователя
    MIN_SECONDS_BETWEEN_MESSAGES: int = 3  # Минимальный интервал между сообщениями (секунды)
    DUPLICATE_MESSAGE_WINDOW_SECONDS: int = 300  # Окно для проверки дубликатов (5 минут)
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # BaseSettings автоматически читает переменные окружения
        # Значения по умолчанию используются если переменные не установлены


settings = Settings()

