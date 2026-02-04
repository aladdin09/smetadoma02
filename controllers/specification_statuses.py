# -*- coding: utf-8 -*-
"""
Контроллер для работы со статусами спецификаций
"""


def list():
    """Список всех статусов спецификаций"""
    try:
        # Откатываем любые незавершенные транзакции перед началом
        try:
            db.rollback()
        except:
            pass
        
        import specification_statuses_service
        import importlib
        importlib.reload(specification_statuses_service)
        # Форма для добавления статуса (в панели справа)
        form_status = SQLFORM(
            db.specification_statuses,
            submit_button='Добавить',
            _id='specificationStatusForm',
            _name='specification_status_form',
            _action=URL('specification_statuses', 'list'),
            _method='POST'
        )
        # Обработка отправки формы добавления: через сервис, чтобы получить точную ошибку
        _form_submitted = (request.post_vars and (
            request.post_vars.get('_formname') == 'specification_status_form' or
            request.post_vars.get('specification_statuses_name') is not None or
            request.post_vars.get('name') is not None
        ))
        if _form_submitted:
            pv = request.post_vars
            name = (pv.get('specification_statuses_name') or pv.get('specification_statuses.name') or
                    pv.get('name') or '').strip() if pv else ''
            if name:
                try:
                    sort_order = request.post_vars.get('specification_statuses_sort_order') or request.post_vars.get('sort_order') or 0
                    try:
                        sort_order = int(sort_order)
                    except (TypeError, ValueError):
                        sort_order = 0
                    is_active = request.post_vars.get('specification_statuses_is_active')
                    if is_active is None:
                        is_active = request.post_vars.get('is_active')
                    is_active = is_active in (True, 'on', 'true', '1', 1)
                    description = request.post_vars.get('specification_statuses_description') or request.post_vars.get('description') or None
                    result = specification_statuses_service.create_status(
                        db, name=name, description=description,
                        sort_order=sort_order, is_active=is_active
                    )
                    if result.get('success'):
                        session.flash = 'Статус спецификации успешно создан'
                        redirect(URL('specification_statuses', 'list'))
                    else:
                        response.flash = 'Ошибка: %s' % result.get('error', 'Данные не добавлены.')
                except Exception as e:
                    try:
                        db.rollback()
                    except:
                        pass
                    response.flash = 'Ошибка при добавлении: %s' % str(e)
            else:
                response.flash = 'Укажите название статуса.'
        else:
            if form_status.process(formname='specification_status_form', keepvalues=False).accepted:
                session.flash = 'Статус спецификации успешно создан'
                redirect(URL('specification_statuses', 'list'))
            elif form_status.errors:
                response.flash = 'Исправьте ошибки в форме'
        if form_status.element('input[type=submit]'):
            form_status.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
        # Панель редактирования: при ?edit=id или при POST формы редактирования
        edit_status = None
        form_edit = None
        show_edit_panel = False
        edit_id = request.vars.get('edit') or request.post_vars.get('edit')
        if edit_id:
            try:
                edit_id = int(edit_id)
            except (TypeError, ValueError):
                edit_id = None
        if edit_id:
            try:
                edit_status = specification_statuses_service.get_status_by_id(db, edit_id)
            except Exception as e:
                try:
                    db.rollback()
                except:
                    pass
                edit_status = None
            if edit_status:
                form_edit = SQLFORM(
                    db.specification_statuses,
                    edit_id,
                    submit_button='Сохранить',
                    showid=False,
                    _id='specificationStatusEditForm',
                    _name='specification_status_edit_form',
                    _action=URL('specification_statuses', 'list', vars=dict(edit=edit_id)),
                    _method='POST'
                )
                if form_edit.process(formname='specification_status_edit_form', keepvalues=False).accepted:
                    session.flash = 'Статус спецификации успешно обновлён'
                    redirect(URL('specification_statuses', 'list'))
                elif form_edit.errors:
                    response.flash = 'Исправьте ошибки в форме'
                if form_edit.element('input[type=submit]'):
                    form_edit.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
                show_edit_panel = True
        try:
            statuses = specification_statuses_service.get_all_statuses(db, order_by='sort_order')
        except Exception as e:
            # Откатываем транзакцию при ошибке
            try:
                db.rollback()
            except:
                pass
            # Пробуем еще раз после rollback
            try:
                statuses = specification_statuses_service.get_all_statuses(db, order_by='sort_order')
            except Exception as e2:
                statuses = []
                session.flash = f'Ошибка загрузки статусов: {str(e2)}'
        import breadcrumbs_helper
        breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
            ('Главная', URL('default', 'index')),
            ('Статус спецификации', None),
        ])
        return dict(
            statuses=statuses,
            breadcrumbs=breadcrumbs,
            form_status=form_status,
            form_edit=form_edit,
            edit_status=edit_status,
            show_edit_panel=show_edit_panel,
        )
    except Exception as e:
        # Откатываем транзакцию при критической ошибке
        try:
            db.rollback()
        except:
            pass
        session.flash = f'Ошибка: {str(e)}'
        redirect(URL('default', 'index'))


def create():
    """Создание нового статуса спецификации"""
    try:
        # Откатываем любые незавершенные транзакции
        try:
            db.rollback()
        except:
            pass
        
        import specification_statuses_service
        import importlib
        importlib.reload(specification_statuses_service)
        form = SQLFORM(db.specification_statuses, submit_button='Создать', _class='form-horizontal')
        if form.process().accepted:
            session.flash = 'Статус спецификации успешно создан'
            redirect(URL('specification_statuses', 'list'))
        elif form.errors:
            response.flash = 'Исправьте ошибки в форме'
        return dict(form=form)
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        session.flash = f'Ошибка: {str(e)}'
        redirect(URL('specification_statuses', 'list'))


def edit():
    """Редактирование статуса спецификации"""
    try:
        # Откатываем любые незавершенные транзакции
        try:
            db.rollback()
        except:
            pass
        
        import specification_statuses_service
        import importlib
        importlib.reload(specification_statuses_service)
        status_id = request.args(0)
        if not status_id:
            session.flash = 'Не указан ID статуса'
            redirect(URL('specification_statuses', 'list'))
        try:
            status = specification_statuses_service.get_status_by_id(db, status_id)
        except Exception as e:
            try:
                db.rollback()
            except:
                pass
            status = None
        if not status:
            session.flash = 'Статус не найден'
            redirect(URL('specification_statuses', 'list'))
        form = SQLFORM(db.specification_statuses, status_id, submit_button='Сохранить', _class='form-horizontal', showid=False)
        if form.process().accepted:
            session.flash = 'Статус спецификации успешно обновлен'
            redirect(URL('specification_statuses', 'list'))
        elif form.errors:
            response.flash = 'Исправьте ошибки в форме'
        return dict(form=form, status=status)
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        session.flash = f'Ошибка: {str(e)}'
        redirect(URL('specification_statuses', 'list'))


def delete():
    """Удаление статуса спецификации"""
    try:
        # Откатываем любые незавершенные транзакции
        try:
            db.rollback()
        except:
            pass
        
        import specification_statuses_service
        import importlib
        importlib.reload(specification_statuses_service)
        status_id = request.args(0)
        if not status_id:
            session.flash = 'Не указан ID статуса'
            redirect(URL('specification_statuses', 'list'))
        try:
            status = specification_statuses_service.get_status_by_id(db, status_id)
        except Exception as e:
            try:
                db.rollback()
            except:
                pass
            status = None
        if not status:
            session.flash = 'Статус не найден'
            redirect(URL('specification_statuses', 'list'))
        result = specification_statuses_service.delete_status(db, status_id)
        if result.get('success'):
            session.flash = 'Статус спецификации успешно удален'
        else:
            session.flash = f'Ошибка при удалении статуса: {result.get("error", "Неизвестная ошибка")}'
        redirect(URL('specification_statuses', 'list'))
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        session.flash = f'Ошибка: {str(e)}'
        redirect(URL('specification_statuses', 'list'))
