# -*- coding: utf-8 -*-
"""
Контроллер для работы с клиентами
"""
import role_helpers


def customer():
    """
    Карточка клиента
    """
    customer_id = request.args(0) or redirect(URL('default', 'index'))
    
    try:
        # Импортируем HTTP для обработки редиректов
        from gluon.http import HTTP
        import customers_service
        customer = customers_service.get_customer_by_id(db, customer_id)
        
        if not customer:
            session.flash = 'Клиент не найден'
            redirect(URL('default', 'index'))
        # Менеджер видит только своих клиентов или клиента без проектов (только что созданного)
        if role_helpers.is_manager(auth):
            manager_customer_ids = role_helpers.get_manager_customer_ids(db, auth.user.id)
            if int(customer_id) not in manager_customer_ids:
                # Разрешить доступ к клиенту без проектов (новый клиент — менеджер может добавить первый проект)
                has_projects = db(db.projects.customer_id == customer_id).select(db.projects.id, limitby=(0, 1)).first()
                if has_projects:
                    raise HTTP(403, 'Доступ запрещён: вы можете видеть только своих клиентов.')
        # Форма для добавления проекта (для sidebar)
        # Создаем форму без сохранения в БД (record=False)
        form_project = SQLFORM.factory(
            Field('name', 'string', length=200, requires=IS_NOT_EMPTY(), label='Название проекта'),
            Field('budget', 'decimal(10,2)', default=0, label='Бюджет проекта'),
            Field('start_date', 'date', label='Дата начала проекта'),
            Field('end_date', 'date', label='Дата окончания проекта'),
            Field('description', 'text', label='Описание проекта'),
            Field('notes', 'text', label='Примечания'),
            Field('sla_hours', 'integer', label='SLA - максимальное время в статусе (часы)'),
            submit_button='Добавить',
            _id='projectForm',
            _name='project_form',
            _action=URL('customers', 'customer', args=[customer_id]),
            _method='POST'
        )
        
        # Обработка формы добавления проекта
        show_project_panel = False
        if form_project.process(formname='project_form', keepvalues=False).accepted:
            # Получаем данные из формы безопасно
            project_name = str(form_project.vars.name) if form_project.vars.name else ''
            try:
                budget = float(form_project.vars.budget) if form_project.vars.budget else 0
            except:
                budget = 0
            start_date = form_project.vars.start_date if form_project.vars.start_date else None
            end_date = form_project.vars.end_date if form_project.vars.end_date else None
            description = str(form_project.vars.description) if form_project.vars.description else None
            notes = str(form_project.vars.notes) if form_project.vars.notes else None
            try:
                sla_hours = int(form_project.vars.sla_hours) if form_project.vars.sla_hours else None
            except:
                sla_hours = None
            
            # Генерируем номер проекта автоматически
            import projects_service
            project_number = projects_service.generate_project_number(db)
            
            # Менеджер при создании проекта назначается ответственным
            manager_id = auth.user.id if role_helpers.is_manager(auth) else None
            # Создаем проект через сервисный слой с правильными параметрами
            result = projects_service.create_project(
                db=db,
                name=project_name,
                customer_id=customer_id,
                status_id=1,  # Автоматически устанавливаем статус = 1
                project_number=project_number,
                budget=budget,
                start_date=start_date,
                end_date=end_date,
                description=description,
                notes=notes,
                sla_hours=sla_hours,
                manager_id=manager_id
            )
            
            if result.get('success'):
                session.flash = 'Проект успешно добавлен'
                redirect(URL('customers', 'customer', args=[customer_id], vars={}))
            else:
                session.flash = f'Ошибка при создании проекта: {result.get("error", "Неизвестная ошибка")}'
                show_project_panel = True
        elif form_project.errors:
            show_project_panel = True
        
        # Настраиваем стили формы
        if form_project.element('input[type=submit]'):
            form_project.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
        
        # Форма для редактирования клиента
        form_edit = SQLFORM(
            db.customers,
            record=customer,
            showid=False,
            submit_button='Сохранить',
            _id='customerEditForm',
            _name='customer_edit_form',
            _action=URL('customers', 'customer', args=[customer_id]),
            _method='POST'
        )
        
        # Обработка формы редактирования клиента
        show_edit_panel = request.vars.get('edit', '') == '1'
        if form_edit.process(formname='customer_edit_form', keepvalues=False).accepted:
            session.flash = 'Клиент успешно обновлен'
            redirect(URL('customers', 'customer', args=[customer_id], vars={}))
        elif form_edit.errors:
            show_edit_panel = True
        
        # Настраиваем стили формы редактирования
        if form_edit.element('input[type=submit]'):
            form_edit.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
        
        # Получаем проекты клиента с информацией о статусах
        import project_statuses_service
        
        # Получаем проекты клиента с join к статусам
        projects = db(db.projects.customer_id == customer_id).select(
            db.projects.ALL,
            db.project_statuses.ALL,
            left=db.project_statuses.on(db.projects.status_id == db.project_statuses.id),
            orderby=~db.projects.created_on
        )
        
        # Получаем все статусы проектов для отображения
        all_statuses = project_statuses_service.get_all_statuses(db, is_active=True, order_by='sort_order')
        status_dict = {}
        status_colors = {}
        for status in all_statuses:
            status_dict[status.id] = status
            status_colors[status.id] = get_status_color(status.name)
        
        # Хлебные крошки: Главная → Клиенты → Клиент
        import breadcrumbs_helper
        breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
            ('Главная', URL('default', 'index')),
            ('Клиенты', URL('customers', 'customers_list')),
            (customer.name, None),
        ])
        return dict(
            customer=customer,
            projects=projects,
            status_dict=status_dict,
            status_colors=status_colors,
            form_project=form_project,
            show_project_panel=show_project_panel,
            form_edit=form_edit,
            show_edit_panel=show_edit_panel,
            breadcrumbs=breadcrumbs,
        )
    except HTTP:
        # Пробрасываем HTTP исключения (редиректы) дальше
        raise
    except Exception as e:
        session.flash = f'Ошибка: {str(e)}'
        redirect(URL('default', 'index'))


def customers_list():
    """
    Список всех клиентов
    """
    # Форма для добавления клиента (для sidebar)
    form_customer = SQLFORM(
        db.customers, 
        submit_button='Добавить', 
        _id='customerForm', 
        _name='customer_form',
        _action=URL('customers', 'customers_list'),
        _method='POST'
    )
    
    # Обработка формы добавления клиента
    if form_customer.process(formname='customer_form', keepvalues=False).accepted:
        customer_id = form_customer.vars.id
        session.flash = 'Клиент успешно добавлен'
        redirect(URL('customers', 'customer', args=[customer_id], vars={}))
    
    # Настраиваем стили формы
    if form_customer.element('input[type=submit]'):
        form_customer.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
    
    # Параметры фильтрации и поиска (определяем до обработки формы редактирования)
    search_term = request.vars.get('search', '')
    
    # Форма для редактирования клиента
    edit_customer_id = request.vars.get('edit_customer_id', None)
    form_edit = None
    show_edit_panel = False
    edit_customer = None
    
    if edit_customer_id:
        try:
            edit_customer_id = int(edit_customer_id)
            # Менеджер может редактировать только своих клиентов
            if role_helpers.is_manager(auth) and auth.user:
                if edit_customer_id not in role_helpers.get_manager_customer_ids(db, auth.user.id):
                    edit_customer_id = None
            if edit_customer_id:
                import customers_service
                edit_customer = customers_service.get_customer_by_id(db, edit_customer_id)
            else:
                edit_customer = None
            if edit_customer:
                # Формируем URL для формы с сохранением параметра поиска
                form_vars = dict(edit_customer_id=edit_customer_id)
                if search_term:
                    form_vars['search'] = search_term
                
                form_edit = SQLFORM(
                    db.customers,
                    record=edit_customer,
                    showid=False,
                    submit_button='Сохранить',
                    _id='customerEditForm',
                    _name='customer_edit_form',
                    _action=URL('customers', 'customers_list', vars=form_vars),
                    _method='POST'
                )
                
                # Обработка формы редактирования
                if form_edit.process(formname='customer_edit_form', keepvalues=False).accepted:
                    session.flash = 'Клиент успешно обновлен'
                    redirect_vars = {}
                    if search_term:
                        redirect_vars['search'] = search_term
                    redirect(URL('customers', 'customers_list', vars=redirect_vars))
                else:
                    # Открываем панель если форма не обработана (первый показ) или есть ошибки
                    show_edit_panel = True
                
                # Настраиваем стили формы редактирования
                if form_edit and form_edit.element('input[type=submit]'):
                    form_edit.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
        except (ValueError, TypeError) as e:
            # Логируем ошибку для отладки
            import logging
            try:
                logging.error(f"Ошибка при редактировании клиента: {str(e)}")
            except:
                pass
    
    try:
        import customers_service
        
        # Менеджер видит только своих клиентов; остальные роли — всех
        manager_customer_ids = None
        if role_helpers.is_manager(auth) and auth.user:
            manager_customer_ids = role_helpers.get_manager_customer_ids(db, auth.user.id)
        if search_term:
            customers = customers_service.search_customers(db, search_term, customer_ids=manager_customer_ids)
        else:
            if manager_customer_ids is not None:
                customers = customers_service.get_customers_for_manager(db, auth.user.id, order_by='name')
            else:
                customers = customers_service.get_all_customers(db, order_by='name')
        
        # Хлебные крошки: Главная → Клиенты
        import breadcrumbs_helper
        breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
            ('Главная', URL('default', 'index')),
            ('Клиенты', None),
        ])
        return dict(
            customers=customers,
            search_term=search_term,
            form_customer=form_customer,
            form_edit=form_edit,
            show_edit_panel=show_edit_panel,
            edit_customer_id=edit_customer_id if edit_customer_id else None,
            breadcrumbs=breadcrumbs,
        )
    except Exception as e:
        import breadcrumbs_helper
        breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
            ('Главная', URL('default', 'index')),
            ('Клиенты', None),
        ])
        return dict(
            customers=[],
            search_term='',
            form_customer=form_customer,
            form_edit=None,
            show_edit_panel=False,
            edit_customer_id=None,
            breadcrumbs=breadcrumbs,
            error=str(e)
        )


def add_customer():
    """
    Добавление нового клиента (обработка формы)
    """
    import customers_service
    
    form = SQLFORM(db.customers, submit_button='Добавить')
    
    if form.process(formname='customer_form').accepted:
        # После успешного добавления перенаправляем на карточку клиента
        customer_id = form.vars.id
        session.flash = 'Клиент успешно добавлен'
        redirect(URL('customers', 'customer', args=[customer_id]))
    elif form.errors:
        session.flash = 'Ошибка при добавлении клиента: ' + ', '.join([str(v) for v in form.errors.values()])
        redirect(URL('default', 'index'))
    
    # Если форма не была отправлена, показываем форму
    return dict(form=form)


def check_phone_duplicate():
    """
    Проверка дубликата клиента по номеру телефона
    """
    import json
    from gluon.serializers import json as json_serializer
    
    phone = request.vars.get('phone', '').strip()
    customer_id = request.vars.get('customer_id', None)  # ID текущего редактируемого клиента (если редактирование)
    
    if not phone:
        return json_serializer({'exists': False, 'message': ''})
    
    # Нормализуем номер телефона (убираем все нецифровые символы кроме +)
    import re
    normalized_phone = re.sub(r'[^\d+]', '', phone)
    # Убираем +7 или 8 в начале, оставляем только цифры
    normalized_phone = re.sub(r'^\+?7?8?', '', normalized_phone)
    
    if not normalized_phone:
        return json_serializer({'exists': False, 'message': ''})
    
    try:
        import customers_service
        
        # Получаем всех клиентов
        customers = customers_service.get_all_customers(db)
        
        # Проверяем каждый клиент
        for customer in customers:
            # Пропускаем текущего редактируемого клиента
            if customer_id and str(customer.id) == str(customer_id):
                continue
            
            if customer.phone:
                # Нормализуем номер из базы
                customer_phone_normalized = re.sub(r'[^\d+]', '', customer.phone)
                customer_phone_normalized = re.sub(r'^\+?7?8?', '', customer_phone_normalized)
                
                # Сравниваем нормализованные номера
                if customer_phone_normalized == normalized_phone:
                    return json_serializer({
                        'exists': True,
                        'message': 'Клиент с таким номером телефона существует',
                        'customer_id': customer.id,
                        'customer_name': customer.full_name or customer.name
                    })
        
        return json_serializer({'exists': False, 'message': ''})
    except Exception as e:
        return json_serializer({'exists': False, 'message': '', 'error': str(e)})


def get_status_color(status_name):
    """
    Возвращает цвет для статуса
    """
    colors = {
        'Лид': 'primary',
        'Заявка': 'info',
        'Коммерческое предложение': 'warning',
        'Заказ': 'success',
        'Производство': 'danger'
    }
    return colors.get(status_name, 'secondary')
