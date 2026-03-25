# frontend

Фронтенд реализован как набор статических HTML/CSS/JS файлов и раздается сервисом `backend`.

## Структура

```text
frontend/
  pages/                  # HTML-страницы
  assets/
    styles/               # базовые и page-specific стили
    scripts/              # JS-модули страниц и сервисов
    images/
      reactions/          # иконки реакций
      courses/            # загруженные обложки курсов (локальный fallback)
```

## Как запускать

Отдельного сборщика (`npm`, webpack, vite) нет.
Для корректной работы запускай `backend`, затем открывай:

- `http://127.0.0.1:8080/`

`backend` монтирует `frontend/assets` в `/assets` и отдает страницы через свои роуты.

## Страницы

- `index.html` — сообщество табулатур
- `auth.html` — авторизация/регистрация
- `account.html` — личный кабинет
- `admin.html` — админ-панель
- `create_tablature.html` — создание табулатуры
- `edit_tablatures.html`, `edit_tablature_detail.html` — личная библиотека
- `courses.html`, `course_detail.html`, `course_create.html`, `course_edit.html`, `course_stats.html`

## Иконки реакций

Файлы в `assets/images/reactions/`:
- `comment.svg`
- `like.svg`
- `fire.svg`
- `wow.svg`

Рекомендации:
- формат: `SVG` или `PNG` с прозрачностью;
- размер исходника: около `32x32`;
- без внешних зависимостей внутри SVG.
