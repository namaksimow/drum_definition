## ml-service (режим mock)

Сервис принимает песни (`mp3/wav`) и выполняет пайплайн:
1. Разделение трека через Spleeter `4stems` (`vocals`, `drums`, `bass`, `other`).
2. Анализ `drums.wav` и выделение событий `kick/snare/hihat`.
3. Построение табулатуры и экспорт артефактов.

Выходные артефакты:
- PNG с частями waveform по инструментам (`parts/{instrument}/...`)
- JSON с табулатурой (`tablature.json`)
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
- `GET /v1/songs` (список локальных песен из папки `songs`)
- `POST /v1/jobs/from-songs/{song_name}` (создать задачу из локальной папки `songs`)
- `GET /v1/jobs/{job_id}`
- `GET /health/live`
- `GET /health/ready`

После `POST /v1/jobs` фоновый mock-worker обрабатывает задачу асинхронно.

## Где лежат результаты

Для задачи с `job_id` результаты сохраняются в:

```text
ml-service/data/results/{job_id}/
  stems/{track_name}/
    vocals.wav
    drums.wav
    bass.wav
    other.wav
  parts/
    kick/*.png
    snare/*.png
    hihat/*.png
  tablature.json
  ascii_tab_report.png
  ascii_tab_report.pdf
```
