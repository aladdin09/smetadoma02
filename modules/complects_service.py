# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей complects (Комплекты)
"""

from datetime import datetime

# Названия статусов проекта для автосмены: Начальный (нет комплектов), Комплектация (есть хотя бы один)
PROJECT_STATUS_INITIAL_NAME = 'Начальный'
PROJECT_STATUS_COMPLECTATION_NAME = 'Комплектация'


def _get_project_status_id_by_name(db, name):
    """Возвращает id статуса проекта по имени или None."""
    import project_statuses_service
    row = project_statuses_service.get_status_by_name(db, name)
    return row.id if row else None


def create_complect(db, customer_id, status_id, description=None, next_step_id=None,
                   execution_time=None, deadline=None, total_amount=0, project_id=None, now=None):
    """
    Создать новый комплект.
    Смена статуса проекта на «Комплектация» при первом комплекте выполняется в контроллере (projects/view).
    """
    try:
        if now is None:
            now = datetime.now()
        project_id_int = int(project_id) if project_id is not None else None
        complect_id = db.complects.insert(
            customer_id=customer_id,
            project_id=project_id_int,
            status_id=status_id,
            status_changed_on=now,
            next_step_id=next_step_id,
            execution_time=execution_time,
            deadline=deadline,
            description=description,
            total_amount=total_amount
        )
        db.commit()
        # Смена статуса проекта выполняется в контроллере (projects/view) после успешного создания
        return {'success': True, 'id': complect_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_complect_by_id(db, complect_id):
    """Получить комплект по ID"""
    try:
        return db.complects(complect_id) or None
    except Exception as e:
        return None


def get_all_complects(db, customer_id=None, status_id=None, order_by='created_on'):
    """Получить все комплекты"""
    try:
        query = db.complects.id > 0
        if customer_id:
            query = query & (db.complects.customer_id == customer_id)
        if status_id:
            query = query & (db.complects.status_id == status_id)
        if order_by == 'created_on':
            return db(query).select(orderby=~db.complects.created_on)
        return db(query).select(orderby=db.complects[order_by])
    except Exception as e:
        return db().select(db.complects.id)


def update_complect(db, complect_id, **kwargs):
    """Обновить комплект"""
    try:
        complect = db.complects(complect_id)
        if not complect:
            return {'success': False, 'error': 'Комплект не найден'}
        allowed_fields = ['customer_id', 'project_id', 'status_id', 'next_step_id',
                         'execution_time', 'deadline', 'description', 'total_amount']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if 'status_id' in update_data:
            update_data['status_changed_on'] = datetime.now()
        if update_data:
            db(db.complects.id == complect_id).update(**update_data)
            db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def update_complect_status(db, complect_id, status_id):
    """Обновить статус комплекта"""
    try:
        complect = db.complects(complect_id)
        if not complect:
            return {'success': False, 'error': 'Комплект не найден'}
        db(db.complects.id == complect_id).update(
            status_id=status_id,
            status_changed_on=datetime.now()
        )
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_complect(db, complect_id):
    """
    Удалить комплект.
    Если у удаляемого комплекта был project_id и после удаления у проекта не остаётся
    комплектов — статус проекта автоматически меняется на «Начальный» (id=1).
    """
    try:
        complect = db.complects(complect_id)
        if not complect:
            return {'success': False, 'error': 'Комплект не найден'}
        project_id = complect.project_id
        db(db.complect_items.complect_id == complect_id).delete()
        db(db.complects.id == complect_id).delete()
        db.commit()
        # Комплектов у проекта не осталось — переводим проект в статус «Начальный»
        if project_id:
            count = db(db.complects.project_id == project_id).count()
            if count == 0:
                status_initial_id = _get_project_status_id_by_name(db, PROJECT_STATUS_INITIAL_NAME)
                if status_initial_id is not None:
                    import projects_service
                    projects_service.update_project_status(db, int(project_id), status_initial_id)
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def search_complects(db, search_term, customer_id=None, status_id=None):
    """Поиск комплектов по описанию"""
    try:
        query = db.complects.description.contains(search_term)
        if customer_id:
            query = query & (db.complects.customer_id == customer_id)
        if status_id:
            query = query & (db.complects.status_id == status_id)
        return db(query).select(orderby=~db.complects.created_on)
    except Exception as e:
        return db().select(db.complects.id)


def get_complect_items(db, complect_id):
    """Получить все позиции комплекта"""
    try:
        return db(db.complect_items.complect_id == complect_id).select(
            orderby=db.complect_items.id
        )
    except Exception as e:
        return db().select(db.complect_items.id)


def calculate_complect_total(db, complect_id):
    """Пересчитать общую сумму комплекта на основе позиций"""
    try:
        items = db(db.complect_items.complect_id == complect_id).select()
        total = sum(float(item.total or 0) for item in items)
        db(db.complects.id == complect_id).update(total_amount=total)
        db.commit()
        return {'success': True, 'total': total}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
