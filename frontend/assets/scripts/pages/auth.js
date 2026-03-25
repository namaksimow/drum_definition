import * as api from "../services/api.js?v=9";

const AUTH_TOKEN_KEY = "drum_auth_token";
const AUTH_USER_KEY = "drum_auth_user";
const CREATE_TABLATURE_PATH = "/create";
const ADMIN_CONSOLE_PATH = "/admin/console";

const loginTabBtn = document.getElementById("loginTabBtn");
const registerTabBtn = document.getElementById("registerTabBtn");
const loginSection = document.getElementById("loginSection");
const registerSection = document.getElementById("registerSection");

const loginEmailInput = document.getElementById("loginEmail");
const loginPasswordInput = document.getElementById("loginPassword");
const registerEmailInput = document.getElementById("registerEmail");
const registerNicknameInput = document.getElementById("registerNickname");
const registerPasswordInput = document.getElementById("registerPassword");
const loginBtn = document.getElementById("loginBtn");
const registerBtn = document.getElementById("registerBtn");
const authStatus = document.getElementById("authStatus");

const guestModeBtn = document.getElementById("guestModeBtn");
const guestConfirmOverlay = document.getElementById("guestConfirmOverlay");
const guestConfirmBtn = document.getElementById("guestConfirmBtn");
const guestCancelBtn = document.getElementById("guestCancelBtn");

function setStatus(message) {
  if (!authStatus) return;
  authStatus.textContent = message || "";
}

function setBusy(isBusy) {
  if (loginBtn) loginBtn.disabled = isBusy;
  if (registerBtn) registerBtn.disabled = isBusy;
  if (loginEmailInput) loginEmailInput.disabled = isBusy;
  if (loginPasswordInput) loginPasswordInput.disabled = isBusy;
  if (registerEmailInput) registerEmailInput.disabled = isBusy;
  if (registerNicknameInput) registerNicknameInput.disabled = isBusy;
  if (registerPasswordInput) registerPasswordInput.disabled = isBusy;
  if (loginTabBtn) loginTabBtn.disabled = isBusy;
  if (registerTabBtn) registerTabBtn.disabled = isBusy;
  if (guestModeBtn) guestModeBtn.disabled = isBusy;
}

function getErrorMessage(error) {
  if (!error) return "Неизвестная ошибка";
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

function isAdminUser(user) {
  const role = String(user?.role || "").toLowerCase();
  const email = String(user?.email || "").toLowerCase();
  return role === "admin" || email === "admin@mail.ru";
}

function redirectAfterAuth(user) {
  if (isAdminUser(user)) {
    window.location.href = ADMIN_CONSOLE_PATH;
    return;
  }
  window.location.href = CREATE_TABLATURE_PATH;
}

function saveAuthState(token, user) {
  if (token) {
    localStorage.setItem(AUTH_TOKEN_KEY, String(token));
  } else {
    localStorage.removeItem(AUTH_TOKEN_KEY);
  }
  if (user) {
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(AUTH_USER_KEY);
  }
}

async function hydrateUser(token, fallbackUser = null) {
  if (!token) return fallbackUser;
  try {
    const payload = await api.fetchAuthMe(token);
    if (payload && payload.user) return payload.user;
  } catch {
    // no-op
  }
  return fallbackUser;
}

function showLoginTab() {
  if (loginSection) loginSection.classList.remove("is-hidden");
  if (registerSection) registerSection.classList.add("is-hidden");
  if (loginTabBtn) loginTabBtn.classList.add("auth-window__tab--active");
  if (registerTabBtn) registerTabBtn.classList.remove("auth-window__tab--active");
  setStatus("Готово к входу.");
}

function showRegisterTab() {
  if (registerSection) registerSection.classList.remove("is-hidden");
  if (loginSection) loginSection.classList.add("is-hidden");
  if (registerTabBtn) registerTabBtn.classList.add("auth-window__tab--active");
  if (loginTabBtn) loginTabBtn.classList.remove("auth-window__tab--active");
  setStatus("Заполни email, nickname и пароль для регистрации.");
}

function openGuestConfirm() {
  if (guestConfirmOverlay) guestConfirmOverlay.classList.remove("is-hidden");
}

function closeGuestConfirm() {
  if (guestConfirmOverlay) guestConfirmOverlay.classList.add("is-hidden");
}

async function handleLogin() {
  const email = loginEmailInput ? loginEmailInput.value.trim() : "";
  const password = loginPasswordInput ? loginPasswordInput.value : "";
  if (!email || !password) {
    setStatus("Для входа заполни email и пароль.");
    return;
  }

  try {
    setBusy(true);
    setStatus("Вход...");
    const payload = await api.loginUser({ email, password });
    const token = payload && payload.access_token ? String(payload.access_token) : "";
    let user = payload && payload.user ? payload.user : null;
    user = await hydrateUser(token, user);
    saveAuthState(token, user);
    setStatus("Вход выполнен. Перенаправляю...");
    redirectAfterAuth(user);
  } catch (error) {
    setStatus(`Ошибка входа: ${getErrorMessage(error)}`);
  } finally {
    setBusy(false);
  }
}

async function handleRegister() {
  const email = registerEmailInput ? registerEmailInput.value.trim() : "";
  const nickname = registerNicknameInput ? registerNicknameInput.value.trim() : "";
  const password = registerPasswordInput ? registerPasswordInput.value : "";
  if (!email || !nickname || !password) {
    setStatus("Для регистрации заполни email, nickname и пароль.");
    return;
  }

  try {
    setBusy(true);
    setStatus("Регистрация...");
    await api.registerUser({ email, password, nickname });
    const payload = await api.loginUser({ email, password });
    const token = payload && payload.access_token ? String(payload.access_token) : "";
    let user = payload && payload.user ? payload.user : null;
    user = await hydrateUser(token, user);
    saveAuthState(token, user);
    setStatus("Регистрация и вход выполнены. Перенаправляю...");
    redirectAfterAuth(user);
  } catch (error) {
    setStatus(`Ошибка регистрации: ${getErrorMessage(error)}`);
  } finally {
    setBusy(false);
  }
}

async function redirectIfAlreadyAuthenticated() {
  const token = localStorage.getItem(AUTH_TOKEN_KEY) || "";
  if (!token) return;
  try {
    setBusy(true);
    const payload = await api.fetchAuthMe(token);
    const user = payload && payload.user ? payload.user : null;
    if (user) {
      saveAuthState(token, user);
      redirectAfterAuth(user);
      return;
    }
  } catch {
    // invalid token; drop stale auth data
  } finally {
    setBusy(false);
  }
  saveAuthState("", null);
}

if (loginTabBtn) {
  loginTabBtn.addEventListener("click", () => {
    showLoginTab();
  });
}

if (registerTabBtn) {
  registerTabBtn.addEventListener("click", () => {
    showRegisterTab();
  });
}

if (loginBtn) {
  loginBtn.addEventListener("click", () => {
    handleLogin();
  });
}

if (registerBtn) {
  registerBtn.addEventListener("click", () => {
    handleRegister();
  });
}

if (guestModeBtn) {
  guestModeBtn.addEventListener("click", () => {
    openGuestConfirm();
  });
}

if (guestCancelBtn) {
  guestCancelBtn.addEventListener("click", () => {
    closeGuestConfirm();
  });
}

if (guestConfirmBtn) {
  guestConfirmBtn.addEventListener("click", () => {
    window.location.href = CREATE_TABLATURE_PATH;
  });
}

if (guestConfirmOverlay) {
  guestConfirmOverlay.addEventListener("click", (event) => {
    if (event.target === guestConfirmOverlay) {
      closeGuestConfirm();
    }
  });
}

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  closeGuestConfirm();
});

showLoginTab();
redirectIfAlreadyAuthenticated();
