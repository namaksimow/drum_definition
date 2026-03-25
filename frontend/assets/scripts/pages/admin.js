import * as api from "../services/api.js?v=22";
import { initTopAuthWidget } from "../services/top_auth_widget.js?v=12";

const subtitleEl = document.getElementById("subtitle");
const statusEl = document.getElementById("status");
const requestsListEl = document.getElementById("requestsList");
const statusFilterEl = document.getElementById("statusFilter");
const refreshBtn = document.getElementById("refreshBtn");
const adminTablaturesListEl = document.getElementById("adminTablaturesList");
const adminCoursesListEl = document.getElementById("adminCoursesList");
const adminUsersListEl = document.getElementById("adminUsersList");

const requestDetailPanelEl = document.getElementById("requestDetailPanel");
const requestDetailMetaEl = document.getElementById("requestDetailMeta");
const requestDetailMessageEl = document.getElementById("requestDetailMessage");
const rejectMessageInput = document.getElementById("rejectMessageInput");
const approveRequestBtn = document.getElementById("approveRequestBtn");
const rejectRequestBtn = document.getElementById("rejectRequestBtn");
const requestModalBackdrop = document.getElementById("requestModalBackdrop");
const closeRequestModalBtn = document.getElementById("closeRequestModalBtn");
const userDetailPanelEl = document.getElementById("userDetailPanel");
const userDetailMetaEl = document.getElementById("userDetailMeta");
const userEditEmailInput = document.getElementById("userEditEmailInput");
const userEditNicknameInput = document.getElementById("userEditNicknameInput");
const userEditRoleSelect = document.getElementById("userEditRoleSelect");
const saveUserBtn = document.getElementById("saveUserBtn");
const deleteUserBtn = document.getElementById("deleteUserBtn");
const userModalBackdrop = document.getElementById("userModalBackdrop");
const closeUserModalBtn = document.getElementById("closeUserModalBtn");

let authToken = "";
let authUser = null;
let requests = [];
let selectedRequestId = null;
let adminTablatures = [];
let adminCourses = [];
let adminUsers = [];
let selectedAdminUserId = null;
const visibilityUpdatesInFlight = new Set();

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

function normalizeVisibility(value) {
  return String(value || "").trim().toLowerCase() === "public" ? "public" : "private";
}

function getVisibilityLabel(value) {
  return normalizeVisibility(value) === "public" ? "публичная" : "приватная";
}

function getToggledVisibility(value) {
  return normalizeVisibility(value) === "public" ? "private" : "public";
}

function normalizeAdminUserRole(value) {
  return String(value || "").trim().toLowerCase() === "author" ? "author" : "user";
}

function getRoleLabel(value) {
  return normalizeAdminUserRole(value) === "author" ? "автор" : "пользователь";
}

function getRequestStatusLabel(value) {
  const normalized = String(value || "").trim().toLowerCase();
  if (normalized === "approved") return "одобрена";
  if (normalized === "rejected") return "отклонена";
  if (normalized === "pending") return "ожидает рассмотрения";
  return normalized || "неизвестно";
}

function isAdmin() {
  const role = String(authUser?.role || "").toLowerCase();
  const email = String(authUser?.email || "").toLowerCase();
  return role === "admin" || email === "admin@mail.ru";
}

function setDetailVisible(visible) {
  if (requestDetailPanelEl) {
    requestDetailPanelEl.classList.toggle("is-hidden", !visible);
  }
}

function closeRequestDetails() {
  selectedRequestId = null;
  renderRequestsList();
  renderRequestDetails();
}

function setUserDetailVisible(visible) {
  if (userDetailPanelEl) {
    userDetailPanelEl.classList.toggle("is-hidden", !visible);
  }
}

function findRequestById(requestId) {
  return requests.find((item) => String(item.id) === String(requestId)) || null;
}

function findAdminUserById(userId) {
  return adminUsers.find((item) => String(item.id) === String(userId)) || null;
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
          <h3 class="card__title">Заявка #${item.id} • ${escapeHtml(item.user_nickname || item.user_email || "неизвестно")}</h3>
          <p class="card__meta">Электронная почта: ${escapeHtml(item.user_email || "-")}</p>
          <p class="card__meta">Статус: ${escapeHtml(getRequestStatusLabel(item.status))} • Создана: ${formatDateTime(item.created_at)}</p>
          <p class="card__text">${escapeHtml(messagePreview)}${suffix}</p>
        </article>
      `;
    })
    .join("");
}

function renderAdminTablatures() {
  if (!adminTablaturesListEl) return;
  if (!adminTablatures.length) {
    adminTablaturesListEl.innerHTML = `
      <article class="card">
        <h3 class="card__title">Табулатуры не найдены</h3>
        <p class="card__meta">Список пуст по текущему фильтру.</p>
      </article>
    `;
    return;
  }

  adminTablaturesListEl.innerHTML = adminTablatures
    .map((item) => {
      const comments = Number(item.comments_count || 0);
      const likes = Number(item.reactions_like_count || 0);
      const fire = Number(item.reactions_fire_count || 0);
      const wow = Number(item.reactions_wow_count || 0);
      const visibility = normalizeVisibility(item.visibility);
      const visibilityLabel = getVisibilityLabel(item.visibility);
      return `
        <article class="card" data-tablature-id="${item.id}">
          <h3 class="card__title">#${item.id} • ${escapeHtml(item.track_file_name || "Без названия")}</h3>
          <p class="card__meta">Автор: ${escapeHtml(item.author || "неизвестно")} • Создано: ${formatDateTime(item.created_at)}</p>
          <button
            class="card__badge card__badge--action"
            type="button"
            data-toggle-visibility-type="tablature"
            data-toggle-visibility-id="${item.id}"
            data-current-visibility="${visibility}"
            title="Нажми, чтобы переключить видимость"
          >
            Видимость: ${visibilityLabel}
          </button>
          <p class="card__social">Комментарии: ${comments} • Нравится: ${likes} • Огонь: ${fire} • Вау: ${wow}</p>
          <div class="card__actions">
            <button class="btn btn--secondary" type="button" data-open-tablature-id="${item.id}">Просмотр</button>
            <button class="btn btn--secondary card__delete-btn" type="button" data-delete-tablature-id="${item.id}">Удалить</button>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderAdminCourses() {
  if (!adminCoursesListEl) return;
  if (!adminCourses.length) {
    adminCoursesListEl.innerHTML = `
      <article class="card">
        <h3 class="card__title">Курсы не найдены</h3>
        <p class="card__meta">Список пуст по текущему фильтру.</p>
      </article>
    `;
    return;
  }

  adminCoursesListEl.innerHTML = adminCourses
    .map((item) => {
      const tags = Array.isArray(item.tags) ? item.tags.map((tag) => escapeHtml(tag)).join(", ") : "";
      const safeTags = tags || "без тегов";
      const visibility = normalizeVisibility(item.visibility);
      const visibilityLabel = getVisibilityLabel(item.visibility);
      const cover = typeof item.cover_image_path === "string" && item.cover_image_path.trim()
        ? `<img class="card__cover" src="${escapeHtml(item.cover_image_path)}" alt="Обложка курса" loading="lazy" />`
        : "";
      return `
        <article class="card" data-course-id="${item.id}">
          ${cover}
          <h3 class="card__title">#${item.id} • ${escapeHtml(item.title || "Без названия")}</h3>
          <p class="card__meta">Автор: ${escapeHtml(item.author || "неизвестно")} • Создано: ${formatDateTime(item.created_at)} • Обновлено: ${formatDateTime(item.updated_at)}</p>
          <button
            class="card__badge card__badge--action"
            type="button"
            data-toggle-visibility-type="course"
            data-toggle-visibility-id="${item.id}"
            data-current-visibility="${visibility}"
            title="Нажми, чтобы переключить видимость"
          >
            Видимость: ${visibilityLabel}
          </button>
          <p class="card__text">${escapeHtml(item.description || "Описание не заполнено.")}</p>
          <p class="card__meta">Теги: ${safeTags}</p>
          <div class="card__actions">
            <button class="btn btn--secondary" type="button" data-open-course-id="${item.id}">Просмотр</button>
            <button class="btn btn--secondary card__delete-btn" type="button" data-delete-course-id="${item.id}">Удалить</button>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderAdminUsers() {
  if (!adminUsersListEl) return;
  if (!adminUsers.length) {
    adminUsersListEl.innerHTML = `
      <article class="card">
        <h3 class="card__title">Пользователи не найдены</h3>
        <p class="card__meta">Список пуст по текущему фильтру.</p>
      </article>
    `;
    return;
  }

  adminUsersListEl.innerHTML = adminUsers
    .map((item) => {
      const selected = String(item.id) === String(selectedAdminUserId);
      const role = normalizeAdminUserRole(item.role);
      const roleLabel = getRoleLabel(item.role);
      return `
        <article class="card ${selected ? "card--selected" : ""}" data-admin-user-id="${item.id}">
          <h3 class="card__title">#${item.id} • ${escapeHtml(item.nickname || "-")}</h3>
          <p class="card__meta">Электронная почта: ${escapeHtml(item.email || "-")}</p>
          <p class="card__meta">Роль: ${escapeHtml(roleLabel)}</p>
        </article>
      `;
    })
    .join("");
}

function renderUserDetails() {
  const selected = selectedAdminUserId ? findAdminUserById(selectedAdminUserId) : null;
  if (!selected) {
    setUserDetailVisible(false);
    return;
  }

  setUserDetailVisible(true);
  const role = normalizeAdminUserRole(selected.role);
  const roleLabel = getRoleLabel(selected.role);
  if (userDetailMetaEl) {
    userDetailMetaEl.textContent = `Пользователь #${selected.id} • Текущая роль: ${roleLabel}`;
  }
  if (userEditEmailInput) {
    userEditEmailInput.value = String(selected.email || "");
  }
  if (userEditNicknameInput) {
    userEditNicknameInput.value = String(selected.nickname || "");
  }
  if (userEditRoleSelect) {
    userEditRoleSelect.value = role;
  }
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
      `Статус: ${getRequestStatusLabel(selected.status)} • ` +
      `Создана: ${formatDateTime(selected.created_at)} • Обновлена: ${formatDateTime(selected.updated_at)}`;
  }
  if (requestDetailMessageEl) {
    requestDetailMessageEl.textContent = String(selected.message || "").trim() || "-";
  }
  if (rejectMessageInput) {
    rejectMessageInput.value = String(selected.admin_message || "");
  }
}

async function toggleAdminTablatureVisibility(tablatureId, currentVisibility) {
  if (!authToken || !isAdmin()) return;
  const normalizedId = Number(tablatureId);
  if (!Number.isFinite(normalizedId)) return;
  const updateKey = `tablature:${normalizedId}`;
  if (visibilityUpdatesInFlight.has(updateKey)) return;

  const nextVisibility = getToggledVisibility(currentVisibility);
  visibilityUpdatesInFlight.add(updateKey);
  try {
    const payload = await api.updateAdminTablatureVisibility(authToken, normalizedId, nextVisibility);
    const updated = payload && typeof payload.tablature === "object" ? payload.tablature : null;
    const resolvedVisibility = normalizeVisibility(updated?.visibility || nextVisibility);
    adminTablatures = adminTablatures.map((item) => {
      if (Number(item.id) !== normalizedId) return item;
      return {
        ...item,
        visibility: resolvedVisibility,
        updated_at: updated?.updated_at || item.updated_at,
      };
    });
    renderAdminTablatures();
    setStatus(`Видимость табулатуры #${normalizedId}: ${resolvedVisibility}`);
  } catch (error) {
    setStatus(`Ошибка изменения видимости табулатуры: ${getErrorMessage(error)}`);
  } finally {
    visibilityUpdatesInFlight.delete(updateKey);
  }
}

async function toggleAdminCourseVisibility(courseId, currentVisibility) {
  if (!authToken || !isAdmin()) return;
  const normalizedId = Number(courseId);
  if (!Number.isFinite(normalizedId)) return;
  const updateKey = `course:${normalizedId}`;
  if (visibilityUpdatesInFlight.has(updateKey)) return;

  const nextVisibility = getToggledVisibility(currentVisibility);
  visibilityUpdatesInFlight.add(updateKey);
  try {
    const payload = await api.updateAdminCourseVisibility(authToken, normalizedId, nextVisibility);
    const updated = payload && typeof payload.course === "object" ? payload.course : null;
    const resolvedVisibility = normalizeVisibility(updated?.visibility || nextVisibility);
    adminCourses = adminCourses.map((item) => {
      if (Number(item.id) !== normalizedId) return item;
      return {
        ...item,
        visibility: resolvedVisibility,
        updated_at: updated?.updated_at || item.updated_at,
      };
    });
    renderAdminCourses();
    setStatus(`Видимость курса #${normalizedId}: ${resolvedVisibility}`);
  } catch (error) {
    setStatus(`Ошибка изменения видимости курса: ${getErrorMessage(error)}`);
  } finally {
    visibilityUpdatesInFlight.delete(updateKey);
  }
}

async function deleteAdminTablatureById(tablatureId) {
  if (!authToken || !isAdmin()) return;
  const normalizedId = Number(tablatureId);
  if (!Number.isFinite(normalizedId)) return;

  const confirmation = window.confirm(`Удалить табулатуру #${normalizedId}?`);
  if (!confirmation) return;

  try {
    await api.deleteAdminTablature(authToken, normalizedId);
    adminTablatures = adminTablatures.filter((item) => Number(item.id) !== normalizedId);
    renderAdminTablatures();
    setStatus(`Табулатура #${normalizedId} удалена.`);
  } catch (error) {
    setStatus(`Ошибка удаления табулатуры: ${getErrorMessage(error)}`);
  }
}

async function deleteAdminCourseById(courseId) {
  if (!authToken || !isAdmin()) return;
  const normalizedId = Number(courseId);
  if (!Number.isFinite(normalizedId)) return;

  const confirmation = window.confirm(`Удалить курс #${normalizedId}?`);
  if (!confirmation) return;

  try {
    await api.deleteAdminCourse(authToken, normalizedId);
    adminCourses = adminCourses.filter((item) => Number(item.id) !== normalizedId);
    renderAdminCourses();
    setStatus(`Курс #${normalizedId} удален.`);
  } catch (error) {
    setStatus(`Ошибка удаления курса: ${getErrorMessage(error)}`);
  }
}

async function loadRequests() {
  if (!authToken || !isAdmin()) {
    if (subtitleEl) subtitleEl.textContent = "Доступно только администратору.";
    requests = [];
    selectedRequestId = null;
    renderRequestsList();
    renderRequestDetails();
    setStatus("Войди под пользователем с ролью администратора.");
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

async function loadAdminContent() {
  if (!authToken || !isAdmin()) {
    adminTablatures = [];
    adminCourses = [];
    if (adminTablaturesListEl) {
      adminTablaturesListEl.innerHTML = `
        <article class="card">
          <h3 class="card__title">Доступ ограничен</h3>
          <p class="card__meta">Только администратор может просматривать этот раздел.</p>
        </article>
      `;
    }
    if (adminCoursesListEl) {
      adminCoursesListEl.innerHTML = `
        <article class="card">
          <h3 class="card__title">Доступ ограничен</h3>
          <p class="card__meta">Только администратор может просматривать этот раздел.</p>
        </article>
      `;
    }
    return;
  }

  try {
    const [tabPayload, coursePayload] = await Promise.all([
      api.fetchAdminTablatures(authToken, "", { limit: 500, offset: 0 }),
      api.fetchAdminCourses(authToken, "", { limit: 500, offset: 0 }),
    ]);
    adminTablatures = Array.isArray(tabPayload.items) ? tabPayload.items : [];
    adminCourses = Array.isArray(coursePayload.items) ? coursePayload.items : [];
    renderAdminTablatures();
    renderAdminCourses();
  } catch (error) {
    adminTablatures = [];
    adminCourses = [];
    renderAdminTablatures();
    renderAdminCourses();
    setStatus(`Ошибка загрузки контента: ${getErrorMessage(error)}`);
  }
}

async function loadAdminUsers() {
  if (!authToken || !isAdmin()) {
    adminUsers = [];
    selectedAdminUserId = null;
    setUserDetailVisible(false);
    if (adminUsersListEl) {
      adminUsersListEl.innerHTML = `
        <article class="card">
          <h3 class="card__title">Доступ ограничен</h3>
          <p class="card__meta">Только администратор может просматривать этот раздел.</p>
        </article>
      `;
    }
    return;
  }

  try {
    const payload = await api.fetchAdminUsers(authToken, {
      role: "all",
      limit: 500,
      offset: 0,
    });
    adminUsers = Array.isArray(payload.items) ? payload.items : [];
    if (!adminUsers.length) {
      selectedAdminUserId = null;
    } else if (!findAdminUserById(selectedAdminUserId)) {
      selectedAdminUserId = null;
    }
    renderAdminUsers();
    renderUserDetails();
  } catch (error) {
    adminUsers = [];
    selectedAdminUserId = null;
    renderAdminUsers();
    renderUserDetails();
    setStatus(`Ошибка загрузки пользователей: ${getErrorMessage(error)}`);
  }
}

if (refreshBtn) {
  refreshBtn.addEventListener("click", () => {
    loadRequests();
    loadAdminContent();
    loadAdminUsers();
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

if (requestModalBackdrop) {
  requestModalBackdrop.addEventListener("click", () => {
    closeRequestDetails();
  });
}

if (closeRequestModalBtn) {
  closeRequestModalBtn.addEventListener("click", () => {
    closeRequestDetails();
  });
}

if (adminTablaturesListEl) {
  adminTablaturesListEl.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const visibilityToggle = target.closest("[data-toggle-visibility-type='tablature']");
    if (visibilityToggle) {
      const tablatureId = Number(visibilityToggle.getAttribute("data-toggle-visibility-id"));
      const currentVisibility = visibilityToggle.getAttribute("data-current-visibility") || "private";
      if (!Number.isFinite(tablatureId)) return;
      toggleAdminTablatureVisibility(tablatureId, currentVisibility);
      return;
    }
    const deleteButton = target.closest("[data-delete-tablature-id]");
    if (deleteButton) {
      const tablatureId = deleteButton.getAttribute("data-delete-tablature-id");
      if (!tablatureId) return;
      deleteAdminTablatureById(tablatureId);
      return;
    }
    const button = target.closest("[data-open-tablature-id]");
    const card = target.closest(".card[data-tablature-id]");
    const tablatureId = button
      ? button.getAttribute("data-open-tablature-id")
      : card?.getAttribute("data-tablature-id");
    if (!tablatureId) return;
    window.location.href = `/community/tablatures/${encodeURIComponent(tablatureId)}?admin=1`;
  });
}

if (adminCoursesListEl) {
  adminCoursesListEl.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const visibilityToggle = target.closest("[data-toggle-visibility-type='course']");
    if (visibilityToggle) {
      const courseId = Number(visibilityToggle.getAttribute("data-toggle-visibility-id"));
      const currentVisibility = visibilityToggle.getAttribute("data-current-visibility") || "private";
      if (!Number.isFinite(courseId)) return;
      toggleAdminCourseVisibility(courseId, currentVisibility);
      return;
    }
    const deleteButton = target.closest("[data-delete-course-id]");
    if (deleteButton) {
      const courseId = deleteButton.getAttribute("data-delete-course-id");
      if (!courseId) return;
      deleteAdminCourseById(courseId);
      return;
    }
    const button = target.closest("[data-open-course-id]");
    const card = target.closest(".card[data-course-id]");
    const courseId = button
      ? button.getAttribute("data-open-course-id")
      : card?.getAttribute("data-course-id");
    if (!courseId) return;
    window.location.href = `/courses/${encodeURIComponent(courseId)}?admin=1`;
  });
}

if (adminUsersListEl) {
  adminUsersListEl.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const card = target.closest(".card[data-admin-user-id]");
    if (!card) return;
    const userId = card.getAttribute("data-admin-user-id");
    if (!userId) return;
    selectedAdminUserId = userId;
    renderAdminUsers();
    renderUserDetails();
  });
}

if (userModalBackdrop) {
  userModalBackdrop.addEventListener("click", () => {
    setUserDetailVisible(false);
  });
}

if (closeUserModalBtn) {
  closeUserModalBtn.addEventListener("click", () => {
    setUserDetailVisible(false);
  });
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeRequestDetails();
    setUserDetailVisible(false);
  }
});

if (saveUserBtn) {
  saveUserBtn.addEventListener("click", async () => {
    if (!authToken || !isAdmin()) return;
    const selected = selectedAdminUserId ? findAdminUserById(selectedAdminUserId) : null;
    if (!selected) {
      setStatus("Сначала выбери пользователя.");
      return;
    }

    const email = userEditEmailInput ? userEditEmailInput.value.trim() : "";
    const nickname = userEditNicknameInput ? userEditNicknameInput.value.trim() : "";
    const role = userEditRoleSelect ? userEditRoleSelect.value : "user";
    if (!email || !nickname) {
      setStatus("Электронная почта и никнейм обязательны.");
      return;
    }

    try {
      saveUserBtn.disabled = true;
      const payload = await api.updateAdminUserAccount(authToken, selected.id, {
        email,
        nickname,
        role,
      });
      const updated = payload && typeof payload.user === "object" ? payload.user : null;
      const updatedRole = normalizeAdminUserRole(updated?.role || role);
      adminUsers = adminUsers.map((item) => {
        if (Number(item.id) !== Number(selected.id)) return item;
        return {
          ...item,
          email: String(updated?.email || email),
          nickname: String(updated?.nickname || nickname),
          role: updatedRole,
        };
      });
      selectedAdminUserId = null;
      renderAdminUsers();
      renderUserDetails();
      setStatus(`Аккаунт пользователя #${selected.id} обновлен.`);
    } catch (error) {
      setStatus(`Ошибка обновления пользователя: ${getErrorMessage(error)}`);
    } finally {
      saveUserBtn.disabled = false;
    }
  });
}

if (deleteUserBtn) {
  deleteUserBtn.addEventListener("click", async () => {
    if (!authToken || !isAdmin()) return;
    const selected = selectedAdminUserId ? findAdminUserById(selectedAdminUserId) : null;
    if (!selected) {
      setStatus("Сначала выбери пользователя.");
      return;
    }

    const confirmation = window.confirm(
      `Удалить пользователя #${selected.id} (${selected.nickname || selected.email || "неизвестно"})? ` +
      "Будут удалены его табулатуры и курсы."
    );
    if (!confirmation) {
      return;
    }

    try {
      deleteUserBtn.disabled = true;
      if (saveUserBtn) saveUserBtn.disabled = true;
      await api.deleteAdminUser(authToken, selected.id);
      adminUsers = adminUsers.filter((item) => Number(item.id) !== Number(selected.id));
      selectedAdminUserId = null;
      renderAdminUsers();
      renderUserDetails();
      setStatus(`Пользователь #${selected.id} удален вместе с его контентом.`);
      await loadAdminContent();
    } catch (error) {
      setStatus(`Ошибка удаления пользователя: ${getErrorMessage(error)}`);
    } finally {
      deleteUserBtn.disabled = false;
      if (saveUserBtn) saveUserBtn.disabled = false;
    }
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
      setStatus(`Заявка #${selected.id} одобрена. Пользователь получил роль автора.`);
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
      await loadAdminContent();
      await loadAdminUsers();
    },
  });
}

init();
