# Решение проблемы "Internal error" / "invalid controller (default/index)"

## Быстрая диагностика

### Шаг 1: Проверьте, что контроллеры вообще загружаются

Откройте на боевом сервере:
```
http://your-server/adminlte5/test/index
```

Если это работает - контроллеры загружаются. Если нет - проблема в конфигурации web2py.

### Шаг 2: Проверьте импорты

```
http://your-server/adminlte5/test/test_import
```

Это покажет, может ли web2py импортировать модуль `dashboard_data`.

### Шаг 3: Проверьте базу данных

```
http://your-server/adminlte5/test/test_db
```

## Что проверить на боевом сервере через SSH:

### 1. Проверьте наличие всех файлов:

```bash
ls -la /opt/web2py/applications/adminlte5/modules/dashboard_data.py
ls -la /opt/web2py/applications/adminlte5/modules/project_statuses_service.py
ls -la /opt/web2py/applications/adminlte5/controllers/default.py
```

Все файлы должны существовать.

### 2. Проверьте права доступа:

```bash
ls -la /opt/web2py/applications/adminlte5/controllers/
ls -la /opt/web2py/applications/adminlte5/modules/
```

Файлы должны быть читаемыми для пользователя, под которым работает web2py (обычно `www-data` или `apache`).

Если права неправильные, исправьте:
```bash
chmod 644 /opt/web2py/applications/adminlte5/controllers/*.py
chmod 644 /opt/web2py/applications/adminlte5/modules/*.py
```

### 3. Проверьте логи ошибок web2py:

```bash
# Последние ошибки
ls -lt /opt/web2py/applications/adminlte5/errors/ | head -5

# Последний файл ошибки (замените на актуальное имя)
cat /opt/web2py/applications/adminlte5/errors/127.0.0.1.2026-01-31.* | tail -50
```

### 4. Проверьте синтаксис Python файлов:

```bash
python3 -m py_compile /opt/web2py/applications/adminlte5/controllers/default.py
python3 -m py_compile /opt/web2py/applications/adminlte5/modules/dashboard_data.py
python3 -m py_compile /opt/web2py/applications/adminlte5/models/db.py
```

Если есть синтаксические ошибки, они будут показаны.

### 5. Проверьте логи веб-сервера:

Если используется Apache:
```bash
tail -f /var/log/apache2/error.log
```

Если используется Nginx:
```bash
tail -f /var/log/nginx/error.log
```

## Наиболее частые причины:

1. **Отсутствует файл `modules/dashboard_data.py` или `modules/project_statuses_service.py`**
   - Решение: Убедитесь, что все файлы загружены через git

2. **Неправильные права доступа к файлам**
   - Решение: `chmod 644` для всех .py файлов

3. **Ошибка в `models/db.py`** (загружается до контроллера)
   - Решение: Проверьте синтаксис и логи ошибок

4. **Проблемы с базой данных** (не может подключиться или таблицы не созданы)
   - Решение: Проверьте конфигурацию БД в `private/appconfig.ini`

5. **Кэш web2py содержит старую версию**
   - Решение: Удалите `__pycache__` директории:
   ```bash
   find /opt/web2py/applications/adminlte5 -type d -name __pycache__ -exec rm -r {} +
   ```

## Временное решение для диагностики:

Если нужно быстро проверить, работает ли контроллер без импортов, можно временно закомментировать импорт в начале `default.py`:

```python
# Временно закомментировано для диагностики
# from dashboard_data import get_dashboard_data, get_status_color

def get_dashboard_data(db, request):
    return {'error': 'Временная заглушка для диагностики'}

def get_status_color(status_name):
    return 'secondary'
```

Если после этого контроллер заработает - проблема точно в импорте модулей.
