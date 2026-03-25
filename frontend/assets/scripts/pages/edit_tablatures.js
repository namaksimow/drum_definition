import * as api from "../services/api.js?v=9";
import { initTopAuthWidget } from "../services/top_auth_widget.js?v=12";

const authGuard = document.getElementById("authGuard");
const editorContent = document.getElementById("editorContent");
const statusEl = document.getElementById("status");
const listEl = document.getElementById("list");
const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");
const resetBtn = document.getElementById("resetBtn");

let authToken = "";

function ensureCoursesMenuButton() {
  const menu = document.querySelector(".menu");
  if (!menu) return;
  const existing = menu.querySelector('a.menu__btn[href="/courses"]');
  if (existing) return;

  const link = document.createElement("a");
  link.className = "menu__btn";
  link.href = "/courses";
  link.textContent = "Курсы";
  menu.appendChild(link);
}

function setStatus(message) {
  if (statusEl) statusEl.textContent = message;
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

function renderList(items) {
  if (!listEl) return;
  if (!items.length) {
    listEl.innerHTML = `
      <article class="card">
        <h3 class="card__title">Пока пусто</h3>
        <p class="card__text">У тебя пока нет сохраненных табулатур.</p>
      </article>
    `;
    return;
  }
  listEl.innerHTML = items
    .map(
      (item) => `
        <article class="card">
          <h3 class="card__title">#${item.id} • ${item.track_file_name || "Без названия"}</h3>
          <p class="card__text">Автор: ${item.author || "неизвестно"}</p>
          <p class="card__meta">Создано: ${formatCreatedAt(item.created_at)}</p>
          <div class="card__actions">
            <button class="btn btn--primary" type="button" data-open-id="${item.id}">Редактировать</button>
          </div>
        </article>
      `
    )
    .join("");
}

async function loadList() {
  if (!authToken) return;
  const query = searchInput && searchInput.value ? searchInput.value.trim() : "";
  try {
    const items = [];
    const pageLimit = 200;
    let offset = 0;
    while (true) {
      const payload = await api.fetchPersonalTablatures(authToken, query, {
        limit: pageLimit,
        offset,
      });
      const chunk = Array.isArray(payload.items) ? payload.items : [];
      items.push(...chunk);
      if (chunk.length < pageLimit) break;
      offset += pageLimit;
    }
    renderList(items);
    setStatus(`Найдено табулатур: ${items.length}`);
  } catch (error) {
    setStatus(`Ошибка загрузки: ${error && error.message ? error.message : String(error)}`);
  }
}

if (searchBtn) {
  searchBtn.addEventListener("click", () => loadList());
}

if (resetBtn) {
  resetBtn.addEventListener("click", () => {
    if (searchInput) searchInput.value = "";
    loadList();
  });
}

if (searchInput) {
  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") loadList();
  });
}

if (listEl) {
  listEl.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const button = target.closest("[data-open-id]");
    if (!button) return;
    const id = button.getAttribute("data-open-id");
    if (!id) return;
    window.location.href = `/edit/tablature/${encodeURIComponent(id)}`;
  });
}

async function init() {
  ensureCoursesMenuButton();
  await initTopAuthWidget({
    onAuthChanged: async ({ token, user }) => {
      authToken = token || "";
      if (!user || !authToken) {
        if (authGuard) authGuard.classList.remove("is-hidden");
        if (editorContent) editorContent.classList.add("is-hidden");
        setStatus("Нужна авторизация.");
        return;
      }
      if (authGuard) authGuard.classList.add("is-hidden");
      if (editorContent) editorContent.classList.remove("is-hidden");
      await loadList();
    },
  });
}

init();
