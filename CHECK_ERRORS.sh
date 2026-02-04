#!/bin/bash
# Скрипт для проверки последних ошибок web2py

echo "=== Последние 5 файлов ошибок ==="
ls -lt /opt/web2py/applications/adminlte5/errors/ 2>/dev/null | head -6

echo ""
echo "=== Содержимое последнего файла ошибки ==="
LATEST_ERROR=$(ls -t /opt/web2py/applications/adminlte5/errors/ 2>/dev/null | head -1)
if [ -n "$LATEST_ERROR" ]; then
    echo "Файл: $LATEST_ERROR"
    echo "---"
    tail -100 "/opt/web2py/applications/adminlte5/errors/$LATEST_ERROR"
else
    echo "Файлы ошибок не найдены"
fi

echo ""
echo "=== Все файлы ошибок (последние 10) ==="
ls -lt /opt/web2py/applications/adminlte5/errors/ 2>/dev/null | head -11
