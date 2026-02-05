# -*- coding: utf-8 -*-
"""
Контроллер для работы с источниками лидов (CRUD, панель справа).
"""


@auth.requires_login()
def list():
    """Список источников лидов + панель добавления/редактирования справа."""
    try:
        # Инициализация формы добавления
        form_status = SQLFORM(
            db.lead_sources,
            submit_button='Добавить',
            _id='leadSourceForm',
            _name='lead_source_form',
            _action=URL('lead_sources', 'list'),
            _method='POST'
        )
        
        # Обработка формы добавления
        if form_status.process(formname='lead_source_form', keepvalues=False).accepted:
            try:
                db.commit()
                session.flash = 'Источник лида успешно создан'
                redirect(URL('lead_sources', 'list'))
            except Exception as commit_error:
                try:
                    db.rollback()
                except:
                    pass
                session.flash = 'Ошибка при сохранении: %s' % str(commit_error)
                redirect(URL('lead_sources', 'list'))
        elif form_status.errors:
            response.flash = 'Исправьте ошибки в форме'
            try:
                db.rollback()
            except:
                pass
        
        if form_status.element('input[type=submit]'):
            form_status.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'

        edit_record = None
        form_edit = None
        show_edit_panel = False
        edit_id = request.vars.get('edit') or request.post_vars.get('edit')
        if edit_id:
            try:
                edit_id = int(edit_id)
            except (TypeError, ValueError):
                edit_id = None
        if edit_id:
            edit_record = db.lead_sources(edit_id)
            if edit_record:
                form_edit = SQLFORM(
                    db.lead_sources,
                    edit_id,
                    submit_button='Сохранить',
                    showid=False,
                    _id='leadSourceEditForm',
                    _name='lead_source_edit_form',
                    _action=URL('lead_sources', 'list', vars=dict(edit=edit_id)),
                    _method='POST'
                )
                if form_edit.process(formname='lead_source_edit_form', keepvalues=False).accepted:
                    try:
                        db.commit()
                        session.flash = 'Источник лида успешно обновлён'
                        redirect(URL('lead_sources', 'list'))
                    except Exception as commit_error:
                        try:
                            db.rollback()
                        except:
                            pass
                        session.flash = 'Ошибка при обновлении: %s' % str(commit_error)
                        redirect(URL('lead_sources', 'list', vars=dict(edit=edit_id)))
                elif form_edit.errors:
                    response.flash = 'Исправьте ошибки в форме'
                    try:
                        db.rollback()
                    except:
                        pass
                if form_edit.element('input[type=submit]'):
                    form_edit.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
                show_edit_panel = True

        rows = db(db.lead_sources.id > 0).select(orderby=db.lead_sources.sort_order | db.lead_sources.name)
        import breadcrumbs_helper
        breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
            ('Главная', URL('default', 'index')),
            ('Источники лидов', None),
        ])
        return dict(
            lead_sources=rows,
            breadcrumbs=breadcrumbs,
            form_status=form_status,
            form_edit=form_edit,
            edit_record=edit_record,
            show_edit_panel=show_edit_panel,
        )
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('default', 'index'))


@auth.requires_login()
def delete():
    """Удаление источника лида."""
    try:
        try:
            db.rollback()
        except:
            pass
        record_id = request.args(0)
        if not record_id:
            session.flash = 'Не указан ID'
            redirect(URL('lead_sources', 'list'))
        record = db.lead_sources(record_id)
        if not record:
            session.flash = 'Источник лида не найден'
            redirect(URL('lead_sources', 'list'))
        db(db.lead_sources.id == record_id).delete()
        db.commit()
        session.flash = 'Источник лида успешно удалён'
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        session.flash = 'Ошибка при удалении: %s' % str(e)
    redirect(URL('lead_sources', 'list'))
