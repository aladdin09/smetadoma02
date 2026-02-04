# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей order_items (Позиции заказа)
"""


def create_order_item(db, order_id, item_name, quantity=1, unit='шт',
                     price=0, description=None):
    """
    Создать новую позицию заказа
    
    Args:
        db: объект базы данных
        order_id: ID заказа
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
        item_id = db.order_items.insert(
            order_id=order_id,
            item_name=item_name,
            quantity=quantity,
            unit=unit,
            price=price,
            total=total,
            description=description
        )
        db.commit()
        
        # Пересчитываем общую сумму заказа
        import orders_service
        orders_service.calculate_order_total(db, order_id)
        
        return {'success': True, 'id': item_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_order_item_by_id(db, item_id):
    """
    Получить позицию заказа по ID
    
    Args:
        db: объект базы данных
        item_id: ID позиции
    
    Returns:
        Row или None: запись позиции или None если не найдена
    """
    try:
        return db.order_items(item_id) or None
    except Exception as e:
        return None


def get_all_order_items(db, order_id=None, order_by='id'):
    """
    Получить все позиции заказа
    
    Args:
        db: объект базы данных
        order_id: фильтр по заказу
        order_by: поле для сортировки
    
    Returns:
        Rows: список всех позиций
    """
    try:
        query = db.order_items.id > 0
        if order_id:
            query = query & (db.order_items.order_id == order_id)
        return db(query).select(orderby=db.order_items[order_by])
    except Exception as e:
        return db().select(db.order_items.id)


def update_order_item(db, item_id, **kwargs):
    """
    Обновить позицию заказа
    
    Args:
        db: объект базы данных
        item_id: ID позиции
        **kwargs: поля для обновления
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        item = db.order_items(item_id)
        if not item:
            return {'success': False, 'error': 'Позиция не найдена'}
        
        allowed_fields = ['order_id', 'item_name', 'quantity', 'unit', 
                         'price', 'description']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        # Пересчитываем итого если изменились количество или цена
        if 'quantity' in update_data or 'price' in update_data:
            quantity = update_data.get('quantity', item.quantity)
            price = update_data.get('price', item.price)
            update_data['total'] = float(quantity) * float(price)
        
        if update_data:
            db(db.order_items.id == item_id).update(**update_data)
            db.commit()
            
            # Пересчитываем общую сумму заказа
            import orders_service
            orders_service.calculate_order_total(db, item.order_id)
        
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_order_item(db, item_id):
    """
    Удалить позицию заказа
    
    Args:
        db: объект базы данных
        item_id: ID позиции
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        item = db.order_items(item_id)
        if not item:
            return {'success': False, 'error': 'Позиция не найдена'}
        
        order_id = item.order_id
        
        db(db.order_items.id == item_id).delete()
        db.commit()
        
        # Пересчитываем общую сумму заказа
        import orders_service
        orders_service.calculate_order_total(db, order_id)
        
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def search_order_items(db, search_term, order_id=None):
    """
    Поиск позиций заказа по названию или описанию
    
    Args:
        db: объект базы данных
        search_term: поисковый запрос
        order_id: фильтр по заказу
    
    Returns:
        Rows: список найденных позиций
    """
    try:
        query = (db.order_items.item_name.contains(search_term)) | \
                (db.order_items.description.contains(search_term))
        if order_id:
            query = query & (db.order_items.order_id == order_id)
        return db(query).select(orderby=db.order_items.id)
    except Exception as e:
        return db().select(db.order_items.id)
