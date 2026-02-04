# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей user_roles (Роли пользователей)
"""


def create_role(db, name, description=None, sort_order=0, is_active=True):
    """Создать новую роль"""
    try:
        role_id = db.user_roles.insert(
            name=name,
            description=description,
            sort_order=sort_order,
            is_active=is_active
        )
        db.commit()
        return {'success': True, 'id': role_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_role_by_id(db, role_id):
    """Получить роль по ID"""
    try:
        return db.user_roles(role_id) or None
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        return None


def get_all_roles(db, is_active=None, order_by='sort_order'):
    """Получить все роли"""
    try:
        query = db.user_roles.id > 0
        if is_active is not None:
            query = query & (db.user_roles.is_active == is_active)
        return db(query).select(orderby=db.user_roles[order_by])
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        try:
            return db().select(db.user_roles.id)
        except:
            return []


def update_role(db, role_id, **kwargs):
    """Обновить роль"""
    try:
        role = db.user_roles(role_id)
        if not role:
            return {'success': False, 'error': 'Роль не найдена'}
        allowed_fields = ['name', 'description', 'sort_order', 'is_active']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if update_data:
            db(db.user_roles.id == role_id).update(**update_data)
            db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_role(db, role_id):
    """Удалить роль"""
    try:
        role = db.user_roles(role_id)
        if not role:
            return {'success': False, 'error': 'Роль не найдена'}
        db(db.user_roles.id == role_id).delete()
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
