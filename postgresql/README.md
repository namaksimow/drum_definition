# postgresql-service

Сервис бизнес-данных поверх PostgreSQL (FastAPI + SQLAlchemy + Alembic).

Важно: это не сервер PostgreSQL, а отдельный HTTP-сервис, который работает с уже запущенной БД.

## Структура

```text
postgresql/
  app/
    domain/                  # ORM-модели и доменные ошибки
    application/             # use-case слой
    adapters/                # SQLAlchemy gateway
    presentation/http/       # FastAPI роуты
    bootstrap.py             # DI
    config.py                # Settings
  migrations/                # Alembic
  create_db.sql              # SQL-схема
  manage.py                  # create-db / migrate / downgrade / revision
  main.py                    # uvicorn entrypoint
```

## Настройка

```bash
cd postgresql
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Создай `postgresql/.env` и укажи минимум:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@127.0.0.1:5432/drum_definition
APP_HOST=0.0.0.0
APP_PORT=8091
JWT_SECRET_KEY=change-me
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

## Миграции

```bash
cd postgresql
source .venv/bin/activate
python manage.py create-db
python manage.py migrate
```

Дополнительно:

```bash
python manage.py downgrade -r -1
python manage.py revision -m "your_message"
```

Если нужна автогенерация Alembic:

```bash
alembic revision --autogenerate -m "your_message"
```

Примечание: поле `alembic_version.version_num` имеет тип `varchar(32)`, поэтому `revision` делай длиной до `32` символов.

## Запуск

```bash
cd postgresql
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8091
```

## Основные API-группы

- health/db:
  - `GET /health/live`
  - `GET /health/ready`
  - `GET /db/tables`
- auth/profile:
  - `POST /auth/register`, `POST /auth/login`
  - `GET /auth/me`, `PATCH /auth/me`
- community:
  - `GET /community/tablatures`, `GET /community/courses`
  - комментарии/реакции/уроки
- personal (`/me/...`):
  - табулатуры, курсы, уроки, прогресс, заявка на роль автора
- admin (`/admin/...`):
  - пользователи, табулатуры, курсы, комментарии, заявки авторов

Полная спецификация: `http://127.0.0.1:8091/docs`.
