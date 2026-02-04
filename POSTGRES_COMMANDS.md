# Полезные команды PostgreSQL

## Получение списка баз данных

### Вариант 1: Через psql
```bash
# Подключитесь к PostgreSQL как суперпользователь
sudo -u postgres psql

# Или с указанием хоста
psql -h localhost -U postgres

# В консоли PostgreSQL выполните:
\l
# или
\list

# Выйти из psql:
\q
```

### Вариант 2: Одной командой
```bash
sudo -u postgres psql -c "\l"
# или
psql -h localhost -U postgres -c "\l"
```

### Вариант 3: SQL запрос
```bash
psql -h localhost -U postgres -c "SELECT datname FROM pg_database WHERE datistemplate = false;"
```

## Получение списка пользователей (ролей)

### Вариант 1: Через psql
```bash
# Подключитесь к PostgreSQL
sudo -u postgres psql

# В консоли выполните:
\du
# или
\du+

# Выйти:
\q
```

### Вариант 2: Одной командой
```bash
sudo -u postgres psql -c "\du"
# или
psql -h localhost -U postgres -c "\du"
```

### Вариант 3: SQL запрос
```bash
psql -h localhost -U postgres -c "SELECT usename, usecreatedb, usesuper FROM pg_user;"
# или более детально:
psql -h localhost -U postgres -c "SELECT rolname, rolsuper, rolcreatedb, rolcanlogin FROM pg_roles;"
```

## Проверка конкретной базы данных

### Подключение к базе данных
```bash
psql -h localhost -U smetadoma -d smetadoma_db
# или
sudo -u postgres psql -d smetadoma_db
```

### Список таблиц в базе данных
```bash
# В psql:
\dt

# Одной командой:
psql -h localhost -U smetadoma -d smetadoma_db -c "\dt"
```

### Детальная информация о таблице
```bash
# В psql:
\d customers
\d+ customers  # более детально

# Одной командой:
psql -h localhost -U smetadoma -d smetadoma_db -c "\d customers"
```

### Список всех объектов (таблицы, индексы, последовательности)
```bash
# В psql:
\dn+  # схемы
\dt+  # таблицы
\di+  # индексы
\ds+  # последовательности
```

## Проверка прав доступа

### Права пользователя на базу данных
```bash
psql -h localhost -U postgres -c "\l smetadoma_db"
```

### Права пользователя на таблицы
```bash
psql -h localhost -U postgres -d smetadoma_db -c "\dp"
# или для конкретной таблицы:
psql -h localhost -U postgres -d smetadoma_db -c "\dp customers"
```

### Права пользователя на схему
```bash
psql -h localhost -U postgres -d smetadoma_db -c "\dn+"
```

## Создание базы данных и пользователя

### Создание базы данных
```bash
sudo -u postgres psql -c "CREATE DATABASE smetadoma_db OWNER smetadoma;"
```

### Создание пользователя
```bash
sudo -u postgres psql -c "CREATE USER smetadoma WITH PASSWORD 'eY^x7ZQJ1OkQf8Y3g^Z2WvUMv1';"
```

### Выдача прав
```bash
# Права на базу данных
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE smetadoma_db TO smetadoma;"

# Права на схему public
sudo -u postgres psql -d smetadoma_db -c "GRANT ALL ON SCHEMA public TO smetadoma;"

# Права на все таблицы в схеме public
sudo -u postgres psql -d smetadoma_db -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO smetadoma;"

# Права на все последовательности (для автоинкремента)
sudo -u postgres psql -d smetadoma_db -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO smetadoma;"

# Права по умолчанию для будущих таблиц
sudo -u postgres psql -d smetadoma_db -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO smetadoma;"
sudo -u postgres psql -d smetadoma_db -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO smetadoma;"
```

## Проверка подключения

### Тест подключения
```bash
psql -h localhost -U smetadoma -d smetadoma_db -c "SELECT version();"
```

### Проверка текущего пользователя
```bash
psql -h localhost -U smetadoma -d smetadoma_db -c "SELECT current_user, current_database();"
```

## Миграция: добавление столбца middle_name в customers

Если при добавлении клиента возникает ошибка `column "middle_name" of relation "customers" does not exist`, выполните:

```bash
psql -h localhost -U smetadoma02 -d smetadoma02_db -c "ALTER TABLE customers ADD COLUMN IF NOT EXISTS middle_name VARCHAR(200);"
```

Или в psql:
```sql
ALTER TABLE customers ADD COLUMN IF NOT EXISTS middle_name VARCHAR(200);
```

При ошибке про столбец `comments` или другие недостающие столбцы выполните полную миграцию:
```bash
psql -h localhost -U smetadoma02 -d smetadoma02_db -f migrations/add_customers_middle_name.sql
```
Или по одному:
```sql
ALTER TABLE customers ADD COLUMN IF NOT EXISTS last_name VARCHAR(200);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS full_name VARCHAR(600);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS comments TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS lead_source_id INTEGER;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS link VARCHAR(500);
```

## Полезные команды в psql

```
\?          - помощь по командам psql
\l          - список баз данных
\du         - список пользователей
\dt         - список таблиц
\d table    - структура таблицы
\dn         - список схем
\c dbname   - переключиться на базу данных
\q          - выйти из psql
\conninfo   - информация о текущем подключении
\timing     - включить/выключить показ времени выполнения
\x          - расширенный формат вывода (вертикальный)
```

## Примеры использования

### Получить список всех баз данных с размерами
```bash
psql -h localhost -U postgres -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) AS size FROM pg_database WHERE datistemplate = false ORDER BY pg_database_size(datname) DESC;"
```

### Получить список всех таблиц с количеством строк
```bash
psql -h localhost -U smetadoma -d smetadoma_db -c "SELECT schemaname, tablename, n_live_tup as row_count FROM pg_stat_user_tables ORDER BY n_live_tup DESC;"
```

### Получить список всех пользователей с их правами
```bash
psql -h localhost -U postgres -c "SELECT r.rolname, r.rolsuper, r.rolcreatedb, r.rolcanlogin, ARRAY(SELECT b.rolname FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles b ON (m.roleid = b.oid) WHERE m.member = r.oid) as member_of FROM pg_catalog.pg_roles r WHERE r.rolname NOT IN ('pg_signal_backend', 'pg_read_all_stats', 'pg_stat_scan_tables', 'pg_monitor', 'pg_read_all_settings', 'pg_read_server_files', 'pg_write_server_files', 'pg_execute_server_program') ORDER BY 1;"
```
