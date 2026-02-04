# Создание таблиц вручную через psql

Если автоматическое создание таблиц через web2py не работает, создайте их вручную через psql.

## Подключение к базе данных:

```bash
psql -h localhost -U smetadoma02 -d smetadoma02_db
```

## Создание таблиц:

Выполните SQL команды ниже. Они создадут все необходимые таблицы.

### 1. Таблица complect_statuses

```sql
CREATE TABLE complect_statuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);
```

### 2. Таблица next_steps

```sql
CREATE TABLE next_steps (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    days INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);
```

### 3. Таблица customers

```sql
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(100),
    address TEXT,
    notes TEXT,
    created_on TIMESTAMP,
    modified_on TIMESTAMP
);
```

### 4. Таблица project_statuses

```sql
CREATE TABLE project_statuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);
```

### 5. Таблица projects

```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    customer_id INTEGER REFERENCES customers(id),
    complect_id INTEGER,
    order_id INTEGER,
    project_number VARCHAR(50) UNIQUE,
    start_date DATE,
    end_date DATE,
    status_id INTEGER REFERENCES project_statuses(id),
    budget DECIMAL(10,2) DEFAULT 0,
    description TEXT,
    notes TEXT,
    created_on TIMESTAMP,
    modified_on TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    status_started_at TIMESTAMP,
    sla_hours INTEGER,
    manager_id INTEGER REFERENCES auth_user(id)
);
```

### 6. Таблица complects

```sql
CREATE TABLE complects (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    project_id INTEGER REFERENCES projects(id),
    status_id INTEGER NOT NULL REFERENCES complect_statuses(id),
    status_changed_on TIMESTAMP,
    next_step_id INTEGER REFERENCES next_steps(id),
    execution_time INTEGER,
    deadline TIMESTAMP,
    description TEXT,
    total_amount DECIMAL(10,2) DEFAULT 0,
    created_on TIMESTAMP,
    modified_on TIMESTAMP
);
```

### 7. Таблица complect_items

```sql
CREATE TABLE complect_items (
    id SERIAL PRIMARY KEY,
    complect_id INTEGER NOT NULL REFERENCES complects(id),
    nomenclature_item_id INTEGER,
    item_name VARCHAR(200) NOT NULL,
    quantity DECIMAL(10,2) DEFAULT 1,
    unit VARCHAR(50) DEFAULT 'шт',
    price DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) DEFAULT 0,
    description TEXT,
    created_on TIMESTAMP
);
```

### 8. Таблица orders

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    complect_id INTEGER REFERENCES complects(id),
    project_id INTEGER REFERENCES projects(id),
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    order_date DATE,
    total_amount DECIMAL(10,2) DEFAULT 0,
    description TEXT,
    created_on TIMESTAMP,
    modified_on TIMESTAMP
);
```

### 9. Таблица order_items

```sql
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    item_name VARCHAR(200) NOT NULL,
    quantity DECIMAL(10,2) DEFAULT 1,
    unit VARCHAR(50) DEFAULT 'шт',
    price DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) DEFAULT 0,
    description TEXT,
    created_on TIMESTAMP
);
```

### 10. Таблица nomenclature_items

```sql
CREATE TABLE nomenclature_items (
    id SERIAL PRIMARY KEY,
    item_number VARCHAR(50) UNIQUE NOT NULL,
    item_date DATE,
    unit VARCHAR(50) DEFAULT 'шт',
    total_cost DECIMAL(10,2) DEFAULT 0,
    description TEXT,
    created_on TIMESTAMP,
    modified_on TIMESTAMP
);
```

### 11. Таблица parts (части дома)

```sql
CREATE TABLE parts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL
);
```

### 12. Таблица required_item_templates (шаблоны обязательных позиций)

```sql
CREATE TABLE required_item_templates (
    id SERIAL PRIMARY KEY,
    part_id INTEGER NOT NULL REFERENCES parts(id),
    name VARCHAR(200) NOT NULL,
    required_qty DECIMAL(10,2) DEFAULT 1,
    unit VARCHAR(50) DEFAULT 'шт'
);
```

### 13. Таблица required_item_materials (допустимые материалы для обязательной позиции)

```sql
CREATE TABLE required_item_materials (
    id SERIAL PRIMARY KEY,
    required_item_template_id INTEGER NOT NULL REFERENCES required_item_templates(id),
    nomenclature_id INTEGER NOT NULL REFERENCES nomenclature_items(id)
);
```

### 14. Таблица specification_required_items (обязательные позиции в конкретной спецификации)

```sql
CREATE TABLE specification_required_items (
    id SERIAL PRIMARY KEY,
    spec_id INTEGER NOT NULL REFERENCES specifications(id),
    part_id INTEGER NOT NULL REFERENCES parts(id),
    template_id INTEGER NOT NULL REFERENCES required_item_templates(id),
    required_qty DECIMAL(10,2) DEFAULT 0,
    added_qty DECIMAL(10,2) DEFAULT 0
);
```

## После создания проверьте:

```sql
\dt
```

Должны появиться все таблицы.

## Примечание:

Таблицы auth_* (auth_user, auth_group и т.д.) создаются автоматически web2py при первом обращении к auth, если они еще не существуют.
