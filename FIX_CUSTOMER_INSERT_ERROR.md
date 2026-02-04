# Исправление ошибки при создании клиента

## Ошибка:
```
LINE 1: INSERT INTO "customers"("notes","created_on","address","name...
                    ^
```

## Возможные причины:

### 1. Таблица customers не создана в PostgreSQL

**Проверка:**
```bash
psql -h localhost -U smetadoma02 -d smetadoma02_db -c "\d customers"
```

**Решение:**
Если таблицы нет, создайте её через web2py:
```
https://eleotapp.ru/adminlte5/test/create_tables_simple
```

### 2. Несоответствие структуры таблицы и модели

**Проверка:**
```bash
# Проверьте структуру таблицы в PostgreSQL
psql -h localhost -U smetadoma02 -d smetadoma02_db -c "\d+ customers"
```

**Решение:**
Если структура не соответствует модели, пересоздайте таблицу:
```sql
-- ВНИМАНИЕ: Это удалит все данные!
DROP TABLE IF EXISTS customers CASCADE;
```

Затем создайте через web2py снова.

### 3. Проблема с полем created_on (datetime)

**Проверка:**
В модели определено:
```python
Field('created_on', 'datetime', default=request.now, writable=False, readable=True)
```

**Решение:**
Проверьте, что в PostgreSQL поле имеет тип `timestamp` или `timestamp without time zone`.

### 4. Проблема с валидаторами

**Проверка:**
В модели есть валидаторы:
```python
db.customers.email.requires = IS_EMPTY_OR(IS_EMAIL())
db.customers.phone.requires = IS_EMPTY_OR(IS_MATCH('^[\d\s\-\+\(\)]+$', error_message='Неверный формат телефона'))
```

**Решение:**
Проверьте, что данные формы проходят валидацию.

## Диагностика:

### 1. Запустите тест создания клиента:

```
https://eleotapp.ru/adminlte5/test/test_create_customer
```

Это покажет:
- Существует ли таблица
- Какие поля есть
- Точную ошибку при создании

### 2. Проверьте структуру таблицы в PostgreSQL:

```bash
psql -h localhost -U smetadoma02 -d smetadoma02_db -c "\d customers"
```

Должны быть поля:
- id (integer, primary key)
- name (varchar(200), NOT NULL)
- phone (varchar(50))
- email (varchar(100))
- address (text)
- notes (text)
- created_on (timestamp)
- modified_on (timestamp)

### 3. Проверьте логи ошибок:

```bash
LATEST_ERROR=$(ls -t /opt/web2py/applications/adminlte5/errors/ | head -1)
tail -200 "/opt/web2py/applications/adminlte5/errors/$LATEST_ERROR"
```

## Быстрое решение:

### Если таблица не создана:

1. Создайте таблицы через web2py:
   ```
   https://eleotapp.ru/adminlte5/test/create_tables_simple
   ```

2. Или через appadmin:
   ```
   https://eleotapp.ru/adminlte5/appadmin
   ```

### Если таблица создана, но структура неправильная:

1. Проверьте структуру:
   ```bash
   psql -h localhost -U smetadoma02 -d smetadoma02_db -c "\d customers"
   ```

2. Если нужно, пересоздайте таблицу (ОСТОРОЖНО - удалит данные!):
   ```sql
   -- Сделайте бэкап данных перед этим!
   DROP TABLE IF EXISTS customers CASCADE;
   ```

3. Затем создайте через web2py снова.

## После исправления:

Попробуйте создать клиента снова. Если ошибка сохраняется, запустите тест и пришлите результат.
