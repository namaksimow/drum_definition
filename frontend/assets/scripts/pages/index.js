import * as api from "../services/api.js?v=9";

const AUTH_TOKEN_KEY = "drum_auth_token";
const AUTH_USER_KEY = "drum_auth_user";

const authState = {
  token: "",
  user: null,
};

const menuButtons = document.querySelectorAll(".menu__btn");
const viewPanels = document.querySelectorAll("[data-view-panel]");
const statusEl = document.getElementById("status");

const uploadBtn = document.getElementById("uploadBtn");
const pdfBtn = document.getElementById("pdfBtn");
const jsonBtn = document.getElementById("jsonBtn");
const fileInput = document.getElementById("songFile");
const jobIdInput = document.getElementById("jobId");
const jsonView = document.getElementById("jsonView");

const authGuest = document.getElementById("authGuest");
const guestAuthToggleBtn = document.getElementById("guestAuthToggleBtn");
const guestAuthPanel = document.getElementById("guestAuthPanel");
const authUser = document.getElementById("authUser");
const authStateEl = document.getElementById("authState");
const personalSubtitle = document.getElementById("personalSubtitle");
const editorSubtitle = document.getElementById("editorSubtitle");

const registerEmailInput = document.getElementById("registerEmail");
const registerNicknameInput = document.getElementById("registerNickname");
const registerPasswordInput = document.getElementById("registerPassword");
const loginEmailInput = document.getElementById("loginEmail");
const loginPasswordInput = document.getElementById("loginPassword");

const registerBtn = document.getElementById("registerBtn");
const loginBtn = document.getElementById("loginBtn");
const logoutBtn = document.getElementById("logoutBtn");
const accountMenuBtn = document.getElementById("accountMenuBtn");
const accountMenu = document.getElementById("accountMenu");
const openAccountBtn = document.getElementById("openAccountBtn");

const communitySearchInput = document.getElementById("communitySearch");
const communitySearchBtn = document.getElementById("communitySearchBtn");
const communityClearBtn = document.getElementById("communityClearBtn");
const communityList = document.getElementById("communityList");

const personalRefreshBtn = document.getElementById("personalRefreshBtn");
const personalList = document.getElementById("personalList");

function activateView(viewName) {
  menuButtons.forEach((button) => {
    button.classList.toggle("menu__btn--active", button.dataset.view === viewName);
  });
  viewPanels.forEach((panel) => {
    panel.classList.toggle("view-panel--active", panel.dataset.viewPanel === viewName);
  });
}

function setStatus(message) {
  if (statusEl) {
    statusEl.textContent = message;
  }
}

function setBusy(isBusy) {
  if (uploadBtn) uploadBtn.disabled = isBusy;
  if (pdfBtn) pdfBtn.disabled = isBusy;
  if (jsonBtn) jsonBtn.disabled = isBusy;
}

function setCommunityBusy(isBusy) {
  if (communitySearchBtn) communitySearchBtn.disabled = isBusy;
  if (communityClearBtn) communityClearBtn.disabled = isBusy;
}

function setAuthBusy(isBusy) {
  if (registerBtn) registerBtn.disabled = isBusy;
  if (loginBtn) loginBtn.disabled = isBusy;
  if (logoutBtn) logoutBtn.disabled = isBusy;
  if (guestAuthToggleBtn) guestAuthToggleBtn.disabled = isBusy;
  if (registerEmailInput) registerEmailInput.disabled = isBusy;
  if (registerNicknameInput) registerNicknameInput.disabled = isBusy;
  if (registerPasswordInput) registerPasswordInput.disabled = isBusy;
  if (loginEmailInput) loginEmailInput.disabled = isBusy;
  if (loginPasswordInput) loginPasswordInput.disabled = isBusy;
}

function closeGuestAuthPanel() {
  if (guestAuthPanel) {
    guestAuthPanel.classList.remove("auth-guest__panel--open");
  }
}

function openGuestAuthPanel() {
  if (guestAuthPanel) {
    guestAuthPanel.classList.add("auth-guest__panel--open");
  }
}

function closeAccountMenu() {
  if (accountMenu) {
    accountMenu.classList.remove("auth-user__menu--open");
  }
}

function openAccountMenu() {
  if (accountMenu) {
    accountMenu.classList.add("auth-user__menu--open");
  }
}

function isAuthenticated() {
  return Boolean(authState.token && authState.user);
}

function updateAuthDependentHints() {
  const authenticated = isAuthenticated();
  if (personalSubtitle) {
    personalSubtitle.classList.toggle("is-hidden", authenticated);
  }
  if (editorSubtitle) {
    editorSubtitle.classList.toggle("is-hidden", authenticated);
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

function saveAuthState(token, user) {
  authState.token = token || "";
  authState.user = user || null;
  if (authState.token) {
    localStorage.setItem(AUTH_TOKEN_KEY, authState.token);
  } else {
    localStorage.removeItem(AUTH_TOKEN_KEY);
  }
  if (authState.user) {
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(authState.user));
  } else {
    localStorage.removeItem(AUTH_USER_KEY);
  }
  renderAuthState();
}

function loadAuthStateFromStorage() {
  const token = localStorage.getItem(AUTH_TOKEN_KEY) || "";
  const userRaw = localStorage.getItem(AUTH_USER_KEY);
  let user = null;
  if (userRaw) {
    try {
      user = JSON.parse(userRaw);
    } catch {
      user = null;
    }
  }
  authState.token = token;
  authState.user = user;
}

function renderAuthState() {
  const authenticated = isAuthenticated();

  if (authGuest) {
    authGuest.classList.toggle("is-hidden", authenticated);
  }
  if (authUser) {
    authUser.style.display = authenticated ? "block" : "none";
  }

  if (authStateEl) {
    if (!authenticated) {
      authStateEl.textContent = "Аккаунт";
    } else {
      authStateEl.textContent = authState.user.nickname || authState.user.email || "Аккаунт";
    }
  }

  if (!authenticated) {
    closeAccountMenu();
    closeGuestAuthPanel();
  } else {
    closeGuestAuthPanel();
  }
  updateAuthDependentHints();
}

function renderTabCards(container, items, emptyTitle, emptyText, mode = "generic") {
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `
      <article class="card">
        <h3 class="card__title">${emptyTitle}</h3>
        <p class="card__text">${emptyText}</p>
      </article>
    `;
    return;
  }

  container.innerHTML = items
    .map(
      (item) => {
        const commentsCount = Number(item.comments_count || 0);
        const likeCount = Number(item.reactions_like_count || 0);
        const fireCount = Number(item.reactions_fire_count || 0);
        const wowCount = Number(item.reactions_wow_count || 0);
        const socialStatsHtml =
          mode === "community"
            ? `
          <div class="card__social" aria-label="Статистика табулатуры">
            <span class="social-stat" title="Комментарии">
              <img class="social-stat__icon" src="/assets/images/reactions/comment.svg" alt="Комментарии" loading="lazy" onerror="this.style.display='none'" />
              <span class="social-stat__value">${commentsCount}</span>
            </span>
            <span class="social-stat" title="Like">
              <img class="social-stat__icon" src="/assets/images/reactions/like.svg" alt="Like" loading="lazy" onerror="this.style.display='none'" />
              <span class="social-stat__value">${likeCount}</span>
            </span>
            <span class="social-stat" title="Fire">
              <img class="social-stat__icon" src="/assets/images/reactions/fire.svg" alt="Fire" loading="lazy" onerror="this.style.display='none'" />
              <span class="social-stat__value">${fireCount}</span>
            </span>
            <span class="social-stat" title="Wow">
              <img class="social-stat__icon" src="/assets/images/reactions/wow.svg" alt="Wow" loading="lazy" onerror="this.style.display='none'" />
              <span class="social-stat__value">${wowCount}</span>
            </span>
          </div>
        `
            : "";
        return `
        <article class="card">
          <h3 class="card__title">#${item.id} • ${item.track_file_name || "Без названия"}</h3>
          <p class="card__text">Автор: ${item.author || "unknown"}</p>
          <p class="card__meta">Создано: ${formatCreatedAt(item.created_at)}</p>
          ${socialStatsHtml}
          <div class="card__actions">
            <button class="btn btn--secondary" type="button" data-open-id="${item.id}">
              Просмотр
            </button>
            <button
              class="btn btn--secondary"
              type="button"
              data-download-id="${item.id}"
              data-task-id="${item.task_id}"
            >
              Скачать PDF
            </button>
          </div>
        </article>
      `;
      }
    )
    .join("");
}

function renderCommunityList(items) {
  renderTabCards(communityList, items, "Ничего не найдено", "Попробуй изменить поисковый запрос.", "community");
}

function renderPersonalList(items) {
  if (!isAuthenticated()) {
    renderTabCards(
      personalList,
      [],
      "Нужна авторизация",
      "Зарегистрируйся или войди, чтобы видеть личную библиотеку."
    );
    return;
  }
  renderTabCards(personalList, items, "Пока пусто", "У тебя пока нет сохраненных табулатур.");
}

async function loadCommunityTablatures() {
  const query = communitySearchInput && communitySearchInput.value ? communitySearchInput.value.trim() : "";
  try {
    setCommunityBusy(true);
    const payload = await api.fetchCommunityTablatures(query);
    const items = Array.isArray(payload.items) ? payload.items : [];
    renderCommunityList(items);
    setStatus(`Публичных табулатур: ${items.length}`);
  } catch (error) {
    renderTabCards(communityList, [], "Ошибка загрузки", getErrorMessage(error));
    setStatus(`Ошибка загрузки библиотеки:\n${getErrorMessage(error)}`);
  } finally {
    setCommunityBusy(false);
  }
}

async function loadPersonalTablatures() {
  if (!isAuthenticated()) {
    renderPersonalList([]);
    return;
  }
  try {
    if (personalRefreshBtn) personalRefreshBtn.disabled = true;
    const payload = await api.fetchPersonalTablatures(authState.token);
    const items = Array.isArray(payload.items) ? payload.items : [];
    renderPersonalList(items);
    setStatus(`Твоих табулатур: ${items.length}`);
  } catch (error) {
    renderTabCards(personalList, [], "Ошибка загрузки", getErrorMessage(error));
    setStatus(`Ошибка загрузки личной библиотеки:\n${getErrorMessage(error)}`);
  } finally {
    if (personalRefreshBtn) personalRefreshBtn.disabled = false;
  }
}

function wireTabCardActions(container, mode = "community") {
  if (!container) return;
  container.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;

    const openButton = target.closest("[data-open-id]");
    if (openButton) {
      const openId = openButton.getAttribute("data-open-id");
      if (openId) {
        if (mode === "personal") {
          window.location.href = `/edit/tablature/${encodeURIComponent(openId)}?mode=view&from=personal`;
        } else {
          window.location.href = `/community/tablatures/${encodeURIComponent(openId)}`;
        }
      }
      return;
    }

    const downloadButton = target.closest("[data-download-id]");
    if (!downloadButton) return;

    const tablatureId = downloadButton.getAttribute("data-download-id");
    const taskId = downloadButton.getAttribute("data-task-id");
    if (!tablatureId || !taskId) return;

    try {
      setStatus(`Скачиваю PDF табулатуры #${tablatureId}...`);
      const blob = await api.fetchPdfByJobId(taskId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `tablature-${tablatureId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setStatus(`PDF табулатуры #${tablatureId} скачан`);
    } catch (error) {
      setStatus(`Ошибка скачивания PDF:\n${getErrorMessage(error)}`);
    }
  });
}

async function refreshAuthFromToken() {
  if (!authState.token) {
    saveAuthState("", null);
    return;
  }
  try {
    const payload = await api.fetchAuthMe(authState.token);
    const user = payload.user || null;
    saveAuthState(authState.token, user);
  } catch {
    saveAuthState("", null);
  }
}

menuButtons.forEach((button) => {
  button.addEventListener("click", async () => {
    const viewName = button.dataset.view;
    activateView(viewName);
    window.location.hash = viewName;
    if (viewName === "community") {
      await loadCommunityTablatures();
    }
    if (viewName === "personal") {
      await loadPersonalTablatures();
    }
  });
});

if (communitySearchBtn) {
  communitySearchBtn.addEventListener("click", () => {
    loadCommunityTablatures();
  });
}

if (communityClearBtn) {
  communityClearBtn.addEventListener("click", () => {
    if (communitySearchInput) communitySearchInput.value = "";
    loadCommunityTablatures();
  });
}

if (communitySearchInput) {
  communitySearchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") loadCommunityTablatures();
  });
}

if (personalRefreshBtn) {
  personalRefreshBtn.addEventListener("click", () => {
    loadPersonalTablatures();
  });
}

wireTabCardActions(communityList, "community");
wireTabCardActions(personalList, "personal");

if (registerBtn) {
  registerBtn.addEventListener("click", async () => {
    const email = registerEmailInput ? registerEmailInput.value.trim() : "";
    const nickname = registerNicknameInput ? registerNicknameInput.value.trim() : "";
    const password = registerPasswordInput ? registerPasswordInput.value : "";
    if (!email || !nickname || !password) {
      setStatus("Для регистрации заполни email, nickname и пароль.");
      return;
    }

    try {
      setAuthBusy(true);
      setStatus("Регистрация...");
      await api.registerUser({ email, password, nickname });
      const loginPayload = await api.loginUser({ email, password });
      saveAuthState(loginPayload.access_token || "", loginPayload.user || null);
      closeGuestAuthPanel();
      setStatus("Регистрация и вход выполнены.");
      await loadPersonalTablatures();
    } catch (error) {
      setStatus(`Ошибка регистрации:\n${getErrorMessage(error)}`);
    } finally {
      setAuthBusy(false);
    }
  });
}

if (loginBtn) {
  loginBtn.addEventListener("click", async () => {
    const email = loginEmailInput ? loginEmailInput.value.trim() : "";
    const password = loginPasswordInput ? loginPasswordInput.value : "";
    if (!email || !password) {
      setStatus("Для входа заполни email и пароль.");
      return;
    }

    try {
      setAuthBusy(true);
      setStatus("Вход...");
      const payload = await api.loginUser({ email, password });
      saveAuthState(payload.access_token || "", payload.user || null);
      closeGuestAuthPanel();
      setStatus("Вход выполнен.");
      await loadPersonalTablatures();
    } catch (error) {
      setStatus(`Ошибка входа:\n${getErrorMessage(error)}`);
    } finally {
      setAuthBusy(false);
    }
  });
}

if (accountMenuBtn) {
  accountMenuBtn.addEventListener("click", () => {
    if (!isAuthenticated()) return;
    if (accountMenu && accountMenu.classList.contains("auth-user__menu--open")) {
      closeAccountMenu();
    } else {
      openAccountMenu();
    }
  });
}

if (guestAuthToggleBtn) {
  guestAuthToggleBtn.addEventListener("click", () => {
    if (isAuthenticated()) return;
    if (guestAuthPanel && guestAuthPanel.classList.contains("auth-guest__panel--open")) {
      closeGuestAuthPanel();
    } else {
      openGuestAuthPanel();
    }
  });
}

if (openAccountBtn) {
  openAccountBtn.addEventListener("click", () => {
    closeAccountMenu();
    window.location.href = "/account";
  });
}

if (logoutBtn) {
  logoutBtn.addEventListener("click", () => {
    saveAuthState("", null);
    renderPersonalList([]);
    setStatus("Выход выполнен.");
  });
}

document.addEventListener("click", (event) => {
  const target = event.target;
  if (!(target instanceof Node)) return;
  if (guestAuthToggleBtn && guestAuthToggleBtn.contains(target)) return;
  if (guestAuthPanel && guestAuthPanel.contains(target)) return;
  if (accountMenuBtn && accountMenuBtn.contains(target)) return;
  if (accountMenu && accountMenu.contains(target)) return;
  closeGuestAuthPanel();
  closeAccountMenu();
});

if (uploadBtn) {
  uploadBtn.addEventListener("click", async () => {
    const file = fileInput && fileInput.files ? fileInput.files[0] : null;
    if (!file) {
      setStatus("Выбери файл перед загрузкой.");
      return;
    }

    try {
      setBusy(true);
      setStatus("Отправка файла в backend...");

      const payload = await api.uploadAudio(file, authState.token);
      const job = payload.job || {};
      const mode = isAuthenticated() ? "Авторизованный режим: будет в личной библиотеке." : "Гостевой режим.";
      setStatus(`Файл отправлен.\njob_id: ${job.id}\nstatus: ${job.status}\n${mode}`);

      if (job.id && jobIdInput) {
        jobIdInput.value = job.id;
      }
      if (isAuthenticated()) {
        await loadPersonalTablatures();
      }
    } catch (error) {
      setStatus(`Ошибка загрузки:\n${getErrorMessage(error)}`);
    } finally {
      setBusy(false);
    }
  });
}

if (pdfBtn) {
  pdfBtn.addEventListener("click", async () => {
    const jobId = jobIdInput ? jobIdInput.value.trim() : "";
    if (!jobId) {
      setStatus("Введи job_id.");
      return;
    }

    try {
      setBusy(true);
      setStatus("Скачиваю PDF...");

      const pdfBlob = await api.fetchPdfByJobId(jobId);
      const pdfUrl = URL.createObjectURL(pdfBlob);
      const link = document.createElement("a");
      link.href = pdfUrl;
      link.download = `tablature-${jobId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(pdfUrl);
      setStatus(`PDF скачан для job_id: ${jobId}`);
    } catch (error) {
      setStatus(`Ошибка получения PDF:\n${getErrorMessage(error)}`);
    } finally {
      setBusy(false);
    }
  });
}

if (jsonBtn) {
  jsonBtn.addEventListener("click", async () => {
    const jobId = jobIdInput ? jobIdInput.value.trim() : "";
    if (!jobId) {
      setStatus("Введи job_id.");
      return;
    }

    try {
      setBusy(true);
      setStatus("Получаю JSON-табулатуру...");

      const payload = await api.fetchTablatureByJobId(jobId);
      if (jsonView) {
        jsonView.textContent = JSON.stringify(payload, null, 2);
      }
      setStatus(`JSON табулатура получена для job_id: ${jobId}`);
    } catch (error) {
      setStatus(`Ошибка получения JSON:\n${getErrorMessage(error)}`);
    } finally {
      setBusy(false);
    }
  });
}

async function init() {
  loadAuthStateFromStorage();
  renderAuthState();
  await refreshAuthFromToken();
  const hashView = String(window.location.hash || "").replace("#", "").trim().toLowerCase();
  if (hashView === "personal") {
    activateView("personal");
  } else {
    activateView("community");
  }
  await loadCommunityTablatures();
  await loadPersonalTablatures();
}

init();
