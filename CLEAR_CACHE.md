# Очистка кэша web2py после удаления файла

## Проблема

После удаления файла `commercial_proposal.pdf` ошибка все еще появляется, потому что web2py кэширует скомпилированные view-файлы.

## Решение

### 1. Убедитесь, что файл удален на боевом сервере:

```bash
# Проверьте, что файла нет
ls -la /opt/web2py/applications/adminlte5/views/complects/commercial_proposal.pdf

# Если файл существует, удалите его:
rm /opt/web2py/applications/adminlte5/views/complects/commercial_proposal.pdf
```

### 2. Очистите кэш web2py:

```bash
cd /opt/web2py/applications/adminlte5

# Удалите все __pycache__ директории
find . -type d -name __pycache__ -exec rm -r {} +

# Удалите скомпилированные .pyc файлы
find . -name "*.pyc" -delete

# Удалите кэш web2py (если есть)
rm -rf compiled/
```

### 3. Перезапустите web2py (если используется как сервис):

```bash
sudo systemctl restart web2py
# или
sudo service web2py restart
```

### 4. Если web2py запущен вручную, перезапустите его

Остановите процесс и запустите заново.

### 5. Проверьте, что изменения залиты через git:

```bash
cd /opt/web2py/applications/adminlte5
git status
git pull  # если изменения были залиты в репозиторий
```

### 6. Проверьте логи ошибок - возможно это старая ошибка:

```bash
# Посмотрите время создания последнего файла ошибки
ls -lt /opt/web2py/applications/adminlte5/errors/ | head -1

# Если файл старый (до удаления), значит это старая ошибка
```

## Альтернативное решение

Если ошибка все еще появляется, можно временно переименовать функцию в контроллере, чтобы web2py не пытался найти view-файл:

В `controllers/complects.py` можно изменить имя функции с `commercial_proposal` на `commercial_proposal_html`, чтобы web2py не искал `.pdf` версию.

Но лучше просто убедиться, что файл удален и кэш очищен.
