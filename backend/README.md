## Backend (Clean Architecture)

Бэкенд разделен на слои:

```text
backend/
  backend_app/
    domain/         # модели и доменные ошибки
    application/    # use-cases + порты
    adapters/       # HTTP-клиент к ml-service и файловый адаптер фронтенда
    presentation/   # FastAPI-роуты и маппинг ошибок
    bootstrap.py    # композиция зависимостей
    main.py         # create_app()
  main.py           # тонкая входная точка для uvicorn
```

## Запуск

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

## Роуты

- `GET /` — HTML страница фронтенда
- `POST /api/upload` — загрузка `mp3/wav` в `ml-service`
- `GET /api/pdf?job_id=...` — получение готового PDF для существующего `job_id`
- `GET /health` — health-check
