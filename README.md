# Drum Definition

Микросервисная система для:
- загрузки аудио и генерации табулатур ударных;
- публикации табулатур и курсов;
- работы личного кабинета, ролей `user/author/admin`;
- хранения медиа в MinIO;
- асинхронной очереди задач через RabbitMQ.

## Сервисы

| Сервис | Порт (dev) | Назначение |
|---|---:|---|
| `backend` | `8080` | Основной HTTP API + раздача фронтенда |
| `ml-service` API | `8000` | Приём задач обработки аудио |
| `ml-service` worker | - | Фоновая обработка задач |
| `postgresql-service` | `8091` | Бизнес-API поверх PostgreSQL |
| `rabbitmq-service` | `8090` | HTTP-обёртка над RabbitMQ |
| `minio-service` | `8070` | HTTP-обёртка над MinIO |
| `minio-server` | `9000` (`9001` console) | S3-совместимое объектное хранилище |

## Быстрый старт

### 1) Требования

- Python `3.8+`
- установленный и запущенный PostgreSQL
- установленный и запущенный RabbitMQ broker
- установленный бинарник `minio` (для `minio-server`)

### 2) Установка зависимостей по сервисам

```bash
for svc in backend postgresql ml-service minio rabbitmq; do
  (
    cd "$svc"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
  )
done
```

### 3) Настройка `.env`

Минимально проверь:
- `postgresql/.env` -> `DATABASE_URL=postgresql+asyncpg://.../drum_definition`
- `ml-service/.env` -> `DATABASE_URL=...`, `RABBITMQ_SERVICE_URL=http://127.0.0.1:8090`

Опционально:
- `ml-service/.env` -> `MINIO_SERVICE_URL=http://127.0.0.1:8070`
- `minio/.env` и `rabbitmq/.env` можно создать на базе `.env.example`

### 4) Запуск всех сервисов одной командой

```bash
bash scripts/dev_services.sh up
```

Скрипт поднимает:
- `postgresql-service` (`8091`)
- `rabbitmq-service` (`8090`)
- `minio-server` (`9000`, console `9001`)
- `minio-service` (`8070`)
- `ml-api` (`8000`)
- `ml-worker`
- `backend` (`8080`)

### 5) Проверка

```bash
bash scripts/dev_services.sh status
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8091/health/live
curl http://127.0.0.1:8090/health/live
curl http://127.0.0.1:8070/health/live
```

Открой приложение: `http://127.0.0.1:8080/`.

## Управление сервисами

```bash
bash scripts/dev_services.sh logs
bash scripts/dev_services.sh logs backend
bash scripts/dev_services.sh restart
bash scripts/dev_services.sh down
bash scripts/dev_services.sh down --keep-minio-server
```

Примечание: обычный `down` останавливает и `minio-server` тоже.

## Тесты

```bash
pytest
```

Покрытие (пример):

```bash
pytest --cov=backend/backend_app --cov=postgresql/app --cov=ml-service/src/ml_service --cov-report=term-missing
```

## Где смотреть детали

- [backend/README.md](backend/README.md)
- [frontend/README.md](frontend/README.md)
- [postgresql/README.md](postgresql/README.md)
- [ml-service/README.md](ml-service/README.md)
- [minio/README.md](minio/README.md)
- [rabbitmq/README.md](rabbitmq/README.md)

## Частые проблемы

- `ML service upload error: Internal Server Error`
  - обычно не доступен `rabbitmq-service` или не запущен `ml-worker`.
- `Queue publish failed ... Not Found`
  - проверь `RABBITMQ_SERVICE_URL`, должен вести на `rabbitmq-service` (`http://127.0.0.1:8090`).
- `Object storage upload failed ... connection refused 127.0.0.1:9000`
  - не запущен `minio-server`.
- миграции Alembic падают на `value too long for type character varying(32)`
  - строка `revision` в миграции должна быть не длиннее `32` символов.
