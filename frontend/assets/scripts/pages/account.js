import * as api from "../services/api.js?v=9";

const AUTH_TOKEN_KEY = "drum_auth_token";
const AUTH_USER_KEY = "drum_auth_user";

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

let authToken = "";
let currentUser = null;

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
    return;
  }

  if (subtitleEl) subtitleEl.textContent = `Пользователь: ${user.nickname || user.email}`;
  if (profileEmailEl) profileEmailEl.textContent = user.email || "-";
  if (profileNicknameEl) profileNicknameEl.textContent = user.nickname || "-";
  if (profileRoleEl) profileRoleEl.textContent = user.role || "-";
  if (nicknameInput) nicknameInput.value = user.nickname || "";
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
    window.location.href = "/";
  });
}

if (searchBtn) {
  searchBtn.addEventListener("click", () => {
    loadPersonalTablatures();
  });
}

if (resetBtn) {
  resetBtn.addEventListener("click", () => {
    if (searchInput) searchInput.value = "";
    loadPersonalTablatures();
  });
}

if (searchInput) {
  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") loadPersonalTablatures();
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

async function init() {
  authToken = localStorage.getItem(AUTH_TOKEN_KEY) || "";
  const ok = await loadMe();
  if (!ok) {
    return;
  }
  await loadPersonalTablatures();
}

init();
