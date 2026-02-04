# Создание всех таблиц в PostgreSQL

## Проверка таблиц:

Используйте правильную команду для просмотра таблиц:
```sql
\dt
```

Или:
```sql
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
```

## Создание таблиц:

### Способ 1: Через web2py (РЕКОМЕНДУЕТСЯ)

Откройте в браузере:
```
https://eleotapp.ru/adminlte5/test/create_tables_simple
```

### Способ 2: Через appadmin

```
https://eleotapp.ru/adminlte5/appadmin
```

Web2py автоматически создаст все таблицы при первом обращении.

### Способ 3: Через web2py shell

На боевом сервере:
```bash
cd /opt/web2py
python3 web2py.py -S adminlte5 -M
```

В консоли web2py выполните:
```python
# Создаем все таблицы
for table_name in sorted(db.tables):
    try:
        db[table_name]._create_table()
        db.commit()
        print(f"✓ {table_name}: создана")
    except Exception as e:
        print(f"✗ {table_name}: {str(e)}")
        db.rollback()

# Выйти
exit()
```

## После создания проверьте:

```sql
\dt
```

Должны появиться таблицы:
- auth_user, auth_group, auth_membership и другие auth_*
- customers
- projects
- project_statuses
- complect_statuses
- complects
- и другие...
