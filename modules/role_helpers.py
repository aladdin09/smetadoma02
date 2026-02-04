# -*- coding: utf-8 -*-
"""
Проверка ролей пользователя для разграничения доступа.
Менеджер (role_id=3) видит только своих клиентов/проекты; admin (1), Собственник (2), РОП (4) — всех.
"""

MANAGER_ROLE_ID = 3


def is_manager(auth):
    """Текущий пользователь — менеджер (видит только своих клиентов)."""
    if not auth or not auth.user:
        return False
    try:
        return int(auth.user.role_id or 0) == MANAGER_ROLE_ID
    except (TypeError, ValueError):
        return False


def get_manager_customer_ids(db, user_id):
    """
    ID клиентов, у которых есть хотя бы один проект с manager_id = user_id.
    Для менеджера это «его» клиенты.
    """
    if not user_id:
        return []
    try:
        rows = db(db.projects.manager_id == user_id).select(db.projects.customer_id, distinct=True)
        return [r.customer_id for r in rows if r.customer_id]
    except Exception:
        return []


def get_manager_project_ids(db, user_id):
    """ID проектов, где manager_id = user_id."""
    if not user_id:
        return []
    try:
        rows = db(db.projects.manager_id == user_id).select(db.projects.id)
        return [r.id for r in rows if r.id]
    except Exception:
        return []
