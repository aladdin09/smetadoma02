# Настройка новой базы данных smetadoma02_db

## ✅ Что уже сделано:

1. Создана база данных: `smetadoma02_db`
2. Создан пользователь: `smetadoma02`
3. Обновлены данные подключения в:
   - `private/appconfig.ini`
   - `models/db.py` (значения по умолчанию)

## 🔧 Что нужно сделать:

### 1. Выдать права пользователю на базу данных

Выполните на боевом сервере:

```bash
# Подключитесь как суперпользователь PostgreSQL
sudo -u postgres psql

# В консоли PostgreSQL выполните:
GRANT ALL PRIVILEGES ON DATABASE smetadoma02_db TO smetadoma02;

# Подключитесь к базе данных
\c smetadoma02_db

# Выдайте права на схему public
GRANT ALL ON SCHEMA public TO smetadoma02;

# Выдайте права на все таблицы (для будущих таблиц)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO smetadoma02;

# Выдайте права на все последовательности (для автоинкремента id)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO smetadoma02;

# Выйдите
\q
```

### 2. Очистить кэш web2py

```bash
cd /opt/web2py/applications/adminlte5
find . -type d -name __pycache__ -exec rm -r {} +
```

### 3. Создать таблицы

Откройте в браузере:
```
https://eleotapp.ru/adminlte5/test/create_tables_simple
```

Или через appadmin:
```
https://eleotapp.ru/adminlte5/appadmin
```

### 4. Проверить результат

```
https://eleotapp.ru/adminlte5/test/test_tables
```

Должно показать таблицы с количеством записей (пока 0, так как таблицы только созданы).

### 5. Проверить главную страницу

```
https://eleotapp.ru/adminlte5/default/index
```

## 🔍 Проверка подключения

### Проверка через psql:

```bash
psql -h localhost -U smetadoma02 -d smetadoma02_db
```

В консоли PostgreSQL:
```sql
-- Проверка текущего пользователя и базы
SELECT current_user, current_database();

-- Проверка прав
\du smetadoma02

-- Список таблиц (после создания)
\dt
```

### Проверка через web2py:

```
https://eleotapp.ru/adminlte5/test/test_db
```

## ⚠️ Если таблицы не создаются:

1. **Проверьте права пользователя:**
   ```bash
   sudo -u postgres psql -c "\du smetadoma02"
   ```

2. **Проверьте, что пользователь может создавать таблицы:**
   ```bash
   psql -h localhost -U smetadoma02 -d smetadoma02_db -c "CREATE TABLE test_table (id SERIAL PRIMARY KEY);"
   psql -h localhost -U smetadoma02 -d smetadoma02_db -c "DROP TABLE test_table;"
   ```

3. **Проверьте логи web2py:**
   ```bash
   LATEST_ERROR=$(ls -t /opt/web2py/applications/adminlte5/errors/ | head -1)
   tail -100 "/opt/web2py/applications/adminlte5/errors/$LATEST_ERROR"
   ```

4. **Проверьте настройки миграции:**
   Убедитесь, что в `private/appconfig.ini`:
   ```ini
   [db]
   migrate = true
   ```

## 📝 Текущие данные подключения:

- **База данных:** `smetadoma02_db`
- **Пользователь:** `smetadoma02`
- **Пароль:** `Lenina21`
- **Хост:** `localhost`
- **Порт:** `5432`
- **URI:** `postgres://smetadoma02:Lenina21@localhost:5432/smetadoma02_db`
