# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей request_statuses (Статусы заявок)
"""


def create_status(db, name, description=None, sort_order=0, is_active=True):
    """
    Создать новый статус заявки
    
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
        status_id = db.request_statuses.insert(
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
    """
    try:
        return db.request_statuses(status_id) or None
    except Exception as e:
        return None


def get_all_statuses(db, is_active=None, order_by='sort_order'):
    """
    Получить все статусы заявок
    
    Args:
        db: объект базы данных
        is_active: фильтр по активности (True/False/None для всех)
        order_by: поле для сортировки
    
    Returns:
        Rows: список всех статусов
    """
    try:
        query = db.request_statuses.id > 0
        if is_active is not None:
            query = query & (db.request_statuses.is_active == is_active)
        return db(query).select(orderby=db.request_statuses[order_by])
    except Exception as e:
        return db().select(db.request_statuses.id)


def update_status(db, status_id, **kwargs):
    """
    Обновить статус заявки
    
    Args:
        db: объект базы данных
        status_id: ID статуса
        **kwargs: поля для обновления (name, description, sort_order, is_active)
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        status = db.request_statuses(status_id)
        if not status:
            return {'success': False, 'error': 'Статус не найден'}
        
        allowed_fields = ['name', 'description', 'sort_order', 'is_active']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if update_data:
            db(db.request_statuses.id == status_id).update(**update_data)
            db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_status(db, status_id):
    """
    Удалить статус заявки
    
    Args:
        db: объект базы данных
        status_id: ID статуса
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        status = db.request_statuses(status_id)
        if not status:
            return {'success': False, 'error': 'Статус не найден'}
        
        db(db.request_statuses.id == status_id).delete()
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def search_statuses(db, search_term, is_active=None):
    """
    Поиск статусов заявок по названию или описанию
    
    Args:
        db: объект базы данных
        search_term: поисковый запрос
        is_active: фильтр по активности
    
    Returns:
        Rows: список найденных статусов
    """
    try:
        query = (db.request_statuses.name.contains(search_term)) | \
                (db.request_statuses.description.contains(search_term))
        if is_active is not None:
            query = query & (db.request_statuses.is_active == is_active)
        return db(query).select(orderby=db.request_statuses.sort_order)
    except Exception as e:
        return db().select(db.request_statuses.id)
