import * as api from "../services/api.js?v=16";

const AUTH_TOKEN_KEY = "drum_auth_token";
const AUTH_USER_KEY = "drum_auth_user";
const AUTH_PAGE_PATH = "/auth";

const statusEl = document.getElementById("status");
const subtitleEl = document.getElementById("accountSubtitle");
const profileEmailEl = document.getElementById("profileEmail");
const profileNicknameEl = document.getElementById("profileNickname");
const profileRoleEl = document.getElementById("profileRole");
const nicknameInput = document.getElementById("nicknameInput");
const saveNicknameBtn = document.getElementById("saveNicknameBtn");
const logoutBtn = document.getElementById("logoutBtn");

const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");
const resetBtn = document.getElementById("resetBtn");
const personalList = document.getElementById("personalList");
const authorCoursesPanel = document.getElementById("authorCoursesPanel");
const courseSearchInput = document.getElementById("courseSearchInput");
const courseSearchBtn = document.getElementById("courseSearchBtn");
const courseResetBtn = document.getElementById("courseResetBtn");
const authorCoursesList = document.getElementById("authorCoursesList");
const authorRequestPanel = document.getElementById("authorRequestPanel");
const authorRequestInfo = document.getElementById("authorRequestInfo");
const authorRequestAdminMessage = document.getElementById("authorRequestAdminMessage");
const authorRequestMessageInput = document.getElementById("authorRequestMessage");
const authorRequestSendBtn = document.getElementById("authorRequestSendBtn");

let authToken = "";
let currentUser = null;
let latestAuthorRoleRequest = null;

function setStatus(message) {
  if (statusEl) {
    statusEl.textContent = message;
  }
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

function getErrorMessage(error) {
  if (!error) return "Unknown error";
  if (typeof error.message === "string") return error.message;
  return String(error);
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function saveUserToStorage(user) {
  if (user) {
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(AUTH_USER_KEY);
  }
}

function renderUser(user) {
  currentUser = user;
  if (!user) {
    if (subtitleEl) subtitleEl.textContent = "Нужно войти в аккаунт.";
    if (profileEmailEl) profileEmailEl.textContent = "-";
    if (profileNicknameEl) profileNicknameEl.textContent = "-";
    if (profileRoleEl) profileRoleEl.textContent = "-";
    if (nicknameInput) nicknameInput.value = "";
    if (authorCoursesPanel) authorCoursesPanel.classList.add("is-hidden");
    if (authorRequestPanel) authorRequestPanel.classList.add("is-hidden");
    return;
  }

  if (subtitleEl) subtitleEl.textContent = `Пользователь: ${user.nickname || user.email}`;
  if (profileEmailEl) profileEmailEl.textContent = user.email || "-";
  if (profileNicknameEl) profileNicknameEl.textContent = user.nickname || "-";
  if (profileRoleEl) profileRoleEl.textContent = user.role || "-";
  if (nicknameInput) nicknameInput.value = user.nickname || "";

  const isAuthor = String(user.role || "").toLowerCase() === "author";
  if (authorCoursesPanel) {
    authorCoursesPanel.classList.toggle("is-hidden", !isAuthor);
  }
  if (authorRequestPanel) {
    authorRequestPanel.classList.toggle("is-hidden", isAuthor);
  }
}

function renderAuthorRoleRequest(item) {
  latestAuthorRoleRequest = item || null;
  if (!authorRequestPanel || !authorRequestInfo || !authorRequestSendBtn || !authorRequestMessageInput) {
    return;
  }
  if (authorRequestAdminMessage) {
    authorRequestAdminMessage.classList.add("is-hidden");
    authorRequestAdminMessage.textContent = "";
  }

  const isAuthorized = Boolean(currentUser && authToken);
  if (!isAuthorized) {
    authorRequestPanel.classList.add("is-hidden");
    return;
  }

  const isAuthor = String(currentUser.role || "").toLowerCase() === "author";
  if (isAuthor) {
    authorRequestPanel.classList.add("is-hidden");
    return;
  }

  authorRequestPanel.classList.remove("is-hidden");

  if (!item) {
    authorRequestInfo.textContent = "Заявка не отправлена.";
    authorRequestMessageInput.value = "";
    authorRequestSendBtn.disabled = false;
    authorRequestMessageInput.disabled = false;
    return;
  }

  const status = String(item.status || "").toLowerCase();
  const createdAtText = formatCreatedAt(item.created_at);
  authorRequestMessageInput.value = String(item.message || "");
  if (status === "pending") {
    authorRequestInfo.textContent = `Заявка отправлена: ${createdAtText}. Статус: pending.`;
    authorRequestSendBtn.disabled = true;
    authorRequestMessageInput.disabled = true;
    return;
  }
  if (status === "approved") {
    authorRequestInfo.textContent = `Заявка одобрена (${createdAtText}).`;
    authorRequestSendBtn.disabled = true;
    authorRequestMessageInput.disabled = true;
    return;
  }

  const adminMessage = String(item.admin_message || "").trim();
  if (status === "rejected") {
    authorRequestInfo.textContent = `Последняя заявка: ${createdAtText}. Статус: rejected.`;
    if (adminMessage && authorRequestAdminMessage) {
      authorRequestAdminMessage.textContent = `Причина отказа администратора:\n${adminMessage}`;
      authorRequestAdminMessage.classList.remove("is-hidden");
    }
  } else if (adminMessage) {
    authorRequestInfo.textContent = `Последняя заявка: ${createdAtText}. Статус: ${status || "unknown"}.`;
  } else {
    authorRequestInfo.textContent = `Последняя заявка: ${createdAtText}. Статус: ${status || "unknown"}. Можно отправить новую.`;
  }
  authorRequestSendBtn.disabled = false;
  authorRequestMessageInput.disabled = false;
}

function renderPersonalList(items) {
  if (!personalList) return;
  if (!items.length) {
    personalList.innerHTML = `
      <article class="card">
        <h3 class="card__title">Пока пусто</h3>
        <p class="card__text">У тебя пока нет сохраненных табулатур.</p>
      </article>
    `;
    return;
  }

  personalList.innerHTML = items
    .map(
      (item) => `
        <article class="card">
          <h3 class="card__title">#${item.id} • ${item.track_file_name || "Без названия"}</h3>
          <p class="card__text">Автор: ${item.author || "unknown"}</p>
          <p class="card__meta">Создано: ${formatCreatedAt(item.created_at)}</p>
          <div class="card__actions">
            <button class="btn btn--secondary" type="button" data-pdf-task-id="${item.task_id}" data-row-id="${item.id}">
              Скачать PDF
            </button>
            <button class="btn btn--secondary" type="button" data-json-task-id="${item.task_id}" data-row-id="${item.id}">
              Показать JSON
            </button>
          </div>
        </article>
      `
    )
    .join("");
}

function renderAuthorCourses(items) {
  if (!authorCoursesList) return;
  if (!items.length) {
    authorCoursesList.innerHTML = `
      <article class="card">
        <h3 class="card__title">Пока пусто</h3>
        <p class="card__text">У тебя пока нет опубликованных курсов.</p>
      </article>
    `;
    return;
  }

  authorCoursesList.innerHTML = items
    .map((item) => {
      const title = escapeHtml(item.title || "Без названия");
      const description = escapeHtml(item.description || "Описание пока не добавлено.");
      const tags = Array.isArray(item.tags) && item.tags.length ? item.tags.map((x) => escapeHtml(x)).join(", ") : "без тегов";
      const cover = item.cover_image_path
        ? `<img class="card__cover" src="${escapeHtml(item.cover_image_path)}" alt="Обложка курса" loading="lazy" />`
        : "";
      const visibility = escapeHtml(item.visibility || "private");
      return `
        <article class="card" data-course-id="${item.id}">
          ${cover}
          <h3 class="card__title">${title}</h3>
          <p class="card__text">${description}</p>
          <p class="card__tags">Теги: ${tags}</p>
          <p class="card__meta">Видимость: ${visibility} • Создано: ${formatCreatedAt(item.created_at)} • Обновлено: ${formatCreatedAt(item.updated_at)}</p>
          <div class="card__actions">
            <button class="btn btn--primary" type="button" data-course-lessons-id="${item.id}">Уроки</button>
            <button class="btn btn--secondary" type="button" data-course-stats-id="${item.id}">Статистика</button>
            <button class="btn btn--secondary" type="button" data-course-edit-id="${item.id}">Редактировать</button>
            <button class="btn btn--secondary" type="button" data-course-delete-id="${item.id}">Удалить</button>
          </div>
        </article>
      `;
    })
    .join("");
}

async function loadMe() {
  if (!authToken) {
    renderUser(null);
    return false;
  }
  try {
    const payload = await api.fetchAuthMe(authToken);
    const user = payload.user || null;
    renderUser(user);
    saveUserToStorage(user);
    return true;
  } catch (error) {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
    renderUser(null);
    setStatus(`Сессия недействительна: ${getErrorMessage(error)}\nВыполни вход на главной странице.`);
    return false;
  }
}

async function loadPersonalTablatures() {
  if (!authToken) {
    renderPersonalList([]);
    return;
  }
  const query = searchInput && searchInput.value ? searchInput.value.trim() : "";
  try {
    const payload = await api.fetchPersonalTablatures(authToken, query);
    const items = Array.isArray(payload.items) ? payload.items : [];
    renderPersonalList(items);
    setStatus(`Загружено табулатур: ${items.length}`);
  } catch (error) {
    setStatus(`Ошибка загрузки личной библиотеки: ${getErrorMessage(error)}`);
    renderPersonalList([]);
  }
}

async function loadAuthorCourses() {
  const isAuthor = Boolean(currentUser && String(currentUser.role || "").toLowerCase() === "author");
  if (!authToken || !isAuthor) {
    renderAuthorCourses([]);
    return;
  }

  const query = courseSearchInput && courseSearchInput.value ? courseSearchInput.value.trim() : "";
  try {
    const payload = await api.fetchPersonalCourses(authToken, query, { limit: 200, offset: 0 });
    const items = Array.isArray(payload.items) ? payload.items : [];
    renderAuthorCourses(items);
    setStatus(`Загружено курсов: ${items.length}`);
  } catch (error) {
    setStatus(`Ошибка загрузки курсов: ${getErrorMessage(error)}`);
    renderAuthorCourses([]);
  }
}

async function loadAuthorRoleRequest() {
  if (!authToken || !currentUser) {
    renderAuthorRoleRequest(null);
    return;
  }

  const isAuthor = String(currentUser.role || "").toLowerCase() === "author";
  if (isAuthor) {
    renderAuthorRoleRequest(null);
    return;
  }

  try {
    const payload = await api.fetchPersonalAuthorRoleRequest(authToken);
    const requestItem = payload && payload.request ? payload.request : null;
    renderAuthorRoleRequest(requestItem);
  } catch (error) {
    setStatus(`Ошибка загрузки заявки на роль автора: ${getErrorMessage(error)}`);
    renderAuthorRoleRequest(null);
  }
}

if (saveNicknameBtn) {
  saveNicknameBtn.addEventListener("click", async () => {
    if (!authToken) {
      setStatus("Нужна авторизация.");
      return;
    }
    const nickname = nicknameInput ? nicknameInput.value.trim() : "";
    if (!nickname) {
      setStatus("Введи nickname.");
      return;
    }

    try {
      saveNicknameBtn.disabled = true;
      const payload = await api.updateAuthMe(authToken, { nickname });
      const user = payload.user || null;
      renderUser(user);
      saveUserToStorage(user);
      setStatus("Никнейм обновлен.");
    } catch (error) {
      setStatus(`Ошибка обновления профиля: ${getErrorMessage(error)}`);
    } finally {
      saveNicknameBtn.disabled = false;
    }
  });
}

if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
    window.location.href = AUTH_PAGE_PATH;
  });
}

if (authorRequestSendBtn) {
  authorRequestSendBtn.addEventListener("click", async () => {
    if (!authToken || !currentUser) {
      setStatus("Нужна авторизация.");
      return;
    }
    if (String(currentUser.role || "").toLowerCase() === "author") {
      setStatus("У тебя уже есть роль author.");
      return;
    }

    const message = authorRequestMessageInput ? authorRequestMessageInput.value.trim() : "";
    if (!message) {
      setStatus("Напиши сообщение для администратора.");
      return;
    }

    try {
      authorRequestSendBtn.disabled = true;
      const payload = await api.createPersonalAuthorRoleRequest(authToken, message);
      const requestItem = payload && payload.request ? payload.request : null;
      renderAuthorRoleRequest(requestItem);
      setStatus("Заявка отправлена администратору.");
    } catch (error) {
      setStatus(`Ошибка отправки заявки: ${getErrorMessage(error)}`);
      await loadAuthorRoleRequest();
    } finally {
      if (latestAuthorRoleRequest && String(latestAuthorRoleRequest.status || "").toLowerCase() === "pending") {
        authorRequestSendBtn.disabled = true;
      } else {
        authorRequestSendBtn.disabled = false;
      }
    }
  });
}

if (searchBtn) {
  searchBtn.addEventListener("click", () => {
    loadPersonalTablatures();
  });
}

if (courseSearchBtn) {
  courseSearchBtn.addEventListener("click", () => {
    loadAuthorCourses();
  });
}

if (resetBtn) {
  resetBtn.addEventListener("click", () => {
    if (searchInput) searchInput.value = "";
    loadPersonalTablatures();
  });
}

if (courseResetBtn) {
  courseResetBtn.addEventListener("click", () => {
    if (courseSearchInput) courseSearchInput.value = "";
    loadAuthorCourses();
  });
}

if (searchInput) {
  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") loadPersonalTablatures();
  });
}

if (courseSearchInput) {
  courseSearchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") loadAuthorCourses();
  });
}

if (personalList) {
  personalList.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;

    const pdfButton = target.closest("[data-pdf-task-id]");
    if (pdfButton) {
      const taskId = pdfButton.getAttribute("data-pdf-task-id");
      const rowId = pdfButton.getAttribute("data-row-id");
      if (!taskId) return;
      try {
        setStatus(`Скачиваю PDF для задачи ${taskId}...`);
        const blob = await api.fetchPdfByJobId(taskId);
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `tablature-${rowId || taskId}.pdf`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
        setStatus("PDF скачан.");
      } catch (error) {
        setStatus(`Ошибка скачивания PDF: ${getErrorMessage(error)}`);
      }
      return;
    }

    const jsonButton = target.closest("[data-json-task-id]");
    if (jsonButton) {
      const taskId = jsonButton.getAttribute("data-json-task-id");
      if (!taskId) return;
      try {
        setStatus(`Получаю JSON для задачи ${taskId}...`);
        const payload = await api.fetchTablatureByJobId(taskId);
        setStatus(JSON.stringify(payload, null, 2));
      } catch (error) {
        setStatus(`Ошибка получения JSON: ${getErrorMessage(error)}`);
      }
    }
  });
}

if (authorCoursesList) {
  authorCoursesList.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;

    const lessonsButton = target.closest("[data-course-lessons-id]");
    if (lessonsButton) {
      const courseId = lessonsButton.getAttribute("data-course-lessons-id");
      if (!courseId) return;
      window.location.href = `/courses/${encodeURIComponent(courseId)}?editable=1&source=account`;
      return;
    }

    const editButton = target.closest("[data-course-edit-id]");
    if (editButton) {
      const courseId = editButton.getAttribute("data-course-edit-id");
      if (!courseId) return;
      window.location.href = `/courses/edit/${encodeURIComponent(courseId)}`;
      return;
    }

    const statsButton = target.closest("[data-course-stats-id]");
    if (statsButton) {
      const courseId = statsButton.getAttribute("data-course-stats-id");
      if (!courseId) return;
      window.location.href = `/courses/${encodeURIComponent(courseId)}/stats`;
      return;
    }

    const deleteButton = target.closest("[data-course-delete-id]");
    if (deleteButton) {
      const courseId = deleteButton.getAttribute("data-course-delete-id");
      if (!courseId || !authToken) return;

      const shouldDelete = window.confirm("Удалить этот курс?");
      if (!shouldDelete) return;

      try {
        setStatus(`Удаляю курс #${courseId}...`);
        await api.deletePersonalCourse(authToken, courseId);
        setStatus("Курс удален.");
        await loadAuthorCourses();
      } catch (error) {
        setStatus(`Ошибка удаления курса: ${getErrorMessage(error)}`);
      }
      return;
    }

    const card = target.closest(".card[data-course-id]");
    if (!card) return;
    const courseId = card.getAttribute("data-course-id");
    if (!courseId) return;
    window.location.href = `/courses/${encodeURIComponent(courseId)}?editable=1&source=account`;
  });
}

async function init() {
  authToken = localStorage.getItem(AUTH_TOKEN_KEY) || "";
  const ok = await loadMe();
  if (!ok) {
    return;
  }
  await loadAuthorRoleRequest();
  await loadPersonalTablatures();
  await loadAuthorCourses();
}

init();
