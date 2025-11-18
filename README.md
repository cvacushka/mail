# Game Mail API

Backend API для системы внутриигровой почты, разработанный на Python с использованием FastAPI.

## Технологический стек

- **FastAPI** - современный веб-фреймворк для создания API
- **PostgreSQL** - реляционная база данных
- **SQLAlchemy** - ORM для работы с БД
- **Alembic** - система миграций базы данных
- **Pydantic** - валидация данных
- **JWT** - аутентификация через токены
- **Docker** - контейнеризация приложения

## Структура проекта

```
backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── auth.py          # Эндпоинты аутентификации
│   │   │   └── messages.py      # Эндпоинты работы с сообщениями
│   │   └── main.py              # Главный роутер API
│   ├── core/
│   │   ├── config.py            # Конфигурация приложения
│   │   ├── security.py          # JWT и хеширование паролей
│   │   └── dependencies.py      # Зависимости FastAPI
│   ├── models/
│   │   ├── user.py              # Модель пользователя
│   │   ├── message.py           # Модель сообщения
│   │   └── attachment.py        # Модель вложения
│   ├── schemas/
│   │   ├── user.py              # Pydantic схемы для пользователей
│   │   ├── message.py           # Pydantic схемы для сообщений
│   │   └── token.py             # Pydantic схемы для токенов
│   ├── services/
│   │   ├── auth_service.py      # Сервис аутентификации
│   │   └── message_service.py   # Сервис работы с сообщениями
│   ├── database.py              # Настройка подключения к БД
│   └── main.py                  # Главный файл приложения
├── alembic/                     # Миграции базы данных
├── requirements.txt             # Зависимости Python
├── Dockerfile                   # Docker образ
├── docker-compose.yml           # Docker Compose конфигурация
└── init_db.sql                  # SQL скрипт инициализации БД
```

## Установка и запуск

### Локальная установка

1. **Клонируйте репозиторий и перейдите в директорию:**
```bash
cd backend
```

2. **Создайте виртуальное окружение:**
```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Настройте переменные окружения:**
```bash
cp .env.example .env
# Отредактируйте .env файл, указав свои настройки
```

5. **Создайте базу данных PostgreSQL:**
```bash
createdb game_mail_db
```

6. **Инициализируйте миграции Alembic:**
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

Или используйте SQL скрипт:
```bash
psql -U postgres -d game_mail_db -f init_db.sql
```

7. **Запустите приложение:**
```bash
uvicorn app.main:app --reload
```

Приложение будет доступно по адресу: http://localhost:8000

### Запуск с Docker

1. **Запустите все сервисы:**
```bash
docker-compose up -d
```

2. **Приложение будет доступно по адресу:** http://localhost:8000

3. **Остановка сервисов:**
```bash
docker-compose down
```

## API Документация

После запуска приложения доступна автоматическая документация:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Эндпоинты API

### Аутентификация

- `POST /api/auth/register` - Регистрация нового пользователя
- `POST /api/auth/login` - Вход в систему (получение JWT токена)

### Работа с сообщениями

- `GET /api/messages` - Список входящих сообщений (с пагинацией)
- `GET /api/messages/sent` - Список отправленных сообщений
- `GET /api/messages/{message_id}` - Просмотр конкретного сообщения
- `POST /api/messages` - Отправка нового сообщения
- `PATCH /api/messages/{message_id}/read` - Отметка о прочтении
- `DELETE /api/messages/{message_id}` - Удаление сообщения

## Использование API

### 1. Регистрация пользователя

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player1",
    "email": "player1@example.com",
    "password": "securepassword123"
  }'
```

### 2. Вход в систему

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=player1&password=securepassword123"
```

Ответ:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Отправка сообщения

```bash
curl -X POST "http://localhost:8000/api/messages" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_id": 2,
    "subject": "Привет!",
    "body": "Это тестовое сообщение",
    "attachments": [
      {
        "attachment_type": "gold",
        "quantity": 100.0
      }
    ]
  }'
```

### 4. Получение входящих сообщений

```bash
curl -X GET "http://localhost:8000/api/messages?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Модели базы данных

### User (Пользователь)
- `id` - уникальный идентификатор
- `username` - имя пользователя (уникальное)
- `email` - email адрес (уникальный)
- `hashed_password` - хешированный пароль
- `is_active` - флаг активности
- `created_at` - дата создания

### Message (Сообщение)
- `id` - уникальный идентификатор
- `sender_id` - ID отправителя
- `recipient_id` - ID получателя
- `subject` - тема сообщения
- `body` - текст сообщения
- `is_read` - флаг прочтения
- `is_deleted_by_sender` - мягкое удаление отправителем
- `is_deleted_by_recipient` - мягкое удаление получателем
- `created_at` - дата создания
- `read_at` - дата прочтения

### Attachment (Вложение)
- `id` - уникальный идентификатор
- `message_id` - ID сообщения
- `attachment_type` - тип вложения (item, currency, gold и т.д.)
- `item_id` - ID игрового предмета
- `item_name` - название предмета
- `quantity` - количество
- `attachment_data` - дополнительные данные (JSON)

## Безопасность

- Пароли хешируются с использованием bcrypt
- JWT токены используются для аутентификации
- Все эндпоинты (кроме регистрации и входа) требуют аутентификации
- Валидация всех входящих данных через Pydantic

## Разработка

### Создание миграций

```bash
alembic revision --autogenerate -m "Описание изменений"
alembic upgrade head
```

### Откат миграций

```bash
alembic downgrade -1
```

## Лицензия

MIT

