# -*- coding: utf-8 -*-
"""
Хелпер хлебных крошек для использования в контроллерах.
Импорт из modules избегает конфликта "No module named applications.adminlte5.modules.models"
при импорте из models после import projects_service.
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
