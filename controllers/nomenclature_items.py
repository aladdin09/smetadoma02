# -*- coding: utf-8 -*-
"""
Контроллер для работы с позициями номенклатуры
"""


def list():
    """
    Список всех позиций номенклатуры
    """
    import nomenclature_items_service
    
    search_term = request.vars.get('search', '')
    edit_id = request.vars.get('edit')
    edit_item = None
    form_edit = None
    show_edit_panel = False
    
    # Панель редактирования: при ?edit=id показываем форму редактирования в панели
    if edit_id:
        try:
            edit_id = int(edit_id)
            edit_item = db.nomenclature_items(edit_id)
        except (TypeError, ValueError):
            edit_item = None
        if edit_item:
            form_edit = SQLFORM(
                db.nomenclature_items,
                edit_id,
                submit_button='Сохранить',
                showid=False,
                _id='nomenclatureItemEditForm',
                _name='nomenclature_item_edit_form',
                _action=URL('nomenclature_items', 'list', vars=dict(edit=edit_id)),
                _method='POST'
            )
            if form_edit.process(formname='nomenclature_item_edit_form', keepvalues=False).accepted:
                session.flash = 'Позиция номенклатуры успешно обновлена'
                redirect(URL('nomenclature_items', 'list'))
            if form_edit.element('input[type=submit]'):
                form_edit.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
            show_edit_panel = True
    
    # Форма для добавления позиции номенклатуры (для sidebar)
    form_create = SQLFORM(
        db.nomenclature_items,
        submit_button='Создать',
        _id='nomenclatureItemCreateForm',
        _name='nomenclature_item_create_form',
        _action=URL('nomenclature_items', 'list'),
        _method='POST'
    )
    
    # Генерируем номер по умолчанию для формы создания
    default_number = nomenclature_items_service.generate_nomenclature_item_number(db)
    if form_create.element('#nomenclature_items_item_number'):
        form_create.element('#nomenclature_items_item_number')['_value'] = default_number
    
    # Обработка формы создания
    if form_create.process(formname='nomenclature_item_create_form', keepvalues=False).accepted:
        session.flash = 'Позиция номенклатуры успешно создана'
        redirect(URL('nomenclature_items', 'list'))
    
    # Настраиваем стили формы создания
    if form_create.element('input[type=submit]'):
        form_create.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
    
    items = []
    try:
        if search_term:
            items = nomenclature_items_service.search_nomenclature_items(db, search_term)
        else:
            items = nomenclature_items_service.get_all_nomenclature_items(db, order_by='created_on')
        
        # Проверяем, что items не None
        if items is None:
            items = []
        
        # Убеждаемся, что items итерируемый (не изменяя его)
        try:
            _ = iter(items)
        except (TypeError, AttributeError):
            items = []
            
    except Exception as e:
        # В случае ошибки возвращаем пустой список
        items = []
        try:
            import logging
            logging.error(f"Ошибка загрузки позиций номенклатуры: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
        except:
            pass
    
    import breadcrumbs_helper
    breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
        ('Главная', URL('default', 'index')),
        ('Номенклатура', None),
    ])
    return dict(
        items=items,
        search_term=search_term,
        breadcrumbs=breadcrumbs,
        form_create=form_create,
        form_edit=form_edit,
        show_edit_panel=show_edit_panel,
        edit_item=edit_item,
        default_number=default_number,
    )


def view():
    """
    Просмотр позиции номенклатуры
    """
    import nomenclature_items_service
    
    item_id = request.args(0)
    if not item_id:
        session.flash = 'Не указан ID позиции номенклатуры'
        redirect(URL('nomenclature_items', 'list'))
    
    item = nomenclature_items_service.get_nomenclature_item_by_id(db, item_id)
    if not item:
        session.flash = 'Позиция номенклатуры не найдена'
        redirect(URL('nomenclature_items', 'list'))
    
    import breadcrumbs_helper
    breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
        ('Главная', URL('default', 'index')),
        ('Номенклатура', URL('nomenclature_items', 'list')),
        (item.item_number or f'Позиция #{item.id}', None),
    ])
    return dict(item=item, breadcrumbs=breadcrumbs)


def create():
    """
    Создание новой позиции номенклатуры
    """
    import nomenclature_items_service
    
    # Генерируем номер по умолчанию
    default_number = nomenclature_items_service.generate_nomenclature_item_number(db)
    
    # Создаем форму
    form = SQLFORM(
        db.nomenclature_items,
        submit_button='Создать',
        _class='form-horizontal'
    )
    
    # Устанавливаем значение по умолчанию для номера
    if form.element('#nomenclature_items_item_number'):
        form.element('#nomenclature_items_item_number')['_value'] = default_number
    
    # Обработка формы
    if form.process().accepted:
        session.flash = 'Позиция номенклатуры успешно создана'
        redirect(URL('nomenclature_items', 'list'))
    elif form.errors:
        response.flash = 'Исправьте ошибки в форме'
    
    return dict(form=form, default_number=default_number)


def edit():
    """
    Редактирование позиции номенклатуры
    """
    import nomenclature_items_service
    
    item_id = request.args(0)
    if not item_id:
        session.flash = 'Не указан ID позиции номенклатуры'
        redirect(URL('nomenclature_items', 'list'))
    
    # Проверяем существование позиции
    item = nomenclature_items_service.get_nomenclature_item_by_id(db, item_id)
    if not item:
        session.flash = 'Позиция номенклатуры не найдена'
        redirect(URL('nomenclature_items', 'list'))
    
    # Создаем форму редактирования
    form = SQLFORM(
        db.nomenclature_items,
        item_id,
        submit_button='Сохранить',
        _class='form-horizontal',
        showid=False
    )
    
    # Обработка формы
    if form.process().accepted:
        session.flash = 'Позиция номенклатуры успешно обновлена'
        redirect(URL('nomenclature_items', 'list'))
    elif form.errors:
        response.flash = 'Исправьте ошибки в форме'
    
    import breadcrumbs_helper
    breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
        ('Главная', URL('default', 'index')),
        ('Номенклатура', URL('nomenclature_items', 'list')),
        ('Редактирование', None),
    ])
    
    return dict(form=form, item=item, breadcrumbs=breadcrumbs)


def delete():
    """
    Удаление позиции номенклатуры
    """
    import nomenclature_items_service
    
    item_id = request.args(0)
    if not item_id:
        session.flash = 'Не указан ID позиции номенклатуры'
        redirect(URL('nomenclature_items', 'list'))
    
    # Проверяем существование позиции
    item = nomenclature_items_service.get_nomenclature_item_by_id(db, item_id)
    if not item:
        session.flash = 'Позиция номенклатуры не найдена'
        redirect(URL('nomenclature_items', 'list'))
    
    # Удаляем позицию
    result = nomenclature_items_service.delete_nomenclature_item(db, item_id)
    
    if result.get('success'):
        session.flash = 'Позиция номенклатуры успешно удалена'
    else:
        session.flash = f'Ошибка при удалении позиции номенклатуры: {result.get("error", "Неизвестная ошибка")}'
    
    redirect(URL('nomenclature_items', 'list'))
