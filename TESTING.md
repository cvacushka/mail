# Руководство по тестированию

## Структура тестов

Тесты разделены на две категории:

### Unit тесты
- `tests/test_auth_service.py` - тесты сервиса аутентификации
- `tests/test_message_service.py` - тесты сервиса сообщений

### Интеграционные тесты
- `tests/test_api_auth.py` - тесты API эндпоинтов аутентификации
- `tests/test_api_messages.py` - тесты API эндпоинтов сообщений

## Запуск тестов

### Быстрый запуск
```bash
cd backend

```

### Запуск конкретного файла
```bash
python -m pytest tests/test_message_service.py -v
```

### Запуск конкретного теста
```bash
python -m pytest tests/test_message_service.py::test_create_message_success -v
```

### Запуск с покрытием кода
```bash
python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
```

### Использование скрипта
```bash
cd backend
./run_tests.sh
```

## Покрытие функционала

### ✅ Аутентификация

**Unit тесты (`test_auth_service.py`):**
- ✅ Регистрация пользователя
- ✅ Дублирование username
- ✅ Дублирование email
- ✅ Аутентификация пользователя
- ✅ Неверный пароль
- ✅ Неактивный пользователь
- ✅ Создание JWT токена

**Интеграционные тесты (`test_api_auth.py`):**
- ✅ Регистрация через API
- ✅ Вход через API
- ✅ Валидация данных
- ✅ Обработка ошибок

### ✅ Сообщения

**Unit тесты (`test_message_service.py`):**
- ✅ Создание сообщения
- ✅ Создание с вложениями
- ✅ Несуществующий получатель
- ✅ Неактивный получатель
- ✅ Отправка самому себе
- ✅ Защита от спама (лимит в минуту)
- ✅ Защита от спама (лимит в час)
- ✅ Минимальный интервал
- ✅ Защита от дубликатов
- ✅ Получение входящих
- ✅ Получение непрочитанных
- ✅ Получение отправленных
- ✅ Получение по ID
- ✅ Доступ к чужим сообщениям
- ✅ Отметка прочтения
- ✅ Мягкое удаление

**Интеграционные тесты (`test_api_messages.py`):**
- ✅ Создание сообщения через API
- ✅ Создание с вложениями
- ✅ Защита от спама через API
- ✅ Получение входящих
- ✅ Получение отправленных
- ✅ Получение конкретного сообщения
- ✅ Отметка прочтения
- ✅ Удаление сообщения
- ✅ Доступ без авторизации
- ✅ Обработка ошибок

## Настройка тестов

### База данных для тестов
Тесты используют SQLite в памяти (не требуют реальной БД):
- Файл: `tests/conftest.py`
- Каждый тест создает чистую БД

### Фикстуры
- `db` - сессия базы данных
- `client` - тестовый клиент FastAPI
- `test_user` - тестовый пользователь
- `test_user2` - второй тестовый пользователь
- `inactive_user` - неактивный пользователь
- `auth_headers` - заголовки авторизации

## Примеры тестов

### Пример unit теста
```python
def test_create_message_success(db, test_user, test_user2):
    """Тест успешного создания сообщения"""
    message_data = MessageCreate(
        recipient_id=test_user2.id,
        subject="Test Subject",
        body="Test Body"
    )
    
    message = MessageService.create_message(db, message_data, test_user.id)
    
    assert message.id is not None
    assert message.sender_id == test_user.id
    assert message.recipient_id == test_user2.id
```

### Пример интеграционного теста
```python
def test_create_message_success(client, auth_headers, test_user2):
    """Тест успешного создания сообщения"""
    response = client.post(
        "/api/messages",
        headers=auth_headers,
        json={
            "recipient_id": test_user2.id,
            "subject": "Test Subject",
            "body": "Test Body"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["subject"] == "Test Subject"
```

## Тестирование защиты от спама

Все механизмы защиты от спама покрыты тестами:

1. **Лимит в минуту** - `test_create_message_spam_limit_per_minute`
2. **Лимит в час** - `test_create_message_spam_limit_per_hour`
3. **Минимальный интервал** - `test_create_message_min_interval_protection`
4. **Дубликаты** - `test_create_message_duplicate_prevention`

См. `ЗАЩИТА_ОТ_СПАМА.md` для подробностей.

## Добавление новых тестов

1. Создайте функцию с префиксом `test_`
2. Используйте фикстуры из `conftest.py`
3. Следуйте структуре существующих тестов
4. Добавьте docstring с описанием теста

## Отладка тестов

### Запуск с подробным выводом
```bash
python -m pytest tests/ -v -s
```

### Запуск с остановкой на первой ошибке
```bash
python -m pytest tests/ -x
```

### Запуск только упавших тестов
```bash
python -m pytest tests/ --lf
```

## Проблемы и решения

### Ошибка: "No module named pytest"
**Решение**: Установите зависимости
```bash
pip install -r requirements.txt
```

### Ошибка: "Database locked"
**Решение**: Убедитесь что тесты используют SQLite в памяти, а не файловую БД

### Тесты проходят, но приложение не работает
**Решение**: Проверьте что используете правильную БД в `config.py` для запуска приложения

## CI/CD

Для автоматического запуска тестов в CI/CD:

```yaml
# .github/workflows/test.yml (пример)
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ --cov=app --cov-report=xml
```
