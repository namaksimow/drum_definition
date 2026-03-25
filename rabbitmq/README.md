# rabbitmq-service

HTTP-обёртка над RabbitMQ. Используется `ml-service` для публикации и чтения задач.

## Компоненты

1. RabbitMQ broker (`amqp://...`) — отдельный процесс.
2. `rabbitmq-service` (FastAPI) — HTTP API проекта для очереди задач.

## Настройка

```bash
cd rabbitmq
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Переменные:

```env
RABBITMQ_URL=amqp://guest:guest@127.0.0.1:5672/
RABBITMQ_QUEUE_NAME=ml.jobs
RABBITMQ_PREFETCH_COUNT=1
RABBITMQ_CONNECT_TIMEOUT_SEC=10.0
RABBITMQ_SERVICE_HOST=0.0.0.0
RABBITMQ_SERVICE_PORT=8090
```

## Запуск broker (macOS + Homebrew)

```bash
brew install rabbitmq
brew services start rabbitmq
rabbitmq-diagnostics ping
```

Примечание: команда именно `brew services`, не `brew service`.

## Запуск rabbitmq-service

```bash
cd rabbitmq
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8090
```

## API

- `GET /health/live`
- `GET /health/ready`
- `POST /v1/jobs` (body: `{ "job_id": "..." }`)
- `GET /v1/jobs/consume?timeout_sec=...`

## Интеграция с ml-service

В `ml-service/.env`:

```env
RABBITMQ_SERVICE_URL=http://127.0.0.1:8090
RABBITMQ_SERVICE_TIMEOUT_SEC=10.0
```

## Опционально: GUI RabbitMQ

```bash
rabbitmq-plugins enable rabbitmq_management
```

После этого UI доступен по `http://127.0.0.1:15672` (`guest/guest` локально).
