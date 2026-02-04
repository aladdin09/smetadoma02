# -*- coding: utf-8 -*-
"""
Дашборд 2: аналитика (те же данные, другой макет для выбора).
"""


def index():
    """Дашборд — вариант «Аналитика»."""
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
    response.view = 'dashboard_analytics/index.html'
    return data
