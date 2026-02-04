# Исправление ошибки в default/index

## Шаг 1: Проверьте диагностические функции

Откройте на боевом сервере:

1. **Проверка импорта dashboard_data**:
   ```
   https://eleotapp.ru/adminlte5/test/test_import
   ```

2. **Проверка вызова get_dashboard_data**:
   ```
   https://eleotapp.ru/adminlte5/test/test_dashboard_data
   ```

3. **Проверка таблиц в базе данных**:
   ```
   https://eleotapp.ru/adminlte5/test/test_tables
   ```

Эти тесты покажут, где именно проблема.

## Шаг 2: Проверьте, что таблицы созданы в PostgreSQL

На боевом сервере через SSH:

```bash
# Подключитесь к базе данных
psql -h localhost -U smetadoma -d smetadoma_db

# Проверьте список таблиц
\dt

# Должны быть таблицы:
# - auth_user
# - customers
# - projects
# - project_statuses
# - complects
# - complect_statuses
# - orders
# и другие...

# Если таблиц нет, выйдите и запустите миграцию:
\q
```

## Шаг 3: Запустите миграцию таблиц

Web2py должен создать таблицы автоматически при первом обращении, если `migrate=true` в `appconfig.ini`.

Если таблицы не создаются автоматически:

1. **Проверьте настройки миграции** в `private/appconfig.ini`:
   ```
   [db]
   migrate = true
   ```

2. **Попробуйте открыть страницу, которая обращается к таблицам**:
   ```
   https://eleotapp.ru/adminlte5/test/test_db
   ```

3. **Или создайте таблицы вручную через appadmin**:
   ```
   https://eleotapp.ru/adminlte5/appadmin
   ```
   Зайдите в раздел управления базой данных и создайте таблицы.

## Шаг 4: Проверьте логи ошибок

```bash
# На боевом сервере
LATEST_ERROR=$(ls -t /opt/web2py/applications/adminlte5/errors/ | head -1)
tail -100 "/opt/web2py/applications/adminlte5/errors/$LATEST_ERROR"
```

## Шаг 5: Залить изменения на боевой сервер

```bash
# На локальном сервере
git add .
git commit -m "Улучшена обработка ошибок в default/index и dashboard_data"
git push

# На боевом сервере
cd /opt/web2py/applications/adminlte5
git pull

# Очистите кэш
find /opt/web2py/applications/adminlte5 -type d -name __pycache__ -exec rm -r {} +
```

## Наиболее вероятные причины:

1. **Таблицы не созданы в PostgreSQL**
   - Решение: Проверьте `test_tables` и создайте таблицы через миграцию

2. **Ошибка в модуле project_statuses_service**
   - Решение: Проверьте `test_import` и `test_dashboard_data`

3. **Проблемы с правами доступа к таблицам**
   - Решение: Убедитесь, что пользователь `smetadoma` имеет права на все таблицы

4. **Ошибка в запросах к базе данных**
   - Решение: Проверьте логи ошибок, там будет детальная информация

## После исправления:

Попробуйте снова:
```
https://eleotapp.ru/adminlte5/default/index
```

Теперь при ошибке вы увидите детальную информацию в логах и на странице (если включен режим отладки).
