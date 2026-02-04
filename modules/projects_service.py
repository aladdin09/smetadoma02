# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей projects (Проекты)
"""

from datetime import datetime

def _now():
    """Текущее время в часовом поясе приложения (как request.now), иначе UTC."""
    try:
        from gluon import current
        return current.request.now
    except Exception:
        return datetime.utcnow()


def create_project(db, name, customer_id=None, request_id=None, order_id=None,
                   project_number=None, start_date=None, end_date=None,
                   status_id=None, budget=0, description=None, notes=None,
                   sla_hours=None, manager_id=None):
    """
    Создать новый проект
    
    Args:
        db: объект базы данных
        name: название проекта (обязательное)
        customer_id: ID клиента
        request_id: ID заявки
        order_id: ID заказа
        project_number: номер проекта
        start_date: дата начала проекта
        end_date: дата окончания проекта
        status_id: ID статуса проекта
        budget: бюджет проекта
        description: описание проекта
        notes: примечания
        sla_hours: SLA - максимальное время в статусе (часы)
        manager_id: ID ответственного менеджера
    
    Returns:
        dict: результат операции {'success': bool, 'id': int, 'error': str}
    """
    try:
        # По умолчанию — статус «Начальный», пока у проекта нет комплектов
        # Если статус не найден, берем первый доступный активный статус
        if status_id is None:
            import project_statuses_service
            row = project_statuses_service.get_status_by_name(db, 'Начальный')
            if row:
                status_id = row.id
            else:
                # Если статус "Начальный" не найден, берем первый активный статус
                all_statuses = project_statuses_service.get_all_statuses(db, is_active=True, order_by='sort_order')
                if all_statuses:
                    first_status = all_statuses.first()
                    if first_status:
                        status_id = first_status.id
                    else:
                        # Если нет активных статусов, берем любой первый
                        any_status = db(db.project_statuses.id > 0).select(db.project_statuses.id, limitby=(0, 1)).first()
                        status_id = any_status.id if any_status else None
                else:
                    # Если вообще нет статусов, берем любой первый (даже неактивный)
                    any_status = db(db.project_statuses.id > 0).select(db.project_statuses.id, limitby=(0, 1)).first()
                    status_id = any_status.id if any_status else None
        
        # Проверяем, что status_id существует в базе (если не None)
        if status_id is not None:
            try:
                status_exists = db(db.project_statuses.id == status_id).select(db.project_statuses.id, limitby=(0, 1)).first()
                if not status_exists:
                    # Статус не существует, пытаемся найти любой доступный
                    any_status = db(db.project_statuses.id > 0).select(db.project_statuses.id, limitby=(0, 1)).first()
                    if any_status:
                        status_id = any_status.id
                    else:
                        return {'success': False, 'error': 'В базе данных нет статусов проектов. Создайте хотя бы один статус.'}
            except Exception:
                # Если проверка не удалась, оставляем status_id как есть
                pass
        project_id = db.projects.insert(
            name=name,
            customer_id=customer_id,
            request_id=request_id,
            order_id=order_id,
            project_number=project_number,
            start_date=start_date,
            end_date=end_date,
            status_id=status_id,
            budget=budget,
            description=description,
            notes=notes,
            sla_hours=sla_hours,
            manager_id=manager_id
        )
        db.commit()
        return {'success': True, 'id': project_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_project_by_id(db, project_id):
    """
    Получить проект по ID
    
    Args:
        db: объект базы данных
        project_id: ID проекта (int)
    
    Returns:
        Row или None: запись проекта или None если не найдена
    """
    try:
        row = db(db.projects.id == project_id).select().first()
        return row
    except Exception as e:
        return None


def get_all_projects(db, customer_id=None, status_id=None, manager_id=None, order_by='created_on'):
    """
    Получить все проекты
    
    Args:
        db: объект базы данных
        customer_id: фильтр по клиенту
        status_id: фильтр по статусу
        manager_id: фильтр по менеджеру
        order_by: поле для сортировки
    
    Returns:
        Rows: список всех проектов
    """
    try:
        query = db.projects.id > 0
        if customer_id:
            query = query & (db.projects.customer_id == customer_id)
        if status_id:
            query = query & (db.projects.status_id == status_id)
        if manager_id:
            query = query & (db.projects.manager_id == manager_id)
        
        if order_by == 'created_on':
            return db(query).select(orderby=~db.projects.created_on)
        return db(query).select(orderby=db.projects[order_by])
    except Exception as e:
        return db().select(db.projects.id)


def update_project(db, project_id, **kwargs):
    """
    Обновить проект
    
    Args:
        db: объект базы данных
        project_id: ID проекта
        **kwargs: поля для обновления
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        project = db.projects(project_id)
        if not project:
            return {'success': False, 'error': 'Проект не найден'}
        
        allowed_fields = ['name', 'customer_id', 'request_id', 'order_id',
                         'project_number', 'start_date', 'end_date', 'status_id',
                         'budget', 'description', 'notes', 'sla_hours', 'manager_id']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        # Если меняется статус, обновляем дату входа в статус (тот же пояс, что и created_on)
        if 'status_id' in update_data:
            update_data['status_started_at'] = _now()
        
        if update_data:
            db(db.projects.id == project_id).update(**update_data)
            db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def update_project_status(db, project_id, status_id):
    """
    Обновить статус проекта
    
    Args:
        db: объект базы данных
        project_id: ID проекта (int)
        status_id: новый ID статуса
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        pid = int(project_id)
        sid = int(status_id)
        project = db.projects(pid)
        if not project:
            return {'success': False, 'error': 'Проект не найден'}
        db(db.projects.id == pid).update(
            status_id=sid,
            status_started_at=_now()
        )
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_project(db, project_id):
    """
    Удалить проект
    
    Args:
        db: объект базы данных
        project_id: ID проекта
    
    Returns:
        dict: результат операции {'success': bool, 'error': str}
    """
    try:
        project = db.projects(project_id)
        if not project:
            return {'success': False, 'error': 'Проект не найден'}
        
        db(db.projects.id == project_id).delete()
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def search_projects(db, search_term, customer_id=None, status_id=None):
    """
    Поиск проектов по названию, номеру проекта или описанию
    
    Args:
        db: объект базы данных
        search_term: поисковый запрос
        customer_id: фильтр по клиенту
        status_id: фильтр по статусу
    
    Returns:
        Rows: список найденных проектов
    """
    try:
        query = (db.projects.name.contains(search_term)) | \
                (db.projects.project_number.contains(search_term)) | \
                (db.projects.description.contains(search_term))
        if customer_id:
            query = query & (db.projects.customer_id == customer_id)
        if status_id:
            query = query & (db.projects.status_id == status_id)
        return db(query).select(orderby=~db.projects.created_on)
    except Exception as e:
        return db().select(db.projects.id)


def get_customer_projects(db, customer_id, order_by='created_on'):
    """
    Получить все проекты клиента
    
    Args:
        db: объект базы данных
        customer_id: ID клиента
        order_by: поле для сортировки
    
    Returns:
        Rows: список проектов клиента
    """
    try:
        query = db.projects.customer_id == customer_id
        if order_by == 'created_on':
            return db(query).select(orderby=~db.projects.created_on)
        return db(query).select(orderby=db.projects[order_by])
    except Exception as e:
        return db().select(db.projects.id)


def get_projects_with_status(db, customer_id=None, status_id=None, order_by='created_on'):
    """
    Получить проекты с информацией о статусах (с join)
    
    Args:
        db: объект базы данных
        customer_id: фильтр по клиенту
        status_id: фильтр по статусу
        order_by: поле для сортировки
    
    Returns:
        Rows: список проектов с информацией о статусах
    """
    try:
        query = db.projects.id > 0
        if customer_id:
            query = query & (db.projects.customer_id == customer_id)
        if status_id:
            query = query & (db.projects.status_id == status_id)
        
        if order_by == 'created_on':
            orderby = ~db.projects.created_on
        else:
            orderby = db.projects[order_by]
        
        return db(query).select(
            db.projects.ALL,
            db.project_statuses.ALL,
            left=db.project_statuses.on(db.projects.status_id == db.project_statuses.id),
            orderby=orderby
        )
    except Exception as e:
        return db().select(db.projects.id)


def generate_project_number(db):
    """
    Сгенерировать следующий номер проекта в формате XXX (001, 002, ...)
    
    Args:
        db: объект базы данных
    
    Returns:
        str: номер проекта в формате 001, 002, ...
    """
    try:
        # Находим все проекты с числовым номером в формате XXX (001, 002, ...)
        all_projects = db(db.projects.project_number != None).select(
            db.projects.project_number
        )
        
        max_num = 0
        for project in all_projects:
            if project.project_number:
                # Проверяем, что номер состоит только из цифр и имеет длину 3
                project_num_str = str(project.project_number).strip()
                if project_num_str.isdigit() and len(project_num_str) == 3:
                    num = int(project_num_str)
                    if num > max_num:
                        max_num = num
        
        # Генерируем следующий номер
        next_num = max_num + 1
        
        # Форматируем с ведущими нулями (001, 002, ...)
        return f'{next_num:03d}'
    except Exception as e:
        # В случае ошибки возвращаем 001
        return '001'
