# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей request_items (Позиции заявки)
"""


def create_request_item(db, request_id, item_name, quantity=1, unit='шт',
                       price=0, description=None):
    """
    Создать новую позицию заявки
    
    Args:
        db: объект базы данных
        request_id: ID заявки
        item_name: название позиции
        quantity: количество
        unit: единица измерения
        price: цена за единицу
        description: описание
    
    Returns:
        dict: результат операции {'success': bool, 'id': int, 'error': str}
    """
    try:
        total = float(quantity) * float(price)
        item_id = db.request_items.insert(
            request_id=request_id,
            item_name=item_name,
            quantity=quantity,
            unit=unit,
            price=price,
            total=total,
            description=description
        )
        db.commit()
        
        # Пересчитываем общую сумму заявки
        import requests_service
        requests_service.calculate_request_total(db, request_id)
        
        return {'success': True, 'id': item_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_request_item_by_id(db, item_id):
    """
    Получить позицию заявки по ID
    
    Args:
        db: объект базы данных
        item_id: ID позиции
    
    Returns:
        Row или None: запись позиции или None если не найдена
    """
    try:
        return db.request_items(item_id) or None
    except Exception as e:
        return None


def get_all_request_items(db, request_id=None, order_by='id'):
    """
    Получить все позиции заявки
    
    Args:
        db: объект базы данных
        request_id: фильтр по заявке
        order_by: поле для сортировки
    
    Returns:
        Rows: список всех позиций
    """
    try:
        query = db.request_items.id > 0
        if request_id:
            query = query & (db.request_items.request_id == request_id)
        return db(query).select(orderby=db.request_items[order_by])
    except Exception as e:
        return db().select(db.request_items.id)


def update_request_item(db, item_id, **kwargs):
    """
    Обновить позицию заявки
    
    Args:
        db: объект базы данных
        item_id: ID позиции
        **kwargs: поля для обновления
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        item = db.request_items(item_id)
        if not item:
            return {'success': False, 'error': 'Позиция не найдена'}
        
        allowed_fields = ['request_id', 'item_name', 'quantity', 'unit', 
                         'price', 'description']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        # Пересчитываем итого если изменились количество или цена
        if 'quantity' in update_data or 'price' in update_data:
            quantity = update_data.get('quantity', item.quantity)
            price = update_data.get('price', item.price)
            update_data['total'] = float(quantity) * float(price)
        
        if update_data:
            db(db.request_items.id == item_id).update(**update_data)
            db.commit()
            
            # Пересчитываем общую сумму заявки
            import requests_service
            requests_service.calculate_request_total(db, item.request_id)
        
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_request_item(db, item_id):
    """
    Удалить позицию заявки
    
    Args:
        db: объект базы данных
        item_id: ID позиции
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        item = db.request_items(item_id)
        if not item:
            return {'success': False, 'error': 'Позиция не найдена'}
        
        request_id = item.request_id
        
        db(db.request_items.id == item_id).delete()
        db.commit()
        
        # Пересчитываем общую сумму заявки
        import requests_service
        requests_service.calculate_request_total(db, request_id)
        
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def search_request_items(db, search_term, request_id=None):
    """
    Поиск позиций заявки по названию или описанию
    
    Args:
        db: объект базы данных
        search_term: поисковый запрос
        request_id: фильтр по заявке
    
    Returns:
        Rows: список найденных позиций
    """
    try:
        query = (db.request_items.item_name.contains(search_term)) | \
                (db.request_items.description.contains(search_term))
        if request_id:
            query = query & (db.request_items.request_id == request_id)
        return db(query).select(orderby=db.request_items.id)
    except Exception as e:
        return db().select(db.request_items.id)
