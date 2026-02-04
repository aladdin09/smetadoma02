# -*- coding: utf-8 -*-
"""
Сервисный слой для работы с таблицей specification_items (Позиции спецификации)
"""


def create_specification_item(db, specification_id, item_name, quantity=1, unit='шт',
                       price=0, description=None, nomenclature_item_id=None):
    """Создать новую позицию спецификации"""
    try:
        total = float(quantity) * float(price)
        item_id = db.specification_items.insert(
            specification_id=specification_id,
            nomenclature_item_id=nomenclature_item_id,
            item_name=item_name,
            quantity=quantity,
            unit=unit,
            price=price,
            total=total,
            description=description
        )
        db.commit()
        import specifications_service
        specifications_service.calculate_specification_total(db, specification_id)
        return {'success': True, 'id': item_id}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def create_specification_items_from_nomenclature(db, specification_id, nomenclature_item_ids):
    """Добавить в спецификацию позиции по выбранным позициям номенклатуры."""
    if not nomenclature_item_ids:
        return {'success': True, 'added': 0, 'error': None}
    try:
        specification_id = int(specification_id)
    except (TypeError, ValueError):
        return {'success': False, 'added': 0, 'error': 'Неверный ID спецификации'}
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
            db.specification_items.insert(
                specification_id=specification_id,
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
                    db.specification_items.insert(
                        specification_id=specification_id,
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
            import specifications_service
            specifications_service.calculate_specification_total(db, specification_id)
        except Exception:
            pass
    return {'success': True, 'added': added, 'error': None}


def get_specification_item_by_id(db, item_id):
    """Получить позицию спецификации по ID"""
    try:
        return db.specification_items(item_id) or None
    except Exception as e:
        return None


def get_all_specification_items(db, specification_id=None, order_by='id'):
    """Получить все позиции спецификации"""
    try:
        query = db.specification_items.id > 0
        if specification_id:
            query = query & (db.specification_items.specification_id == specification_id)
        return db(query).select(orderby=db.specification_items[order_by])
    except Exception as e:
        return db().select(db.specification_items.id)


def update_specification_item(db, item_id, **kwargs):
    """Обновить позицию спецификации"""
    try:
        item = db.specification_items(item_id)
        if not item:
            return {'success': False, 'error': 'Позиция не найдена'}
        allowed_fields = ['specification_id', 'nomenclature_item_id', 'item_name', 'quantity', 'unit', 'price', 'description']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if 'quantity' in update_data or 'price' in update_data:
            quantity = update_data.get('quantity', item.quantity)
            price = update_data.get('price', item.price)
            update_data['total'] = float(quantity) * float(price)
        if update_data:
            db(db.specification_items.id == item_id).update(**update_data)
            db.commit()
            import specifications_service
            specifications_service.calculate_specification_total(db, item.specification_id)
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_specification_item(db, item_id):
    """Удалить позицию спецификации"""
    try:
        item = db.specification_items(item_id)
        if not item:
            return {'success': False, 'error': 'Позиция не найдена'}
        specification_id = item.specification_id
        db(db.specification_items.id == item_id).delete()
        db.commit()
        import specifications_service
        specifications_service.calculate_specification_total(db, specification_id)
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def search_specification_items(db, search_term, specification_id=None):
    """Поиск позиций спецификации"""
    try:
        query = (db.specification_items.item_name.contains(search_term)) | \
                (db.specification_items.description.contains(search_term))
        if specification_id:
            query = query & (db.specification_items.specification_id == specification_id)
        return db(query).select(orderby=db.specification_items.id)
    except Exception as e:
        return db().select(db.specification_items.id)
