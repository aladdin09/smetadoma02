# -*- coding: utf-8 -*-
"""
Общая логика данных для дашбордов (проекты, статусы, суммы).
Используется в default.index и в контроллерах dashboard_*.
"""


def get_status_color(status_name):
    """Цвет Bootstrap для статуса проекта."""
    colors = {
        'Лид': 'primary',
        'Заявка': 'info',
        'Начальный': 'info',
        'Комплектация': 'primary',
        'КП у РОПа': 'info',
        'Исправление КП': 'warning',
        'КП согласовано': 'warning',
        'КП отправлено': 'warning',
        'Заказ оформлен': 'success',
        'В производстве': 'danger',
        'Доставка': 'info',
        'Монтаж': 'primary',
        'Акт подписан': 'success',
        'Закрыт': 'secondary'
    }
    return colors.get(status_name, 'secondary')


# Порядок статусов по id для блока «Проекты по статусам» на главной (названия берутся из БД)
DASHBOARD_STATUS_ORDER = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


def safe_db_query(db, query_func, default_value=None):
    """
    Безопасное выполнение запроса к БД с автоматическим rollback при ошибке
    
    Args:
        db: объект базы данных
        query_func: функция, которая выполняет запрос
        default_value: значение по умолчанию при ошибке
    
    Returns:
        результат запроса или default_value при ошибке
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Откатываем транзакцию перед запросом
            # Делаем это несколько раз, так как rollback сам может вызвать ошибку
            for _ in range(3):
                try:
                    db.rollback()
                    break  # Если rollback успешен, выходим из цикла
                except Exception as rollback_err:
                    # Если rollback вызвал ошибку, пробуем еще раз
                    if attempt < max_retries - 1:
                        continue
                    # Если это последняя попытка, пробуем выполнить запрос без rollback
                    pass
            
            # Выполняем запрос
            result = query_func()
            
            # Коммитим успешный запрос
            try:
                db.commit()
            except Exception as commit_err:
                # Если commit не удался, откатываем
                try:
                    db.rollback()
                except:
                    pass
                # Если это не последняя попытка, пробуем еще раз
                if attempt < max_retries - 1:
                    continue
                return default_value
            
            return result
        except Exception as e:
            error_str = str(e)
            # Если это ошибка транзакции, пробуем откатить и повторить
            if "transaction" in error_str.lower() or "aborted" in error_str.lower():
                # Откатываем транзакцию при ошибке
                for _ in range(3):
                    try:
                        db.rollback()
                        break
                    except:
                        pass
                # Если это не последняя попытка, пробуем еще раз
                if attempt < max_retries - 1:
                    continue
            # Если это другая ошибка или последняя попытка, возвращаем значение по умолчанию
            return default_value
    
    # Если все попытки не удались, возвращаем значение по умолчанию
    return default_value


def get_dashboard_data(db, request, auth=None):
    """
    Возвращает словарь данных для дашборда. Если передан auth и пользователь — менеджер (role_id=3),
    возвращаются только проекты/клиенты/суммы по его проектам (manager_id = user.id).
    auth лучше передавать из контроллера, иначе берётся из current (может быть не тот контекст).
    """
    # Откатываем любые незавершенные транзакции в начале
    try:
        db.rollback()
    except:
        pass

    if auth is None:
        try:
            from gluon import current
            auth = getattr(current, 'auth', None)
        except Exception:
            auth = None
    import project_statuses_service
    import role_helpers
    # Ограничение для менеджера: только проекты, где он ответственный
    manager_project_query = None
    if auth and getattr(auth, 'user', None) and role_helpers.is_manager(auth):
        manager_project_query = db.projects.manager_id == auth.user.id

    try:
        # Получаем статусы с обработкой ошибок через safe_db_query
        all_statuses = safe_db_query(
            db,
            lambda: project_statuses_service.get_all_statuses(db, is_active=True, order_by='sort_order'),
            default_value=[]
        )
        
        if not all_statuses:
            # Если не удалось получить статусы, возвращаем пустые данные
            return dict(
                dashboard_stats=[],
                total_projects=0,
                total_customers=0,
                total_orders=0,
                projects=[],
                all_customers=[],
                all_statuses=[],
                status_colors={},
                project_specification_sums={},
                dashboard_specification_total=0,
                filter_customer='',
                filter_status='',
                filter_name='',
                filter_project_number='',
                error="Не удалось получить статусы проектов"
            )
        # Словарь: id статуса -> запись (поиск по id 1..11, названия из БД)
        status_by_id = {s.id: s for s in all_statuses}
        base_query = manager_project_query if manager_project_query is not None else (db.projects.id > 0)
        dashboard_stats = []
        for status_id in DASHBOARD_STATUS_ORDER:
            status = status_by_id.get(status_id)
            if status is None:
                continue
            q = (db.projects.status_id == status.id) & base_query if manager_project_query else (db.projects.status_id == status.id)
            projects_count = safe_db_query(db, lambda qq=q: db(qq).count(), default_value=0)
            dashboard_stats.append({
                'name': status.name,
                'id': status.id,
                'count': projects_count,
                'color': get_status_color(status.name),
                'sum': 0  # Вычислим ниже после project_specification_sums
            })
        total_projects = safe_db_query(db, lambda: db(base_query).count(), default_value=0)
        # Клиенты: для менеджера — только у которых есть его проекты
        if manager_project_query:
            manager_customer_ids = role_helpers.get_manager_customer_ids(db, auth.user.id)
            total_customers = len(manager_customer_ids) if manager_customer_ids else 0
            manager_project_ids = role_helpers.get_manager_project_ids(db, auth.user.id)
            total_orders = safe_db_query(db, lambda: db(db.orders.project_id.belongs(manager_project_ids)).count(), default_value=0) if manager_project_ids else 0
            all_customers = safe_db_query(db, lambda: db(db.customers.id.belongs(manager_customer_ids)).select(db.customers.id, db.customers.name, orderby=db.customers.name), default_value=[]) if manager_customer_ids else []
        else:
            total_customers = safe_db_query(db, lambda: db(db.customers.id > 0).count(), default_value=0)
            total_orders = safe_db_query(db, lambda: db(db.orders.id > 0).count(), default_value=0)
            all_customers = safe_db_query(db, lambda: db(db.customers.id > 0).select(db.customers.id, db.customers.name, orderby=db.customers.name), default_value=[])
        projects = safe_db_query(
            db,
            lambda: db(base_query).select(
                db.projects.ALL,
                db.customers.ALL,
                db.project_statuses.ALL,
                left=[
                    db.customers.on(db.projects.customer_id == db.customers.id),
                    db.project_statuses.on(db.projects.status_id == db.project_statuses.id)
                ],
                orderby=~db.projects.created_on
            ),
            default_value=[]
        )
        # Получаем статусы для status_colors (используем уже полученные)
        status_colors = {s.id: get_status_color(s.name) for s in all_statuses}
        # Суммы спецификаций по проектам — считаем напрямую; для менеджера только по его проектам
        project_specification_sums = {}
        try:
            spec_query = db.specifications.project_id != None
            rows = db(spec_query).select(db.specifications.project_id, db.specifications.total_amount)
            allowed_project_ids = None
            if manager_project_query:
                allowed_project_ids = role_helpers.get_manager_project_ids(db, auth.user.id)
            for row in rows:
                pid = row.project_id
                if pid:
                    pid = int(pid)
                    if allowed_project_ids is not None and pid not in allowed_project_ids:
                        continue
                    project_specification_sums[pid] = project_specification_sums.get(pid, 0) + float(row.total_amount or 0)
        except Exception:
            project_specification_sums = {}
        dashboard_specification_total = sum(project_specification_sums.values()) if project_specification_sums else 0

        # Суммы по статусам проектов — считаем напрямую (для менеджера base_query уже ограничен)
        for stat in dashboard_stats:
            try:
                q = (db.projects.status_id == stat['id']) & base_query if manager_project_query else (db.projects.status_id == stat['id'])
                project_ids = [int(r.id) for r in db(q).select(db.projects.id)]
                stat['sum'] = sum(project_specification_sums.get(pid, 0) for pid in project_ids if pid)
            except Exception:
                stat['sum'] = 0
        return dict(
            dashboard_stats=dashboard_stats,
            total_projects=total_projects,
            total_customers=total_customers,
            total_orders=total_orders,
            projects=projects,
            all_customers=all_customers,
            all_statuses=all_statuses,
            status_colors=status_colors,
            project_specification_sums=project_specification_sums,
            dashboard_specification_total=dashboard_specification_total,
            filter_customer=request.vars.get('filter_customer', ''),
            filter_status=request.vars.get('filter_status', ''),
            filter_name=request.vars.get('filter_name', ''),
            filter_project_number=request.vars.get('filter_project_number', ''),
        )
    except Exception as e:
        # Откатываем транзакцию при любой ошибке
        try:
            db.rollback()
        except:
            pass
        
        import traceback
        error_traceback = traceback.format_exc()
        # Пытаемся получить хотя бы базовые данные
        try:
            import project_statuses_service
            all_statuses = safe_db_query(
                db,
                lambda: project_statuses_service.get_all_statuses(db, is_active=True, order_by='sort_order'),
                default_value=[]
            )
            status_by_id = {s.id: s for s in all_statuses}
            dashboard_stats = []
            for status_id in DASHBOARD_STATUS_ORDER:
                if status_id in status_by_id:
                    s = status_by_id[status_id]
                    dashboard_stats.append({'name': s.name, 'id': s.id, 'count': 0, 'color': get_status_color(s.name), 'sum': 0})
        except Exception as e2:
            dashboard_stats = []
            all_statuses = []
        return dict(
            dashboard_stats=dashboard_stats,
            total_projects=0,
            total_customers=0,
            total_orders=0,
            projects=[],
            all_customers=[],
            all_statuses=all_statuses if 'all_statuses' in locals() else [],
            status_colors={},
            project_specification_sums={},
            dashboard_specification_total=0,
            filter_customer='',
            filter_status='',
            filter_name='',
            filter_project_number='',
            error=str(e),
            error_traceback=error_traceback,
            error_type=type(e).__name__
        )
