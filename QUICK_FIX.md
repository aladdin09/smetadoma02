# Быстрое решение проблемы "Internal error"

## Если даже `/adminlte5/test/index` не работает

Это означает, что проблема в загрузке **моделей** (файлы в `models/`), которые загружаются **до** контроллеров.

## Что проверить на боевом сервере:

### 1. Проверьте файл `private/appconfig.ini`

```bash
cat /opt/web2py/applications/adminlte5/private/appconfig.ini
```

Файл должен существовать и содержать настройки базы данных.

### 2. Проверьте права доступа к файлу базы данных

```bash
ls -la /opt/web2py/applications/adminlte5/databases/
```

Директория `databases/` должна существовать и быть доступной для записи.

### 3. Проверьте версию web2py

```bash
python3 -c "import gluon; print(gluon.__version__)"
```

Должна быть версия 3.0.10 или новее.

### 4. Проверьте логи ошибок

```bash
# Последние 5 файлов ошибок
ls -lt /opt/web2py/applications/adminlte5/errors/ | head -5

# Последний файл ошибки (замените на актуальное имя)
tail -100 /opt/web2py/applications/adminlte5/errors/127.0.0.1.* | tail -50
```

### 5. Временное решение - отключить проверку версии

Если проблема в проверке версии web2py, можно временно закомментировать в `models/db.py`:

```python
# Временно закомментировано
# if web2py_version < list(map(int, REQUIRED_WEB2PY_VERSION.split(".")[:3])):
#     raise HTTP(500, f"Requires web2py version...")
```

### 6. Временное решение - использовать минимальную конфигурацию

Если проблема в AppConfig, можно временно заменить в `models/db.py`:

```python
# Вместо:
configuration = AppConfig(reload=True)

# Использовать:
class SimpleConfig:
    def get(self, key, default=None):
        config = {
            "db.uri": "sqlite://storage.sqlite",
            "db.pool_size": 10,
            "db.migrate": True,
        }
        return config.get(key, default)
configuration = SimpleConfig()
```

## После исправления:

1. Очистите кэш Python:
```bash
find /opt/web2py/applications/adminlte5 -type d -name __pycache__ -exec rm -r {} +
```

2. Перезапустите web2py (если используется как сервис):
```bash
sudo systemctl restart web2py
# или
sudo service web2py restart
```

3. Проверьте снова:
```
https://eleotapp.ru/adminlte5/test/index
```
