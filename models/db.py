# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
# AppConfig configuration made easy. Look inside private/appconfig.ini
# Auth is for authenticaiton and access control
# -------------------------------------------------------------------------
from gluon import DAL
from gluon.tools import Auth
from gluon.validators import IS_IN_DB, IS_EMPTY_OR, IS_EMAIL, IS_MATCH, IS_INT_IN_RANGE, IS_FLOAT_IN_RANGE, IS_NOT_EMPTY
import os
import re
import datetime

REQUIRED_WEB2PY_VERSION = "3.0.10"

# -------------------------------------------------------------------------
# This scaffolding model makes your app work on Google App Engine too
# File is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

try:
    web2py_version_string = request.global_settings.web2py_version.split("-")[0]
    web2py_version = list(map(int, web2py_version_string.split(".")[:3]))
    if web2py_version < list(map(int, REQUIRED_WEB2PY_VERSION.split(".")[:3])):
        raise HTTP(500, f"Requires web2py version {REQUIRED_WEB2PY_VERSION} or newer, not {web2py_version_string}")
except Exception as version_error:
    # Если не удалось проверить версию, пропускаем проверку
    try:
        import logging
        logging.warning(f"Не удалось проверить версию web2py: {str(version_error)}")
    except:
        pass

# -------------------------------------------------------------------------
# if SSL/HTTPS is properly configured and you want all HTTP requests to
# be redirected to HTTPS, uncomment the line below:
# -------------------------------------------------------------------------
# request.requires_https()

# -------------------------------------------------------------------------
# Configuration class (можно переопределить db.uri через private/appconfig.ini или переменные окружения)
# -------------------------------------------------------------------------
class DefaultConfig:
    def get(self, key, default=None):
        defaults = {
            "db.uri": "postgres://smetadoma02:Lenina21@localhost:5432/smetadoma02_db?set search_path=public",
            "db.pool_size": 10,
            "db.migrate": True,
            "app.production": False,
            "host.names": ["*"],
            "smtp.server": "",
            "smtp.sender": "",
            "smtp.login": "",
            "smtp.tls": False,
            "smtp.ssl": False,
            "app.author": "",
            "app.description": "",
            "app.keywords": "",
            "app.generator": "",
            "app.toolbar": False,
            "google.analytics_id": "",
            "scheduler.enabled": False,
            "scheduler.heartbeat": 1,
        }
        return defaults.get(key, default)

configuration = DefaultConfig()

if "GAE_APPLICATION" not in os.environ:
    # ---------------------------------------------------------------------
    # Подключение к базе данных PostgreSQL
    # Формат: postgres://username:password@host:port/database
    # ---------------------------------------------------------------------
    try:
        db = DAL(
            configuration.get("db.uri"),
            pool_size=configuration.get("db.pool_size"),
            migrate=configuration.get("db.migrate"),
            fake_migrate=False,
            check_reserved=["all"]
        )
        # Обработчик ошибок транзакций PostgreSQL
        original_execute = db._adapter.execute
        def safe_execute(*args, **kwargs):
            try:
                return original_execute(*args, **kwargs)
            except Exception as e:
                error_str = str(e)
                error_type = type(e).__name__
                if "duplicatetable" in error_type.lower() or "already exists" in error_str.lower() or ("relation" in error_str.lower() and "already exists" in error_str.lower()):
                    try:
                        db.commit()
                    except:
                        try:
                            db.rollback()
                        except:
                            pass
                    return None
                if "transaction" in error_str.lower() or "aborted" in error_str.lower() or "25P02" in error_str or "InFailedSqlTransaction" in error_type:
                    try:
                        db.rollback()
                        return original_execute(*args, **kwargs)
                    except Exception as retry_err:
                        retry_error_str = str(retry_err)
                        retry_error_type = type(retry_err).__name__
                        if "duplicatetable" in retry_error_type.lower() or "already exists" in retry_error_str.lower():
                            try:
                                db.commit()
                            except:
                                try:
                                    db.rollback()
                                except:
                                    pass
                            return None
                        try:
                            db.rollback()
                        except:
                            pass
                        raise retry_err
                raise
        db._adapter.execute = safe_execute
    except Exception as dal_error:
        error_str = str(dal_error)
        if "already exists" in error_str.lower() or "duplicate" in error_str.lower():
            try:
                db = DAL(
                    configuration.get("db.uri"),
                    pool_size=configuration.get("db.pool_size"),
                    migrate=False,
                    fake_migrate=False,
                    check_reserved=["all"]
                )
            except Exception:
                raise dal_error
        else:
            raise
else:
    # ---------------------------------------------------------------------
    # connect to Google Firestore
    # ---------------------------------------------------------------------
    db = DAL("firestore")
    # ---------------------------------------------------------------------
    # store sessions and tickets there
    # ---------------------------------------------------------------------
    session.connect(request, response, db=db)
    # ---------------------------------------------------------------------
    # or store session in Memcache, Redis, etc.
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db = MEMDB(Client()))
    # ---------------------------------------------------------------------

# -------------------------------------------------------------------------
# by default give a view/generic.extension to all actions from localhost
# none otherwise. a pattern can be "controller/function.extension"
# -------------------------------------------------------------------------
response.generic_patterns = [] 
if request.is_local and not configuration.get("app.production"):
    response.generic_patterns.append("*")

# -------------------------------------------------------------------------
# choose a style for forms
# -------------------------------------------------------------------------
response.formstyle = "bootstrap4_inline"
response.form_label_separator = ""

# -------------------------------------------------------------------------
# (optional) optimize handling of static files
# -------------------------------------------------------------------------
# response.optimize_css = "concat,minify,inline"
# response.optimize_js = "concat,minify,inline"

# -------------------------------------------------------------------------
# (optional) static assets folder versioning
# -------------------------------------------------------------------------
# response.static_version = "0.0.0"

# -------------------------------------------------------------------------
# Here is sample code if you need for
# - email capabilities
# - authentication (registration, login, logout, ... )
# - authorization (role based authorization)
# - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
# - old style crud actions
# (more options discussed in gluon/tools.py)
# -------------------------------------------------------------------------

# host names must be a list of allowed host names (glob syntax allowed)
auth = Auth(db, host_names=configuration.get("host.names"))

# -------------------------------------------------------------------------
# Таблица: Филиалы
# -------------------------------------------------------------------------
db.define_table('branches',
    Field('name', 'string', length=200, required=True, label='Название филиала'),
    Field('address', 'text', label='Адрес филиала'),
    Field('phone', 'string', length=50, label='Телефон филиала'),
    Field('email', 'string', length=100, label='Email филиала'),
    Field('description', 'text', label='Описание'),
    Field('is_active', 'boolean', default=True, label='Активен'),
    Field('sort_order', 'integer', default=0, label='Порядок сортировки'),
    format='%(name)s'
)

# -------------------------------------------------------------------------
# Таблица: Роли пользователей (нужна до auth для связи auth_user -> user_roles)
# -------------------------------------------------------------------------
db.define_table('user_roles',
    Field('name', 'string', length=100, required=True, label='Название роли'),
    Field('description', 'text', label='Описание'),
    Field('sort_order', 'integer', default=0, label='Порядок сортировки'),
    Field('is_active', 'boolean', default=True, label='Активна'),
    format='%(name)s'
)

# -------------------------------------------------------------------------
# create all tables needed by auth, maybe add a list of extra fields
# -------------------------------------------------------------------------
auth.settings.extra_fields["auth_user"] = [
    Field('nic', 'string', length=128, required=True, unique=True, label='Логин'),
    Field('branch_id', 'reference branches', label='Филиал'),
    Field('role_id', 'reference user_roles', label='Роль')
]
try:
    # Откатываем транзакцию перед созданием таблиц auth
    try:
        db.rollback()
    except:
        pass
    auth.define_tables(username=False, signature=False)
    try:
        db.commit()
    except:
        try:
            db.rollback()
        except:
            pass
except Exception as auth_error:
    # Если таблицы auth уже существуют, игнорируем ошибку
    error_str = str(auth_error)
    # Откатываем транзакцию при любой ошибке
    try:
        db.rollback()
    except:
        pass
    if "already exists" in error_str.lower() or "duplicate" in error_str.lower():
        # Таблицы уже существуют, это нормально
        try:
            import logging
            logging.debug(f"Таблицы auth уже существуют: {error_str[:100]}")
        except:
            pass
    elif "transaction" in error_str.lower() or "aborted" in error_str.lower():
        # Ошибка транзакции - пробуем еще раз после rollback
        try:
            db.rollback()
            auth.define_tables(username=False, signature=False)
            try:
                db.commit()
            except:
                try:
                    db.rollback()
                except:
                    pass
        except:
            pass
    else:
        # Другая ошибка - пробрасываем дальше только если это не ошибка транзакции
        pass

# -------------------------------------------------------------------------
# configure email
# -------------------------------------------------------------------------
mail = auth.settings.mailer
mail.settings.server = "logging" if request.is_local else configuration.get("smtp.server")
mail.settings.sender = configuration.get("smtp.sender")
mail.settings.login = configuration.get("smtp.login")
mail.settings.tls = configuration.get("smtp.tls") or False
mail.settings.ssl = configuration.get("smtp.ssl") or False

# -------------------------------------------------------------------------
# configure auth policy
# -------------------------------------------------------------------------
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True
# Вход по полю nic (логин), а не по email
auth.settings.login_userfield = 'nic'
# Не проверять поле входа как email (иначе при вводе nic показывается «неправильный email»)
auth.settings.login_email_validate = False
# После входа — на главную, после выхода — на страницу входа
auth.settings.login_next = lambda: URL('default', 'index')
auth.settings.logout_next = URL('default', 'user', args=['login'])
# Обычный HTTP-редирект (не через JavaScript)
auth.settings.client_side = False
# При неверном логине или пароле показывать одно сообщение (не уточнять, что именно неверно)
auth.settings.login_specify_error = False
auth.messages['invalid_login'] = 'Неправильное имя пользователя или пароль'
auth.messages['login_button'] = 'Войти'
# Отключить регистрацию (вход только по учётным записям из Настроек)
auth.settings.actions_disabled = ['register']

# -------------------------------------------------------------------------  
# read more at http://dev.w3.org/html5/markup/meta.name.html               
# -------------------------------------------------------------------------
response.meta.author = configuration.get("app.author")
response.meta.description = configuration.get("app.description")
response.meta.keywords = configuration.get("app.keywords")
response.meta.generator = configuration.get("app.generator")
response.show_toolbar = configuration.get("app.toolbar")

# -------------------------------------------------------------------------
# your http://google.com/analytics id                                      
# -------------------------------------------------------------------------
response.google_analytics_id = configuration.get("google.analytics_id")

# -------------------------------------------------------------------------
# maybe use the scheduler
# -------------------------------------------------------------------------
if configuration.get("scheduler.enabled"):
    from gluon.scheduler import Scheduler
    scheduler = Scheduler(db, heartbeat=configuration.get("scheduler.heartbeat"))

# -------------------------------------------------------------------------
# Define your tables below (or better in another model file) for example
#
# >>> db.define_table("mytable", Field("myfield", "string"))
#
# Fields can be "string","text","password","integer","double","boolean"
#       "date","time","datetime","blob","upload", "reference TABLENAME"
# There is an implicit "id integer autoincrement" field
# Consult manual for more options, validators, etc.
#
# More API examples for controllers:
#
# >>> db.mytable.insert(myfield="value")
# >>> rows = db(db.mytable.myfield == "value").select(db.mytable.ALL)
# >>> for row in rows: print row.id, row.myfield
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
# CRM система для учета клиентов и позиций номенклатуры деревянных домов
# -------------------------------------------------------------------------
# user_roles определена выше (перед auth) для связи с auth_user

# Таблица: Статусы спецификаций
db.define_table('specification_statuses',
    Field('name', 'string', length=100, required=True, label='Название статуса'),
    Field('description', 'text', label='Описание'),
    Field('sort_order', 'integer', default=0, label='Порядок сортировки'),
    Field('is_active', 'boolean', default=True, label='Активен'),
    format='%(name)s'
)

# Таблица: Следующие шаги
db.define_table('next_steps',
    Field('name', 'string', length=200, required=True, label='Название шага'),
    Field('description', 'text', label='Описание'),
    Field('days', 'integer', default=0, label='Количество дней на выполнение'),
    Field('is_active', 'boolean', default=True, label='Активен'),
    format='%(name)s'
)

# Таблица: Источники лидов
db.define_table('lead_sources',
    Field('name', 'string', length=200, required=True, label='Название источника'),
    Field('is_active', 'boolean', default=True, label='Активен'),
    Field('sort_order', 'integer', default=0, label='Порядок сортировки'),
    format='%(name)s'
)

# Валидаторы для lead_sources
db.lead_sources.name.requires = IS_NOT_EMPTY(error_message='Название источника обязательно для заполнения')

# Таблица: Клиенты
db.define_table('customers',
    Field('name', 'string', length=200, required=True, label='Имя'),
    Field('middle_name', 'string', length=200, label='Отчество'),
    Field('last_name', 'string', length=200, label='Фамилия'),
    Field('full_name', 'string', length=600, writable=False, readable=True, label='ФИО'),
    Field('phone', 'string', length=50, required=True, label='Телефон'),
    Field('email', 'string', length=100, label='Email'),
    Field('address', 'text', required=True, label='Адрес'),
    Field('lead_source_id', 'reference lead_sources', label='Источник лида'),
    Field('link', 'string', length=500, label='Ссылка'),
    Field('notes', 'text', label='Примечания'),
    Field('comments', 'text', label='Комментарии'),
    Field('created_on', 'datetime', default=request.now, writable=False, readable=True),
    Field('modified_on', 'datetime', default=request.now, update=request.now, writable=False, readable=True),
    format='%(name)s'
)

# Обработчики для автоматического вычисления ФИО при вставке и обновлении
def update_full_name_on_insert(fields):
    """Вычисляет ФИО при вставке записи"""
    parts = []
    if fields.get('last_name'):
        parts.append(fields['last_name'])
    if fields.get('name'):
        parts.append(fields['name'])
    if fields.get('middle_name'):
        parts.append(fields['middle_name'])
    fields['full_name'] = ' '.join(parts) if parts else fields.get('name', '')

def update_full_name_on_update(set_obj, fields):
    """Вычисляет ФИО при обновлении записи"""
    # Вычисляем full_name только если изменяются поля name, last_name или middle_name
    if 'name' in fields or 'last_name' in fields or 'middle_name' in fields:
        try:
            # Получаем ID из запроса set_obj
            query = set_obj.query
            rows = db(query).select(db.customers.id, limitby=(0, 1))
            if rows:
                customer_id = rows.first().id
                # Получаем текущие значения из базы
                row = db(db.customers.id == customer_id).select(db.customers.name, db.customers.middle_name, db.customers.last_name).first()
                if row:
                    parts = []
                    last_name = fields.get('last_name', row.last_name)
                    name = fields.get('name', row.name)
                    middle_name = fields.get('middle_name', row.middle_name)
                    if last_name:
                        parts.append(last_name)
                    if name:
                        parts.append(name)
                    if middle_name:
                        parts.append(middle_name)
                    fields['full_name'] = ' '.join(parts) if parts else name or ''
        except Exception:
            # В случае ошибки вычисляем только из fields
            parts = []
            if fields.get('last_name'):
                parts.append(fields['last_name'])
            if fields.get('name'):
                parts.append(fields['name'])
            if fields.get('middle_name'):
                parts.append(fields['middle_name'])
            if parts:
                fields['full_name'] = ' '.join(parts)

db.customers._before_insert.append(update_full_name_on_insert)
db.customers._before_update.append(update_full_name_on_update)

# Таблица: Статусы проектов
db.define_table('project_statuses',
    Field('name', 'string', length=100, required=True, label='Название статуса'),
    Field('description', 'text', label='Описание'),
    Field('sort_order', 'integer', default=0, label='Порядок сортировки'),
    Field('is_active', 'boolean', default=True, label='Активен'),
    format='%(name)s'
)

# Таблица: Проекты
db.define_table('projects',
    Field('name', 'string', length=200, required=True, label='Название проекта'),
    Field('customer_id', 'reference customers', label='Клиент'),
    Field('specification_id', 'integer', label='Спецификация'),  # Будет изменено на reference после определения specifications
    Field('order_id', 'integer', label='Заказ'),  # Будет изменено на reference после определения orders
    Field('project_number', 'string', length=50, unique=True, label='Номер проекта'),
    Field('start_date', 'date', label='Дата начала проекта'),
    Field('end_date', 'date', label='Дата окончания проекта'),
    Field('status_id', 'reference project_statuses', label='Статус проекта'),
    Field('budget', 'decimal(10,2)', default=0, label='Бюджет проекта'),
    Field('description', 'text', label='Описание проекта'),
    Field('notes', 'text', label='Примечания'),
    Field('created_on', 'datetime', default=request.now, writable=False, readable=True),
    Field('modified_on', 'datetime', default=request.now, update=request.now, writable=False, readable=True),
    Field('created_at', 'datetime', default=datetime.datetime.utcnow, writable=False, readable=True, label='Дата создания'),
    Field('updated_at', 'datetime', default=datetime.datetime.utcnow, update=datetime.datetime.utcnow, writable=False, readable=True, label='Дата обновления'),
    Field('status_started_at', 'datetime', default=request.now, label='Дата входа в текущий статус'),
    Field('sla_hours', 'integer', default=None, label='SLA - максимальное время в статусе (часы)'),
    Field('manager_id', 'reference auth_user', label='Ответственный менеджер'),
    format='%(name)s'
)

# Таблица: Спецификации
db.define_table('specifications',
    Field('customer_id', 'reference customers', required=True, label='Клиент'),
    Field('project_id', 'reference projects', label='Проект'),
    Field('status_id', 'reference specification_statuses', required=True, label='Статус'),
    Field('status_changed_on', 'datetime', default=request.now, label='Дата и время изменения статуса'),
    Field('next_step_id', 'reference next_steps', label='Следующий шаг'),
    Field('execution_time', 'integer', label='Время на выполнение (дни)'),
    Field('deadline', 'datetime', label='Дедлайн'),
    Field('description', 'text', label='Описание спецификации'),
    Field('total_amount', 'decimal(10,2)', default=0, label='Общая сумма'),
    Field('created_on', 'datetime', default=request.now, writable=False, readable=True),
    Field('modified_on', 'datetime', default=request.now, update=request.now, writable=False, readable=True),
    format='%(id)s - %(customer_id)s'
)

# Таблица: Заказы
db.define_table('orders',
    Field('specification_id', 'reference specifications', label='Спецификация'),
    Field('project_id', 'reference projects', label='Проект'),
    Field('customer_id', 'reference customers', required=True, label='Клиент'),
    Field('order_number', 'string', length=50, unique=True, required=True, label='Номер заказа'),
    Field('order_date', 'date', default=request.now.date(), label='Дата заказа'),
    Field('total_amount', 'decimal(10,2)', default=0, label='Общая сумма'),
    Field('description', 'text', label='Описание заказа'),
    Field('created_on', 'datetime', default=request.now, writable=False, readable=True),
    Field('modified_on', 'datetime', default=request.now, update=request.now, writable=False, readable=True),
    format='%(order_number)s'
)

# Таблица: Позиции заказа
db.define_table('order_items',
    Field('order_id', 'reference orders', required=True, label='Заказ'),
    Field('item_name', 'string', length=200, required=True, label='Название позиции'),
    Field('quantity', 'decimal(10,2)', default=1, label='Количество'),
    Field('unit', 'string', length=50, default='шт', label='Единица измерения'),
    Field('price', 'decimal(10,2)', default=0, label='Цена за единицу'),
    Field('total', 'decimal(10,2)', default=0, label='Итого'),
    Field('description', 'text', label='Описание'),
    Field('created_on', 'datetime', default=request.now, writable=False, readable=True),
    format='%(item_name)s'
)

# Таблица: Типы позиций номенклатуры
db.define_table('nomenclature_item_types',
    Field('name', 'string', length=100, required=True, unique=True, label='Название типа'),
    Field('description', 'text', label='Описание типа'),
    Field('sort_order', 'integer', default=0, label='Порядок сортировки'),
    Field('is_active', 'boolean', default=True, label='Активен'),
    format='%(name)s'
)

# Таблица: Части дома (parts)
db.define_table('parts',
    Field('name', 'string', length=200, required=True, label='Название'),
    format='%(name)s'
)

# Таблица: Шаблоны обязательных позиций
db.define_table('required_item_templates',
    Field('part_id', 'reference parts', required=True, label='Часть дома'),
    Field('name', 'string', length=200, required=True, label='Название'),
    Field('required_qty', 'decimal(10,2)', default=1, label='Обязательное количество'),
    Field('unit', 'string', length=50, default='шт', label='Единица измерения'),
    format='%(name)s'
)

# Таблица: Позиции спецификации
db.define_table('specification_items',
    Field('specification_id', 'reference specifications', required=True, label='Спецификация'),
    Field('part_id', 'reference parts', label='Часть дома'),
    Field('template_id', 'reference required_item_templates', label='Шаблон обязательной позиции'),
    Field('nomenclature_item_id', 'integer', label='Позиция номенклатуры'),
    Field('item_name', 'string', length=200, required=True, label='Название позиции'),
    Field('quantity', 'decimal(10,2)', default=1, label='Количество'),
    Field('unit', 'string', length=50, default='шт', label='Единица измерения'),
    Field('price', 'decimal(10,2)', default=0, label='Цена за единицу'),
    Field('total', 'decimal(10,2)', default=0, label='Итого'),
    Field('description', 'text', label='Описание'),
    Field('created_on', 'datetime', default=request.now, writable=False, readable=True),
    format='%(item_name)s'
)

# Таблица: Позиции номенклатуры
db.define_table('nomenclature_items',
    Field('item_number', 'string', length=50, unique=True, required=True, label='Номер позиции номенклатуры'),
    Field('item_type_id', 'reference nomenclature_item_types', label='Тип позиции'),
    Field('item_date', 'date', default=request.now.date(), label='Дата позиции'),
    Field('unit', 'string', length=50, default='шт', label='Единица измерения'),
    Field('total_cost', 'decimal(10,2)', default=0, label='Общая стоимость'),
    Field('description', 'text', label='Описание позиции номенклатуры'),
    Field('created_on', 'datetime', default=request.now, writable=False, readable=True),
    Field('modified_on', 'datetime', default=request.now, update=request.now, writable=False, readable=True),
    format='%(item_number)s'
)

# Таблица: Допустимые материалы для обязательной позиции
db.define_table('required_item_materials',
    Field('required_item_template_id', 'reference required_item_templates', required=True, label='Шаблон обязательной позиции'),
    Field('nomenclature_id', 'reference nomenclature_items', required=True, label='Позиция номенклатуры'),
    format='%(id)s'
)

# Таблица: Обязательные позиции в конкретной спецификации
db.define_table('specification_required_items',
    Field('spec_id', 'reference specifications', required=True, label='Спецификация'),
    Field('part_id', 'reference parts', required=True, label='Часть дома'),
    Field('template_id', 'reference required_item_templates', required=True, label='Шаблон обязательной позиции'),
    Field('required_qty', 'decimal(10,2)', default=0, label='Требуемое количество'),
    Field('added_qty', 'decimal(10,2)', default=0, label='Добавленное количество'),
    format='%(id)s'
)

# Таблица: Коммерческие предложения (КП)
db.define_table('commercial_proposals',
    Field('specification_id', 'reference specifications', required=True, label='Спецификация'),
    Field('customer_id', 'reference customers', required=True, label='Клиент'),
    Field('proposal_number', 'string', length=50, unique=True, required=True, label='Номер КП'),
    Field('proposal_date', 'date', default=request.now.date(), label='Дата формирования КП'),
    Field('total_amount', 'decimal(10,2)', default=0, label='Общая сумма'),
    Field('description', 'text', label='Описание КП'),
    Field('status', 'string', length=50, default='draft', label='Статус КП'),  # draft, sent, accepted, rejected
    Field('pdf_path', 'string', length=500, label='Путь к PDF файлу'),
    Field('created_on', 'datetime', default=request.now, writable=False, readable=True),
    Field('modified_on', 'datetime', default=request.now, update=request.now, writable=False, readable=True),
    format='%(proposal_number)s'
)

# Таблица: Позиции коммерческого предложения
db.define_table('commercial_proposal_items',
    Field('proposal_id', 'reference commercial_proposals', required=True, label='КП'),
    Field('item_type_name', 'string', length=100, default='', label='Тип позиции'),
    Field('item_name', 'string', length=200, required=True, label='Название позиции'),
    Field('quantity', 'decimal(10,2)', default=1, label='Количество'),
    Field('unit', 'string', length=50, default='шт', label='Единица измерения'),
    Field('price', 'decimal(10,2)', default=0, label='Цена за единицу'),
    Field('total', 'decimal(10,2)', default=0, label='Итого'),
    Field('description', 'text', label='Описание'),
    Field('created_on', 'datetime', default=request.now, writable=False, readable=True),
    format='%(item_name)s'
)

# Ссылка позиции спецификации на номенклатуру (поле остаётся integer, валидатор проверяет наличие в nomenclature_items)
db.specification_items.nomenclature_item_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.nomenclature_items.id, '%(item_number)s'))
db.specification_items.part_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.parts.id, '%(name)s'))
db.specification_items.template_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.required_item_templates.id, '%(name)s'))
db.nomenclature_items.item_type_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.nomenclature_item_types.id, '%(name)s'))
db.required_item_templates.part_id.requires = IS_IN_DB(db, db.parts.id, '%(name)s')
db.required_item_materials.required_item_template_id.requires = IS_IN_DB(db, db.required_item_templates.id, '%(name)s')
db.required_item_materials.nomenclature_id.requires = IS_IN_DB(db, db.nomenclature_items.id, '%(item_number)s')
db.specification_required_items.spec_id.requires = IS_IN_DB(db, db.specifications.id, '%(id)s')
db.specification_required_items.part_id.requires = IS_IN_DB(db, db.parts.id, '%(name)s')
db.specification_required_items.template_id.requires = IS_IN_DB(db, db.required_item_templates.id, '%(name)s')
db.commercial_proposals.specification_id.requires = IS_IN_DB(db, db.specifications.id, '%(id)s')
db.commercial_proposals.customer_id.requires = IS_IN_DB(db, db.customers.id, '%(name)s')
db.commercial_proposal_items.proposal_id.requires = IS_IN_DB(db, db.commercial_proposals.id, '%(proposal_number)s')
db.commercial_proposal_items.quantity.requires = IS_FLOAT_IN_RANGE(0.01, 1000000)
db.commercial_proposal_items.price.requires = IS_EMPTY_OR(IS_FLOAT_IN_RANGE(0, 10000000))

# -------------------------------------------------------------------------
# Индексы для оптимизации запросов
# -------------------------------------------------------------------------
db.specifications.customer_id.requires = IS_IN_DB(db, db.customers.id, '%(name)s')
db.specifications.project_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.projects.id, '%(name)s'))
db.specifications.status_id.requires = IS_IN_DB(db, db.specification_statuses.id, '%(name)s')
db.specifications.next_step_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.next_steps.id, '%(name)s'))
db.specification_items.specification_id.requires = IS_IN_DB(db, db.specifications.id, '%(id)s')
db.orders.customer_id.requires = IS_IN_DB(db, db.customers.id, '%(name)s')
db.orders.project_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.projects.id, '%(name)s'))
db.orders.specification_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.specifications.id, '%(id)s'))
db.order_items.order_id.requires = IS_IN_DB(db, db.orders.id, '%(order_number)s')
db.projects.customer_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.customers.id, '%(name)s'))
# Обновляем тип полей specification_id и order_id на reference после определения таблиц specifications и orders
db.projects.specification_id.type = db.specifications
db.projects.order_id.type = db.orders
db.projects.specification_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.specifications.id, '%(id)s'))
db.projects.order_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.orders.id, '%(order_number)s'))
db.projects.status_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.project_statuses.id, '%(name)s'))
db.projects.manager_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.auth_user.id, '%(first_name)s %(last_name)s'))
db.auth_user.nic.requires = [IS_NOT_EMPTY(error_message='Укажите логин'), IS_MATCH(r'^\w+$', error_message='Только буквы, цифры и подчёркивание')]
db.auth_user.branch_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.branches.id, '%(name)s'))
db.auth_user.role_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.user_roles.id, '%(name)s'))
db.branches.email.requires = IS_EMPTY_OR(IS_EMAIL())

# -------------------------------------------------------------------------
# Валидаторы для полей
# -------------------------------------------------------------------------
db.customers.email.requires = IS_EMPTY_OR(IS_EMAIL())
db.customers.phone.requires = IS_MATCH('^[\d\s\-\+\(\)]+$', error_message='Неверный формат телефона')
db.customers.lead_source_id.requires = IS_EMPTY_OR(IS_IN_DB(db, db.lead_sources.id, '%(name)s'))
db.specifications.execution_time.requires = IS_EMPTY_OR(IS_INT_IN_RANGE(0, 1000))
db.specification_items.quantity.requires = IS_FLOAT_IN_RANGE(0.01, 1000000)
db.specification_items.price.requires = IS_EMPTY_OR(IS_FLOAT_IN_RANGE(0, 10000000))
db.order_items.quantity.requires = IS_FLOAT_IN_RANGE(0.01, 1000000)
db.order_items.price.requires = IS_EMPTY_OR(IS_FLOAT_IN_RANGE(0, 10000000))
db.projects.budget.requires = IS_EMPTY_OR(IS_FLOAT_IN_RANGE(0, 100000000))

# -------------------------------------------------------------------------
# after defining tables, uncomment below to enable auditing
# -------------------------------------------------------------------------
# auth.enable_record_versioning(db)
