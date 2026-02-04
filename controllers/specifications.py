# -*- coding: utf-8 -*-
"""
Контроллер для работы со спецификациями
"""
from gluon.http import HTTP
import role_helpers


def get_status_color(status_name):
    """Возвращает цвет для статуса"""
    colors = {
        'Лид': 'primary',
        'Спецификация': 'info',
        'Коммерческое предложение': 'warning',
        'Заказ': 'success',
        'Производство': 'danger'
    }
    return colors.get(status_name, 'secondary')


def view_specification():
    """Карточка спецификации"""
    specification_id = request.args(0) or redirect(URL('default', 'index'))
    try:
        import specifications_service
        import specification_items_service
        specification = specifications_service.get_specification_by_id(db, specification_id)
        if not specification:
            session.flash = 'Спецификация не найдена'
            redirect(URL('default', 'index'))
        # Менеджер видит только спецификации своих проектов/клиентов
        if role_helpers.is_manager(auth):
            if specification.project_id:
                if specification.project_id not in role_helpers.get_manager_project_ids(db, auth.user.id):
                    raise HTTP(403, 'Доступ запрещён: вы можете видеть только свои спецификации.')
            else:
                if specification.customer_id not in role_helpers.get_manager_customer_ids(db, auth.user.id):
                    raise HTTP(403, 'Доступ запрещён: вы можете видеть только свои спецификации.')
        import customers_service
        customer = customers_service.get_customer_by_id(db, specification.customer_id)
        import specification_statuses_service
        status = specification_statuses_service.get_status_by_id(db, specification.status_id)
        next_step = None
        if specification.next_step_id:
            import next_steps_service
            next_step = next_steps_service.get_next_step_by_id(db, specification.next_step_id)
        # Получаем позиции спецификации с JOIN к номенклатуре, частям дома и типам позиций
        specification_items = db(db.specification_items.specification_id == specification_id).select(
            db.specification_items.ALL,
            db.nomenclature_items.description,
            db.nomenclature_items.item_type_id,
            db.nomenclature_item_types.name,
            db.parts.name,
            left=[
                db.nomenclature_items.on(db.specification_items.nomenclature_item_id == db.nomenclature_items.id),
                db.nomenclature_item_types.on(db.nomenclature_items.item_type_id == db.nomenclature_item_types.id),
                db.parts.on(db.specification_items.part_id == db.parts.id),
            ],
            orderby=db.specification_items.id
        )
        all_statuses = specification_statuses_service.get_all_statuses(db, is_active=True, order_by='sort_order')
        import next_steps_service
        all_next_steps = next_steps_service.get_all_next_steps(db, is_active=True)
        status_colors = {}
        if status:
            status_colors[status.id] = get_status_color(status.name)
        # Получаем номенклатуру с типами через LEFT JOIN
        nomenclature_items = db(db.nomenclature_items.id > 0).select(
            db.nomenclature_items.ALL,
            db.nomenclature_item_types.name,
            left=db.nomenclature_item_types.on(db.nomenclature_items.item_type_id == db.nomenclature_item_types.id),
            orderby=db.nomenclature_items.item_number
        )
        # Получаем все активные типы номенклатуры для фильтра
        nomenclature_item_types = db(db.nomenclature_item_types.is_active == True).select(
            db.nomenclature_item_types.id,
            db.nomenclature_item_types.name,
            orderby=db.nomenclature_item_types.sort_order
        )
        # Хлебные крошки: Главная → Клиенты → Клиент [→ Проект] → Спецификация
        import breadcrumbs_helper
        project = None
        if specification.project_id:
            import projects_service
            project = projects_service.get_project_by_id(db, specification.project_id)
        if customer:
            items = [
                ('Главная', URL('default', 'index')),
                ('Клиенты', URL('customers', 'customers_list')),
                (customer.name, URL('customers', 'customer', args=[customer.id])),
            ]
            if project:
                items.append((project.name or project.project_number or 'Проект', URL('projects', 'view', args=[project.id])))
            items.append(('Спецификация #%s' % specification.id, None))
        else:
            items = [
                ('Главная', URL('default', 'index')),
                ('Спецификация #%s' % specification.id, None),
            ]
        breadcrumbs = breadcrumbs_helper.make_breadcrumbs(items)
        
        # Проверяем, существует ли КП для этой спецификации
        commercial_proposal = db(db.commercial_proposals.specification_id == specification_id).select().first()
        
        # Группировка позиций по типу номенклатуры (порядок по первому вхождению типа)
        from collections import OrderedDict
        specification_items_grouped = OrderedDict()
        for item in specification_items:
            type_name = (item.nomenclature_item_types.name if item.nomenclature_item_types and item.nomenclature_item_types.name else '-')
            if type_name not in specification_items_grouped:
                specification_items_grouped[type_name] = []
            specification_items_grouped[type_name].append(item)
        specification_items_grouped = list(specification_items_grouped.items())
        
        return dict(
            specification_obj=specification,
            customer=customer,
            project=project,
            status=status,
            next_step=next_step,
            specification_items=specification_items,
            specification_items_grouped=specification_items_grouped,
            all_statuses=all_statuses,
            all_next_steps=all_next_steps,
            status_colors=status_colors,
            nomenclature_items=nomenclature_items,
            nomenclature_item_types=nomenclature_item_types,
            breadcrumbs=breadcrumbs,
            commercial_proposal=commercial_proposal,
        )
    except Exception as e:
        session.flash = f'Ошибка: {str(e)}'
        redirect(URL('default', 'index'))


def add_specification():
    """Добавление новой спецификации для клиента"""
    customer_id = request.args(0)
    if not customer_id:
        session.flash = 'Не указан ID клиента'
        redirect(URL('default', 'index'))
    try:
        from gluon.http import HTTP
        import customers_service
        import specifications_service
        import specification_statuses_service
        customer = customers_service.get_customer_by_id(db, customer_id)
        if not customer:
            session.flash = 'Клиент не найден'
            redirect(URL('default', 'index'))
        # Менеджер может добавлять спецификации только своим клиентам
        if role_helpers.is_manager(auth) and int(customer_id) not in role_helpers.get_manager_customer_ids(db, auth.user.id):
            raise HTTP(403, 'Доступ запрещён: вы можете работать только со своими клиентами.')
        all_statuses = specification_statuses_service.get_all_statuses(db, is_active=True, order_by='sort_order')
        if not all_statuses:
            session.flash = 'Нет доступных статусов. Создайте статусы в системе.'
            redirect(URL('customers', 'customer', args=[customer_id]))
        first_status = all_statuses.first()
        if not first_status:
            session.flash = 'Не удалось получить статус по умолчанию'
            redirect(URL('customers', 'customer', args=[customer_id]))
        default_status_id = first_status.id
        result = specifications_service.create_specification(
            db,
            customer_id=customer_id,
            status_id=default_status_id,
            description='Новая спецификация',
            total_amount=0
        )
        if result.get('success'):
            specification_id = result.get('id')
            if specification_id:
                session.flash = 'Спецификация успешно создана'
                redirect(URL('specifications', 'view_specification', args=[specification_id], vars={}))
            else:
                session.flash = 'Ошибка: не получен ID созданной спецификации'
                redirect(URL('customers', 'customer', args=[customer_id]))
        else:
            session.flash = f'Ошибка при создании спецификации: {result.get("error", "Неизвестная ошибка")}'
            redirect(URL('customers', 'customer', args=[customer_id]))
    except HTTP:
        raise
    except Exception as e:
        db.rollback()
        session.flash = f'Ошибка при создании спецификации: {str(e)}'
        if 'customer_id' in locals():
            redirect(URL('customers', 'customer', args=[customer_id]))
        else:
            redirect(URL('default', 'index'))


def add_items_from_nomenclature():
    """Добавить в спецификацию позиции по выбранным позициям номенклатуры (POST: nomenclature_item_ids, specification_id в args)."""
    specification_id = request.args(0) or redirect(URL('default', 'index'))
    if request.env.request_method != 'POST':
        redirect(URL('specifications', 'view_specification', args=[specification_id]))
    try:
        import importlib
        import specification_items_service
        importlib.reload(specification_items_service)
        import specifications_service
        specification = specifications_service.get_specification_by_id(db, specification_id)
        if not specification:
            session.flash = 'Спецификация не найдена'
            redirect(URL('default', 'index'))
        nomenclature_item_ids = request.post_vars.get('nomenclature_item_ids')
        if nomenclature_item_ids is None:
            nomenclature_item_ids = []
        elif isinstance(nomenclature_item_ids, str):
            s = nomenclature_item_ids.strip()
            nomenclature_item_ids = [x.strip() for x in s.split(',') if x.strip()]
        elif not isinstance(nomenclature_item_ids, list):
            nomenclature_item_ids = [nomenclature_item_ids] if nomenclature_item_ids else []
        specification_id = int(specification_id)
        result = specification_items_service.create_specification_items_from_nomenclature(db, specification_id, nomenclature_item_ids)
        if result.get('success'):
            added = result.get('added', 0)
            session.flash = 'Добавлено позиций: %s' % added if added else 'Выберите позиции номенклатуры'
        else:
            session.flash = 'Ошибка при добавлении: %s' % (result.get('error') or 'неизвестная ошибка')
        redirect(URL('specifications', 'view_specification', args=[specification_id]))
    except HTTP:
        raise
    except Exception as e:
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('specifications', 'view_specification', args=[specification_id]))


def edit_item_quantity():
    """Редактировать количество позиции спецификации. args: [item_id]. POST: quantity. Поддерживает AJAX."""
    item_id = request.args(0) or redirect(URL('default', 'index'))
    is_ajax = request.env.http_x_requested_with == 'XMLHttpRequest' or request.env.content_type == 'application/json'
    
    try:
        import specification_items_service
        item = specification_items_service.get_specification_item_by_id(db, item_id)
        if not item:
            if request.env.request_method == 'POST' and is_ajax:
                response.headers['Content-Type'] = 'application/json'
                return response.json(dict(success=False, error='Позиция не найдена'))
            session.flash = 'Позиция не найдена'
            redirect(URL('default', 'index'))
        
        if request.env.request_method == 'POST':
            from decimal import Decimal
            quantity = request.post_vars.get('quantity')
            if quantity is None:
                if is_ajax:
                    response.headers['Content-Type'] = 'application/json'
                    return response.json(dict(success=False, error='Не указано количество'))
                session.flash = 'Не указано количество'
                redirect(URL('specifications', 'view_specification', args=[item.specification_id]))
            
            try:
                quantity = Decimal(str(quantity))
                if quantity <= 0:
                    raise ValueError('Количество должно быть больше нуля')
            except (ValueError, TypeError) as e:
                if is_ajax:
                    response.headers['Content-Type'] = 'application/json'
                    return response.json(dict(success=False, error='Некорректное значение количества'))
                session.flash = 'Некорректное значение количества'
                redirect(URL('specifications', 'view_specification', args=[item.specification_id]))
            
            # Обновляем quantity и пересчитываем total
            price = item.price or Decimal('0')
            total = quantity * price
            
            db(db.specification_items.id == item_id).update(
                quantity=quantity,
                total=total
            )
            db.commit()
            
            # Пересчитываем общую сумму спецификации
            total_sum = db(db.specification_items.specification_id == item.specification_id).select(
                db.specification_items.total.sum()
            ).first()[db.specification_items.total.sum()] or Decimal('0')
            
            db(db.specifications.id == item.specification_id).update(total_amount=total_sum)
            db.commit()
            
            if is_ajax:
                response.headers['Content-Type'] = 'application/json'
                return response.json(dict(success=True, quantity=float(quantity), total=float(total)))
            
            session.flash = 'Количество обновлено'
            redirect(URL('specifications', 'view_specification', args=[item.specification_id]))
        else:
            # GET запрос - редирект на просмотр спецификации
            redirect(URL('specifications', 'view_specification', args=[item.specification_id]))
    except HTTP:
        raise
    except Exception as e:
        if is_ajax:
            response.headers['Content-Type'] = 'application/json'
            return response.json(dict(success=False, error=str(e)))
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('default', 'index'))


def delete_item():
    """Удалить позицию спецификации. args: [item_id]. Редирект на карточку спецификации."""
    item_id = request.args(0) or redirect(URL('default', 'index'))
    try:
        import specification_items_service
        item = specification_items_service.get_specification_item_by_id(db, item_id)
        if not item:
            session.flash = 'Позиция не найдена'
            redirect(URL('default', 'index'))
        specification_id = item.specification_id
        result = specification_items_service.delete_specification_item(db, item_id)
        if result.get('success'):
            session.flash = 'Позиция удалена'
        else:
            session.flash = 'Ошибка при удалении: %s' % (result.get('error') or '')
        redirect(URL('specifications', 'view_specification', args=[specification_id]))
    except HTTP:
        raise
    except Exception as e:
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('default', 'index'))


def update_prices():
    """Обновить цены всех позиций спецификации из номенклатуры."""
    specification_id = request.args(0) or redirect(URL('default', 'index'))
    try:
        from decimal import Decimal
        import specifications_service
        
        # Проверяем существование спецификации
        specification = specifications_service.get_specification_by_id(db, specification_id)
        if not specification:
            session.flash = 'Спецификация не найдена'
            redirect(URL('default', 'index'))
        
        # Проверяем права доступа
        if not auth.user:
            raise HTTP(403, 'Требуется авторизация')
        
        # Получаем все позиции спецификации с номенклатурой
        items = db(
            (db.specification_items.specification_id == specification_id) &
            (db.specification_items.nomenclature_item_id != None)
        ).select(
            db.specification_items.ALL,
            db.nomenclature_items.total_cost,
            left=db.nomenclature_items.on(
                db.specification_items.nomenclature_item_id == db.nomenclature_items.id
            )
        )
        
        updated_count = 0
        for row in items:
            item = row.specification_items
            nom = row.nomenclature_items
            
            if nom and nom.total_cost is not None:
                # Обновляем цену и итог
                new_price = Decimal(str(nom.total_cost))
                new_total = new_price * Decimal(str(item.quantity or 0))
                
                db(db.specification_items.id == item.id).update(
                    price=new_price,
                    total=new_total
                )
                updated_count += 1
        
        if updated_count > 0:
            db.commit()
            
            # Пересчитываем общую сумму спецификации
            total_sum = db(db.specification_items.specification_id == specification_id).select(
                db.specification_items.total.sum()
            ).first()[db.specification_items.total.sum()] or Decimal('0')
            
            db(db.specifications.id == specification_id).update(total_amount=total_sum)
            db.commit()
            
            session.flash = 'Обновлено цен: %d. Общая сумма пересчитана.' % updated_count
        else:
            session.flash = 'Нет позиций с привязкой к номенклатуре для обновления'
        
        redirect(URL('specifications', 'view_specification', args=[specification_id]))
    except HTTP:
        raise
    except Exception as e:
        session.flash = 'Ошибка при обновлении цен: %s' % str(e)
        redirect(URL('specifications', 'view_specification', args=[specification_id]))


def _generate_proposal_pdf(proposal, specification, customer, proposal_items, save_to_file=False):
    """Генерация PDF файла коммерческого предложения. Возвращает BytesIO или путь к файлу."""
    import os
    from io import BytesIO
    
    try:
        # Пробуем использовать xhtml2pdf (pisa)
        from xhtml2pdf import pisa
        
        # Формируем HTML содержимое
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="author" content="Система управления спецификациями">
            <meta name="subject" content="Коммерческое предложение">
            <title>КП """ + str(proposal.proposal_number) + """</title>
            <style>
                @page {
                    size: A4;
                    margin: 2cm;
                    @top-center {
                        content: "КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ";
                        font-size: 10pt;
                        color: #666;
                    }
                }
                @media print {
                    body {
                        print-color-adjust: exact;
                        -webkit-print-color-adjust: exact;
                    }
                    .items-table th {
                        -webkit-print-color-adjust: exact;
                        print-color-adjust: exact;
                    }
                }
                body {
                    font-family: Arial, sans-serif;
                    font-size: 10pt;
                    color: #000;
                    margin: 0;
                    padding: 0;
                }
                h1 {
                    text-align: center;
                    color: #1f4788;
                    font-size: 18pt;
                    margin-bottom: 30px;
                    page-break-after: avoid;
                }
                .info-table {
                    width: 100%;
                    margin-bottom: 20px;
                    border-collapse: collapse;
                }
                .info-table td {
                    padding: 6px;
                    vertical-align: top;
                }
                .info-table td:first-child {
                    font-weight: bold;
                    width: 150px;
                }
                .items-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                    page-break-inside: avoid;
                }
                .items-table th {
                    background-color: #4472C4;
                    color: white;
                    padding: 10px;
                    text-align: left;
                    font-weight: bold;
                    border: 1px solid #000;
                    -webkit-print-color-adjust: exact;
                    print-color-adjust: exact;
                }
                .items-table td {
                    padding: 8px;
                    border: 1px solid #000;
                }
                .items-table tr:nth-child(even) td {
                    background-color: #F2F2F2;
                    -webkit-print-color-adjust: exact;
                    print-color-adjust: exact;
                }
                .items-table tr:last-child {
                    background-color: #e0e0e0 !important;
                    font-weight: bold;
                    -webkit-print-color-adjust: exact;
                    print-color-adjust: exact;
                }
                .text-right {
                    text-align: right;
                }
                .text-center {
                    text-align: center;
                }
                .notes {
                    margin-top: 20px;
                    page-break-inside: avoid;
                }
            </style>
        </head>
        <body>
            <h1>КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ</h1>
            
            <table class="info-table">
                <tr>
                    <td>Номер КП:</td>
                    <td>""" + (proposal.proposal_number or '-') + """</td>
                </tr>
                <tr>
                    <td>Дата:</td>
                    <td>""" + (proposal.proposal_date.strftime('%d.%m.%Y') if proposal.proposal_date else '-') + """</td>
                </tr>
                <tr>
                    <td>Клиент:</td>
                    <td>""" + (customer.full_name or customer.name or '-') + """</td>
                </tr>
                <tr>
                    <td>Телефон:</td>
                    <td>""" + (customer.phone or '-') + """</td>
                </tr>
                <tr>
                    <td>Email:</td>
                    <td>""" + (customer.email or '-') + """</td>
                </tr>
            </table>
            
            <table class="items-table">
                <thead>
                    <tr>
                        <th>№</th>
                        <th>Наименование</th>
                        <th class="text-center">Кол-во</th>
                        <th class="text-center">Ед.</th>
                        <th class="text-right">Цена</th>
                        <th class="text-right">Сумма</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Добавляем позиции
        if proposal_items:
            for idx, item in enumerate(proposal_items, 1):
                html_content += """
                    <tr>
                        <td>""" + str(idx) + """</td>
                        <td>""" + (item.item_name or '-').replace('<', '&lt;').replace('>', '&gt;') + """</td>
                        <td class="text-center">""" + str(item.quantity if item.quantity else '0') + """</td>
                        <td class="text-center">""" + (item.unit or 'шт') + """</td>
                        <td class="text-right">""" + f"{float(item.price or 0):,.2f}".replace(',', ' ') + """</td>
                        <td class="text-right">""" + f"{float(item.total or 0):,.2f}".replace(',', ' ') + """</td>
                    </tr>
                """
        
        # Итоговая строка
        html_content += """
                    <tr>
                        <td colspan="2"><strong>ИТОГО:</strong></td>
                        <td></td>
                        <td></td>
                        <td></td>
                        <td class="text-right"><strong>""" + f"{float(proposal.total_amount or 0):,.2f}".replace(',', ' ') + """</strong></td>
                    </tr>
                </tbody>
            </table>
        """
        
        # Примечания
        if proposal.description:
            html_content += """
            <div style="margin-top: 20px;">
                <strong>Примечания:</strong><br>
                """ + proposal.description.replace('\n', '<br>').replace('<', '&lt;').replace('>', '&gt;') + """
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        # Генерируем PDF
        buffer = BytesIO()
        result = pisa.CreatePDF(html_content, dest=buffer, encoding='UTF-8')
        
        if result.err:
            raise Exception('Ошибка при создании PDF: %s' % str(result.err))
        
        buffer.seek(0)
        
        if save_to_file:
            # Сохраняем в файл
            uploads_dir = os.path.join(request.folder, 'uploads', 'commercial_proposals')
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
            
            filename = 'KP-%s.pdf' % proposal.proposal_number.replace('/', '-').replace('\\', '-')
            filepath = os.path.join(uploads_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(buffer.read())
            
            # Возвращаем относительный путь
            return 'uploads/commercial_proposals/' + filename
        else:
            return buffer
            
    except ImportError:
        # Если xhtml2pdf не установлен, пробуем weasyprint
        try:
            from weasyprint import HTML
            
            # Используем тот же HTML контент
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {
                        size: A4;
                        margin: 2cm;
                    }
                    body {
                        font-family: Arial, sans-serif;
                        font-size: 10pt;
                    }
                    h1 {
                        text-align: center;
                        color: #1f4788;
                        font-size: 18pt;
                        margin-bottom: 30px;
                    }
                    .info-table {
                        width: 100%;
                        margin-bottom: 20px;
                    }
                    .info-table td {
                        padding: 6px;
                        vertical-align: top;
                    }
                    .info-table td:first-child {
                        font-weight: bold;
                        width: 150px;
                    }
                    .items-table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 20px;
                    }
                    .items-table th {
                        background-color: #4472C4;
                        color: white;
                        padding: 10px;
                        text-align: left;
                        font-weight: bold;
                    }
                    .items-table td {
                        padding: 8px;
                        border: 1px solid #000;
                    }
                    .items-table tr:nth-child(even) {
                        background-color: #F2F2F2;
                    }
                    .items-table tr:last-child {
                        background-color: #fff;
                        font-weight: bold;
                    }
                    .text-right {
                        text-align: right;
                    }
                    .text-center {
                        text-align: center;
                    }
                </style>
            </head>
            <body>
                <h1>КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ</h1>
                
                <table class="info-table">
                    <tr>
                        <td>Номер КП:</td>
                        <td>""" + (proposal.proposal_number or '-') + """</td>
                    </tr>
                    <tr>
                        <td>Дата:</td>
                        <td>""" + (proposal.proposal_date.strftime('%d.%m.%Y') if proposal.proposal_date else '-') + """</td>
                    </tr>
                    <tr>
                        <td>Клиент:</td>
                        <td>""" + (customer.full_name or customer.name or '-') + """</td>
                    </tr>
                    <tr>
                        <td>Телефон:</td>
                        <td>""" + (customer.phone or '-') + """</td>
                    </tr>
                    <tr>
                        <td>Email:</td>
                        <td>""" + (customer.email or '-') + """</td>
                    </tr>
                </table>
                
                <table class="items-table">
                    <thead>
                        <tr>
                            <th>№</th>
                            <th>Наименование</th>
                            <th class="text-center">Кол-во</th>
                            <th class="text-center">Ед.</th>
                            <th class="text-right">Цена</th>
                            <th class="text-right">Сумма</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            if proposal_items:
                for idx, item in enumerate(proposal_items, 1):
                    html_content += """
                        <tr>
                            <td>""" + str(idx) + """</td>
                            <td>""" + (item.item_name or '-').replace('<', '&lt;').replace('>', '&gt;') + """</td>
                            <td class="text-center">""" + str(item.quantity if item.quantity else '0') + """</td>
                            <td class="text-center">""" + (item.unit or 'шт') + """</td>
                            <td class="text-right">""" + f"{float(item.price or 0):,.2f}".replace(',', ' ') + """</td>
                            <td class="text-right">""" + f"{float(item.total or 0):,.2f}".replace(',', ' ') + """</td>
                        </tr>
                    """
            
            html_content += """
                        <tr>
                            <td colspan="2"><strong>ИТОГО:</strong></td>
                            <td></td>
                            <td></td>
                            <td></td>
                            <td class="text-right"><strong>""" + f"{float(proposal.total_amount or 0):,.2f}".replace(',', ' ') + """</strong></td>
                        </tr>
                    </tbody>
                </table>
            """
            
            if proposal.description:
                html_content += """
                <div style="margin-top: 20px;">
                    <strong>Примечания:</strong><br>
                    """ + proposal.description.replace('\n', '<br>').replace('<', '&lt;').replace('>', '&gt;') + """
                </div>
                """
            
            html_content += """
            </body>
            </html>
            """
            
            buffer = BytesIO()
            HTML(string=html_content).write_pdf(buffer)
            buffer.seek(0)
            
            if save_to_file:
                uploads_dir = os.path.join(request.folder, 'uploads', 'commercial_proposals')
                if not os.path.exists(uploads_dir):
                    os.makedirs(uploads_dir)
                
                filename = 'KP-%s.pdf' % proposal.proposal_number.replace('/', '-').replace('\\', '-')
                filepath = os.path.join(uploads_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(buffer.read())
                
                return 'uploads/commercial_proposals/' + filename
            else:
                return buffer
                
        except ImportError:
            raise Exception('Не установлена библиотека для генерации PDF. Установите одну из: pip install xhtml2pdf или pip install weasyprint')
    except Exception as e:
        raise Exception('Ошибка при генерации PDF: %s' % str(e))


def create_commercial_proposal():
    """Сформировать коммерческое предложение из спецификации."""
    specification_id = request.args(0) or redirect(URL('default', 'index'))
    try:
        from decimal import Decimal
        import specifications_service
        import datetime
        
        # Проверяем существование спецификации
        specification = specifications_service.get_specification_by_id(db, specification_id)
        if not specification:
            session.flash = 'Спецификация не найдена'
            redirect(URL('default', 'index'))
        
        # Проверяем права доступа
        if not auth.user:
            raise HTTP(403, 'Требуется авторизация')
        
        # Генерируем номер КП (формат: КП-YYYYMMDD-XXX)
        today = datetime.date.today()
        date_prefix = today.strftime('%Y%m%d')
        
        # Ищем последний КП с таким префиксом
        last_proposal = db(
            db.commercial_proposals.proposal_number.like('КП-%s-%%' % date_prefix)
        ).select(
            db.commercial_proposals.proposal_number,
            orderby=~db.commercial_proposals.proposal_number,
            limitby=(0, 1)
        ).first()
        
        if last_proposal:
            # Извлекаем номер из последнего КП
            try:
                last_num = int(last_proposal.proposal_number.split('-')[-1])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1
        
        proposal_number = 'КП-%s-%03d' % (date_prefix, new_num)
        
        # Проверяем, не существует ли уже КП для этой спецификации
        existing_proposal = db(db.commercial_proposals.specification_id == specification_id).select().first()
        if existing_proposal:
            session.flash = 'Для этой спецификации уже существует КП: %s' % existing_proposal.proposal_number
            redirect(URL('specifications', 'view_specification', args=[specification_id]))
        
        # Получаем все позиции спецификации с типом номенклатуры
        spec_items = db(db.specification_items.specification_id == specification_id).select(
            db.specification_items.ALL,
            db.nomenclature_item_types.name,
            left=[
                db.nomenclature_items.on(db.specification_items.nomenclature_item_id == db.nomenclature_items.id),
                db.nomenclature_item_types.on(db.nomenclature_items.item_type_id == db.nomenclature_item_types.id),
            ],
            orderby=db.specification_items.id
        )
        
        if not spec_items:
            session.flash = 'В спецификации нет позиций для формирования КП'
            redirect(URL('specifications', 'view_specification', args=[specification_id]))
        
        # Создаем КП
        proposal_id = db.commercial_proposals.insert(
            specification_id=specification_id,
            customer_id=specification.customer_id,
            proposal_number=proposal_number,
            proposal_date=today,
            total_amount=specification.total_amount or Decimal('0'),
            description='Коммерческое предложение по спецификации #%s' % specification_id,
            status='draft'
        )
        db.commit()
        
        # Копируем позиции из спецификации в КП (с типом номенклатуры)
        total_sum = Decimal('0')
        for row in spec_items:
            item = row.specification_items
            item_type_name = (row.nomenclature_item_types.name if row.nomenclature_item_types and row.nomenclature_item_types.name else '') or ''
            item_total = Decimal(str(item.quantity or 0)) * Decimal(str(item.price or 0))
            total_sum += item_total
            
            db.commercial_proposal_items.insert(
                proposal_id=proposal_id,
                item_type_name=item_type_name,
                item_name=item.item_name,
                quantity=item.quantity,
                unit=item.unit,
                price=item.price,
                total=item_total,
                description=item.description
            )
        
        # Обновляем общую сумму КП
        db(db.commercial_proposals.id == proposal_id).update(total_amount=total_sum)
        db.commit()
        
        # Получаем данные для генерации PDF
        proposal = db.commercial_proposals(proposal_id)
        customer = db.customers(proposal.customer_id)
        proposal_items = db(db.commercial_proposal_items.proposal_id == proposal_id).select(
            orderby=db.commercial_proposal_items.id
        )
        
        # Генерируем и сохраняем PDF файл
        try:
            pdf_path = _generate_proposal_pdf(proposal, specification, customer, proposal_items, save_to_file=True)
            db(db.commercial_proposals.id == proposal_id).update(pdf_path=pdf_path)
            db.commit()
        except Exception as pdf_error:
            # Если не удалось создать PDF, продолжаем без него
            import logging
            try:
                logging.warning('Не удалось создать PDF для КП %s: %s' % (proposal_number, str(pdf_error)))
            except:
                pass
        
        session.flash = 'Коммерческое предложение %s успешно создано' % proposal_number
        redirect(URL('specifications', 'view_specification', args=[specification_id]))
    except HTTP:
        raise
    except Exception as e:
        session.flash = 'Ошибка при создании КП: %s' % str(e)
        redirect(URL('specifications', 'view_specification', args=[specification_id]))


def view_commercial_proposal_page():
    """Открыть КП в виде страницы А4: актуальные позиции из спецификации (количества и цены пересчитываются), дерево по типам."""
    proposal_id = request.args(0) or redirect(URL('default', 'index'))
    try:
        proposal = db.commercial_proposals(proposal_id)
        if not proposal:
            session.flash = 'Коммерческое предложение не найдено'
            redirect(URL('default', 'index'))
        customer = db.customers(proposal.customer_id)
        specification_id = proposal.specification_id
        # Берём актуальные позиции из спецификации (пересчёт количества, цены, суммы)
        specification_items = db(db.specification_items.specification_id == specification_id).select(
            db.specification_items.ALL,
            db.nomenclature_items.description,
            db.nomenclature_item_types.name,
            left=[
                db.nomenclature_items.on(db.specification_items.nomenclature_item_id == db.nomenclature_items.id),
                db.nomenclature_item_types.on(db.nomenclature_items.item_type_id == db.nomenclature_item_types.id),
            ],
            orderby=db.specification_items.id
        )
        # Пересчёт total по каждой позиции и общей суммы
        from decimal import Decimal
        total_amount = Decimal('0')
        for row in specification_items:
            si = row.specification_items
            qty = Decimal(str(si.quantity or 0))
            price = Decimal(str(si.price or 0))
            row.recalc_total = float(qty * price)
            total_amount += qty * price
        # Группировка по типу позиции (порядок по первому вхождению)
        from collections import OrderedDict
        grouped = OrderedDict()
        for row in specification_items:
            type_name = (row.nomenclature_item_types.name if row.nomenclature_item_types and row.nomenclature_item_types.name else '-') or '-'
            if type_name not in grouped:
                grouped[type_name] = []
            grouped[type_name].append(row)
        proposal_items_grouped = list(grouped.items())
        response.view = 'specifications/view_commercial_proposal_page.html'
        return dict(
            proposal=proposal,
            customer=customer,
            proposal_items_grouped=proposal_items_grouped,
            total_amount=float(total_amount),
            total_amount_formatted=f"{float(total_amount):,.2f}".replace(',', ' '),
        )
    except HTTP:
        raise
    except Exception as e:
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('default', 'index'))


def view_commercial_proposal_pdf():
    """Просмотр PDF файла коммерческого предложения."""
    proposal_id = request.args(0) or redirect(URL('default', 'index'))
    try:
        # Получаем КП
        proposal = db.commercial_proposals(proposal_id)
        if not proposal:
            session.flash = 'Коммерческое предложение не найдено'
            redirect(URL('default', 'index'))
        
        # Если PDF файл уже существует, возвращаем его
        if proposal.pdf_path:
            import os
            pdf_file_path = os.path.join(request.folder, proposal.pdf_path)
            if os.path.exists(pdf_file_path):
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = 'inline; filename="KP-%s.pdf"' % proposal.proposal_number
                with open(pdf_file_path, 'rb') as f:
                    return f.read()
        
        # Если PDF файла нет, генерируем его на лету
        specification = db.specifications(proposal.specification_id)
        customer = db.customers(proposal.customer_id)
        proposal_items = db(db.commercial_proposal_items.proposal_id == proposal_id).select(
            orderby=db.commercial_proposal_items.id
        )
        
        buffer = _generate_proposal_pdf(proposal, specification, customer, proposal_items, save_to_file=False)
        
        # Возвращаем PDF файл с правильными заголовками для печати
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename="KP-%s.pdf"' % proposal.proposal_number.replace('/', '-')
        response.headers['Content-Description'] = 'Коммерческое предложение %s' % proposal.proposal_number
        return buffer.read()
            
    except HTTP:
        raise
    except Exception as e:
        session.flash = 'Ошибка при генерации PDF: %s' % str(e)
        redirect(URL('specifications', 'view_specification', args=[proposal.specification_id if 'proposal' in locals() and proposal else 0]))


# ID статусов спецификации для кнопок на карточке проекта
SPECIFICATION_STATUS_ROP_ID = 2            # На согласовании у РОПа
SPECIFICATION_STATUS_ISPRAVLENIE_ID = 3    # Исправление
SPECIFICATION_STATUS_KP_SOGLASOVANO_ID = 4 # КП согласовано
SPECIFICATION_STATUS_KP_OTPRAVLENO_ID = 5  # КП отправлено
SPECIFICATION_STATUS_ZAKAZ_ID = 6          # Заказ


# ID статусов проекта при действиях со спецификацией
PROJECT_STATUS_KP_U_ROPA_ID = 3       # КП у РОПа — при «На согласование РОПу»
PROJECT_STATUS_ISPRAVLENIE_KP_ID = 4  # Исправление КП — при «Исправить»
PROJECT_STATUS_KP_SOGLASOVANO_ID = 5 # КП согласовано — при «Согласовать КП»
PROJECT_STATUS_KP_OTPRAVLENO_ID = 6  # КП отправлено — при «КП отправлено»
PROJECT_STATUS_ZAKAZ_OFORMLEN_ID = 7 # Заказ оформлен — при «Создать заказ»


def set_status_rop():
    """Перевести спецификацию в статус «На согласовании у РОПа» (id=2), проект — в «КП у РОПа» (id=3). args: [specification_id]."""
    specification_id = request.args(0) or redirect(URL('default', 'index'))
    try:
        import specifications_service
        specification = specifications_service.get_specification_by_id(db, specification_id)
        if not specification:
            session.flash = 'Спецификация не найдена'
            redirect(URL('default', 'index'))
        project_id = specification.project_id
        result = specifications_service.update_specification_status(db, specification_id, SPECIFICATION_STATUS_ROP_ID)
        if result.get('success'):
            session.flash = 'Статус спецификации изменён на «На согласовании у РОПа»'
            if project_id:
                import projects_service
                upd = projects_service.update_project_status(db, int(project_id), PROJECT_STATUS_KP_U_ROPA_ID)
                if not upd.get('success'):
                    session.flash += '. Статус проекта не обновлён: %s' % (upd.get('error') or '')
        else:
            session.flash = 'Ошибка: %s' % (result.get('error') or '')
        if project_id:
            redirect(URL('projects', 'view', args=[project_id]))
        else:
            redirect(URL('specifications', 'view_specification', args=[specification_id]))
    except HTTP:
        raise
    except Exception as e:
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('default', 'index'))


def set_status_ispravlenie():
    """Перевести спецификацию в статус «Исправление» (id=3), проект — в «Исправление КП» (id=4). args: [specification_id]."""
    specification_id = request.args(0) or redirect(URL('default', 'index'))
    try:
        import specifications_service
        specification = specifications_service.get_specification_by_id(db, specification_id)
        if not specification:
            session.flash = 'Спецификация не найдена'
            redirect(URL('default', 'index'))
        project_id = specification.project_id
        result = specifications_service.update_specification_status(db, specification_id, SPECIFICATION_STATUS_ISPRAVLENIE_ID)
        if result.get('success'):
            session.flash = 'Статус спецификации изменён на «Исправление»'
            if project_id:
                import projects_service
                upd = projects_service.update_project_status(db, int(project_id), PROJECT_STATUS_ISPRAVLENIE_KP_ID)
                if not upd.get('success'):
                    session.flash += '. Статус проекта не обновлён: %s' % (upd.get('error') or '')
        else:
            session.flash = 'Ошибка: %s' % (result.get('error') or '')
        if project_id:
            redirect(URL('projects', 'view', args=[project_id]))
        else:
            redirect(URL('specifications', 'view_specification', args=[specification_id]))
    except HTTP:
        raise
    except Exception as e:
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('default', 'index'))


def set_status_kp_soglasovano():
    """Перевести спецификацию в статус «КП согласовано» (id=4), проект — в «КП согласовано» (id=5). args: [specification_id]."""
    specification_id = request.args(0) or redirect(URL('default', 'index'))
    try:
        import specifications_service
        specification = specifications_service.get_specification_by_id(db, specification_id)
        if not specification:
            session.flash = 'Спецификация не найдена'
            redirect(URL('default', 'index'))
        project_id = specification.project_id
        result = specifications_service.update_specification_status(db, specification_id, SPECIFICATION_STATUS_KP_SOGLASOVANO_ID)
        if result.get('success'):
            session.flash = 'Статус спецификации изменён на «КП согласовано»'
            if project_id:
                import projects_service
                upd = projects_service.update_project_status(db, int(project_id), PROJECT_STATUS_KP_SOGLASOVANO_ID)
                if not upd.get('success'):
                    session.flash += '. Статус проекта не обновлён: %s' % (upd.get('error') or '')
        else:
            session.flash = 'Ошибка: %s' % (result.get('error') or '')
        if project_id:
            redirect(URL('projects', 'view', args=[project_id]))
        else:
            redirect(URL('specifications', 'view_specification', args=[specification_id]))
    except HTTP:
        raise
    except Exception as e:
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('default', 'index'))


def set_status_kp_otpravleno():
    """Перевести спецификацию в статус «КП отправлено» (id=5), проект — в «КП отправлено» (id=6). args: [specification_id]."""
    specification_id = request.args(0) or redirect(URL('default', 'index'))
    try:
        import specifications_service
        specification = specifications_service.get_specification_by_id(db, specification_id)
        if not specification:
            session.flash = 'Спецификация не найдена'
            redirect(URL('default', 'index'))
        project_id = specification.project_id
        result = specifications_service.update_specification_status(db, specification_id, SPECIFICATION_STATUS_KP_OTPRAVLENO_ID)
        if result.get('success'):
            session.flash = 'Статус спецификации изменён на «КП отправлено»'
            if project_id:
                import projects_service
                upd = projects_service.update_project_status(db, int(project_id), PROJECT_STATUS_KP_OTPRAVLENO_ID)
                if not upd.get('success'):
                    session.flash += '. Статус проекта не обновлён: %s' % (upd.get('error') or '')
        else:
            session.flash = 'Ошибка: %s' % (result.get('error') or '')
        if project_id:
            redirect(URL('projects', 'view', args=[project_id]))
        else:
            redirect(URL('specifications', 'view_specification', args=[specification_id]))
    except HTTP:
        raise
    except Exception as e:
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('default', 'index'))


def set_status_chernovik():
    """Перевести спецификацию в статус «Черновик». args: [specification_id]."""
    specification_id = request.args(0) or redirect(URL('default', 'index'))
    try:
        import specifications_service
        specification = specifications_service.get_specification_by_id(db, specification_id)
        if not specification:
            session.flash = 'Спецификация не найдена'
            redirect(URL('default', 'index'))
        project_id = specification.project_id
        chernovik = db(db.specification_statuses.name == 'Черновик').select().first()
        if not chernovik:
            session.flash = 'Статус «Черновик» не найден в справочнике'
            if project_id:
                redirect(URL('projects', 'view', args=[project_id]))
            else:
                redirect(URL('specifications', 'view_specification', args=[specification_id]))
        result = specifications_service.update_specification_status(db, specification_id, chernovik.id)
        if result.get('success'):
            session.flash = 'Статус спецификации изменён на «Черновик»'
        else:
            session.flash = 'Ошибка: %s' % (result.get('error') or '')
        if project_id:
            redirect(URL('projects', 'view', args=[project_id]))
        else:
            redirect(URL('specifications', 'view_specification', args=[specification_id]))
    except HTTP:
        raise
    except Exception as e:
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('default', 'index'))


def set_status_zakaz():
    """Создать заказ из спецификации (копирование в orders и order_items), перевести спецификацию в статус «Заказ» (id=6). args: [specification_id]."""
    specification_id = request.args(0) or redirect(URL('default', 'index'))
    try:
        import specifications_service
        import orders_service
        specification = specifications_service.get_specification_by_id(db, specification_id)
        if not specification:
            session.flash = 'Спецификация не найдена'
            redirect(URL('default', 'index'))
        project_id = specification.project_id
        result = orders_service.create_order_from_specification(db, specification_id)
        if not result.get('success'):
            session.flash = 'Ошибка при создании заказа: %s' % (result.get('error') or '')
            if project_id:
                redirect(URL('projects', 'view', args=[project_id]))
            else:
                redirect(URL('specifications', 'view_specification', args=[specification_id]))
        order_id = result.get('id')
        specifications_service.update_specification_status(db, specification_id, SPECIFICATION_STATUS_ZAKAZ_ID)
        if project_id:
            import projects_service
            projects_service.update_project_status(db, int(project_id), PROJECT_STATUS_ZAKAZ_OFORMLEN_ID)
        session.flash = 'Заказ создан из спецификации'
        redirect(URL('orders', 'view', args=[order_id]))
    except HTTP:
        raise
    except Exception as e:
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('default', 'index'))
