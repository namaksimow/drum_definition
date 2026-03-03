## ml-service (режим mock)

Сервис принимает загруженные аудиофайлы и строит артефакты по ударным:
- PNG с частями waveform по инструментам
- JSON с табулатурой
- PNG/PDF-отчет с ASCII-табулатурой

Текущая реализация использует mock-адаптеры (локальная файловая система + in-memory очередь/репозиторий).
Адаптеры для PostgreSQL/MinIO/RabbitMQ позже подключаются через слой `ports/`.

## Структура проекта

```text
ml-service/
  src/ml_service/
    api/
    worker/
    domain/
    services/
    ports/
    adapters/mock/
  data/
    uploads/
    results/
```

## Запуск

```bash
cd ml-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src uvicorn ml_service.api.main:app --reload
```

## API

- `POST /v1/jobs` (multipart-поле: `file`)
- `GET /v1/jobs/{job_id}`
- `GET /health/live`
- `GET /health/ready`

После `POST /v1/jobs` фоновый mock-worker обрабатывает задачу асинхронно.
