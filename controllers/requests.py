# -*- coding: utf-8 -*-
"""
Контроллер для работы с заявками
"""


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


def view_request():
    """
    Карточка заявки
    """
    request_id = request.args(0) or redirect(URL('default', 'index'))
    
    try:
        import requests_service
        import request_items_service
        
        # Получаем заявку
        req = requests_service.get_request_by_id(db, request_id)
        if not req:
            session.flash = 'Заявка не найдена'
            redirect(URL('default', 'index'))
        
        # Получаем клиента
        import customers_service
        customer = customers_service.get_customer_by_id(db, req.customer_id)
        
        # Получаем статус
        import request_statuses_service
        status = request_statuses_service.get_status_by_id(db, req.status_id)
        
        # Получаем следующий шаг
        next_step = None
        if req.next_step_id:
            import next_steps_service
            next_step = next_steps_service.get_next_step_by_id(db, req.next_step_id)
        
        # Получаем позиции заявки
        request_items = request_items_service.get_all_request_items(db, request_id=request_id)
        
        # Получаем все статусы для выпадающего списка
        all_statuses = request_statuses_service.get_all_statuses(db, is_active=True, order_by='sort_order')
        
        # Получаем все следующие шаги для выпадающего списка
        import next_steps_service
        all_next_steps = next_steps_service.get_all_next_steps(db, is_active=True)
        
        # Получаем цвета для статусов
        status_colors = {}
        if status:
            status_colors[status.id] = get_status_color(status.name)
        
        return dict(
            request_obj=req,
            customer=customer,
            status=status,
            next_step=next_step,
            request_items=request_items,
            all_statuses=all_statuses,
            all_next_steps=all_next_steps,
            status_colors=status_colors
        )
    except Exception as e:
        session.flash = f'Ошибка: {str(e)}'
        redirect(URL('default', 'index'))


def add_request():
    """
    Добавление новой заявки для клиента
    """
    customer_id = request.args(0)
    if not customer_id:
        session.flash = 'Не указан ID клиента'
        redirect(URL('default', 'index'))
    
    try:
        import customers_service
        import requests_service
        import request_statuses_service
        
        # Проверяем существование клиента
        customer = customers_service.get_customer_by_id(db, customer_id)
        if not customer:
            session.flash = 'Клиент не найден'
            redirect(URL('default', 'index'))
        
        # Получаем первый статус по умолчанию (обычно "Лид" или первый активный)
        all_statuses = request_statuses_service.get_all_statuses(db, is_active=True, order_by='sort_order')
        if not all_statuses:
            session.flash = 'Нет доступных статусов. Создайте статусы в системе.'
            redirect(URL('customers', 'customer', args=[customer_id]))
        
        # Получаем первый статус
        first_status = all_statuses.first()
        if not first_status:
            session.flash = 'Не удалось получить статус по умолчанию'
            redirect(URL('customers', 'customer', args=[customer_id]))
        
        default_status_id = first_status.id
        
        # Создаем новую заявку через сервисный слой
        result = requests_service.create_request(
            db, 
            customer_id=customer_id,
            status_id=default_status_id,
            description='Новая заявка',
            total_amount=0
        )
        
        if result.get('success'):
            request_id = result.get('id')
            if request_id:
                session.flash = 'Заявка успешно создана'
                redirect(URL('requests', 'view_request', args=[request_id], vars={}))
            else:
                session.flash = 'Ошибка: не получен ID созданной заявки'
                redirect(URL('customers', 'customer', args=[customer_id]))
        else:
            error_msg = result.get('error', 'Неизвестная ошибка')
            session.flash = f'Ошибка при создании заявки: {error_msg}'
            redirect(URL('customers', 'customer', args=[customer_id]))
            
    except HTTP:
        # Пробрасываем HTTP исключения (редиректы) дальше
        raise
    except Exception as e:
        db.rollback()
        session.flash = f'Ошибка при создании заявки: {str(e)}'
        # Если customer_id доступен, редиректим на карточку клиента, иначе на index
        if 'customer_id' in locals():
            redirect(URL('customers', 'customer', args=[customer_id]))
        else:
            redirect(URL('default', 'index'))
