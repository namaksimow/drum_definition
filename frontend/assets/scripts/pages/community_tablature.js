import * as api from "../services/api.js?v=11";

const AUTH_TOKEN_KEY = "drum_auth_token";

const metaEl = document.getElementById("meta");
const tabEl = document.getElementById("tabView");
const statusEl = document.getElementById("status");
const commentsListEl = document.getElementById("commentsList");
const commentInputEl = document.getElementById("commentInput");
const commentSubmitBtn = document.getElementById("commentSubmitBtn");
const reactionHintEl = document.getElementById("reactionHint");
const backLinkEl = document.getElementById("backLink");

const reactionLikeBtn = document.getElementById("reactionLikeBtn");
const reactionFireBtn = document.getElementById("reactionFireBtn");
const reactionWowBtn = document.getElementById("reactionWowBtn");
const reactionLikeCount = document.getElementById("reactionLikeCount");
const reactionFireCount = document.getElementById("reactionFireCount");
const reactionWowCount = document.getElementById("reactionWowCount");
const INSTRUMENT_LABELS = { hihat: "хэт", snare: "малый", kick: "бочка" };

function visibilityLabel(value) {
  return String(value || "").toLowerCase() === "public" ? "публичная" : "приватная";
}

const state = {
  tablatureId: null,
  authToken: "",
  authUser: null,
  currentReaction: null,
  adminViewRequested: false,
  adminViewEnabled: false,
};

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

function getTablatureIdFromPath() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  const last = parts[parts.length - 1];
  const id = Number(last);
  return Number.isFinite(id) ? id : null;
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

function isAdminUser(user) {
  const role = String(user?.role || "").toLowerCase();
  const email = String(user?.email || "").toLowerCase();
  return role === "admin" || email === "admin@mail.ru";
}

function updateAdminMode() {
  state.adminViewEnabled = Boolean(
    state.adminViewRequested && state.authToken && state.authUser && isAdminUser(state.authUser)
  );
}

function asTabData(jsonFormat) {
  if (!jsonFormat) return null;
  if (typeof jsonFormat === "object") return jsonFormat;
  if (typeof jsonFormat === "string") {
    try {
      return JSON.parse(jsonFormat);
    } catch {
      return null;
    }
  }
  return null;
}

function formatAsciiTablature(tabData) {
  if (!tabData || !Array.isArray(tabData.lines) || !tabData.lines.length) {
    return "Нет данных табулатуры";
  }

  const out = [];
  tabData.lines.forEach((line) => {
    const bars = Array.isArray(line.bars) ? line.bars : [];
    const startSec = Number(line.start_sec);
    const endSec = Number(line.end_sec);
    const startSecText = Number.isFinite(startSec) ? `${startSec.toFixed(3)}s` : `${line.start_sec}s`;
    const endSecText = Number.isFinite(endSec) ? `${endSec.toFixed(3)}s` : `${line.end_sec}s`;

    out.push(`строка ${line.line_number} | такты ${line.first_bar}-${line.last_bar} | ${startSecText} - ${endSecText}`);

    ["hihat", "snare", "kick"].forEach((instrument) => {
      const row = bars
        .map((bar) => {
          const pattern = bar?.instruments?.[instrument]?.pattern || "";
          return `|${pattern}|`;
        })
        .join("");
      const label = INSTRUMENT_LABELS[instrument] || instrument;
      out.push(`${label.padEnd(5, " ")}${row}`);
    });

    out.push("");
  });

  return out.join("\n").trimEnd();
}

function renderComments(items) {
  if (!commentsListEl) return;
  if (!items.length) {
    commentsListEl.innerHTML = `<p class="comment-item__head">Комментариев пока нет.</p>`;
    return;
  }

  commentsListEl.innerHTML = items
    .map((item) => {
      const actions = state.adminViewEnabled
        ? `
          <div class="comment-item__actions">
            <button class="btn btn--secondary" type="button" data-delete-comment-id="${item.id}">Удалить</button>
          </div>
        `
        : "";
      return `
        <article class="comment-item">
          <p class="comment-item__head">${escapeHtml(item.author || "неизвестно")} • ${formatCreatedAt(item.created_at)}</p>
          <p class="comment-item__body">${escapeHtml(item.content || "")}</p>
          ${actions}
        </article>
      `;
    })
    .join("");
}

function updateReactionButtons(counts = {}, myReaction = null) {
  const like = Number(counts.like || 0);
  const fire = Number(counts.fire || 0);
  const wow = Number(counts.wow || 0);
  if (reactionLikeCount) reactionLikeCount.textContent = String(like);
  if (reactionFireCount) reactionFireCount.textContent = String(fire);
  if (reactionWowCount) reactionWowCount.textContent = String(wow);

  const active = String(myReaction || "").toLowerCase();
  if (reactionLikeBtn) reactionLikeBtn.classList.toggle("reaction-btn--active", active === "like");
  if (reactionFireBtn) reactionFireBtn.classList.toggle("reaction-btn--active", active === "fire");
  if (reactionWowBtn) reactionWowBtn.classList.toggle("reaction-btn--active", active === "wow");
}

function applyAuthUI() {
  const isAuthed = Boolean(state.authToken && state.authUser);
  const isAdminMode = Boolean(state.adminViewEnabled);
  if (commentInputEl) commentInputEl.disabled = !isAuthed || isAdminMode;
  if (commentSubmitBtn) commentSubmitBtn.disabled = !isAuthed || isAdminMode;
  if (reactionLikeBtn) reactionLikeBtn.disabled = isAdminMode;
  if (reactionFireBtn) reactionFireBtn.disabled = isAdminMode;
  if (reactionWowBtn) reactionWowBtn.disabled = isAdminMode;
  if (reactionHintEl) {
    if (isAdminMode) {
      reactionHintEl.textContent = "Режим администратора: можно просматривать табулатуру и удалять комментарии.";
    } else if (isAuthed) {
      reactionHintEl.textContent = `Авторизован как ${state.authUser.nickname || state.authUser.email}.`;
    } else {
      reactionHintEl.textContent = "Войди в аккаунт, чтобы оставлять реакции и комментарии.";
    }
  }
}

function applyBackLink() {
  if (!backLinkEl) return;
  backLinkEl.setAttribute("href", state.adminViewEnabled ? "/admin/console" : "/");
}

async function loadCommunityTablature() {
  if (!state.tablatureId) return;
  const payload = state.adminViewEnabled
    ? await api.fetchAdminTablatureById(state.authToken, state.tablatureId)
    : await api.fetchCommunityTablatureById(state.tablatureId);
  const tablature = payload.tablature || {};
  const visibilityText = state.adminViewEnabled ? ` • Видимость: ${visibilityLabel(tablature.visibility)}` : "";
  metaEl.textContent =
    `#${tablature.id} • Автор: ${tablature.author || "неизвестно"} • Создано: ${formatCreatedAt(tablature.created_at)}` +
    visibilityText;
  const tabData = asTabData(tablature.json_format);
  tabEl.textContent = formatAsciiTablature(tabData);
}

async function loadComments() {
  if (!state.tablatureId) return;
  const payload = state.adminViewEnabled
    ? await api.fetchAdminTablatureComments(state.authToken, state.tablatureId, { limit: 150, offset: 0 })
    : await api.fetchCommunityTablatureComments(state.tablatureId, { limit: 150, offset: 0 });
  const items = Array.isArray(payload.items) ? payload.items : [];
  renderComments(items);
}

async function loadReactions() {
  if (!state.tablatureId) return;
  if (state.adminViewEnabled) {
    state.currentReaction = null;
    updateReactionButtons({}, null);
    return;
  }
  const payload = await api.fetchCommunityTablatureReactions(state.tablatureId, state.authToken || "");
  const reactions = payload.reactions || {};
  state.currentReaction = reactions.my_reaction || null;
  updateReactionButtons(reactions.counts || {}, state.currentReaction);
}

async function refreshAll() {
  await loadCommunityTablature();
  await loadComments();
  await loadReactions();
}

async function initAuth() {
  const token = localStorage.getItem(AUTH_TOKEN_KEY) || "";
  state.authToken = token;
  state.authUser = null;
  if (!token) return;
  try {
    const payload = await api.fetchAuthMe(token);
    state.authUser = payload.user || null;
  } catch {
    state.authToken = "";
    state.authUser = null;
  }
  updateAdminMode();
}

async function onReactionClick(reactionType) {
  if (state.adminViewEnabled) {
    setStatus("В режиме администратора реакции отключены.");
    return;
  }
  if (!state.authToken || !state.authUser) {
    setStatus("Нужно авторизоваться, чтобы оставить реакцию.");
    return;
  }
  if (!state.tablatureId) return;

  try {
    const payload = await api.setCommunityTablatureReaction(state.authToken, state.tablatureId, reactionType);
    const reactions = payload.reactions || {};
    state.currentReaction = reactions.my_reaction || null;
    updateReactionButtons(reactions.counts || {}, state.currentReaction);
    setStatus("Реакция обновлена.");
  } catch (error) {
    setStatus(`Ошибка реакции: ${getErrorMessage(error)}`);
  }
}

async function onSubmitComment() {
  if (state.adminViewEnabled) {
    setStatus("В режиме администратора комментарии не добавляются.");
    return;
  }
  if (!state.authToken || !state.authUser) {
    setStatus("Нужно авторизоваться, чтобы оставить комментарий.");
    return;
  }
  if (!state.tablatureId) return;
  const content = commentInputEl ? commentInputEl.value.trim() : "";
  if (!content) {
    setStatus("Комментарий пустой.");
    return;
  }

  try {
    if (commentSubmitBtn) commentSubmitBtn.disabled = true;
    await api.createCommunityTablatureComment(state.authToken, state.tablatureId, content);
    if (commentInputEl) commentInputEl.value = "";
    await loadComments();
    setStatus("Комментарий добавлен.");
  } catch (error) {
    setStatus(`Ошибка комментария: ${getErrorMessage(error)}`);
  } finally {
    if (commentSubmitBtn) commentSubmitBtn.disabled = !Boolean(state.authToken && state.authUser);
  }
}

async function onDeleteComment(commentId) {
  if (!state.adminViewEnabled || !state.authToken || !state.tablatureId) {
    setStatus("Удаление комментария доступно только администратору.");
    return;
  }
  if (!window.confirm("Удалить комментарий?")) return;

  try {
    await api.deleteAdminTablatureComment(state.authToken, state.tablatureId, commentId);
    await loadComments();
    setStatus("Комментарий удален.");
  } catch (error) {
    setStatus(`Ошибка удаления комментария: ${getErrorMessage(error)}`);
  }
}

if (reactionLikeBtn) {
  reactionLikeBtn.addEventListener("click", () => onReactionClick("like"));
}
if (reactionFireBtn) {
  reactionFireBtn.addEventListener("click", () => onReactionClick("fire"));
}
if (reactionWowBtn) {
  reactionWowBtn.addEventListener("click", () => onReactionClick("wow"));
}
if (commentSubmitBtn) {
  commentSubmitBtn.addEventListener("click", () => onSubmitComment());
}
if (commentsListEl) {
  commentsListEl.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const button = target.closest("[data-delete-comment-id]");
    if (!button) return;
    const commentId = Number(button.getAttribute("data-delete-comment-id"));
    if (!Number.isFinite(commentId)) return;
    onDeleteComment(commentId);
  });
}

async function init() {
  state.tablatureId = getTablatureIdFromPath();
  if (!state.tablatureId) {
    metaEl.textContent = "Некорректный id табулатуры.";
    tabEl.textContent = "Ошибка: не удалось определить id.";
    return;
  }

  const params = new URLSearchParams(window.location.search || "");
  state.adminViewRequested = String(params.get("admin") || "").toLowerCase() === "1";

  await initAuth();
  updateAdminMode();
  applyBackLink();
  applyAuthUI();

  try {
    await refreshAll();
    if (state.adminViewRequested && !state.adminViewEnabled) {
      setStatus("Режим администратора недоступен. Показан публичный просмотр.");
    } else {
      setStatus("Готово.");
    }
  } catch (error) {
    metaEl.textContent = "Ошибка загрузки.";
    tabEl.textContent = getErrorMessage(error);
    setStatus(`Ошибка: ${getErrorMessage(error)}`);
  }
}

init();
