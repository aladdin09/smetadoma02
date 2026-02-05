# -*- coding: utf-8 -*-
"""
Контроллер для работы с договорами
"""
from gluon.http import HTTP
import datetime
import traceback


@auth.requires_login()
def supply():
    """Договор на поставку"""
    specification_id = request.args(0)
    if not specification_id:
        session.flash = 'Не указан ID спецификации'
        redirect(URL('default', 'index'))
    
    try:
        specification_id = int(specification_id)
    except (ValueError, TypeError):
        session.flash = 'Неверный ID спецификации'
        redirect(URL('default', 'index'))
    
    try:
        # Получаем спецификацию
        specification = db(db.specifications.id == specification_id).select().first()
        if not specification:
            session.flash = 'Спецификация не найдена'
            redirect(URL('default', 'index'))
        
        # Получаем данные клиента
        customer = db(db.customers.id == specification.customer_id).select().first()
        if not customer:
            session.flash = 'Клиент не найден'
            redirect(URL('default', 'index'))
        
        # Получаем позиции спецификации
        specification_items = db(db.specification_items.specification_id == specification_id).select(
            db.specification_items.ALL,
            db.nomenclature_items.description,
            db.nomenclature_items.item_number,
            left=[
                db.nomenclature_items.on(db.specification_items.nomenclature_item_id == db.nomenclature_items.id)
            ],
            orderby=db.specification_items.id
        )
        
        # Получаем позиции для КП (Приложения) с группировкой по типам
        kp_items = db(db.specification_items.specification_id == specification_id).select(
            db.specification_items.ALL,
            db.nomenclature_items.description,
            db.nomenclature_item_types.name,
            left=[
                db.nomenclature_items.on(db.specification_items.nomenclature_item_id == db.nomenclature_items.id),
                db.nomenclature_item_types.on(db.nomenclature_items.item_type_id == db.nomenclature_item_types.id),
            ],
            orderby=db.specification_items.id
        )
        
        # Группируем позиции по типам для КП
        from collections import OrderedDict
        from decimal import Decimal
        kp_items_grouped = OrderedDict()
        kp_total_amount = Decimal('0')
        for row in kp_items:
            type_name = (row.nomenclature_item_types.name if row.nomenclature_item_types and row.nomenclature_item_types.name else '-') or '-'
            if type_name not in kp_items_grouped:
                kp_items_grouped[type_name] = []
            # Пересчитываем сумму для каждой позиции
            si = row.specification_items
            qty = Decimal(str(si.quantity or 0))
            price = Decimal(str(si.price or 0))
            row.recalc_total = float(qty * price)
            kp_total_amount += qty * price
            kp_items_grouped[type_name].append(row)
        kp_items_grouped = list(kp_items_grouped.items())
        
        # Формируем полное имя клиента в порядке: Фамилия Имя Отчество
        try:
            # Собираем ФИО из отдельных полей в правильном порядке
            name_parts = []
            # 1. Фамилия
            if hasattr(customer, 'last_name') and customer.last_name:
                name_parts.append(str(customer.last_name).strip())
            # 2. Имя (поле name в таблице)
            if hasattr(customer, 'name') and customer.name:
                name_parts.append(str(customer.name).strip())
            # 3. Отчество
            if hasattr(customer, 'middle_name') and customer.middle_name:
                name_parts.append(str(customer.middle_name).strip())
            
            if name_parts:
                customer_full_name = ' '.join(name_parts)
            elif hasattr(customer, 'full_name') and customer.full_name:
                customer_full_name = str(customer.full_name).strip()
            elif hasattr(customer, 'name') and customer.name:
                customer_full_name = str(customer.name).strip()
            else:
                customer_full_name = 'Не указано'
        except Exception as name_error:
            # В случае ошибки пробуем использовать готовые поля
            try:
                customer_full_name = getattr(customer, 'full_name', None) or getattr(customer, 'name', None) or 'Не указано'
                if customer_full_name:
                    customer_full_name = str(customer_full_name).strip()
            except:
                customer_full_name = 'Не указано'
        
        # Получаем текущую дату
        from datetime import date, datetime
        try:
            if hasattr(request, 'now') and request.now:
                if isinstance(request.now, datetime):
                    contract_date = request.now.date()
                elif isinstance(request.now, date):
                    contract_date = request.now
                else:
                    contract_date = date.today()
            else:
                contract_date = date.today()
        except:
            contract_date = date.today()
        
        return dict(
            specification=specification,
            customer=customer,
            customer_full_name=customer_full_name,
            specification_items=specification_items,
            contract_date=contract_date,
            kp_items_grouped=kp_items_grouped,
            kp_total_amount=float(kp_total_amount),
            kp_total_amount_formatted=("{:,.2f}".format(float(kp_total_amount))).replace(',', ' ')
        )
    except Exception as e:
        error_msg = str(e) + '\n' + traceback.format_exc()
        # Логируем ошибку для отладки
        try:
            import logging
            logging.error('Ошибка в contracts.supply: %s' % error_msg)
        except:
            pass
        session.flash = 'Ошибка при формировании договора: %s' % str(e)
        redirect(URL('default', 'index'))


@auth.requires_login()
def assembly():
    """Договор сборки"""
    specification_id = request.args(0)
    if not specification_id:
        session.flash = 'Не указан ID спецификации'
        redirect(URL('default', 'index'))
    
    try:
        specification_id = int(specification_id)
    except (ValueError, TypeError):
        session.flash = 'Неверный ID спецификации'
        redirect(URL('default', 'index'))
    
    try:
        # Получаем спецификацию
        specification = db(db.specifications.id == specification_id).select().first()
        if not specification:
            session.flash = 'Спецификация не найдена'
            redirect(URL('default', 'index'))
        
        # Получаем данные клиента
        customer = db(db.customers.id == specification.customer_id).select().first()
        if not customer:
            session.flash = 'Клиент не найден'
            redirect(URL('default', 'index'))
        
        # Получаем позиции спецификации
        specification_items = db(db.specification_items.specification_id == specification_id).select(
            db.specification_items.ALL,
            db.nomenclature_items.description,
            db.nomenclature_items.item_number,
            left=[
                db.nomenclature_items.on(db.specification_items.nomenclature_item_id == db.nomenclature_items.id)
            ],
            orderby=db.specification_items.id
        )
        
        # Формируем полное имя клиента в порядке: Фамилия Имя Отчество
        try:
            # Собираем ФИО из отдельных полей в правильном порядке
            name_parts = []
            # 1. Фамилия
            if hasattr(customer, 'last_name') and customer.last_name:
                name_parts.append(str(customer.last_name).strip())
            # 2. Имя (поле name в таблице)
            if hasattr(customer, 'name') and customer.name:
                name_parts.append(str(customer.name).strip())
            # 3. Отчество
            if hasattr(customer, 'middle_name') and customer.middle_name:
                name_parts.append(str(customer.middle_name).strip())
            
            if name_parts:
                customer_full_name = ' '.join(name_parts)
            elif hasattr(customer, 'full_name') and customer.full_name:
                customer_full_name = str(customer.full_name).strip()
            elif hasattr(customer, 'name') and customer.name:
                customer_full_name = str(customer.name).strip()
            else:
                customer_full_name = 'Не указано'
        except Exception as name_error:
            # В случае ошибки пробуем использовать готовые поля
            try:
                customer_full_name = getattr(customer, 'full_name', None) or getattr(customer, 'name', None) or 'Не указано'
                if customer_full_name:
                    customer_full_name = str(customer_full_name).strip()
            except:
                customer_full_name = 'Не указано'
        
        # Получаем текущую дату
        from datetime import date, datetime
        try:
            if hasattr(request, 'now') and request.now:
                if isinstance(request.now, datetime):
                    contract_date = request.now.date()
                elif isinstance(request.now, date):
                    contract_date = request.now
                else:
                    contract_date = date.today()
            else:
                contract_date = date.today()
        except:
            contract_date = date.today()
        
        return dict(
            specification=specification,
            customer=customer,
            customer_full_name=customer_full_name,
            specification_items=specification_items,
            contract_date=contract_date
        )
    except Exception as e:
        error_msg = str(e) + '\n' + traceback.format_exc()
        # Логируем ошибку для отладки
        try:
            import logging
            logging.error('Ошибка в contracts.assembly: %s' % error_msg)
        except:
            pass
        session.flash = 'Ошибка при формировании договора: %s' % str(e)
        redirect(URL('default', 'index'))
