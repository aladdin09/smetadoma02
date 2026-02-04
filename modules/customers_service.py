# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей customers (Клиенты)
"""


def create_customer(db, name, phone=None, email=None, address=None, notes=None):
    """
    Создать нового клиента
    
    Args:
        db: объект базы данных
        name: имя клиента
        phone: телефон
        email: email
        address: адрес
        notes: примечания
    
    Returns:
        dict: результат операции {'success': bool, 'id': int, 'error': str}
    """
    try:
        customer_id = db.customers.insert(
            name=name,
            phone=phone,
            email=email,
            address=address,
            notes=notes
        )
        db.commit()
        return {'success': True, 'id': customer_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_customer_by_id(db, customer_id):
    """
    Получить клиента по ID
    
    Args:
        db: объект базы данных
        customer_id: ID клиента
    
    Returns:
        Row или None: запись клиента или None если не найдена
    """
    try:
        return db.customers(customer_id) or None
    except Exception as e:
        return None


def get_all_customers(db, order_by='name', limitby=None, customer_ids=None):
    """
    Получить клиентов. Если задан customer_ids — только этих (для менеджера).
    """
    try:
        query = db.customers.id > 0
        if customer_ids is not None and len(customer_ids) == 0:
            return db(db.customers.id < 0).select()  # пустой результат (структура как у customers)
        if customer_ids is not None:
            query = db.customers.id.belongs(customer_ids)
        if limitby:
            return db(query).select(orderby=db.customers[order_by], limitby=limitby)
        return db(query).select(orderby=db.customers[order_by])
    except Exception as e:
        return db().select(db.customers.id)


def get_customers_for_manager(db, user_id, order_by='name'):
    """Клиенты, у которых есть хотя бы один проект с manager_id = user_id."""
    import role_helpers
    ids = role_helpers.get_manager_customer_ids(db, user_id)
    return get_all_customers(db, order_by=order_by, customer_ids=ids if ids else [])


def update_customer(db, customer_id, **kwargs):
    """
    Обновить клиента
    
    Args:
        db: объект базы данных
        customer_id: ID клиента
        **kwargs: поля для обновления (name, phone, email, address, notes)
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        customer = db.customers(customer_id)
        if not customer:
            return {'success': False, 'error': 'Клиент не найден'}
        
        allowed_fields = ['name', 'phone', 'email', 'address', 'notes']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if update_data:
            db(db.customers.id == customer_id).update(**update_data)
            db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_customer(db, customer_id):
    """
    Удалить клиента
    
    Args:
        db: объект базы данных
        customer_id: ID клиента
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        customer = db.customers(customer_id)
        if not customer:
            return {'success': False, 'error': 'Клиент не найден'}
        
        db(db.customers.id == customer_id).delete()
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def search_customers(db, search_term, order_by='name', customer_ids=None):
    """
    Поиск клиентов. Если задан customer_ids — ищем только среди них (для менеджера).
    """
    try:
        query = (db.customers.name.contains(search_term)) | \
                (db.customers.phone.contains(search_term)) | \
                (db.customers.email.contains(search_term)) | \
                (db.customers.address.contains(search_term))
        if customer_ids is not None:
            if not customer_ids:
                return db().select(db.customers.id)
            query = query & db.customers.id.belongs(customer_ids)
        return db(query).select(orderby=db.customers[order_by])
    except Exception as e:
        return db().select(db.customers.id)


def get_customer_specifications(db, customer_id):
    """
    Получить все спецификации клиента
    """
    try:
        return db(db.specifications.customer_id == customer_id).select(
            orderby=~db.specifications.created_on
        )
    except Exception as e:
        return db().select(db.specifications.id)
