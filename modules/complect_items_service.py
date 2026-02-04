# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей complect_items (Позиции комплекта)
"""


def create_complect_item(db, complect_id, item_name, quantity=1, unit='шт',
                       price=0, description=None, nomenclature_item_id=None):
    """Создать новую позицию комплекта (опционально со ссылкой на номенклатуру)"""
    try:
        total = float(quantity) * float(price)
        item_id = db.complect_items.insert(
            complect_id=complect_id,
            nomenclature_item_id=nomenclature_item_id,
            item_name=item_name,
            quantity=quantity,
            unit=unit,
            price=price,
            total=total,
            description=description
        )
        db.commit()
        import complects_service
        complects_service.calculate_complect_total(db, complect_id)
        return {'success': True, 'id': item_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def create_complect_items_from_nomenclature(db, complect_id, nomenclature_item_ids):
    """
    Добавить в комплект позиции по выбранным позициям номенклатуры.
    nomenclature_item_ids — список id из nomenclature_items.
    """
    if not nomenclature_item_ids:
        return {'success': True, 'added': 0, 'error': None}
    try:
        complect_id = int(complect_id)
    except (TypeError, ValueError):
        return {'success': False, 'added': 0, 'error': 'Неверный ID комплекта'}
    added = 0
    for nid in nomenclature_item_ids:
        try:
            nid = int(nid)
        except (TypeError, ValueError):
            continue
        nom = db.nomenclature_items(nid)
        if not nom:
            continue
        item_name = (nom.item_number or (nom.description[:200] if nom.description else 'Позиция #%s' % nid))
        item_name = (item_name or 'Позиция #%s' % nid)[:200]
        price = float(nom.total_cost or 0)
        quantity = 1
        unit = (getattr(nom, 'unit', None) or 'шт').strip() or 'шт'
        total = price * quantity
        desc = nom.description
        if desc and len(desc) > 65535:
            desc = desc[:65535]
        try:
            db.complect_items.insert(
                complect_id=complect_id,
                nomenclature_item_id=nid,
                item_name=item_name,
                quantity=quantity,
                unit=unit,
                price=price,
                total=total,
                description=desc
            )
            added += 1
        except Exception as e:
            err = str(e).lower()
            if 'nomenclature_item_id' in err or 'no such column' in err or 'unknown column' in err:
                try:
                    db.complect_items.insert(
                        complect_id=complect_id,
                        item_name=item_name,
                        quantity=quantity,
                        unit=unit,
                        price=price,
                        total=total,
                        description=desc
                    )
                    added += 1
                except Exception as e2:
                    db.rollback()
                    return {'success': False, 'added': added, 'error': str(e2)}
            else:
                db.rollback()
                return {'success': False, 'added': added, 'error': str(e)}
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return {'success': False, 'added': 0, 'error': 'Commit: %s' % str(e)}
    if added:
        try:
            import complects_service
            complects_service.calculate_complect_total(db, complect_id)
        except Exception:
            pass
    return {'success': True, 'added': added, 'error': None}


def get_complect_item_by_id(db, item_id):
    """Получить позицию комплекта по ID"""
    try:
        return db.complect_items(item_id) or None
    except Exception as e:
        return None


def get_all_complect_items(db, complect_id=None, order_by='id'):
    """Получить все позиции комплекта"""
    try:
        query = db.complect_items.id > 0
        if complect_id:
            query = query & (db.complect_items.complect_id == complect_id)
        return db(query).select(orderby=db.complect_items[order_by])
    except Exception as e:
        return db().select(db.complect_items.id)


def update_complect_item(db, item_id, **kwargs):
    """Обновить позицию комплекта"""
    try:
        item = db.complect_items(item_id)
        if not item:
            return {'success': False, 'error': 'Позиция не найдена'}
        allowed_fields = ['complect_id', 'nomenclature_item_id', 'item_name', 'quantity', 'unit', 'price', 'description']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if 'quantity' in update_data or 'price' in update_data:
            quantity = update_data.get('quantity', item.quantity)
            price = update_data.get('price', item.price)
            update_data['total'] = float(quantity) * float(price)
        if update_data:
            db(db.complect_items.id == item_id).update(**update_data)
            db.commit()
            import complects_service
            complects_service.calculate_complect_total(db, item.complect_id)
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_complect_item(db, item_id):
    """Удалить позицию комплекта"""
    try:
        item = db.complect_items(item_id)
        if not item:
            return {'success': False, 'error': 'Позиция не найдена'}
        complect_id = item.complect_id
        db(db.complect_items.id == item_id).delete()
        db.commit()
        import complects_service
        complects_service.calculate_complect_total(db, complect_id)
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def search_complect_items(db, search_term, complect_id=None):
    """Поиск позиций комплекта"""
    try:
        query = (db.complect_items.item_name.contains(search_term)) | \
                (db.complect_items.description.contains(search_term))
        if complect_id:
            query = query & (db.complect_items.complect_id == complect_id)
        return db(query).select(orderby=db.complect_items.id)
    except Exception as e:
        return db().select(db.complect_items.id)
