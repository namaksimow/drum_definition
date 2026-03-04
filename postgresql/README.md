## PostgreSQL Service (Clean Architecture)

В папке `postgresql` теперь отдельный микросервис с чистой архитектурой:

```text
postgresql/
  app/
    domain/                  # доменные ошибки + ORM-модели
    application/             # use-cases и порты
    adapters/                # инфраструктура (async SQLAlchemy gateway)
    presentation/http/       # FastAPI роуты
    bootstrap.py             # композиция зависимостей
    config.py                # настройки
  migrations/
    versions/0001_initial_schema.py
  create_db.sql              # исходная схема
  manage.py                  # create-db / migrate / downgrade / revision
  main.py                    # entrypoint для uvicorn
```

## Что в `create_db.sql`

Схема содержит основные сущности:
- справочники (`roles`, `visibilities`, `status`, `actions`)
- пользователи (`users`)
- контент/курсы/трек/табулатуры
- комментарии/реакции/статистика
- индексы по частым связям

Первая миграция (`0001_initial_schema`) применяет эту схему автоматически.

Сервис рассчитан на асинхронный драйвер `asyncpg`.
Текущие ORM-модели находятся в `app/domain/models.py`.

## Установка

```bash
cd postgresql
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

В `.env` указывай URL в формате:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/drum_definition
```

## Создание БД и миграции

1. Создать базу (если ее еще нет):
```bash
python manage.py create-db
```

2. Применить миграции:
```bash
python manage.py migrate
```

3. Откатить миграции:
```bash
python manage.py downgrade --revision -1
```

4. Создать новую миграцию:
```bash
python manage.py revision -m "add new table"
```

По умолчанию `revision` запускается с `--autogenerate` (берет изменения из `app/domain/models.py`).
Если нужна пустая миграция:

```bash
python manage.py revision -m "manual migration" --empty
```
Примечание: `create-db` также использует `asyncpg`.

## Запуск сервиса

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8090
```

## Роуты

- `GET /health/live` — liveness
- `GET /health/ready` — проверка соединения с БД
- `GET /db/tables` — список таблиц в текущей БД
