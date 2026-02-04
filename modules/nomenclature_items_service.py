# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей nomenclature_items (Позиции номенклатуры)
"""

from datetime import datetime


def create_nomenclature_item(db, item_number, item_date=None,
                        total_cost=0,
                        description=None,
                        unit='шт',
                        item_type_id=None):
    """
    Создать новую позицию номенклатуры
    
    Args:
        db: объект базы данных
        item_number: номер позиции номенклатуры
        item_date: дата позиции
        total_cost: общая стоимость
        description: описание позиции номенклатуры
        unit: единица измерения
    
    Returns:
        dict: результат операции {'success': bool, 'id': int, 'error': str}
    """
    try:
        if not item_date:
            from datetime import date
            item_date = date.today()
        
        item_id = db.nomenclature_items.insert(
            item_number=item_number,
            item_date=item_date,
            total_cost=total_cost,
            description=description,
            unit=(unit or 'шт').strip() or 'шт',
            item_type_id=item_type_id
        )
        db.commit()
        return {'success': True, 'id': item_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_nomenclature_item_by_id(db, item_id):
    """
    Получить позицию номенклатуры по ID
    
    Args:
        db: объект базы данных
        item_id: ID позиции номенклатуры
    
    Returns:
        Row или None: запись позиции номенклатуры или None если не найдена
    """
    try:
        return db.nomenclature_items(item_id) or None
    except Exception as e:
        return None


def get_nomenclature_item_by_number(db, item_number):
    """
    Получить позицию номенклатуры по номеру
    
    Args:
        db: объект базы данных
        item_number: номер позиции номенклатуры
    
    Returns:
        Row или None: запись позиции номенклатуры или None если не найдена
    """
    try:
        return db(db.nomenclature_items.item_number == item_number).select().first()
    except Exception as e:
        return None


def get_all_nomenclature_items(db, order_by='created_on'):
    """
    Получить все позиции номенклатуры с типами
    
    Args:
        db: объект базы данных
        order_by: поле для сортировки
    
    Returns:
        Rows: список всех позиций номенклатуры с данными типов
    """
    try:
        query = db.nomenclature_items.id > 0
        
        if order_by == 'created_on':
            return db(query).select(
                db.nomenclature_items.ALL,
                db.nomenclature_item_types.ALL,
                left=db.nomenclature_item_types.on(db.nomenclature_items.item_type_id == db.nomenclature_item_types.id),
                orderby=~db.nomenclature_items.created_on
            )
        return db(query).select(
            db.nomenclature_items.ALL,
            db.nomenclature_item_types.ALL,
            left=db.nomenclature_item_types.on(db.nomenclature_items.item_type_id == db.nomenclature_item_types.id),
            orderby=db.nomenclature_items[order_by]
        )
    except Exception as e:
        # В случае ошибки возвращаем пустой список
        return []


def update_nomenclature_item(db, item_id, **kwargs):
    """
    Обновить позицию номенклатуры
    
    Args:
        db: объект базы данных
        item_id: ID позиции номенклатуры
        **kwargs: поля для обновления
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        item = db.nomenclature_items(item_id)
        if not item:
            return {'success': False, 'error': 'Позиция номенклатуры не найдена'}
        
        allowed_fields = ['item_number', 'item_date', 
                         'total_cost', 'description', 'unit', 'item_type_id']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if update_data:
            db(db.nomenclature_items.id == item_id).update(**update_data)
            db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_nomenclature_item(db, item_id):
    """
    Удалить позицию номенклатуры
    
    Args:
        db: объект базы данных
        item_id: ID позиции номенклатуры
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        item = db.nomenclature_items(item_id)
        if not item:
            return {'success': False, 'error': 'Позиция номенклатуры не найдена'}
        
        db(db.nomenclature_items.id == item_id).delete()
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def search_nomenclature_items(db, search_term):
    """
    Поиск позиций номенклатуры по номеру, описанию или типу дома
    
    Args:
        db: объект базы данных
        search_term: поисковый запрос
    
    Returns:
        Rows: список найденных позиций номенклатуры с данными типов
    """
    try:
        query = (db.nomenclature_items.item_number.contains(search_term)) | \
                (db.nomenclature_items.description.contains(search_term))
        return db(query).select(
            db.nomenclature_items.ALL,
            db.nomenclature_item_types.ALL,
            left=db.nomenclature_item_types.on(db.nomenclature_items.item_type_id == db.nomenclature_item_types.id),
            orderby=~db.nomenclature_items.created_on
        )
    except Exception as e:
        # В случае ошибки возвращаем пустой список
        return []


def generate_nomenclature_item_number(db):
    """
    Сгенерировать уникальный номер позиции номенклатуры
    
    Args:
        db: объект базы данных
    
    Returns:
        str: номер позиции номенклатуры в формате NOM-YYYYMMDD-XXXX
    """
    try:
        from datetime import datetime
        today = datetime.now().strftime('%Y%m%d')
        prefix = f'NOM-{today}-'
        
        # Находим последнюю позицию номенклатуры с таким префиксом
        last_item = db(db.nomenclature_items.item_number.like(f'{prefix}%')).select(
            orderby=~db.nomenclature_items.item_number,
            limitby=(0, 1)
        ).first()
        
        if last_item:
            last_num = int(last_item.item_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        return f'{prefix}{new_num:04d}'
    except Exception as e:
        return f'NOM-{datetime.now().strftime("%Y%m%d")}-0001'


def calculate_nomenclature_item_from_order(db, order_id, item_id=None):
    """
    Рассчитать позицию номенклатуры на основе заказа
    
    Args:
        db: объект базы данных
        order_id: ID заказа
        item_id: ID позиции номенклатуры (если обновляем существующую)
    
    Returns:
        dict: результат операции {'success': bool, 'item_id': int, 'total_cost': float, 'error': str}
    """
    try:
        order = db.orders(order_id)
        if not order:
            return {'success': False, 'error': 'Заказ не найден'}
        
        # Получаем позиции заказа
        items = db(db.order_items.order_id == order_id).select()
        total_cost = sum(float(item.total or 0) for item in items)
        
        if item_id:
            # Обновляем существующую позицию номенклатуры
            db(db.nomenclature_items.id == item_id).update(
                total_cost=total_cost
            )
            db.commit()
            return {'success': True, 'item_id': item_id, 'total_cost': total_cost}
        else:
            # Создаем новую позицию номенклатуры
            item_number = generate_nomenclature_item_number(db)
            result = create_nomenclature_item(
                db, item_number, total_cost=total_cost
            )
            if result['success']:
                return {'success': True, 'item_id': result['id'], 'total_cost': total_cost}
            return result
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
