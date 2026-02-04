# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

import traceback
import sys

# Попытка импорта с обработкой ошибок
try:
    from dashboard_data import get_dashboard_data, get_status_color
except ImportError as import_err:
    # Если импорт не удался, попробуем альтернативные варианты
    try:
        import dashboard_data
        get_dashboard_data = dashboard_data.get_dashboard_data
        get_status_color = dashboard_data.get_status_color
    except Exception as import_err2:
        # Если и это не помогло, создадим заглушки (полный набор ключей для шаблонов)
        def get_dashboard_data(db, request, auth=None):
            return dict(
                error=f'Ошибка импорта dashboard_data: {str(import_err)}, {str(import_err2)}',
                dashboard_stats=[], total_projects=0, total_customers=0, total_orders=0,
                projects=[], all_customers=[], all_statuses=[], status_colors={},
                project_specification_sums={}, dashboard_specification_total=0,
                filter_customer='', filter_status='', filter_name='', filter_project_number='',
            )
        def get_status_color(status_name):
            return 'secondary'
except Exception:
    # Полная заглушка на случай любой другой ошибки при импорте
    def get_dashboard_data(db, request, auth=None):
        return dict(
            error='Критическая ошибка импорта dashboard_data',
            dashboard_stats=[], total_projects=0, total_customers=0, total_orders=0,
            projects=[], all_customers=[], all_statuses=[], status_colors={},
            project_specification_sums={}, dashboard_specification_total=0,
            filter_customer='', filter_status='', filter_name='', filter_project_number='',
        )
    def get_status_color(status_name):
        return 'secondary'


@auth.requires_login()
def index():
    """
    Дашборд + правая панель добавления клиента (главная страница).
    Неавторизованные пользователи перенаправляются на страницу входа.
    """
    # Откатываем любые незавершенные транзакции в начале
    try:
        db.rollback()
    except:
        pass
    
    try:
        show_customer_panel = False
        
        # Откатываем транзакцию перед созданием формы
        try:
            db.rollback()
        except:
            pass
        
        form_customer = SQLFORM(
            db.customers,
            submit_button='Добавить',
            _id='customerForm',
            _name='customer_form'
        )
        
        # Обрабатываем форму с обработкой ошибок транзакций
        try:
            form_result = form_customer.process(formname='customer_form')
            if form_result.accepted:
                try:
                    db.commit()
                    session.flash = 'Клиент успешно добавлен'
                    redirect(URL('customers', 'customer', args=[form_customer.vars.id]))
                except Exception as commit_err:
                    try:
                        db.rollback()
                    except:
                        pass
                    # Если commit не удался, показываем ошибку
                    show_customer_panel = True
                    form_customer.errors = {'_error': 'Ошибка сохранения: ' + str(commit_err)}
            elif form_customer.errors:
                try:
                    db.rollback()
                except:
                    pass
                show_customer_panel = True
                # Логируем ошибки формы для диагностики
                import logging
                try:
                    error_msg = ', '.join([f"{k}: {v}" for k, v in form_customer.errors.items()])
                    logging.error(f"Ошибки формы клиента: {error_msg}")
                except:
                    pass
        except Exception as form_err:
            # Если обработка формы вызвала ошибку, откатываем транзакцию
            try:
                db.rollback()
            except:
                pass
            show_customer_panel = True
            form_customer.errors = {'_error': 'Ошибка обработки формы: ' + str(form_err)}
        
        if request.vars.get('open_customer_panel') == '1':
            show_customer_panel = True
        
        # Откатываем транзакцию перед вызовом get_dashboard_data
        try:
            db.rollback()
        except:
            pass
        
        data = get_dashboard_data(db, request, auth)
        form_customer.element('input[type=submit]')['_class'] = 'btn btn-primary btn-block'
        data['form_customer'] = form_customer
        data['show_customer_panel'] = show_customer_panel
        if 'error' not in data:
            data.setdefault('error', None)
        # Гарантируем наличие переменных для шаблона (на случай неполного ответа get_dashboard_data)
        data.setdefault('project_specification_sums', {})
        data.setdefault('dashboard_specification_total', 0)
        # Если есть ошибка в данных, логируем её
        if data.get('error'):
            import logging
            try:
                logging.error(f"Ошибка в get_dashboard_data: {data.get('error')}\nTraceback: {data.get('error_traceback', 'N/A')}")
            except:
                pass
        response.view = 'default/index.html'
        return data
    except Exception as e:
        # Детальная информация об ошибке для диагностики
        try:
            error_type = type(e).__name__
            error_message = str(e)
            error_traceback = traceback.format_exc()
            error_html = f"""
            <html><body style="font-family: monospace; padding: 20px;">
            <h1>Ошибка в default/index</h1>
            <h2>Тип ошибки: {error_type}</h2>
            <h3>Сообщение: {error_message}</h3>
            <h3>Traceback:</h3>
            <pre style="background: #f0f0f0; padding: 10px; overflow: auto;">{error_traceback}</pre>
            </body></html>
            """
            raise HTTP(500, error_html)
        except:
            # Если даже вывод ошибки не работает, просто вернем текст
            raise HTTP(500, f"Ошибка в default/index: {str(e)}")


def migrate_specification_statuses():
    """
    Однократная миграция: копирует данные из complect_statuses в specification_statuses.
    Вызовите один раз: /adminlte5/default/migrate_specification_statuses
    если при создании спецификации была ошибка FK (status_id не найден в specification_statuses).
    """
    try:
        _adapter = db._adapter.__class__.__module__
        if 'postgres' in _adapter:
            db.executesql(
                "INSERT INTO specification_statuses (id, name, description, sort_order, is_active) "
                "SELECT id, name, description, sort_order, is_active FROM complect_statuses "
                "ON CONFLICT (id) DO NOTHING"
            )
            db.executesql(
                "SELECT setval(pg_get_serial_sequence('specification_statuses', 'id')::regclass, "
                "COALESCE((SELECT MAX(id) FROM specification_statuses), 0))"
            )
        else:
            db.executesql(
                "INSERT OR IGNORE INTO specification_statuses (id, name, description, sort_order, is_active) "
                "SELECT id, name, description, sort_order, is_active FROM complect_statuses"
            )
        db.commit()
        session.flash = 'Миграция выполнена: статусы скопированы из complect_statuses в specification_statuses.'
    except Exception as e:
        try:
            db.rollback()
        except:
            pass
        session.flash = f'Ошибка миграции: {str(e)}'
    redirect(URL('default', 'index'))


def get_status_color_by_id(status_id):
    """
    Возвращает цвет для статуса по ID
    """
    try:
        status = db.specification_statuses(status_id)
        if status:
            return get_status_color(status.name)
    except:
        pass
    return 'secondary'



# ---- API (example) -----
@auth.requires_login()
def api_get_user_email():
    if not request.env.request_method == 'GET': raise HTTP(403)
    return response.json({'status':'success', 'email':auth.user.email})

# ---- Smart Grid (example) -----
@auth.requires_membership('admin') # can only be accessed by members of admin groupd
def grid():
    response.view = 'generic.html' # use a generic view
    tablename = request.args(0)
    if not tablename in db.tables: raise HTTP(403)
    grid = SQLFORM.smartgrid(db[tablename], args=[tablename], deletable=False, editable=False)
    return dict(grid=grid)

# ---- Embedded wiki (example) ----
def wiki():
    auth.wikimenu() # add the wiki to the menu
    return auth.wiki() 

# ---- Первоначальная настройка (когда в системе ещё нет пользователей) -----
def first_run():
    """
    Страница создания первого пользователя. Доступна только когда в auth_user нет записей.
    Создаёт роли по умолчанию (если пусто) и форму для первого пользователя.
    """
    try:
        user_count = db(db.auth_user.id > 0).count()
    except Exception:
        user_count = 1  # при ошибке не показывать форму
    if user_count > 0:
        session.flash = 'В системе уже есть пользователи. Войдите в систему.'
        redirect(URL('default', 'user', args=['login']))
    # Создать роли по умолчанию, если таблица ролей пуста
    try:
        if db(db.user_roles.id > 0).count() == 0:
            for i, name in enumerate(['Admin', 'Собственник', 'Менеджер', 'РОП'], 1):
                db.user_roles.insert(name=name, sort_order=i, is_active=True)
            db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
    form = SQLFORM.factory(
        Field('nic', 'string', length=128, requires=[IS_NOT_EMPTY(), IS_MATCH(r'^\w+$', error_message='Только буквы, цифры и _')], label='Логин'),
        Field('email', 'string', length=128, requires=[IS_NOT_EMPTY(), IS_EMAIL()], label='Email'),
        Field('password', 'password', requires=IS_NOT_EMPTY(), label='Пароль'),
        Field('first_name', 'string', length=128, label='Имя'),
        Field('last_name', 'string', length=128, label='Фамилия'),
        Field('role_id', 'reference user_roles', requires=IS_IN_DB(db, db.user_roles.id, '%(name)s'), label='Роль'),
        submit_button='Создать первого пользователя',
        _id='first_run_form',
        _name='first_run_form',
    )
    if form.process(formname='first_run_form').accepted:
        try:
            pw = form.vars.password
            user_id = db.auth_user.insert(
                nic=form.vars.nic,
                email=form.vars.email,
                password=auth.table_user().password.validate(pw, form.vars)[0],
                first_name=form.vars.first_name or '',
                last_name=form.vars.last_name or '',
                role_id=form.vars.role_id,
            )
            db.commit()
            session.flash = 'Первый пользователь создан. Войдите в систему.'
            redirect(URL('default', 'user', args=['login']))
        except Exception as e:
            try:
                db.rollback()
            except Exception:
                pass
            response.flash = 'Ошибка при создании пользователя: %s' % str(e)
    if form.errors:
        response.flash = 'Исправьте ошибки в форме'
    return dict(form=form)


# ---- Action for login/register/etc (required for auth) -----
def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    # Если пользователей ещё нет — перенаправить на первоначальную настройку
    if request.args(0) == 'login':
        try:
            if db(db.auth_user.id > 0).count() == 0:
                redirect(URL('default', 'first_run'))
        except Exception:
            pass
    # Чтобы на странице входа показывались ошибки (неверный пароль и т.д.)
    if request.args(0) == 'login' and session.flash:
        response.flash = session.flash
        session.flash = None
    return dict(form=auth())

# ---- action to server uploaded static content (required) ---
@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)




def test_reportlab():
    try:
        import reportlab
        return "ReportLab доступен"
    except Exception as e:
        return "ReportLab НЕ найден: " + str(e)
