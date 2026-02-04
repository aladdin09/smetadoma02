# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей requests (Заявки)
"""

from datetime import datetime


def create_request(db, customer_id, status_id, description=None, next_step_id=None,
                   execution_time=None, deadline=None, total_amount=0, now=None):
    """
    Создать новую заявку
    
    Args:
        db: объект базы данных
        customer_id: ID клиента
        status_id: ID статуса
        description: описание заявки
        next_step_id: ID следующего шага
        execution_time: время на выполнение (дни)
        deadline: дедлайн
        total_amount: общая сумма
        now: текущее время (datetime)
    
    Returns:
        dict: результат операции {'success': bool, 'id': int, 'error': str}
    """
    try:
        if now is None:
            now = datetime.now()
        request_id = db.requests.insert(
            customer_id=customer_id,
            status_id=status_id,
            status_changed_on=now,
            next_step_id=next_step_id,
            execution_time=execution_time,
            deadline=deadline,
            description=description,
            total_amount=total_amount
        )
        db.commit()
        return {'success': True, 'id': request_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_request_by_id(db, request_id):
    """
    Получить заявку по ID
    
    Args:
        db: объект базы данных
        request_id: ID заявки
    
    Returns:
        Row или None: запись заявки или None если не найдена
    """
    try:
        return db.requests(request_id) or None
    except Exception as e:
        return None


def get_all_requests(db, customer_id=None, status_id=None, order_by='created_on'):
    """
    Получить все заявки
    
    Args:
        db: объект базы данных
        customer_id: фильтр по клиенту
        status_id: фильтр по статусу
        order_by: поле для сортировки
    
    Returns:
        Rows: список всех заявок
    """
    try:
        query = db.requests.id > 0
        if customer_id:
            query = query & (db.requests.customer_id == customer_id)
        if status_id:
            query = query & (db.requests.status_id == status_id)
        
        if order_by == 'created_on':
            return db(query).select(orderby=~db.requests.created_on)
        return db(query).select(orderby=db.requests[order_by])
    except Exception as e:
        return db().select(db.requests.id)


def update_request(db, request_id, **kwargs):
    """
    Обновить заявку
    
    Args:
        db: объект базы данных
        request_id: ID заявки
        **kwargs: поля для обновления
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        request = db.requests(request_id)
        if not request:
            return {'success': False, 'error': 'Заявка не найдена'}
        
        allowed_fields = ['customer_id', 'status_id', 'next_step_id', 
                         'execution_time', 'deadline', 'description', 'total_amount']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        # Если меняется статус, обновляем дату изменения статуса
        if 'status_id' in update_data:
            from datetime import datetime
            update_data['status_changed_on'] = datetime.now()
        
        if update_data:
            db(db.requests.id == request_id).update(**update_data)
            db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def update_request_status(db, request_id, status_id):
    """
    Обновить статус заявки
    
    Args:
        db: объект базы данных
        request_id: ID заявки
        status_id: новый ID статуса
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        request = db.requests(request_id)
        if not request:
            return {'success': False, 'error': 'Заявка не найдена'}
        
        from datetime import datetime
        db(db.requests.id == request_id).update(
            status_id=status_id,
            status_changed_on=datetime.now()
        )
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_request(db, request_id):
    """
    Удалить заявку
    
    Args:
        db: объект базы данных
        request_id: ID заявки
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        request = db.requests(request_id)
        if not request:
            return {'success': False, 'error': 'Заявка не найдена'}
        
        # Удаляем связанные позиции заявки
        db(db.request_items.request_id == request_id).delete()
        
        # Удаляем заявку
        db(db.requests.id == request_id).delete()
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def search_requests(db, search_term, customer_id=None, status_id=None):
    """
    Поиск заявок по описанию
    
    Args:
        db: объект базы данных
        search_term: поисковый запрос
        customer_id: фильтр по клиенту
        status_id: фильтр по статусу
    
    Returns:
        Rows: список найденных заявок
    """
    try:
        query = db.requests.description.contains(search_term)
        if customer_id:
            query = query & (db.requests.customer_id == customer_id)
        if status_id:
            query = query & (db.requests.status_id == status_id)
        return db(query).select(orderby=~db.requests.created_on)
    except Exception as e:
        return db().select(db.requests.id)


def get_request_items(db, request_id):
    """
    Получить все позиции заявки
    
    Args:
        db: объект базы данных
        request_id: ID заявки
    
    Returns:
        Rows: список позиций заявки
    """
    try:
        return db(db.request_items.request_id == request_id).select(
            orderby=db.request_items.id
        )
    except Exception as e:
        return db().select(db.request_items.id)


def calculate_request_total(db, request_id):
    """
    Пересчитать общую сумму заявки на основе позиций
    
    Args:
        db: объект базы данных
        request_id: ID заявки
    
    Returns:
        dict: результат операции {'success': bool, 'total': float, 'error': str}
    """
    try:
        items = db(db.request_items.request_id == request_id).select()
        total = sum(float(item.total or 0) for item in items)
        
        db(db.requests.id == request_id).update(total_amount=total)
        db.commit()
        return {'success': True, 'total': total}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
