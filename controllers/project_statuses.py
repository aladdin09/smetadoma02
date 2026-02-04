# -*- coding: utf-8 -*-
"""
Контроллер для работы со статусами проектов
"""


def list():
    """
    Список всех статусов проектов
    """
    import project_statuses_service
    import importlib
    importlib.reload(project_statuses_service)
    # Форма для добавления статуса (в панели справа)
    form_status = SQLFORM(
        db.project_statuses,
        submit_button='Добавить',
        _id='projectStatusForm',
        _name='project_status_form',
        _action=URL('project_statuses', 'list'),
        _method='POST'
    )
    if form_status.process(formname='project_status_form', keepvalues=False).accepted:
        session.flash = 'Статус проекта успешно создан'
        redirect(URL('project_statuses', 'list'))
    if form_status.element('input[type=submit]'):
        form_status.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
    # Панель редактирования: при ?edit=id показываем форму редактирования в панели
    edit_status = None
    form_edit = None
    show_edit_panel = False
    edit_id = request.vars.get('edit')
    if edit_id:
        edit_status = project_statuses_service.get_status_by_id(db, edit_id)
        if edit_status:
            form_edit = SQLFORM(
                db.project_statuses,
                edit_id,
                submit_button='Сохранить',
                showid=False,
                _id='projectStatusEditForm',
                _name='project_status_edit_form',
                _action=URL('project_statuses', 'list', vars=dict(edit=edit_id)),
                _method='POST'
            )
            if form_edit.process(formname='project_status_edit_form', keepvalues=False).accepted:
                session.flash = 'Статус проекта успешно обновлён'
                redirect(URL('project_statuses', 'list'))
            if form_edit.element('input[type=submit]'):
                form_edit.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
            show_edit_panel = True
    statuses = project_statuses_service.get_all_statuses(db, order_by='sort_order')
    import breadcrumbs_helper
    breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
        ('Главная', URL('default', 'index')),
        ('Статус проекта', None),
    ])
    return dict(
        statuses=statuses,
        breadcrumbs=breadcrumbs,
        form_status=form_status,
        form_edit=form_edit,
        edit_status=edit_status,
        show_edit_panel=show_edit_panel,
    )


def create():
    """
    Создание нового статуса проекта
    """
    import project_statuses_service
    import importlib
    # Перезагружаем модуль для применения изменений
    importlib.reload(project_statuses_service)
    
    # Создаем форму
    form = SQLFORM(
        db.project_statuses,
        submit_button='Создать',
        _class='form-horizontal'
    )
    
    # Обработка формы
    if form.process().accepted:
        session.flash = 'Статус проекта успешно создан'
        redirect(URL('project_statuses', 'list'))
    elif form.errors:
        response.flash = 'Исправьте ошибки в форме'
    
    return dict(form=form)


def edit():
    """
    Редактирование статуса проекта
    """
    import project_statuses_service
    import importlib
    # Перезагружаем модуль для применения изменений
    importlib.reload(project_statuses_service)
    
    status_id = request.args(0)
    if not status_id:
        session.flash = 'Не указан ID статуса'
        redirect(URL('project_statuses', 'list'))
    
    # Проверяем существование статуса
    status = project_statuses_service.get_status_by_id(db, status_id)
    if not status:
        session.flash = 'Статус не найден'
        redirect(URL('project_statuses', 'list'))
    
    # Создаем форму редактирования
    form = SQLFORM(
        db.project_statuses,
        status_id,
        submit_button='Сохранить',
        _class='form-horizontal',
        showid=False
    )
    
    # Обработка формы
    if form.process().accepted:
        session.flash = 'Статус проекта успешно обновлен'
        redirect(URL('project_statuses', 'list'))
    elif form.errors:
        response.flash = 'Исправьте ошибки в форме'
    
    return dict(form=form, status=status)


def delete():
    """
    Удаление статуса проекта
    """
    import project_statuses_service
    import importlib
    # Перезагружаем модуль для применения изменений
    importlib.reload(project_statuses_service)
    
    status_id = request.args(0)
    if not status_id:
        session.flash = 'Не указан ID статуса'
        redirect(URL('project_statuses', 'list'))
    
    # Проверяем существование статуса
    status = project_statuses_service.get_status_by_id(db, status_id)
    if not status:
        session.flash = 'Статус не найден'
        redirect(URL('project_statuses', 'list'))
    
    # Удаляем статус
    result = project_statuses_service.delete_status(db, status_id)
    
    if result.get('success'):
        session.flash = 'Статус проекта успешно удален'
    else:
        session.flash = f'Ошибка при удалении статуса: {result.get("error", "Неизвестная ошибка")}'
    
    redirect(URL('project_statuses', 'list'))
