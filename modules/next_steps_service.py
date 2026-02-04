# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей next_steps (Следующие шаги)
"""


def create_next_step(db, name, description=None, days=0, is_active=True):
    """
    Создать новый следующий шаг
    
    Args:
        db: объект базы данных
        name: название шага
        description: описание шага
        days: количество дней на выполнение
        is_active: активен ли шаг
    
    Returns:
        dict: результат операции {'success': bool, 'id': int, 'error': str}
    """
    try:
        step_id = db.next_steps.insert(
            name=name,
            description=description,
            days=days,
            is_active=is_active
        )
        db.commit()
        return {'success': True, 'id': step_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_next_step_by_id(db, step_id):
    """
    Получить следующий шаг по ID
    
    Args:
        db: объект базы данных
        step_id: ID шага
    
    Returns:
        Row или None: запись шага или None если не найдена
    """
    try:
        return db.next_steps(step_id) or None
    except Exception as e:
        return None


def get_all_next_steps(db, is_active=None, order_by='name'):
    """
    Получить все следующие шаги
    
    Args:
        db: объект базы данных
        is_active: фильтр по активности (True/False/None для всех)
        order_by: поле для сортировки
    
    Returns:
        Rows: список всех шагов
    """
    try:
        query = db.next_steps.id > 0
        if is_active is not None:
            query = query & (db.next_steps.is_active == is_active)
        return db(query).select(orderby=db.next_steps[order_by])
    except Exception as e:
        return db().select(db.next_steps.id)


def update_next_step(db, step_id, **kwargs):
    """
    Обновить следующий шаг
    
    Args:
        db: объект базы данных
        step_id: ID шага
        **kwargs: поля для обновления (name, description, days, is_active)
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        step = db.next_steps(step_id)
        if not step:
            return {'success': False, 'error': 'Шаг не найден'}
        
        allowed_fields = ['name', 'description', 'days', 'is_active']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if update_data:
            db(db.next_steps.id == step_id).update(**update_data)
            db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_next_step(db, step_id):
    """
    Удалить следующий шаг
    
    Args:
        db: объект базы данных
        step_id: ID шага
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        step = db.next_steps(step_id)
        if not step:
            return {'success': False, 'error': 'Шаг не найден'}
        
        db(db.next_steps.id == step_id).delete()
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def search_next_steps(db, search_term, is_active=None):
    """
    Поиск следующих шагов по названию или описанию
    
    Args:
        db: объект базы данных
        search_term: поисковый запрос
        is_active: фильтр по активности
    
    Returns:
        Rows: список найденных шагов
    """
    try:
        query = (db.next_steps.name.contains(search_term)) | \
                (db.next_steps.description.contains(search_term))
        if is_active is not None:
            query = query & (db.next_steps.is_active == is_active)
        return db(query).select(orderby=db.next_steps.name)
    except Exception as e:
        return db().select(db.next_steps.id)
