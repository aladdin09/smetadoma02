# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей nomenclature_item_types (Типы позиций номенклатуры)
"""


def create_item_type(db, name, description=None, sort_order=0, is_active=True):
    """Создать новый тип позиции номенклатуры"""
    try:
        item_type_id = db.nomenclature_item_types.insert(
            name=name,
            description=description,
            sort_order=sort_order,
            is_active=is_active
        )
        db.commit()
        return {'success': True, 'id': item_type_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_item_type_by_id(db, item_type_id):
    """Получить тип позиции номенклатуры по ID"""
    try:
        return db.nomenclature_item_types(item_type_id) or None
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        return None


def get_all_item_types(db, is_active=None, order_by='sort_order'):
    """Получить все типы позиций номенклатуры"""
    try:
        query = db.nomenclature_item_types.id > 0
        if is_active is not None:
            query = query & (db.nomenclature_item_types.is_active == is_active)
        return db(query).select(orderby=db.nomenclature_item_types[order_by])
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        try:
            return db().select(db.nomenclature_item_types.id)
        except:
            return []


def update_item_type(db, item_type_id, **kwargs):
    """Обновить тип позиции номенклатуры"""
    try:
        item_type = db.nomenclature_item_types(item_type_id)
        if not item_type:
            return {'success': False, 'error': 'Тип позиции номенклатуры не найден'}
        allowed_fields = ['name', 'description', 'sort_order', 'is_active']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if update_data:
            db(db.nomenclature_item_types.id == item_type_id).update(**update_data)
            db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_item_type(db, item_type_id):
    """Удалить тип позиции номенклатуры"""
    try:
        item_type = db.nomenclature_item_types(item_type_id)
        if not item_type:
            return {'success': False, 'error': 'Тип позиции номенклатуры не найден'}
        db(db.nomenclature_item_types.id == item_type_id).delete()
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
