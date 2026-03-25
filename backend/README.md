# backend

HTTP-шлюз проекта:
- отдает фронтенд-страницы и статику (`frontend/`);
- проксирует бизнес-запросы в `postgresql-service`;
- отправляет задачи обработки аудио в `ml-service`;
- работает с `minio-service` для медиа (обложки курсов).

## Структура

```text
backend/
  backend_app/
    domain/         # доменные модели/ошибки
    application/    # use-case слой
    adapters/       # HTTP-адаптеры к внешним сервисам
    presentation/   # FastAPI роуты
    bootstrap.py    # DI-контейнер
    config.py       # настройки
    main.py         # create_app()
  main.py           # entrypoint для uvicorn
```

## Зависимости

- `ml-service` (`ML_SERVICE_URL`)
- `postgresql-service` (`POSTGRES_SERVICE_URL`)
- опционально `minio-service` (`MINIO_SERVICE_URL`)

## Настройки окружения

- `ML_SERVICE_URL` (по умолчанию `http://127.0.0.1:8000`)
- `POSTGRES_SERVICE_URL` (по умолчанию `http://127.0.0.1:8090`)
- `BACKEND_HTTP_TIMEOUT_SEC` (по умолчанию `120.0`)
- `MINIO_SERVICE_URL` (по умолчанию `http://127.0.0.1:8070`)

Если запускаешь через `scripts/dev_services.sh`, переменные подставляются автоматически.

## Запуск вручную

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

POSTGRES_SERVICE_URL=http://127.0.0.1:8091 \
ML_SERVICE_URL=http://127.0.0.1:8000 \
MINIO_SERVICE_URL=http://127.0.0.1:8070 \
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

## Основные роуты

UI-страницы:
- `GET /`
- `GET /auth`
- `GET /account`
- `GET /admin`
- `GET /create`
- `GET /edit`
- `GET /edit/tablature/{tablature_id}`
- `GET /courses`, `GET /courses/create`, `GET /courses/edit/{course_id}`, `GET /courses/{course_id}`

API:
- `POST /api/upload`
- `GET /api/jobs/{job_id}`
- `GET /api/tablature?job_id=...`
- `GET /api/pdf?job_id=...`
- `POST /api/auth/register`, `POST /api/auth/login`, `GET/PATCH /api/auth/me`
- `GET /api/community/...`
- `GET/POST/PATCH/DELETE /api/personal/...`
- `GET/PATCH/DELETE /api/admin/...`
- `POST /api/courses/cover`, `GET /api/media/{object_key:path}`
- `GET /health`

Полная спецификация доступна в `http://127.0.0.1:8080/docs`.
