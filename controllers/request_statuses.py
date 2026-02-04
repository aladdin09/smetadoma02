# -*- coding: utf-8 -*-
"""
Контроллер для работы со статусами заявок
"""


def list():
    """
    Список всех статусов заявок
    """
    import request_statuses_service
    
    # Получаем все статусы
    statuses = request_statuses_service.get_all_statuses(db, order_by='sort_order')
    
    return dict(statuses=statuses)


def create():
    """
    Создание нового статуса заявки
    """
    import request_statuses_service
    
    # Создаем форму
    form = SQLFORM(
        db.request_statuses,
        submit_button='Создать',
        _class='form-horizontal'
    )
    
    # Обработка формы
    if form.process().accepted:
        session.flash = 'Статус заявки успешно создан'
        redirect(URL('request_statuses', 'list'))
    elif form.errors:
        response.flash = 'Исправьте ошибки в форме'
    
    return dict(form=form)


def edit():
    """
    Редактирование статуса заявки
    """
    import request_statuses_service
    
    status_id = request.args(0)
    if not status_id:
        session.flash = 'Не указан ID статуса'
        redirect(URL('request_statuses', 'list'))
    
    # Проверяем существование статуса
    status = request_statuses_service.get_status_by_id(db, status_id)
    if not status:
        session.flash = 'Статус не найден'
        redirect(URL('request_statuses', 'list'))
    
    # Создаем форму редактирования
    form = SQLFORM(
        db.request_statuses,
        status_id,
        submit_button='Сохранить',
        _class='form-horizontal',
        showid=False
    )
    
    # Обработка формы
    if form.process().accepted:
        session.flash = 'Статус заявки успешно обновлен'
        redirect(URL('request_statuses', 'list'))
    elif form.errors:
        response.flash = 'Исправьте ошибки в форме'
    
    return dict(form=form, status=status)


def delete():
    """
    Удаление статуса заявки
    """
    import request_statuses_service
    
    status_id = request.args(0)
    if not status_id:
        session.flash = 'Не указан ID статуса'
        redirect(URL('request_statuses', 'list'))
    
    # Проверяем существование статуса
    status = request_statuses_service.get_status_by_id(db, status_id)
    if not status:
        session.flash = 'Статус не найден'
        redirect(URL('request_statuses', 'list'))
    
    # Удаляем статус
    result = request_statuses_service.delete_status(db, status_id)
    
    if result.get('success'):
        session.flash = 'Статус заявки успешно удален'
    else:
        session.flash = f'Ошибка при удалении статуса: {result.get("error", "Неизвестная ошибка")}'
    
    redirect(URL('request_statuses', 'list'))
