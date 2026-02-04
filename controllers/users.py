# -*- coding: utf-8 -*-
"""
Контроллер для работы с пользователями (auth_user)
"""
from gluon.http import HTTP


def list():
    """Список всех пользователей"""
    try:
        try:
            db.rollback()
        except:
            pass

        # Форма добавления: nic (логин), email, first_name, last_name, branch_id, role_id, password
        form_add = SQLFORM(
            db.auth_user,
            fields=['nic', 'email', 'first_name', 'last_name', 'branch_id', 'role_id', 'password'],
            submit_button='Добавить',
            _id='userForm',
            _name='user_form',
            _action=URL('users', 'list'),
            _method='POST'
        )
        if form_add.process(formname='user_form', keepvalues=False).accepted:
            session.flash = 'Пользователь успешно создан'
            redirect(URL('users', 'list'))
        elif form_add.errors:
            response.flash = 'Исправьте ошибки в форме'
        if form_add.element('input[type=submit]'):
            form_add.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'

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
            edit_record = db.auth_user(edit_id)
            if edit_record:
                # Редактирование без поля password (чтобы не перезаписать хеш пустым)
                form_edit = SQLFORM(
                    db.auth_user,
                    edit_id,
                    fields=['nic', 'email', 'first_name', 'last_name', 'branch_id', 'role_id'],
                    submit_button='Сохранить',
                    showid=False,
                    _id='userEditForm',
                    _name='user_edit_form',
                    _action=URL('users', 'list', vars=dict(edit=edit_id)),
                    _method='POST'
                )
                if form_edit.process(formname='user_edit_form', keepvalues=False).accepted:
                    session.flash = 'Пользователь успешно обновлён'
                    redirect(URL('users', 'list'))
                elif form_edit.errors:
                    response.flash = 'Исправьте ошибки в форме'
                if form_edit.element('input[type=submit]'):
                    form_edit.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
                show_edit_panel = True

        # Список пользователей с названием филиала и роли
        rows = db(db.auth_user.id > 0).select(
            db.auth_user.id,
            db.auth_user.nic,
            db.auth_user.email,
            db.auth_user.first_name,
            db.auth_user.last_name,
            db.auth_user.branch_id,
            db.auth_user.role_id,
            db.branches.name,
            db.user_roles.name,
            left=[
                db.branches.on(db.auth_user.branch_id == db.branches.id),
                db.user_roles.on(db.auth_user.role_id == db.user_roles.id),
            ],
            orderby=[db.auth_user.last_name, db.auth_user.first_name]
        )
        import breadcrumbs_helper
        breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
            ('Главная', URL('default', 'index')),
            ('Пользователи', None),
        ])
        return dict(
            users=rows,
            breadcrumbs=breadcrumbs,
            form_add=form_add,
            form_edit=form_edit,
            edit_record=edit_record,
            show_edit_panel=show_edit_panel,
        )
    except HTTP:
        raise
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('default', 'index'))


def delete():
    """Удаление пользователя"""
    try:
        try:
            db.rollback()
        except:
            pass
        user_id = request.args(0)
        if not user_id:
            session.flash = 'Не указан ID пользователя'
            redirect(URL('users', 'list'))
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            session.flash = 'Неверный ID пользователя'
            redirect(URL('users', 'list'))
        row = db.auth_user(user_id)
        if not row:
            session.flash = 'Пользователь не найден'
            redirect(URL('users', 'list'))
        db(db.auth_user.id == user_id).delete()
        db.commit()
        session.flash = 'Пользователь успешно удалён'
        redirect(URL('users', 'list'))
    except HTTP:
        raise
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('users', 'list'))
