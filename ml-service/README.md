# ml-service

Сервис обработки аудио для генерации табулатур ударных.

Основной пайплайн:
1. принять MP3;
2. выделить инструменты (Spleeter);
3. анализ ударных (librosa + постобработка пиков);
4. собрать JSON табулатуры и PDF;
5. сохранить результаты и обновить статус задачи.

## Архитектура

```text
ml-service/
  src/ml_service/
    api/                  # FastAPI API
    worker/               # фоновый воркер
    services/             # бизнес-логика задач
    domain/               # доменные сущности
    adapters/queue/       # HTTP-клиент rabbitmq-service
    adapters/minio/       # HTTP-клиент minio-service
    adapters/mock/        # in-memory адаптеры для dev/tests
  data/
    uploads/
    results/
```

## Зависимости

- `postgresql-service` (хранение метаданных задач/табулатур)
- `rabbitmq-service` + RabbitMQ broker (очередь)
- опционально `minio-service` + `minio-server` (хранение аудио в объектном хранилище)

## Настройки (`ml-service/.env`)

Ключевые переменные:
- `DATABASE_URL=postgresql+asyncpg://.../drum_definition`
- `RABBITMQ_SERVICE_URL=http://127.0.0.1:8090`
- `RABBITMQ_SERVICE_TIMEOUT_SEC=10.0`
- `MINIO_SERVICE_URL=http://127.0.0.1:8070` (опционально)
- `ML_SERVICE_RUN_WORKER_IN_API=false`
- `ML_SERVICE_DATA_DIR=...` (опционально)
- `ML_SERVICE_SONGS_DIR=...` (опционально)

Если `RABBITMQ_SERVICE_URL` не задан, используется `MockQueue`.

## Запуск вручную

```bash
cd ml-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

API:

```bash
cd ml-service
source .venv/bin/activate
PYTHONPATH=src uvicorn ml_service.api.main:app --reload --host 0.0.0.0 --port 8000
```

Worker (отдельный процесс):

```bash
cd ml-service
source .venv/bin/activate
PYTHONPATH=src python -m ml_service.worker.main
```

## API

- `GET /health/live`
- `GET /health/ready`
- `POST /v1/jobs` (multipart `file`, опционально `user_id`, `tablature_name`)
- `GET /v1/jobs`
- `GET /v1/jobs/{job_id}`
- `GET /v1/jobs/{job_id}/tablature`
- `GET /v1/jobs/{job_id}/pdf`
- `GET /v1/songs`
- `POST /v1/jobs/from-songs/{song_name}`

## Где лежат результаты

По умолчанию локально:

```text
ml-service/data/results/{job_id}/
  stems/
  parts/
  tablature.json
  ascii_tab_report.png
  ascii_tab_report.pdf
```

Если задан `MINIO_SERVICE_URL`, входной файл задачи сохраняется в объектном хранилище.

## Диагностика

- Ошибка `Queue publish failed ... Not Found`:
  - `RABBITMQ_SERVICE_URL` указывает не на тот сервис (должен быть `rabbitmq-service`).
- Задачи застревают в `queued`:
  - не запущен worker.
- Ошибки object storage:
  - проверь доступность `minio-service` (`8070`) и `minio-server` (`9000`).
