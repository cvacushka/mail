# Быстрый старт

## Запуск с Docker (рекомендуется)

1. **Запустите все сервисы:**
```bash
docker-compose up -d
```

2. **Приложение доступно по адресу:** http://localhost:8000
3. **Документация API:** http://localhost:8000/docs

## Локальный запуск

1. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

2. **Создайте файл .env:**
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/game_mail_db
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

3. **Создайте базу данных:**
```bash
createdb game_mail_db
psql -U postgres -d game_mail_db -f init_db.sql
```

4. **Запустите приложение:**
```bash
uvicorn app.main:app --reload
```

## Первые шаги

1. **Зарегистрируйте пользователя:**
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'
```

2. **Войдите в систему:**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=password123"
```

3. **Используйте полученный токен для доступа к API:**
```bash
curl -X GET "http://localhost:8000/api/messages" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

