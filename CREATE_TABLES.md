# Создание таблиц в PostgreSQL

## Проблема

Таблицы определены в моделях (`models/db.py`), но не созданы в базе данных PostgreSQL. Ошибка: `relation "customers" does not exist`.

## Решение 1: Автоматическое создание через web2py

### Шаг 1: Убедитесь, что миграция включена

Проверьте файл `private/appconfig.ini`:
```ini
[db]
migrate = true
```

### Шаг 2: Откройте страницу создания таблиц

```
https://eleotapp.ru/adminlte5/test/create_tables
```

Эта функция попытается создать все таблицы автоматически.

### Шаг 3: Проверьте результат

После выполнения проверьте:
```
https://eleotapp.ru/adminlte5/test/test_tables
```

## Решение 2: Создание через appadmin

1. Откройте:
   ```
   https://eleotapp.ru/adminlte5/appadmin
   ```

2. Зайдите в раздел "Database administration"

3. Web2py автоматически создаст таблицы при первом обращении

## Решение 3: Ручное создание через SQL

Если автоматическое создание не работает, создайте таблицы вручную:

```bash
# Подключитесь к базе данных
psql -h localhost -U smetadoma -d smetadoma_db
```

Затем выполните SQL команды для создания таблиц. Но лучше использовать web2py, так как он правильно создаст все связи и индексы.

## Решение 4: Пересоздание через web2py shell

На боевом сервере через SSH:

```bash
cd /opt/web2py
python3 web2py.py -S adminlte5 -M

# В консоли web2py:
>>> db.customers._create_table()
>>> db.projects._create_table()
>>> db.project_statuses._create_table()
# и так далее для всех таблиц
>>> db.commit()
>>> exit()
```

## Проверка после создания

После создания таблиц проверьте:

1. **Список таблиц**:
   ```
   https://eleotapp.ru/adminlte5/test/test_tables
   ```

2. **Простой запрос**:
   ```
   https://eleotapp.ru/adminlte5/test/test_simple_query
   ```

3. **Главная страница**:
   ```
   https://eleotapp.ru/adminlte5/default/index
   ```

## Если таблицы все еще не создаются

1. **Проверьте права пользователя PostgreSQL**:
   ```bash
   psql -h localhost -U postgres -c "\du smetadoma"
   ```

2. **Убедитесь, что пользователь имеет права на создание таблиц**:
   ```bash
   psql -h localhost -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE smetadoma_db TO smetadoma;"
   psql -h localhost -U postgres -d smetadoma_db -c "GRANT ALL ON SCHEMA public TO smetadoma;"
   ```

3. **Проверьте логи web2py**:
   ```bash
   LATEST_ERROR=$(ls -t /opt/web2py/applications/adminlte5/errors/ | head -1)
   tail -100 "/opt/web2py/applications/adminlte5/errors/$LATEST_ERROR"
   ```
