# -*- coding: utf-8 -*-
"""
Диагностический контроллер для отладки проблем на боевом сервере.
Использование: http://your-server/adminlte5/debug/test
"""

import traceback
import sys
import os

def test():
    """Базовый тест - проверяет, что контроллер вообще загружается"""
    return dict(
        message="Контроллер debug загружен успешно",
        python_version=sys.version,
        sys_path=sys.path[:5],  # Первые 5 путей
    )

def test_imports():
    """Тест импортов"""
    results = {}
    
    # Тест импорта dashboard_data
    try:
        from dashboard_data import get_dashboard_data, get_status_color
        results['dashboard_data'] = "OK"
    except Exception as e:
        results['dashboard_data'] = f"ОШИБКА: {str(e)}\n{traceback.format_exc()}"
    
    # Тест импорта db
    try:
        db_test = db(db.customers.id > 0).count()
        results['db'] = f"OK (customers count: {db_test})"
    except Exception as e:
        results['db'] = f"ОШИБКА: {str(e)}\n{traceback.format_exc()}"
    
    # Тест импорта auth
    try:
        auth_test = auth
        results['auth'] = "OK"
    except Exception as e:
        results['auth'] = f"ОШИБКА: {str(e)}\n{traceback.format_exc()}"
    
    return dict(results=results)

def test_default_index():
    """Тест вызова функции index из default контроллера"""
    try:
        from default import index
        result = index()
        return dict(
            status="OK",
            result_type=type(result).__name__,
            result_keys=list(result.keys()) if isinstance(result, dict) else "не словарь"
        )
    except Exception as e:
        return dict(
            status="ОШИБКА",
            error_type=type(e).__name__,
            error_message=str(e),
            traceback=traceback.format_exc()
        )

def test_file_permissions():
    """Проверка прав доступа к файлам"""
    import stat
    results = {}
    
    files_to_check = [
        'controllers/default.py',
        'models/db.py',
        'modules/dashboard_data.py',
    ]
    
    for file_path in files_to_check:
        full_path = os.path.join(request.folder, file_path)
        try:
            if os.path.exists(full_path):
                file_stat = os.stat(full_path)
                results[file_path] = {
                    'exists': True,
                    'readable': os.access(full_path, os.R_OK),
                    'size': file_stat.st_size,
                    'permissions': oct(stat.S_IMODE(file_stat.st_mode))
                }
            else:
                results[file_path] = {'exists': False}
        except Exception as e:
            results[file_path] = {'error': str(e)}
    
    return dict(results=results)

def test_all():
    """Запуск всех тестов"""
    return dict(
        test=test(),
        imports=test_imports(),
        default_index=test_default_index(),
        file_permissions=test_file_permissions(),
        request_folder=request.folder,
        app_name=request.application,
    )
