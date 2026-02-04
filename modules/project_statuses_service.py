# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей project_statuses (Статусы проектов)
"""


def create_status(db, name, description=None, sort_order=0, is_active=True):
    """
    Создать новый статус проекта
    
    Args:
        db: объект базы данных
        name: название статуса
        description: описание статуса
        sort_order: порядок сортировки
        is_active: активен ли статус
    
    Returns:
        dict: результат операции {'success': bool, 'id': int, 'error': str}
    """
    try:
        status_id = db.project_statuses.insert(
            name=name,
            description=description,
            sort_order=sort_order,
            is_active=is_active
        )
        db.commit()
        return {'success': True, 'id': status_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_status_by_id(db, status_id):
    """
    Получить статус по ID
    
    Args:
        db: объект базы данных
        status_id: ID статуса
    
    Returns:
        Row или None: запись статуса или None если не найдена
    
    Note: Не делает rollback/commit - это должно делаться вызывающим кодом
    """
    try:
        result = db.project_statuses(status_id) or None
        return result
    except Exception as e:
        return None


def get_status_by_name(db, name):
    """
    Получить статус по точному названию.
    
    Returns:
        Row или None
    
    Note: Не делает rollback/commit - это должно делаться вызывающим кодом
    """
    try:
        n = (name or '').strip()
        if not n:
            return None
        row = db(db.project_statuses.name == n).select().first()
        return row
    except Exception:
        return None


def get_all_statuses(db, is_active=None, order_by='sort_order'):
    """
    Получить все статусы проектов
    
    Args:
        db: объект базы данных
        is_active: фильтр по активности (True/False/None для всех)
        order_by: поле для сортировки
    
    Returns:
        Rows: список всех статусов
    
    Note: Не делает rollback/commit - это должно делаться вызывающим кодом
    """
    try:
        query = db.project_statuses.id > 0
        if is_active is not None:
            query = query & (db.project_statuses.is_active == is_active)
        result = db(query).select(orderby=db.project_statuses[order_by])
        return result
    except Exception as e:
        # При ошибке возвращаем пустой результат
        # Не делаем rollback здесь - это должно делаться вызывающим кодом
        raise  # Пробрасываем ошибку дальше, чтобы safe_db_query мог обработать


def update_status(db, status_id, **kwargs):
    """
    Обновить статус проекта
    
    Args:
        db: объект базы данных
        status_id: ID статуса
        **kwargs: поля для обновления (name, description, sort_order, is_active)
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        status = db.project_statuses(status_id)
        if not status:
            return {'success': False, 'error': 'Статус не найден'}
        
        allowed_fields = ['name', 'description', 'sort_order', 'is_active']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if update_data:
            db(db.project_statuses.id == status_id).update(**update_data)
            db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_status(db, status_id):
    """
    Удалить статус проекта
    
    Args:
        db: объект базы данных
        status_id: ID статуса
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        status = db.project_statuses(status_id)
        if not status:
            return {'success': False, 'error': 'Статус не найден'}
        
        db(db.project_statuses.id == status_id).delete()
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def search_statuses(db, search_term, is_active=None):
    """
    Поиск статусов проектов по названию или описанию
    
    Args:
        db: объект базы данных
        search_term: поисковый запрос
        is_active: фильтр по активности
    
    Returns:
        Rows: список найденных статусов
    """
    try:
        query = (db.project_statuses.name.contains(search_term)) | \
                (db.project_statuses.description.contains(search_term))
        if is_active is not None:
            query = query & (db.project_statuses.is_active == is_active)
        return db(query).select(orderby=db.project_statuses.sort_order)
    except Exception as e:
        return db().select(db.project_statuses.id)
