# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей specifications (Спецификации)
"""

from datetime import datetime

PROJECT_STATUS_INITIAL_NAME = 'Начальный'
PROJECT_STATUS_COMPLECTATION_NAME = 'Комплектация'


def _get_project_status_id_by_name(db, name):
    """Возвращает id статуса проекта по имени или None."""
    import project_statuses_service
    row = project_statuses_service.get_status_by_name(db, name)
    return row.id if row else None


def create_specification(db, customer_id, status_id, description=None, next_step_id=None,
                   execution_time=None, deadline=None, total_amount=0, project_id=None, now=None):
    """Создать новую спецификацию."""
    try:
        if now is None:
            now = datetime.now()
        project_id_int = int(project_id) if project_id is not None else None
        specification_id = db.specifications.insert(
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
        return {'success': True, 'id': specification_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_specification_by_id(db, specification_id):
    """Получить спецификацию по ID"""
    try:
        return db.specifications(specification_id) or None
    except Exception as e:
        return None


def get_all_specifications(db, customer_id=None, status_id=None, order_by='created_on'):
    """Получить все спецификации"""
    try:
        query = db.specifications.id > 0
        if customer_id:
            query = query & (db.specifications.customer_id == customer_id)
        if status_id:
            query = query & (db.specifications.status_id == status_id)
        if order_by == 'created_on':
            return db(query).select(orderby=~db.specifications.created_on)
        return db(query).select(orderby=db.specifications[order_by])
    except Exception as e:
        return db().select(db.specifications.id)


def update_specification(db, specification_id, **kwargs):
    """Обновить спецификацию"""
    try:
        specification = db.specifications(specification_id)
        if not specification:
            return {'success': False, 'error': 'Спецификация не найдена'}
        allowed_fields = ['customer_id', 'project_id', 'status_id', 'next_step_id',
                         'execution_time', 'deadline', 'description', 'total_amount']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if 'status_id' in update_data:
            update_data['status_changed_on'] = datetime.now()
        if update_data:
            db(db.specifications.id == specification_id).update(**update_data)
            db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def update_specification_status(db, specification_id, status_id):
    """Обновить статус спецификации"""
    try:
        specification = db.specifications(specification_id)
        if not specification:
            return {'success': False, 'error': 'Спецификация не найдена'}
        db(db.specifications.id == specification_id).update(
            status_id=status_id,
            status_changed_on=datetime.now()
        )
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_specification(db, specification_id):
    """Удалить спецификацию."""
    try:
        specification = db.specifications(specification_id)
        if not specification:
            return {'success': False, 'error': 'Спецификация не найдена'}
        project_id = specification.project_id
        db(db.specification_items.specification_id == specification_id).delete()
        db(db.specifications.id == specification_id).delete()
        db.commit()
        if project_id:
            count = db(db.specifications.project_id == project_id).count()
            if count == 0:
                status_initial_id = _get_project_status_id_by_name(db, PROJECT_STATUS_INITIAL_NAME)
                if status_initial_id is not None:
                    import projects_service
                    projects_service.update_project_status(db, int(project_id), status_initial_id)
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def search_specifications(db, search_term, customer_id=None, status_id=None):
    """Поиск спецификаций по описанию"""
    try:
        query = db.specifications.description.contains(search_term)
        if customer_id:
            query = query & (db.specifications.customer_id == customer_id)
        if status_id:
            query = query & (db.specifications.status_id == status_id)
        return db(query).select(orderby=~db.specifications.created_on)
    except Exception as e:
        return db().select(db.specifications.id)


def get_specification_items(db, specification_id):
    """Получить все позиции спецификации"""
    try:
        return db(db.specification_items.specification_id == specification_id).select(
            orderby=db.specification_items.id
        )
    except Exception as e:
        return db().select(db.specification_items.id)


def calculate_specification_total(db, specification_id):
    """Пересчитать общую сумму спецификации на основе позиций"""
    try:
        items = db(db.specification_items.specification_id == specification_id).select()
        total = sum(float(item.total or 0) for item in items)
        db(db.specifications.id == specification_id).update(total_amount=total)
        db.commit()
        return {'success': True, 'total': total}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}
