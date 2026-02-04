# -*- coding: utf-8 -*-
"""
Контроллер для работы с проектами
"""
import role_helpers


def view():
    """
    Карточка проекта
    """
    raw_id = request.args(0)
    if not raw_id:
        session.flash = 'Не указан ID проекта'
        redirect(URL('default', 'index'))
    try:
        project_id = int(raw_id)
    except (TypeError, ValueError):
        session.flash = 'Неверный ID проекта'
        redirect(URL('default', 'index'))
    
    try:
        from gluon.http import HTTP
        import breadcrumbs_helper
        import projects_service
        import customers_service
        import project_statuses_service
        
        # Получаем проект (явный запрос по id)
        try:
            project = db(db.projects.id == project_id).select().first()
        except Exception as db_err:
            session.flash = 'Ошибка БД при загрузке проекта: %s' % str(db_err)
            redirect(URL('default', 'index'))
        if not project:
            session.flash = 'Проект с ID %s не найден в базе.' % project_id
            redirect(URL('default', 'index'))
        # Менеджер видит только проекты, где он ответственный
        if role_helpers.is_manager(auth) and project.manager_id != auth.user.id:
            from gluon.http import HTTP
            raise HTTP(403, 'Доступ запрещён: вы можете видеть только свои проекты.')
        # Получаем клиента
        customer = None
        if project.customer_id:
            customer = customers_service.get_customer_by_id(db, project.customer_id)
        
        # Получаем статус проекта
        status = None
        if project.status_id:
            status = project_statuses_service.get_status_by_id(db, project.status_id)
        
        # Получаем спецификации проекта
        specifications = db(db.specifications.project_id == project_id).select(
            db.specifications.ALL,
            db.specification_statuses.ALL,
            left=db.specification_statuses.on(db.specifications.status_id == db.specification_statuses.id),
            orderby=~db.specifications.created_on
        )
        
        # Получаем заказы проекта
        orders = db(db.orders.project_id == project_id).select(
            db.orders.ALL,
            orderby=~db.orders.created_on
        )
        
        # Получаем цвета статусов для отображения
        status_colors = {}
        if status:
            status_colors[status.id] = get_status_color(status.name)
        
        # Получаем цвета статусов спецификаций
        specification_status_colors = {}
        import specification_statuses_service
        all_specification_statuses = specification_statuses_service.get_all_statuses(db, is_active=True, order_by='sort_order')
        for comp_status in all_specification_statuses:
            specification_status_colors[comp_status.id] = get_specification_status_color(comp_status.name)
        
        # Форма для добавления спецификации (для sidebar)
        form_specification = SQLFORM.factory(
            Field('description', 'text', label='Описание спецификации'),
            Field('execution_time', 'integer', label='Время на выполнение (дни)'),
            Field('deadline', 'datetime', label='Дедлайн'),
            Field('total_amount', 'decimal(10,2)', default=0, label='Общая сумма'),
            submit_button='Добавить',
            _id='specificationForm',
            _name='specification_form',
            _action=URL('projects', 'view', args=[project_id]),
            _method='POST'
        )
        
        # Обработка формы добавления спецификации
        show_specification_panel = False
        if form_specification.process(formname='specification_form', keepvalues=False).accepted:
            description = str(form_specification.vars.description) if form_specification.vars.description else None
            try:
                execution_time = int(form_specification.vars.execution_time) if form_specification.vars.execution_time else None
            except:
                execution_time = None
            deadline = form_specification.vars.deadline if form_specification.vars.deadline else None
            try:
                total_amount = float(form_specification.vars.total_amount) if form_specification.vars.total_amount else 0
            except:
                total_amount = 0
            if not all_specification_statuses:
                session.flash = 'Нет доступных статусов спецификаций. Создайте статусы в системе.'
                show_specification_panel = True
            else:
                first_status = all_specification_statuses.first()
                default_status_id = first_status.id if first_status else None
                if not default_status_id:
                    session.flash = 'Не удалось получить статус по умолчанию'
                    show_specification_panel = True
                else:
                    customer_id_for_specification = project.customer_id if project.customer_id else None
                    if not customer_id_for_specification:
                        session.flash = 'У проекта не указан клиент. Невозможно создать спецификацию.'
                        show_specification_panel = True
                    else:
                        import specifications_service
                        import projects_service
                        import project_statuses_service
                        result = specifications_service.create_specification(
                            db=db,
                            customer_id=customer_id_for_specification,
                            project_id=int(project_id),
                            status_id=default_status_id,
                            description=description or 'Новая спецификация',
                            execution_time=execution_time,
                            deadline=deadline,
                            total_amount=total_amount
                        )
                        if result.get('success'):
                            # Первая спецификация у проекта — переводим статус проекта в «Комплектация»
                            pid = int(project_id)
                            count = db(db.specifications.project_id == pid).count()
                            if count == 1:
                                status_row = project_statuses_service.get_status_by_name(db, 'Комплектация')
                                status_complectation_id = status_row.id if status_row else 2  # запас: id=2
                                upd = projects_service.update_project_status(db, pid, status_complectation_id)
                                if not upd.get('success'):
                                    session.flash = 'Спецификация добавлена, но статус проекта не обновлён: %s' % upd.get('error', '')
                                else:
                                    session.flash = 'Спецификация успешно добавлена'
                            else:
                                session.flash = 'Спецификация успешно добавлена'
                            redirect(URL('projects', 'view', args=[project_id], vars={}))
                        else:
                            session.flash = f'Ошибка при создании спецификации: {result.get("error", "Неизвестная ошибка")}'
                            show_specification_panel = True
        elif form_specification.errors:
            show_specification_panel = True
        if form_specification.element('input[type=submit]'):
            form_specification.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'

        # Панель редактирования спецификации (edit_spec_id в request.vars)
        show_edit_specification_panel = False
        form_edit_specification = None
        edit_spec_id = request.vars.get('edit_spec_id')
        if edit_spec_id:
            try:
                edit_spec_id = int(edit_spec_id)
            except (TypeError, ValueError):
                edit_spec_id = None
        if edit_spec_id:
            spec_record = db((db.specifications.id == edit_spec_id) & (db.specifications.project_id == project_id)).select().first()
            if spec_record:
                form_edit_specification = SQLFORM(
                    db.specifications,
                    spec_record.id,
                    fields=['description', 'execution_time', 'deadline', 'total_amount'],
                    showid=False,
                    _id='editSpecificationForm',
                    _name='edit_specification_form',
                    _action=URL('projects', 'view', args=[project_id], vars=dict(edit_spec_id=edit_spec_id)),
                    _method='POST'
                )
                if form_edit_specification.process(formname='edit_specification_form', keepvalues=False).accepted:
                    session.flash = 'Спецификация обновлена'
                    redirect(URL('projects', 'view', args=[project_id], vars={}))
                elif form_edit_specification.errors:
                    show_edit_specification_panel = True
                else:
                    show_edit_specification_panel = True
                if form_edit_specification.element('input[type=submit]'):
                    form_edit_specification.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'

        # ID статусов спецификации для кнопок
        specification_status_rop_id = 2
        specification_status_ispravlenie_id = 3
        specification_status_kp_soglasovano_id = 4  # КП согласовано
        specification_status_kp_otpravleno_id = 5    # КП отправлено
        specification_status_zakaz_id = 6            # Заказ
        # Если хоть у одной спецификации статус не «Черновик», кнопки КП и На согласование РОПу скрываем у всех
        has_non_chernovik = any(comp.specification_statuses and getattr(comp.specification_statuses, 'name', '') != 'Черновик' for comp in specifications) if specifications else False
        # Хлебные крошки (из modules, чтобы не конфликтовать с models)
        if customer:
            breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
                ('Главная', URL('default', 'index')),
                ('Клиенты', URL('customers', 'customers_list')),
                (customer.name, URL('customers', 'customer', args=[customer.id])),
                (project.name or project.project_number or 'Проект', None),
            ])
        else:
            breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
                ('Главная', URL('default', 'index')),
                (project.name or project.project_number or 'Проект', None),
            ])
        return dict(
            project=project,
            customer=customer,
            status=status,
            specifications=specifications,
            orders=orders,
            status_colors=status_colors,
            specification_status_colors=specification_status_colors,
            form_specification=form_specification,
            show_specification_panel=show_specification_panel,
            form_edit_specification=form_edit_specification,
            show_edit_specification_panel=show_edit_specification_panel,
            specification_status_rop_id=specification_status_rop_id,
            specification_status_ispravlenie_id=specification_status_ispravlenie_id,
            specification_status_kp_soglasovano_id=specification_status_kp_soglasovano_id,
            specification_status_kp_otpravleno_id=specification_status_kp_otpravleno_id,
            specification_status_zakaz_id=specification_status_zakaz_id,
            has_non_chernovik=has_non_chernovik,
            breadcrumbs=breadcrumbs,
        )
    except HTTP:
        # Пробрасываем HTTP исключения (редиректы) дальше
        raise
    except Exception as e:
        session.flash = f'Ошибка: {str(e)}'
        redirect(URL('default', 'index'))


def delete():
    """Удаление проекта. args: [project_id]. vars: customer_id — для редиректа на карточку клиента."""
    project_id = request.args(0)
    if not project_id:
        session.flash = 'Не указан ID проекта'
        redirect(URL('default', 'index'))
    try:
        project_id = int(project_id)
    except (TypeError, ValueError):
        session.flash = 'Неверный ID проекта'
        redirect(URL('default', 'index'))
    import projects_service
    result = projects_service.delete_project(db, project_id)
    if result.get('success'):
        session.flash = 'Проект успешно удалён'
    else:
        session.flash = result.get('error', 'Ошибка при удалении проекта')
    customer_id = request.vars.get('customer_id')
    if customer_id:
        redirect(URL('customers', 'customer', args=[customer_id]))
    redirect(URL('default', 'index'))


def get_status_color(status_name):
    """
    Возвращает цвет для статуса проекта
    """
    colors = {
        'Лид': 'primary',
        'Заявка': 'info',
        'КП отправлено': 'warning',
        'КП согласовано': 'warning',
        'Заказ оформлен': 'success',
        'В производстве': 'danger',
        'Доставка': 'info',
        'Монтаж': 'primary',
        'Акт подписан': 'success',
        'Закрыт': 'secondary'
    }
    return colors.get(status_name, 'secondary')


def get_specification_status_color(status_name):
    """Возвращает цвет для статуса спецификации"""
    colors = {
        'Лид': 'primary',
        'Спецификация': 'info',
        'Коммерческое предложение': 'warning',
        'Заказ': 'success',
        'Производство': 'danger'
    }
    return colors.get(status_name, 'secondary')
