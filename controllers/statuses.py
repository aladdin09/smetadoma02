# -*- coding: utf-8 -*-
"""
Контроллер для работы со статусами
"""


def list():
    """
    Список всех статусов
    """
    import statuses_service
    
    # Получаем все статусы
    statuses = statuses_service.get_all_statuses(db, order_by='sort_order')
    
    return dict(statuses=statuses)


def create():
    """
    Создание нового статуса
    """
    import statuses_service
    
    # Создаем форму
    form = SQLFORM(
        db.statuses,
        submit_button='Создать',
        _class='form-horizontal'
    )
    
    # Обработка формы
    if form.process().accepted:
        session.flash = 'Статус успешно создан'
        redirect(URL('statuses', 'list'))
    elif form.errors:
        response.flash = 'Исправьте ошибки в форме'
    
    return dict(form=form)


def edit():
    """
    Редактирование статуса
    """
    import statuses_service
    
    status_id = request.args(0)
    if not status_id:
        session.flash = 'Не указан ID статуса'
        redirect(URL('statuses', 'list'))
    
    # Проверяем существование статуса
    status = statuses_service.get_status_by_id(db, status_id)
    if not status:
        session.flash = 'Статус не найден'
        redirect(URL('statuses', 'list'))
    
    # Создаем форму редактирования
    form = SQLFORM(
        db.statuses,
        status_id,
        submit_button='Сохранить',
        _class='form-horizontal',
        showid=False
    )
    
    # Обработка формы
    if form.process().accepted:
        session.flash = 'Статус успешно обновлен'
        redirect(URL('statuses', 'list'))
    elif form.errors:
        response.flash = 'Исправьте ошибки в форме'
    
    return dict(form=form, status=status)


def delete():
    """
    Удаление статуса
    """
    import statuses_service
    
    status_id = request.args(0)
    if not status_id:
        session.flash = 'Не указан ID статуса'
        redirect(URL('statuses', 'list'))
    
    # Проверяем существование статуса
    status = statuses_service.get_status_by_id(db, status_id)
    if not status:
        session.flash = 'Статус не найден'
        redirect(URL('statuses', 'list'))
    
    # Удаляем статус
    result = statuses_service.delete_status(db, status_id)
    
    if result.get('success'):
        session.flash = 'Статус успешно удален'
    else:
        session.flash = f'Ошибка при удалении статуса: {result.get("error", "Неизвестная ошибка")}'
    
    redirect(URL('statuses', 'list'))
