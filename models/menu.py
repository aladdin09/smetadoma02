# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

# ----------------------------------------------------------------------------------------------------------------------
# this is the main application menu add/remove items as required
# ----------------------------------------------------------------------------------------------------------------------

response.menu = [
    ('Главная', False, URL('default', 'index'), []),
    ('Дашборды', False, '#', [
        ('Главная', False, URL('default', 'index')),
        ('Главный (Gentelella)', False, URL('dashboard_main', 'index_gentelella')),
        ('Главный (Gentelella B5)', False, URL('dashboard_main', 'index_gentelella_bs5')),
        ('Главный (DeskApp)', False, URL('dashboard_main', 'index_deskapp')),
        ('Аналитика', False, URL('dashboard_analytics', 'index')),
        ('Обзор', False, URL('dashboard_overview', 'index')),
    ]),
    (T('Номенклатура'), False, URL('nomenclature_items', 'list'), []),
    (T('Настройки'), False, '#', [
        (T('Статусы комплектов'), False, URL('complect_statuses', 'list')),
        (T('Статусы проектов'), False, URL('project_statuses', 'list')),
        (T('Типы позиций номенклатуры'), False, URL('nomenclature_item_types', 'list')),
    ])
]
