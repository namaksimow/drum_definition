import * as api from "../services/api.js?v=17";
import { initTopAuthWidget } from "../services/top_auth_widget.js?v=8";

const subtitleEl = document.getElementById("subtitle");
const statusEl = document.getElementById("status");
const requestsListEl = document.getElementById("requestsList");
const statusFilterEl = document.getElementById("statusFilter");
const refreshBtn = document.getElementById("refreshBtn");

const requestDetailPanelEl = document.getElementById("requestDetailPanel");
const requestDetailContentEl = document.getElementById("requestDetailContent");
const requestDetailMetaEl = document.getElementById("requestDetailMeta");
const requestDetailMessageEl = document.getElementById("requestDetailMessage");
const rejectMessageInput = document.getElementById("rejectMessageInput");
const approveRequestBtn = document.getElementById("approveRequestBtn");
const rejectRequestBtn = document.getElementById("rejectRequestBtn");

let authToken = "";
let authUser = null;
let requests = [];
let selectedRequestId = null;

function setStatus(message) {
  if (statusEl) statusEl.textContent = message;
}

function getErrorMessage(error) {
  if (!error) return "Unknown error";
  const raw = typeof error.message === "string" ? error.message : String(error);
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.detail === "string") return parsed.detail;
  } catch {
    // no-op
  }
  return raw;
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

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function isAdmin() {
  return Boolean(authUser && String(authUser.role || "").toLowerCase() === "admin");
}

function setDetailVisible(visible) {
  if (requestDetailPanelEl) {
    requestDetailPanelEl.classList.toggle("is-hidden", !visible);
  }
  if (requestDetailContentEl) {
    requestDetailContentEl.classList.toggle("is-hidden", !visible);
  }
}

function findRequestById(requestId) {
  return requests.find((item) => String(item.id) === String(requestId)) || null;
}

function renderRequestsList() {
  if (!requestsListEl) return;
  if (!requests.length) {
    requestsListEl.innerHTML = `
      <article class="card">
        <h3 class="card__title">Заявок нет</h3>
        <p class="card__meta">По выбранному фильтру записи не найдены.</p>
      </article>
    `;
    return;
  }

  requestsListEl.innerHTML = requests
    .map((item) => {
      const selected = String(item.id) === String(selectedRequestId);
      const messagePreview = String(item.message || "").trim().slice(0, 120);
      const suffix = String(item.message || "").trim().length > 120 ? "..." : "";
      return `
        <article class="card ${selected ? "card--selected" : ""}" data-request-id="${item.id}">
          <h3 class="card__title">Заявка #${item.id} • ${escapeHtml(item.user_nickname || item.user_email || "unknown")}</h3>
          <p class="card__meta">Email: ${escapeHtml(item.user_email || "-")}</p>
          <p class="card__meta">Статус: ${escapeHtml(item.status || "pending")} • Создана: ${formatDateTime(item.created_at)}</p>
          <p class="card__text">${escapeHtml(messagePreview)}${suffix}</p>
        </article>
      `;
    })
    .join("");
}

function renderRequestDetails() {
  const selected = selectedRequestId ? findRequestById(selectedRequestId) : null;
  if (!selected) {
    setDetailVisible(false);
    return;
  }

  setDetailVisible(true);
  if (requestDetailMetaEl) {
    requestDetailMetaEl.textContent =
      `Заявка #${selected.id} • Пользователь: ${selected.user_nickname || selected.user_email || "-"} • ` +
      `Статус: ${selected.status || "pending"} • ` +
      `Создана: ${formatDateTime(selected.created_at)} • Обновлена: ${formatDateTime(selected.updated_at)}`;
  }
  if (requestDetailMessageEl) {
    requestDetailMessageEl.textContent = String(selected.message || "").trim() || "-";
  }
  if (rejectMessageInput) {
    rejectMessageInput.value = String(selected.admin_message || "");
  }
}

async function loadRequests() {
  if (!authToken || !isAdmin()) {
    if (subtitleEl) subtitleEl.textContent = "Доступно только администратору.";
    requests = [];
    selectedRequestId = null;
    renderRequestsList();
    renderRequestDetails();
    setStatus("Войди под пользователем с ролью admin.");
    return;
  }

  const statusFilter = statusFilterEl ? String(statusFilterEl.value || "pending") : "pending";
  try {
    const payload = await api.fetchAdminAuthorRoleRequests(authToken, {
      status: statusFilter || "pending",
      limit: 200,
      offset: 0,
    });
    requests = Array.isArray(payload.items) ? payload.items : [];
    if (subtitleEl) subtitleEl.textContent = `Администратор: ${authUser.nickname || authUser.email}`;

    if (!requests.length) {
      selectedRequestId = null;
    } else if (!findRequestById(selectedRequestId)) {
      selectedRequestId = null;
    }

    renderRequestsList();
    renderRequestDetails();
    setStatus(`Загружено заявок: ${requests.length}`);
  } catch (error) {
    requests = [];
    selectedRequestId = null;
    renderRequestsList();
    renderRequestDetails();
    setStatus(`Ошибка загрузки заявок: ${getErrorMessage(error)}`);
  }
}

if (refreshBtn) {
  refreshBtn.addEventListener("click", () => {
    loadRequests();
  });
}

if (statusFilterEl) {
  statusFilterEl.addEventListener("change", () => {
    loadRequests();
  });
}

if (requestsListEl) {
  requestsListEl.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const card = target.closest(".card[data-request-id]");
    if (!card) return;
    const requestId = card.getAttribute("data-request-id");
    if (!requestId) return;
    selectedRequestId = requestId;
    renderRequestsList();
    renderRequestDetails();
  });
}

if (approveRequestBtn) {
  approveRequestBtn.addEventListener("click", async () => {
    if (!authToken || !isAdmin()) return;
    const selected = selectedRequestId ? findRequestById(selectedRequestId) : null;
    if (!selected) {
      setStatus("Сначала выбери заявку.");
      return;
    }
    try {
      approveRequestBtn.disabled = true;
      if (rejectRequestBtn) rejectRequestBtn.disabled = true;
      await api.updateAdminAuthorRoleRequest(authToken, selected.id, "approved");
      setStatus(`Заявка #${selected.id} одобрена. Пользователь получил роль author.`);
      await loadRequests();
    } catch (error) {
      setStatus(`Ошибка обновления заявки: ${getErrorMessage(error)}`);
    } finally {
      approveRequestBtn.disabled = false;
      if (rejectRequestBtn) rejectRequestBtn.disabled = false;
    }
  });
}

if (rejectRequestBtn) {
  rejectRequestBtn.addEventListener("click", async () => {
    if (!authToken || !isAdmin()) return;
    const selected = selectedRequestId ? findRequestById(selectedRequestId) : null;
    if (!selected) {
      setStatus("Сначала выбери заявку.");
      return;
    }
    const reason = rejectMessageInput ? rejectMessageInput.value.trim() : "";
    if (!reason) {
      setStatus("Для отклонения нужно заполнить сообщение причины.");
      return;
    }
    try {
      rejectRequestBtn.disabled = true;
      if (approveRequestBtn) approveRequestBtn.disabled = true;
      await api.updateAdminAuthorRoleRequest(authToken, selected.id, "rejected", reason);
      setStatus(`Заявка #${selected.id} отклонена.`);
      await loadRequests();
    } catch (error) {
      setStatus(`Ошибка обновления заявки: ${getErrorMessage(error)}`);
    } finally {
      rejectRequestBtn.disabled = false;
      if (approveRequestBtn) approveRequestBtn.disabled = false;
    }
  });
}

async function init() {
  await initTopAuthWidget({
    onAuthChanged: async ({ token, user }) => {
      authToken = token || "";
      authUser = user || null;
      await loadRequests();
    },
  });
}

init();
