-- Миграция: приведение таблицы customers в соответствие с моделью (db.py)
-- Выполнить при ошибках вида: column "..." of relation "customers" does not exist
-- Подключение: psql -h localhost -U smetadoma02 -d smetadoma02_db -f add_customers_middle_name.sql

ALTER TABLE customers ADD COLUMN IF NOT EXISTS middle_name VARCHAR(200);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS last_name VARCHAR(200);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS full_name VARCHAR(600);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS comments TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS lead_source_id INTEGER;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS link VARCHAR(500);
