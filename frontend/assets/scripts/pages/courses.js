import * as api from "../services/api.js?v=12";
import { initTopAuthWidget } from "../services/top_auth_widget.js?v=8";

const subtitleEl = document.getElementById("coursesSubtitle");
const statusEl = document.getElementById("status");
const searchInput = document.getElementById("courseSearchInput");
const searchBtn = document.getElementById("courseSearchBtn");
const resetBtn = document.getElementById("courseResetBtn");
const addBtn = document.getElementById("courseAddBtn");
const addHint = document.getElementById("courseAddHint");
const listEl = document.getElementById("coursesList");

let authToken = "";
let authUser = null;

function setStatus(message) {
  if (statusEl) statusEl.textContent = message;
}

function setAddHint(message) {
  if (addHint) addHint.textContent = message || "";
}

function getErrorMessage(error) {
  if (!error) return "Unknown error";
  const raw = typeof error.message === "string" ? error.message : String(error);
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.detail === "string") {
      return parsed.detail;
    }
  } catch {
    // no-op
  }
  return raw;
}

function formatCreatedAt(value) {
  if (!value) return "Неизвестно";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("ru-RU", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderCourses(items) {
  if (!listEl) return;
  if (!items.length) {
    listEl.innerHTML = `
      <article class="card">
        <h3 class="card__title">Курсы не найдены</h3>
        <p class="card__text">Попробуй изменить параметры поиска.</p>
      </article>
    `;
    return;
  }

  listEl.innerHTML = items
    .map((course) => {
      const safeTitle = escapeHtml(course.title || "Без названия");
      const safeAuthor = escapeHtml(course.author || "unknown");
      const safeDescription = escapeHtml(course.description || "Описание пока не добавлено.");
      const tags = Array.isArray(course.tags) ? course.tags.map((x) => escapeHtml(x)) : [];
      const tagsText = tags.length ? tags.join(", ") : "без тегов";
      const cover = typeof course.cover_image_path === "string" && course.cover_image_path.trim()
        ? `<img class="card__cover" src="${escapeHtml(course.cover_image_path)}" alt="Обложка курса" loading="lazy" />`
        : "";
      return `
        <article class="card" data-course-id="${course.id}">
          ${cover}
          <h3 class="card__title">${safeTitle}</h3>
          <p class="card__meta">Автор: ${safeAuthor} • Создано: ${formatCreatedAt(course.created_at)} • Обновлено: ${formatCreatedAt(course.updated_at)}</p>
          <p class="card__text">${safeDescription}</p>
          <p class="card__tags">Теги: ${tagsText}</p>
          <div class="card__actions">
            <button class="btn btn--secondary" type="button" data-course-open-id="${course.id}">Открыть курс</button>
          </div>
        </article>
      `;
    })
    .join("");
}

function applyAuthUi() {
  setAddHint("");
  if (!subtitleEl) return;
  if (!authUser) {
    subtitleEl.textContent = "Поиск курсов по названию, автору и тегам.";
    return;
  }
  subtitleEl.textContent = `Поиск курсов. Вход выполнен: ${authUser.nickname || authUser.email}.`;
}

async function loadCourses() {
  const query = searchInput ? searchInput.value.trim() : "";
  try {
    const payload = await api.fetchCourses(query, { limit: 200, offset: 0 });
    const items = Array.isArray(payload.items) ? payload.items : [];
    renderCourses(items);
    setStatus(`Найдено курсов: ${items.length}`);
  } catch (error) {
    renderCourses([]);
    setStatus(`Ошибка загрузки курсов: ${getErrorMessage(error)}`);
  }
}

if (searchBtn) {
  searchBtn.addEventListener("click", () => {
    loadCourses();
  });
}

if (resetBtn) {
  resetBtn.addEventListener("click", () => {
    if (searchInput) searchInput.value = "";
    loadCourses();
  });
}

if (searchInput) {
  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      loadCourses();
    }
  });
}

if (addBtn) {
  addBtn.addEventListener("click", () => {
    setAddHint("");
    if (!authUser || !authToken) {
      setAddHint("чтобы опубликовать курс, станьте автором");
      return;
    }
    if (String(authUser.role || "").toLowerCase() !== "author") {
      setAddHint("чтобы опубликовать курс, станьте автором");
      return;
    }
    window.location.href = "/courses/create";
  });
}

if (listEl) {
  listEl.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;

    const button = target.closest("[data-course-open-id]");
    if (button) {
      const courseId = button.getAttribute("data-course-open-id");
      if (!courseId) return;
      window.location.href = `/courses/${encodeURIComponent(courseId)}`;
      return;
    }

    const card = target.closest(".card[data-course-id]");
    if (!card) return;
    const courseId = card.getAttribute("data-course-id");
    if (!courseId) return;
    window.location.href = `/courses/${encodeURIComponent(courseId)}`;
  });
}

async function init() {
  await initTopAuthWidget({
    onAuthChanged: async ({ token, user }) => {
      authToken = token || "";
      authUser = user || null;
      applyAuthUi();
    },
  });

  await loadCourses();
}

init();
