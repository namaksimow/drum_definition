import * as api from "./api.js?v=16";

const AUTH_TOKEN_KEY = "drum_auth_token";
const AUTH_USER_KEY = "drum_auth_user";
const ADMIN_CONSOLE_PATH = "/admin/console";
const AUTH_PAGE_PATH = "/auth";

function shouldKeepAdminOnCurrentPage() {
  const params = new URLSearchParams(window.location.search || "");
  return String(params.get("admin") || "").toLowerCase() === "1";
}

function isAdminUser(user) {
  const role = String(user?.role || "").toLowerCase();
  const email = String(user?.email || "").toLowerCase();
  return role === "admin" || email === "admin@mail.ru";
}

function redirectAfterAuthIfAdmin(user) {
  if (!isAdminUser(user)) return;
  if (window.location.pathname.startsWith("/admin")) return;
  if (shouldKeepAdminOnCurrentPage()) return;
  window.location.href = ADMIN_CONSOLE_PATH;
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

export async function initTopAuthWidget({ onAuthChanged } = {}) {
  const authEntryBtn = document.getElementById("authEntryBtn");
  const authPanel = document.getElementById("authPanel");
  const authPanelStatus = document.getElementById("authPanelStatus");
  const loginEmailInput = document.getElementById("loginEmail");
  const loginPasswordInput = document.getElementById("loginPassword");
  const loginBtn = document.getElementById("loginBtn");
  const registerEmailInput = document.getElementById("registerEmail");
  const registerNicknameInput = document.getElementById("registerNickname");
  const registerPasswordInput = document.getElementById("registerPassword");
  const registerBtn = document.getElementById("registerBtn");

  const state = {
    token: localStorage.getItem(AUTH_TOKEN_KEY) || "",
    user: null,
  };

  const emitAuthChanged = async () => {
    if (!onAuthChanged) return;
    await onAuthChanged({
      token: state.token,
      user: state.user,
    });
  };

  const setPanelStatus = (message) => {
    if (!authPanelStatus) return;
    authPanelStatus.textContent = message || "";
  };

  const closePanel = () => {
    if (!authPanel) return;
    authPanel.classList.remove("top-auth__panel--open");
  };

  const setButtonLabel = () => {
    if (!authEntryBtn) return;
    if (!state.user) {
      authEntryBtn.textContent = "Вход";
      return;
    }
    authEntryBtn.textContent = state.user.nickname || state.user.email || "Аккаунт";
  };

  const persistAuthState = () => {
    if (state.token) {
      localStorage.setItem(AUTH_TOKEN_KEY, state.token);
    } else {
      localStorage.removeItem(AUTH_TOKEN_KEY);
    }
    if (state.user) {
      localStorage.setItem(AUTH_USER_KEY, JSON.stringify(state.user));
    } else {
      localStorage.removeItem(AUTH_USER_KEY);
    }
  };

  const renderAccountActionsPanel = () => {
    if (!authPanel || !state.user) return;
    const admin = isAdminUser(state.user);
    const openActionHtml = admin
      ? ""
      : '<button class="btn btn--secondary" type="button" data-auth-action="open">Личный аккаунт</button>';
    authPanel.innerHTML = `
      <article class="top-auth__card">
        <h3 class="top-auth__title">Аккаунт</h3>
        <div class="top-auth__actions">
          ${openActionHtml}
          <button class="btn btn--secondary" type="button" data-auth-action="logout">Выйти</button>
        </div>
      </article>
    `;

    const openBtn = authPanel.querySelector('[data-auth-action="open"]');
    if (openBtn) {
      openBtn.addEventListener("click", () => {
        window.location.href = "/account";
      });
    }

    const logoutBtn = authPanel.querySelector('[data-auth-action="logout"]');
    if (logoutBtn) {
      logoutBtn.addEventListener("click", async () => {
        state.token = "";
        state.user = null;
        persistAuthState();
        setButtonLabel();
        closePanel();
        await emitAuthChanged();
        window.location.href = AUTH_PAGE_PATH;
      });
    }
  };

  const toggleAccountActionsPanel = () => {
    if (!authPanel || !state.user) return;
    renderAccountActionsPanel();
    authPanel.classList.toggle("top-auth__panel--open");
  };

  const hydrateUserFromToken = async () => {
    if (!state.token) return;
    try {
      const mePayload = await api.fetchAuthMe(state.token);
      if (mePayload && mePayload.user) {
        state.user = mePayload.user;
      }
    } catch {
      // no-op: keep user from login payload
    }
  };

  const verifyToken = async () => {
    if (!state.token) {
      state.user = null;
      setButtonLabel();
      await emitAuthChanged();
      return;
    }
    try {
      const payload = await api.fetchAuthMe(state.token);
      state.user = payload && payload.user ? payload.user : null;
    } catch {
      state.token = "";
      state.user = null;
      persistAuthState();
    }
    setButtonLabel();
    await emitAuthChanged();
  };

  if (authEntryBtn) {
    authEntryBtn.addEventListener("click", (event) => {
      event.preventDefault();
      if (state.user) {
        toggleAccountActionsPanel();
        return;
      }
      window.location.href = AUTH_PAGE_PATH;
    });
  }

  if (loginBtn) {
    loginBtn.addEventListener("click", async () => {
      const email = loginEmailInput ? loginEmailInput.value.trim() : "";
      const password = loginPasswordInput ? loginPasswordInput.value : "";
      if (!email || !password) {
        setPanelStatus("Для входа заполни email и пароль.");
        return;
      }

      try {
        loginBtn.disabled = true;
        if (registerBtn) registerBtn.disabled = true;
        setPanelStatus("Вход...");
        const payload = await api.loginUser({ email, password });
        state.token = payload && payload.access_token ? String(payload.access_token) : "";
        state.user = payload && payload.user ? payload.user : null;
        await hydrateUserFromToken();
        persistAuthState();
        setButtonLabel();
        closePanel();
        setPanelStatus("Вход выполнен.");
        await emitAuthChanged();
        redirectAfterAuthIfAdmin(state.user);
      } catch (error) {
        setPanelStatus(`Ошибка входа: ${getErrorMessage(error)}`);
      } finally {
        loginBtn.disabled = false;
        if (registerBtn) registerBtn.disabled = false;
      }
    });
  }

  if (registerBtn) {
    registerBtn.addEventListener("click", async () => {
      const email = registerEmailInput ? registerEmailInput.value.trim() : "";
      const nickname = registerNicknameInput ? registerNicknameInput.value.trim() : "";
      const password = registerPasswordInput ? registerPasswordInput.value : "";
      if (!email || !nickname || !password) {
        setPanelStatus("Для регистрации заполни email, nickname и пароль.");
        return;
      }

      try {
        registerBtn.disabled = true;
        if (loginBtn) loginBtn.disabled = true;
        setPanelStatus("Регистрация...");
        await api.registerUser({ email, password, nickname });
        const payload = await api.loginUser({ email, password });
        state.token = payload && payload.access_token ? String(payload.access_token) : "";
        state.user = payload && payload.user ? payload.user : null;
        await hydrateUserFromToken();
        persistAuthState();
        setButtonLabel();
        closePanel();
        setPanelStatus("Регистрация и вход выполнены.");
        await emitAuthChanged();
        redirectAfterAuthIfAdmin(state.user);
      } catch (error) {
        setPanelStatus(`Ошибка регистрации: ${getErrorMessage(error)}`);
      } finally {
        registerBtn.disabled = false;
        if (loginBtn) loginBtn.disabled = false;
      }
    });
  }

  document.addEventListener("click", (event) => {
    if (!authPanel || !authEntryBtn) return;
    const target = event.target;
    if (!(target instanceof Node)) return;
    if (authEntryBtn.contains(target)) return;
    if (authPanel.contains(target)) return;
    closePanel();
  });

  await verifyToken();
  redirectAfterAuthIfAdmin(state.user);
  return { ...state };
}
