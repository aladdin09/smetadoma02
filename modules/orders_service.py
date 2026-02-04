# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей orders (Заказы)
"""

from datetime import datetime


def create_order(db, customer_id, order_number, order_date=None, project_id=None,
                 specification_id=None, description=None, total_amount=0):
    """
    Создать новый заказ
    
    Args:
        db: объект базы данных
        customer_id: ID клиента
        order_number: номер заказа
        order_date: дата заказа
        project_id: ID проекта
        specification_id: ID спецификации (если заказ создан из спецификации)
        description: описание заказа
        total_amount: общая сумма
    
    Returns:
        dict: результат операции {'success': bool, 'id': int, 'error': str}
    """
    try:
        if not order_date:
            from datetime import date
            order_date = date.today()
        
        order_id = db.orders.insert(
            customer_id=customer_id,
            order_number=order_number,
            order_date=order_date,
            project_id=project_id,
            specification_id=specification_id,
            description=description,
            total_amount=total_amount
        )
        db.commit()
        return {'success': True, 'id': order_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def create_order_from_specification(db, specification_id):
    """
    Создать заказ из спецификации: копировать данные спецификации в заказ, позиции спецификации в позиции заказа.
    
    Args:
        db: объект базы данных
        specification_id: ID спецификации
    
    Returns:
        dict: результат операции {'success': bool, 'id': int, 'error': str}
    """
    try:
        specification = db.specifications(specification_id)
        if not specification:
            return {'success': False, 'error': 'Спецификация не найдена'}
        
        order_number = generate_order_number(db)
        from datetime import date
        order_date = date.today()
        
        order_id = db.orders.insert(
            specification_id=specification_id,
            project_id=specification.project_id,
            customer_id=specification.customer_id,
            order_number=order_number,
            order_date=order_date,
            total_amount=specification.total_amount or 0,
            description=specification.description or ''
        )
        
        specification_items = db(db.specification_items.specification_id == specification_id).select()
        for item in specification_items:
            db.order_items.insert(
                order_id=order_id,
                item_name=item.item_name,
                quantity=item.quantity,
                unit=item.unit or 'шт',
                price=item.price or 0,
                total=item.total or 0,
                description=item.description or ''
            )
        
        db.commit()
        return {'success': True, 'id': order_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_order_by_id(db, order_id):
    """
    Получить заказ по ID
    
    Args:
        db: объект базы данных
        order_id: ID заказа
    
    Returns:
        Row или None: запись заказа или None если не найдена
    """
    try:
        return db.orders(order_id) or None
    except Exception as e:
        return None


def get_order_by_number(db, order_number):
    """
    Получить заказ по номеру
    
    Args:
        db: объект базы данных
        order_number: номер заказа
    
    Returns:
        Row или None: запись заказа или None если не найдена
    """
    try:
        return db(db.orders.order_number == order_number).select().first()
    except Exception as e:
        return None


def get_all_orders(db, customer_id=None, project_id=None, specification_id=None, order_by='created_on'):
    """
    Получить все заказы
    
    Args:
        db: объект базы данных
        customer_id: фильтр по клиенту
        project_id: фильтр по проекту
        complect_id: фильтр по комплекту
        order_by: поле для сортировки
    
    Returns:
        Rows: список всех заказов
    """
    try:
        query = db.orders.id > 0
        if customer_id:
            query = query & (db.orders.customer_id == customer_id)
        if project_id:
            query = query & (db.orders.project_id == project_id)
        if complect_id:
            query = query & (db.orders.complect_id == complect_id)
        
        if order_by == 'created_on':
            return db(query).select(orderby=~db.orders.created_on)
        return db(query).select(orderby=db.orders[order_by])
    except Exception as e:
        return db().select(db.orders.id)


def update_order(db, order_id, **kwargs):
    """
    Обновить заказ
    
    Args:
        db: объект базы данных
        order_id: ID заказа
        **kwargs: поля для обновления
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        order = db.orders(order_id)
        if not order:
            return {'success': False, 'error': 'Заказ не найден'}
        
        allowed_fields = ['customer_id', 'project_id', 'complect_id', 'order_number', 'order_date',
                         'description', 'total_amount']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if update_data:
            db(db.orders.id == order_id).update(**update_data)
            db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_order(db, order_id):
    """
    Удалить заказ
    
    Args:
        db: объект базы данных
        order_id: ID заказа
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        order = db.orders(order_id)
        if not order:
            return {'success': False, 'error': 'Заказ не найден'}
        
        # Удаляем связанные позиции заказа
        db(db.order_items.order_id == order_id).delete()
        
        # Удаляем заказ
        db(db.orders.id == order_id).delete()
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def search_orders(db, search_term, customer_id=None):
    """
    Поиск заказов по номеру или описанию
    
    Args:
        db: объект базы данных
        search_term: поисковый запрос
        customer_id: фильтр по клиенту
    
    Returns:
        Rows: список найденных заказов
    """
    try:
        query = (db.orders.order_number.contains(search_term)) | \
                (db.orders.description.contains(search_term))
        if customer_id:
            query = query & (db.orders.customer_id == customer_id)
        return db(query).select(orderby=~db.orders.created_on)
    except Exception as e:
        return db().select(db.orders.id)


def get_order_items(db, order_id):
    """
    Получить все позиции заказа
    
    Args:
        db: объект базы данных
        order_id: ID заказа
    
    Returns:
        Rows: список позиций заказа
    """
    try:
        return db(db.order_items.order_id == order_id).select(
            orderby=db.order_items.id
        )
    except Exception as e:
        return db().select(db.order_items.id)


def calculate_order_total(db, order_id):
    """
    Пересчитать общую сумму заказа на основе позиций
    
    Args:
        db: объект базы данных
        order_id: ID заказа
    
    Returns:
        dict: результат операции {'success': bool, 'total': float, 'error': str}
    """
    try:
        items = db(db.order_items.order_id == order_id).select()
        total = sum(float(item.total or 0) for item in items)
        
        db(db.orders.id == order_id).update(total_amount=total)
        db.commit()
        return {'success': True, 'total': total}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def generate_order_number(db):
    """
    Сгенерировать уникальный номер заказа
    
    Args:
        db: объект базы данных
    
    Returns:
        str: номер заказа в формате ORD-YYYYMMDD-XXXX
    """
    try:
        from datetime import datetime
        today = datetime.now().strftime('%Y%m%d')
        prefix = f'ORD-{today}-'
        
        # Находим последний заказ с таким префиксом
        last_order = db(db.orders.order_number.like(f'{prefix}%')).select(
            orderby=~db.orders.order_number,
            limitby=(0, 1)
        ).first()
        
        if last_order:
            last_num = int(last_order.order_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f'{prefix}{new_num:04d}'
    except Exception as e:
        return f'ORD-{datetime.now().strftime("%Y%m%d")}-0001'
