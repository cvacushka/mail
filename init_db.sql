-- SQL скрипт для инициализации базы данных системы внутриигровой почты
-- Этот скрипт создает все необходимые таблицы, индексы и связи

-- Таблица пользователей (игроков)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Индексы для таблицы users
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Таблица сообщений
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    is_deleted_by_sender BOOLEAN DEFAULT FALSE,
    is_deleted_by_recipient BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP WITH TIME ZONE
);

-- Индексы для таблицы messages
CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_recipient_id ON messages(recipient_id);
CREATE INDEX IF NOT EXISTS idx_messages_is_read ON messages(is_read);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_recipient_read ON messages(recipient_id, is_read);
CREATE INDEX IF NOT EXISTS idx_sender_created ON messages(sender_id, created_at);

-- Таблица вложений (для игровых предметов/валюты)
CREATE TABLE IF NOT EXISTS attachments (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    attachment_type VARCHAR(50) NOT NULL,
    item_id INTEGER,
    item_name VARCHAR(200),
    quantity NUMERIC(10, 2) DEFAULT 1.0,
    attachment_data JSONB
);

-- Индексы для таблицы attachments
CREATE INDEX IF NOT EXISTS idx_attachments_message_id ON attachments(message_id);
CREATE INDEX IF NOT EXISTS idx_attachments_type ON attachments(attachment_type);

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Таблица пользователей (игроков)';
COMMENT ON TABLE messages IS 'Таблица сообщений внутриигровой почты';
COMMENT ON TABLE attachments IS 'Таблица вложений к сообщениям (игровые предметы, валюта и т.д.)';

COMMENT ON COLUMN messages.is_deleted_by_sender IS 'Флаг мягкого удаления сообщения отправителем';
COMMENT ON COLUMN messages.is_deleted_by_recipient IS 'Флаг мягкого удаления сообщения получателем';
COMMENT ON COLUMN attachments.attachment_type IS 'Тип вложения: item, currency, gold и т.д.';
COMMENT ON COLUMN attachments.attachment_data IS 'JSON данные с дополнительными данными о вложении';

