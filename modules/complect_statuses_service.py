# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей complect_statuses (Статусы комплектов)
"""


def create_status(db, name, description=None, sort_order=0, is_active=True):
    """Создать новый статус комплекта"""
    try:
        status_id = db.complect_statuses.insert(
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
    """Получить статус по ID"""
    try:
        return db.complect_statuses(status_id) or None
    except Exception as e:
        # Откатываем транзакцию при ошибке
        try:
            db.rollback()
        except:
            pass
        return None


def get_all_statuses(db, is_active=None, order_by='sort_order'):
    """Получить все статусы комплектов"""
    try:
        query = db.complect_statuses.id > 0
        if is_active is not None:
            query = query & (db.complect_statuses.is_active == is_active)
        return db(query).select(orderby=db.complect_statuses[order_by])
    except Exception as e:
        # Откатываем транзакцию при ошибке
        try:
            db.rollback()
        except:
            pass
        # Пробуем вернуть пустой результат
        try:
            return db().select(db.complect_statuses.id)
        except:
            return []


def update_status(db, status_id, **kwargs):
    """Обновить статус комплекта"""
    try:
        status = db.complect_statuses(status_id)
        if not status:
            return {'success': False, 'error': 'Статус не найден'}
        allowed_fields = ['name', 'description', 'sort_order', 'is_active']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if update_data:
            db(db.complect_statuses.id == status_id).update(**update_data)
            db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_status(db, status_id):
    """Удалить статус комплекта"""
    try:
        status = db.complect_statuses(status_id)
        if not status:
            return {'success': False, 'error': 'Статус не найден'}
        db(db.complect_statuses.id == status_id).delete()
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def search_statuses(db, search_term, is_active=None):
    """Поиск статусов комплектов"""
    try:
        query = (db.complect_statuses.name.contains(search_term)) | \
                (db.complect_statuses.description.contains(search_term))
        if is_active is not None:
            query = query & (db.complect_statuses.is_active == is_active)
        return db(query).select(orderby=db.complect_statuses.sort_order)
    except Exception as e:
        # Откатываем транзакцию при ошибке
        try:
            db.rollback()
        except:
            pass
        # Пробуем вернуть пустой результат
        try:
            return db().select(db.complect_statuses.id)
        except:
            return []
