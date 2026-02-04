# -*- coding: utf-8 -*-
"""
Контроллер для работы с типами позиций номенклатуры (nomenclature_item_types)
"""

def list():
    """Список и создание/редактирование типов позиций номенклатуры"""

    import nomenclature_item_types_service
    import importlib
    importlib.reload(nomenclature_item_types_service)

    # ID записи для редактирования
    edit_id = request.vars.edit
    record = None
    form_edit = None
    show_edit_panel = False

    # Если есть edit_id — загружаем запись
    if edit_id:
        try:
            edit_id = int(edit_id)
            record = db.nomenclature_item_types(edit_id)
        except:
            record = None

        if record:
            # Форма редактирования
            form_edit = SQLFORM(
                db.nomenclature_item_types,
                record,
                formname='edit_form',
                submit_button='Сохранить',
                showid=False
            )

            if form_edit.process(formname='edit_form').accepted:
                session.flash = 'Тип позиции номенклатуры обновлён'
                redirect(URL('nomenclature_item_types', 'list'))

            elif form_edit.errors:
                response.flash = 'Исправьте ошибки в форме'

            show_edit_panel = True

    # Форма создания (работает только если НЕ редактируем)
    form_status = None
    if not record:
        form_status = SQLFORM(
            db.nomenclature_item_types,
            formname='create_form',
            submit_button='Добавить',
            showid=False
        )

        if form_status.process(formname='create_form').accepted:
            session.flash = 'Тип позиции номенклатуры создан'
            redirect(URL('nomenclature_item_types', 'list'))

        elif form_status.errors:
            response.flash = 'Исправьте ошибки в форме'

    # Список типов
    item_types = db(db.nomenclature_item_types).select(orderby=db.nomenclature_item_types.sort_order)

    # Хлебные крошки
    import breadcrumbs_helper
    breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
        ('Главная', URL('default', 'index')),
        ('Типы позиций номенклатуры', None),
    ])

    return dict(
        item_types=item_types,
        breadcrumbs=breadcrumbs,
        form_status=form_status,
        form_edit=form_edit,
        show_edit_panel=show_edit_panel,
        edit_item_type=record
    )


def edit():
    """Редактирование типа позиции номенклатуры"""
    try:
        try:
            db.rollback()
        except:
            pass

        import nomenclature_item_types_service
        import importlib
        importlib.reload(nomenclature_item_types_service)
        
        item_type_id = request.args(0)
        if not item_type_id:
            session.flash = 'Не указан ID типа позиции номенклатуры'
            redirect(URL('nomenclature_item_types', 'list'))
        
        # Преобразуем ID в int для безопасности
        try:
            item_type_id = int(item_type_id)
        except (ValueError, TypeError):
            session.flash = 'Неверный ID типа позиции номенклатуры'
            redirect(URL('nomenclature_item_types', 'list'))
        
        try:
            item_type = nomenclature_item_types_service.get_item_type_by_id(db, item_type_id)
        except Exception:
            try:
                db.rollback()
            except:
                pass
            item_type = None
        
        if not item_type:
            session.flash = 'Тип позиции номенклатуры не найден'
            redirect(URL('nomenclature_item_types', 'list'))
        
        # Создаем форму редактирования (используем ID напрямую, как в nomenclature_items)
        form = SQLFORM(
            db.nomenclature_item_types,
            item_type_id,
            submit_button='Сохранить',
            _class='form-horizontal',
            showid=False
        )
        
        # Обработка формы
        if form.process().accepted:
            session.flash = 'Тип позиции номенклатуры успешно обновлён'
            redirect(URL('nomenclature_item_types', 'list'))
        elif form.errors:
            response.flash = 'Исправьте ошибки в форме'
        
        import breadcrumbs_helper
        breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
            ('Главная', URL('default', 'index')),
            ('Типы позиций номенклатуры', URL('nomenclature_item_types', 'list')),
            ('Редактирование', None),
        ])
        
        return dict(form=form, item_type=item_type, breadcrumbs=breadcrumbs)
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('nomenclature_item_types', 'list'))


def delete():
    """Удаление типа позиции номенклатуры"""
    try:
        try:
            db.rollback()
        except:
            pass

        import nomenclature_item_types_service
        import importlib
        importlib.reload(nomenclature_item_types_service)
        item_type_id = request.args(0)
        if not item_type_id:
            session.flash = 'Не указан ID типа позиции номенклатуры'
            redirect(URL('nomenclature_item_types', 'list'))
        try:
            item_type = nomenclature_item_types_service.get_item_type_by_id(db, item_type_id)
        except Exception:
            try:
                db.rollback()
            except:
                pass
            item_type = None
        if not item_type:
            session.flash = 'Тип позиции номенклатуры не найден'
            redirect(URL('nomenclature_item_types', 'list'))
        result = nomenclature_item_types_service.delete_item_type(db, item_type_id)
        if result.get('success'):
            session.flash = 'Тип позиции номенклатуры успешно удалён'
        else:
            session.flash = result.get('error', 'Ошибка при удалении типа позиции номенклатуры')
        redirect(URL('nomenclature_item_types', 'list'))
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('nomenclature_item_types', 'list'))
