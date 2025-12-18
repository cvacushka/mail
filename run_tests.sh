#!/bin/bash
# Скрипт для запуска тестов

echo "========================================="
echo "Запуск тестов Game Mail API"
echo "========================================="

# Определяем команду python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "Ошибка: Python не найден!"
    exit 1
fi

echo "Используется: $PYTHON_CMD"
$PYTHON_CMD --version

# Проверка виртуального окружения
if [ -d "venv" ]; then
    echo "Активация виртуального окружения..."
    source venv/bin/activate
    PYTHON_CMD=python
elif [ -d ".venv" ]; then
    echo "Активация виртуального окружения..."
    source .venv/bin/activate
    PYTHON_CMD=python
fi

# Установка зависимостей если нужно
if ! $PYTHON_CMD -m pytest --version &> /dev/null; then
    echo "Установка тестовых зависимостей..."
    $PYTHON_CMD -m pip install -r requirements.txt
fi

echo ""
echo "Запуск всех тестов..."
echo "========================================="
$PYTHON_CMD -m pytest tests/ -v --tb=short

echo ""
echo "========================================="
echo "Запуск тестов с покрытием кода..."
echo "========================================="
python -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

echo ""
echo "========================================="
echo "Тесты завершены!"
echo "Отчет о покрытии: htmlcov/index.html"
echo "========================================="

