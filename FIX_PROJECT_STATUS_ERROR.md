# Исправление ошибки при создании проекта

## Ошибка:
```
insert or update on table "projects" violates foreign key constraint "projects_status_id_fkey"
DETAIL: Key (status_id)=(1) is not present in table "project_statuses".
```

## Причина:
При создании проекта передается `status_id=1`, но такого статуса нет в таблице `project_statuses`.

## Решение:

### 1. Исправлен код в `modules/projects_service.py`

Теперь функция `create_project`:
- Сначала пытается найти статус "Начальный"
- Если не найден, берет первый активный статус
- Если нет активных, берет любой первый статус
- **Перед вставкой проверяет, что status_id существует в базе**
- Если статуса нет, возвращает понятную ошибку

### 2. Что нужно сделать на тестовом сервере:

#### Вариант А: Создать статус с id=1 (если нужен именно этот ID)

```bash
psql -h localhost -U smetadoma02 -d smetadoma02_db
```

В консоли PostgreSQL:
```sql
-- Проверьте, какие статусы есть
SELECT id, name FROM project_statuses ORDER BY id;

-- Если нужно создать статус с id=1, сначала проверьте, свободен ли этот ID
-- Если свободен, создайте:
INSERT INTO project_statuses (id, name, sort_order, is_active) 
VALUES (1, 'Начальный', 1, true);

-- Или используйте существующий статус
```

#### Вариант Б: Использовать существующие статусы (РЕКОМЕНДУЕТСЯ)

1. **Проверьте, какие статусы есть в базе:**
   ```bash
   psql -h localhost -U smetadoma02 -d smetadoma02_db -c "SELECT id, name, is_active FROM project_statuses ORDER BY sort_order, id;"
   ```

2. **Создайте статус "Начальный" через интерфейс:**
   ```
   https://eleotapp.ru/adminlte5/project_statuses/create
   ```

3. **Или создайте через SQL:**
   ```sql
   INSERT INTO project_statuses (name, sort_order, is_active, description) 
   VALUES ('Начальный', 1, true, 'Начальный статус проекта');
   ```

### 3. Залить исправленный код:

```bash
git add .
git commit -m "Исправлена ошибка при создании проекта - проверка существования status_id"
git push
```

На тестовом сервере:
```bash
cd /opt/web2py/applications/adminlte5
git pull
find . -type d -name __pycache__ -exec rm -r {} +
```

### 4. Проверка:

После исправления попробуйте создать проект снова. Теперь:
- Если статус "Начальный" существует - будет использован он
- Если нет - будет использован первый активный статус
- Если вообще нет статусов - будет возвращена понятная ошибка

## Дополнительно:

Если ошибка все еще появляется, проверьте:
1. **Где вызывается create_project с status_id=1:**
   ```bash
   grep -r "status_id.*=.*1" /opt/web2py/applications/adminlte5/controllers/
   grep -r "status_id.*=.*1" /opt/web2py/applications/adminlte5/modules/
   ```

2. **Проверьте логи ошибок:**
   ```bash
   LATEST_ERROR=$(ls -t /opt/web2py/applications/adminlte5/errors/ | head -1)
   tail -100 "/opt/web2py/applications/adminlte5/errors/$LATEST_ERROR"
   ```
