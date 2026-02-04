# -*- coding: utf-8 -*-
"""
Универсальный помощник для формирования хлебных крошек.

Использование в контроллере:
    from breadcrumbs import make_breadcrumbs

    breadcrumbs = make_breadcrumbs([
        ('Главная', URL('default', 'index')),
        ('Раздел', URL('controller', 'action')),
        ('Текущая страница', None),  # или просто ('Текущая страница',)
    ])
    return dict(..., breadcrumbs=breadcrumbs)

В представлении:
    {{if breadcrumbs:}}
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        {{for crumb in breadcrumbs:}}
        {{if crumb['url']:}}
        <li class="breadcrumb-item"><a href="{{=crumb['url']}}">{{=crumb['label']}}</a></li>
        {{else:}}
        <li class="breadcrumb-item active" aria-current="page">{{=crumb['label']}}</li>
        {{pass}}
        {{pass}}
      </ol>
    </nav>
    {{pass}}
"""


def make_breadcrumbs(items):
    """
    Строит список хлебных крошек для передачи в представление.

    :param items: список кортежей (подпись, url) или (подпись,) для текущей страницы.
                  url=None или отсутствие url — текущая (активная) страница.
    :return: список словарей [{'label': str, 'url': str|None}, ...]
    """
    result = []
    for item in items:
        if not item:
            continue
        if len(item) == 1:
            result.append({'label': item[0], 'url': None})
        else:
            label, url = item[0], item[1]
            result.append({'label': label, 'url': url})
    return result
