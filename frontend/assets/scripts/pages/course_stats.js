import * as api from "../services/api.js?v=15";
import { initTopAuthWidget } from "../services/top_auth_widget.js?v=12";

const titleEl = document.getElementById("courseTitle");
const subtitleEl = document.getElementById("courseSubtitle");
const statusEl = document.getElementById("status");
const firstVisitorInfoEl = document.getElementById("firstVisitorInfo");
const visitorsListEl = document.getElementById("visitorsList");
const completionsListEl = document.getElementById("completionsList");

let authToken = "";
let authUser = null;
let courseId = null;

function setStatus(message) {
  if (statusEl) statusEl.textContent = message;
}

function getErrorMessage(error) {
  if (!error) return "Неизвестная ошибка";
  const raw = typeof error.message === "string" ? error.message : String(error);
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.detail === "string") return parsed.detail;
  } catch {
    // no-op
  }
  return raw;
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatDateTime(value) {
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

function getCourseIdFromPath() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  const coursesIndex = parts.indexOf("courses");
  if (coursesIndex < 0 || parts.length <= coursesIndex + 2) return null;
  const rawId = Number(parts[coursesIndex + 1]);
  if (!Number.isInteger(rawId) || rawId <= 0) return null;
  return rawId;
}

function renderVisitors(items) {
  if (!firstVisitorInfoEl || !visitorsListEl) return;
  if (!items.length) {
    firstVisitorInfoEl.textContent = "Пока нет данных о посещениях курса.";
    visitorsListEl.innerHTML = `
      <article class="stat-row">
        <p class="stat-row__main">Посещений пока нет</p>
        <p class="stat-row__meta">-</p>
      </article>
    `;
    return;
  }

  const first = items[0];
  firstVisitorInfoEl.textContent = `Первый посетитель: ${first.user_name} (${formatDateTime(first.first_visit_at)})`;

  visitorsListEl.innerHTML = items
    .map(
      (item) => `
        <article class="stat-row">
          <p class="stat-row__main">${escapeHtml(item.user_name || "неизвестно")}</p>
          <p class="stat-row__meta">${formatDateTime(item.first_visit_at)}</p>
        </article>
      `
    )
    .join("");
}

function renderCompletions(items) {
  if (!completionsListEl) return;
  if (!items.length) {
    completionsListEl.innerHTML = `
      <article class="stat-row">
        <p class="stat-row__main">Нет данных о прохождении уроков</p>
        <p class="stat-row__meta">-</p>
      </article>
    `;
    return;
  }

  completionsListEl.innerHTML = items
    .map(
      (item) => `
        <article class="stat-row">
          <p class="stat-row__main">${escapeHtml(item.user_name || "неизвестно")} • ${escapeHtml(item.lesson_title || "Без названия урока")}</p>
          <p class="stat-row__meta">${formatDateTime(item.completed_at)}</p>
        </article>
      `
    )
    .join("");
}

async function loadStatistics() {
  if (!courseId) return;

  if (!authToken || !authUser) {
    if (titleEl) titleEl.textContent = `Курс #${courseId}`;
    if (subtitleEl) subtitleEl.textContent = "Нужен вход под автором курса.";
    renderVisitors([]);
    renderCompletions([]);
    setStatus("Для просмотра статистики войди в аккаунт автора.");
    return;
  }

  if (String(authUser.role || "").toLowerCase() !== "author") {
    if (titleEl) titleEl.textContent = `Курс #${courseId}`;
    if (subtitleEl) subtitleEl.textContent = "Статистика доступна только автору курса.";
    renderVisitors([]);
    renderCompletions([]);
    setStatus("Только пользователь с ролью автора может смотреть статистику.");
    return;
  }

  try {
    const payload = await api.fetchPersonalCourseStats(authToken, courseId);
    const stats = payload && payload.stats ? payload.stats : {};
    const visitors = Array.isArray(stats.visitors) ? stats.visitors : [];
    const completions = Array.isArray(stats.lesson_completions) ? stats.lesson_completions : [];

    if (titleEl) titleEl.textContent = stats.course_title || `Курс #${courseId}`;
    if (subtitleEl) {
      subtitleEl.textContent = `Статистика курса: посещения и прохождение уроков`;
    }

    renderVisitors(visitors);
    renderCompletions(completions);
    setStatus(`Посещений: ${visitors.length} • Записей по прохождению уроков: ${completions.length}`);
  } catch (error) {
    renderVisitors([]);
    renderCompletions([]);
    setStatus(`Ошибка загрузки статистики: ${getErrorMessage(error)}`);
  }
}

async function init() {
  courseId = getCourseIdFromPath();
  if (!courseId) {
    setStatus("Некорректный id курса.");
    return;
  }

  await initTopAuthWidget({
    onAuthChanged: async ({ token, user }) => {
      authToken = token || "";
      authUser = user || null;
      await loadStatistics();
    },
  });
}

init();
