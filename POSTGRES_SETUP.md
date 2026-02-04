# Настройка PostgreSQL

## Что было изменено:

1. **Файл `private/appconfig.ini`**:
   - URI подключения изменен на PostgreSQL
   - `postgres://smetadoma:eY^x7ZQJ1OkQf8Y3g^Z2WvUMv1@localhost:5432/smetadoma_db`

2. **Файл `models/db.py`**:
   - Обновлены значения по умолчанию для PostgreSQL

## Проверка перед запуском:

### 1. Убедитесь, что PostgreSQL запущен:

```bash
sudo systemctl status postgresql
# или
sudo service postgresql status
```

### 2. Проверьте, что база данных существует:

```bash
sudo -u postgres psql -c "\l" | grep smetadoma_db
```

Если базы нет, создайте её:

```bash
sudo -u postgres psql -c "CREATE DATABASE smetadoma_db OWNER smetadoma;"
```

### 3. Проверьте, что пользователь существует и имеет права:

```bash
sudo -u postgres psql -c "\du" | grep smetadoma
```

Если пользователя нет, создайте:

```bash
sudo -u postgres psql -c "CREATE USER smetadoma WITH PASSWORD 'eY^x7ZQJ1OkQf8Y3g^Z2WvUMv1';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE smetadoma_db TO smetadoma;"
```

### 4. Установите драйвер PostgreSQL для Python (если не установлен):

```bash
pip3 install psycopg2-binary
# или
apt-get install python3-psycopg2
```

### 5. Проверьте подключение:

```bash
psql -h localhost -U smetadoma -d smetadoma_db
# Введите пароль: eY^x7ZQJ1OkQf8Y3g^Z2WvUMv1
```

### 6. Если PostgreSQL на другом хосте/порту:

Измените URI в `private/appconfig.ini`:
```
uri = postgres://smetadoma:eY^x7ZQJ1OkQf8Y3g^Z2WvUMv1@HOST:PORT/smetadoma_db
```

Замените:
- `HOST` на IP адрес или домен сервера PostgreSQL
- `PORT` на порт (обычно 5432)

## После настройки:

1. Очистите кэш Python:
```bash
find /opt/web2py/applications/adminlte5 -type d -name __pycache__ -exec rm -r {} +
```

2. Перезапустите web2py (если используется как сервис):
```bash
sudo systemctl restart web2py
```

3. Проверьте работу:
```
https://eleotapp.ru/adminlte5/test/index
```

## Возможные проблемы:

1. **Ошибка "psycopg2 not found"**:
   - Установите: `pip3 install psycopg2-binary`

2. **Ошибка "connection refused"**:
   - Проверьте, что PostgreSQL запущен
   - Проверьте настройки `pg_hba.conf` и `postgresql.conf`

3. **Ошибка "authentication failed"**:
   - Проверьте пароль и имя пользователя
   - Проверьте права пользователя в PostgreSQL

4. **Ошибка "database does not exist"**:
   - Создайте базу данных (см. выше)
