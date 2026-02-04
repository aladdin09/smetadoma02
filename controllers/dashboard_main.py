# -*- coding: utf-8 -*-
"""
Дашборд 1: главный (проекты по статусам, таблица, панель клиента).
"""


def index():
    """Редирект на главную (default/index)."""
    redirect(URL('default', 'index'))


def index_gentelella():
    """Дашборд — вариант с Gentelella (layout_gentelella, стили Gentelella)."""
    from dashboard_data import get_dashboard_data
    show_customer_panel = False
    form_customer = SQLFORM(
        db.customers,
        submit_button='Добавить',
        _id='customerForm',
        _name='customer_form'
    )
    if form_customer.process(formname='customer_form').accepted:
        session.flash = 'Клиент успешно добавлен'
        redirect(URL('customers', 'customer', args=[form_customer.vars.id]))
    elif form_customer.errors:
        show_customer_panel = True
    if request.vars.get('open_customer_panel') == '1':
        show_customer_panel = True
    data = get_dashboard_data(db, request, auth)
    form_customer.element('input[type=submit]')['_class'] = 'btn btn-success'
    data['form_customer'] = form_customer
    data['show_customer_panel'] = show_customer_panel
    data.setdefault('error', None)
    response.view = 'dashboard_main/index_gentelella.html'
    return data


def index_gentelella_bs5():
    """Дашборд — вариант Gentelella на Bootstrap 5.3 (layout_gentelella_bs5)."""
    from dashboard_data import get_dashboard_data
    show_customer_panel = False
    form_customer = SQLFORM(
        db.customers,
        submit_button='Добавить',
        _id='customerForm',
        _name='customer_form'
    )
    if form_customer.process(formname='customer_form').accepted:
        session.flash = 'Клиент успешно добавлен'
        redirect(URL('customers', 'customer', args=[form_customer.vars.id]))
    elif form_customer.errors:
        show_customer_panel = True
    if request.vars.get('open_customer_panel') == '1':
        show_customer_panel = True
    data = get_dashboard_data(db, request, auth)
    form_customer.element('input[type=submit]')['_class'] = 'btn btn-primary'
    data['form_customer'] = form_customer
    data['show_customer_panel'] = show_customer_panel
    data.setdefault('error', None)
    response.view = 'dashboard_main/index_gentelella_bs5.html'
    return data


def index_deskapp():
    """Дашборд — вариант с DeskApp (без локальных стилей, для сравнения)."""
    from dashboard_data import get_dashboard_data
    show_customer_panel = False
    form_customer = SQLFORM(
        db.customers,
        submit_button='Добавить',
        _id='customerForm',
        _name='customer_form'
    )
    if form_customer.process(formname='customer_form').accepted:
        session.flash = 'Клиент успешно добавлен'
        redirect(URL('customers', 'customer', args=[form_customer.vars.id]))
    elif form_customer.errors:
        show_customer_panel = True
    if request.vars.get('open_customer_panel') == '1':
        show_customer_panel = True
    data = get_dashboard_data(db, request, auth)
    form_customer.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
    data['form_customer'] = form_customer
    data['show_customer_panel'] = show_customer_panel
    data.setdefault('error', None)
    response.view = 'dashboard_main/index_deskapp.html'
    return data
