# minio-service

HTTP-обёртка над MinIO для хранения объектов (`PUT/GET`), которую используют `backend` и `ml-service`.

## Компоненты

1. `minio-server` (бинарник `minio`) — само S3-хранилище.
2. `minio-service` (FastAPI) — HTTP API проекта поверх MinIO.

## Настройка `minio-service`

```bash
cd minio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Переменные в `minio/.env`:

```env
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=drum-media
MINIO_SECURE=false
MINIO_SERVICE_HOST=0.0.0.0
MINIO_SERVICE_PORT=8070
```

## Запуск без Docker

### 1) Запусти MinIO server

```bash
mkdir -p .run/minio-data
MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin \
minio server .run/minio-data --address :9000 --console-address :9001
```

Web-консоль: `http://127.0.0.1:9001`.

### 2) Запусти minio-service

```bash
cd minio
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8070
```

## API

- `GET /health/live`
- `GET /health/ready`
- `PUT /v1/objects/{object_key:path}`
- `GET /v1/objects/{object_key:path}`

## Интеграция

В `backend` и `ml-service`:

```env
MINIO_SERVICE_URL=http://127.0.0.1:8070
```

## Диагностика

- `connection refused 127.0.0.1:9000`: не запущен `minio-server`.
- `Object storage upload failed`: проверь `MINIO_SERVICE_URL` и `/health/ready` сервиса.
