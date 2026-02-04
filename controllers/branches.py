# -*- coding: utf-8 -*-
"""
Контроллер для работы с филиалами (branches)
"""
from gluon.http import HTTP


def list():
    """Список всех филиалов"""
    try:
        try:
            db.rollback()
        except:
            pass

        form_add = SQLFORM(
            db.branches,
            submit_button='Добавить',
            _id='branchForm',
            _name='branch_form',
            _action=URL('branches', 'list'),
            _method='POST'
        )
        if form_add.process(formname='branch_form', keepvalues=False).accepted:
            session.flash = 'Филиал успешно создан'
            redirect(URL('branches', 'list'))
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
            edit_record = db.branches(edit_id)
            if edit_record:
                form_edit = SQLFORM(
                    db.branches,
                    edit_id,
                    submit_button='Сохранить',
                    showid=False,
                    _id='branchEditForm',
                    _name='branch_edit_form',
                    _action=URL('branches', 'list', vars=dict(edit=edit_id)),
                    _method='POST'
                )
                if form_edit.process(formname='branch_edit_form', keepvalues=False).accepted:
                    session.flash = 'Филиал успешно обновлён'
                    redirect(URL('branches', 'list'))
                elif form_edit.errors:
                    response.flash = 'Исправьте ошибки в форме'
                if form_edit.element('input[type=submit]'):
                    form_edit.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
                show_edit_panel = True

        rows = db(db.branches.id > 0).select(orderby=[db.branches.sort_order, db.branches.name])
        import breadcrumbs_helper
        breadcrumbs = breadcrumbs_helper.make_breadcrumbs([
            ('Главная', URL('default', 'index')),
            ('Филиалы', None),
        ])
        return dict(
            branches=rows,
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
    """Удаление филиала"""
    try:
        try:
            db.rollback()
        except:
            pass
        branch_id = request.args(0)
        if not branch_id:
            session.flash = 'Не указан ID филиала'
            redirect(URL('branches', 'list'))
        try:
            branch_id = int(branch_id)
        except (TypeError, ValueError):
            session.flash = 'Неверный ID филиала'
            redirect(URL('branches', 'list'))
        row = db.branches(branch_id)
        if not row:
            session.flash = 'Филиал не найден'
            redirect(URL('branches', 'list'))
        db(db.branches.id == branch_id).delete()
        db.commit()
        session.flash = 'Филиал успешно удалён'
        redirect(URL('branches', 'list'))
    except HTTP:
        raise
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        session.flash = 'Ошибка: %s' % str(e)
        redirect(URL('branches', 'list'))
