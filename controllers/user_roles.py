# -*- coding: utf-8 -*-
"""
Контроллер для работы с ролями пользователей (user_roles)
"""


def list():
    """Список всех ролей"""
    try:
        try:
            db.rollback()
        except:
            pass

        import user_roles_service
        import importlib
        importlib.reload(user_roles_service)

        form_status = SQLFORM(
            db.user_roles,
            submit_button='Добавить',
            _id='userRoleForm',
            _name='user_role_form',
            _action=URL('user_roles', 'list'),
            _method='POST'
        )

        _form_submitted = (request.post_vars and (
            request.post_vars.get('_formname') == 'user_role_form' or
            request.post_vars.get('user_roles_name') is not None or
            request.post_vars.get('name') is not None
        ))
        if _form_submitted:
            pv = request.post_vars
            name = (pv.get('user_roles_name') or pv.get('name') or '').strip() if pv else ''
            if name:
                try:
                    sort_order = pv.get('user_roles_sort_order') or pv.get('sort_order') or 0
                    try:
                        sort_order = int(sort_order)
                    except (TypeError, ValueError):
                        sort_order = 0
                    is_active = pv.get('user_roles_is_active') or pv.get('is_active')
                    is_active = is_active in (True, 'on', 'true', '1', 1)
                    description = pv.get('user_roles_description') or pv.get('description') or None
                    result = user_roles_service.create_role(
                        db, name=name, description=description,
                        sort_order=sort_order, is_active=is_active
                    )
                    if result.get('success'):
                        session.flash = 'Роль успешно создана'
                        redirect(URL('user_roles', 'list'))
                    else:
                        response.flash = 'Ошибка: %s' % result.get('error', 'Данные не добавлены.')
                except Exception as e:
                    try:
                        db.rollback()
                    except:
                        pass
                    response.flash = 'Ошибка при добавлении: %s' % str(e)
            else:
                response.flash = 'Укажите название роли.'
        else:
            if form_status.process(formname='user_role_form', keepvalues=False).accepted:
                session.flash = 'Роль успешно создана'
                redirect(URL('user_roles', 'list'))
            elif form_status.errors:
                response.flash = 'Исправьте ошибки в форме'
        if form_status.element('input[type=submit]'):
            form_status.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'

        edit_role = None
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
                edit_role = user_roles_service.get_role_by_id(db, edit_id)
            except Exception:
                try:
                    db.rollback()
                except:
                    pass
                edit_role = None
            if edit_role:
                form_edit = SQLFORM(
                    db.user_roles,
                    edit_id,
                    submit_button='Сохранить',
                    showid=False,
                    _id='userRoleEditForm',
                    _name='user_role_edit_form',
                    _action=URL('user_roles', 'list', vars=dict(edit=edit_id)),
                    _method='POST'
                )
                if form_edit.process(formname='user_role_edit_form', keepvalues=False).accepted:
                    session.flash = 'Роль успешно обновлена'
                    redirect(URL('user_roles', 'list'))
                elif form_edit.errors:
                    response.flash = 'Исправьте ошибки в форме'
                if form_edit.element('input[type=submit]'):
                    form_edit.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
                show_edit_panel = True

        try:
            roles = user_roles_service.get_all_roles(db, order_by='sort_order')
        except Exception:
            try:
                db.rollback()
            except:
                pass
            try:
                roles = user_roles_service.get_all_roles(db, order_by='sort_order')
            except Exception:
                roles = []
                session.flash = 'Ошибка загрузки ролей'

        import breadcrumbs_helper
        breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
            ('Главная', URL('default', 'index')),
            ('Роли', None),
        ])
        return dict(
            roles=roles,
            breadcrumbs=breadcrumbs,
            form_status=form_status,
            form_edit=form_edit,
            edit_role=edit_role,
            show_edit_panel=show_edit_panel,
        )
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('default', 'index'))


def delete():
    """Удаление роли"""
    try:
        try:
            db.rollback()
        except:
            pass

        import user_roles_service
        import importlib
        importlib.reload(user_roles_service)
        role_id = request.args(0)
        if not role_id:
            session.flash = 'Не указан ID роли'
            redirect(URL('user_roles', 'list'))
        try:
            role = user_roles_service.get_role_by_id(db, role_id)
        except Exception:
            try:
                db.rollback()
            except:
                pass
            role = None
        if not role:
            session.flash = 'Роль не найдена'
            redirect(URL('user_roles', 'list'))
        result = user_roles_service.delete_role(db, role_id)
        if result.get('success'):
            session.flash = 'Роль успешно удалена'
        else:
            session.flash = result.get('error', 'Ошибка при удалении роли')
        redirect(URL('user_roles', 'list'))
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('user_roles', 'list'))
