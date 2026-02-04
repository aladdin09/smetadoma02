# -*- coding: utf-8 -*-
"""
Контроллер для работы с заказами
"""


def view():
    """Карточка заказа"""
    order_id = request.args(0) or redirect(URL('default', 'index'))
    try:
        from gluon.http import HTTP
        import orders_service
        import customers_service
        order = orders_service.get_order_by_id(db, order_id)
        if not order:
            session.flash = 'Заказ не найден'
            redirect(URL('default', 'index'))
        customer = None
        if order.customer_id:
            customer = customers_service.get_customer_by_id(db, order.customer_id)
        project = None
        if order.project_id:
            import projects_service
            project = projects_service.get_project_by_id(db, order.project_id)
        specification = None
        if order.specification_id:
            import specifications_service
            specification = specifications_service.get_specification_by_id(db, order.specification_id)
        order_items = orders_service.get_order_items(db, order_id)
        # Хлебные крошки: Главная → Клиенты → Клиент [→ Проект] → Заказ
        import breadcrumbs_helper
        if customer:
            items = [
                ('Главная', URL('default', 'index')),
                ('Клиенты', URL('customers', 'customers_list')),
                (customer.name, URL('customers', 'customer', args=[customer.id])),
            ]
            if project:
                items.append((project.name or project.project_number or 'Проект', URL('projects', 'view', args=[project.id])))
            items.append((order.order_number or 'Заказ #%s' % order.id, None))
        else:
            items = [
                ('Главная', URL('default', 'index')),
                (order.order_number or 'Заказ #%s' % order.id, None),
            ]
        breadcrumbs = breadcrumbs_helper.make_breadcrumbs(items)
        return dict(
            order=order,
            customer=customer,
            project=project,
            specification=specification,
            order_items=order_items,
            breadcrumbs=breadcrumbs,
        )
    except HTTP:
        raise
    except Exception as e:
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('default', 'index'))
