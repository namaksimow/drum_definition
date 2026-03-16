import * as api from "../services/api.js?v=12";
import { initTopAuthWidget } from "../services/top_auth_widget.js?v=8";

const subtitleEl = document.getElementById("subtitle");
const statusEl = document.getElementById("status");

const authorGuard = document.getElementById("authorGuard");
const createPanel = document.getElementById("createPanel");

const titleInput = document.getElementById("courseTitleInput");
const descriptionInput = document.getElementById("courseDescriptionInput");
const tagsInput = document.getElementById("courseTagsInput");
const visibilitySelect = document.getElementById("courseVisibilitySelect");
const coverFileInput = document.getElementById("coverFileInput");
const coverPreview = document.getElementById("coverPreview");
const createCourseBtn = document.getElementById("createCourseBtn");

let authToken = "";
let authUser = null;
let selectedCoverFile = null;

function setStatus(message) {
  if (statusEl) statusEl.textContent = message;
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

function parseTags(raw) {
  const result = [];
  const seen = new Set();
  String(raw || "")
    .split(",")
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean)
    .forEach((tag) => {
      if (!seen.has(tag)) {
        seen.add(tag);
        result.push(tag);
      }
    });
  return result;
}

function isAuthor() {
  return Boolean(authUser && String(authUser.role || "").toLowerCase() === "author");
}

function applyAccessUi() {
  const allowed = isAuthor();
  if (authorGuard) authorGuard.classList.toggle("is-hidden", allowed);
  if (createPanel) createPanel.classList.toggle("is-hidden", !allowed);

  if (!subtitleEl) return;
  if (!authUser) {
    subtitleEl.innerHTML = "Для создания курса нужен вход под пользователем с ролью <code>author</code>.";
    return;
  }
  subtitleEl.innerHTML = `Вход выполнен: ${authUser.nickname || authUser.email}. Роль: ${authUser.role || "user"}.`;
}

if (coverFileInput) {
  coverFileInput.addEventListener("change", () => {
    const file = coverFileInput.files && coverFileInput.files[0] ? coverFileInput.files[0] : null;
    selectedCoverFile = file;

    if (!file) {
      if (coverPreview) {
        coverPreview.src = "";
        coverPreview.classList.add("is-hidden");
      }
      return;
    }

    if (!String(file.type || "").startsWith("image/")) {
      setStatus("Неверный формат файла: выбери изображение.");
      coverFileInput.value = "";
      selectedCoverFile = null;
      if (coverPreview) {
        coverPreview.src = "";
        coverPreview.classList.add("is-hidden");
      }
      return;
    }

    if (coverPreview) {
      coverPreview.src = URL.createObjectURL(file);
      coverPreview.classList.remove("is-hidden");
    }
  });
}

if (createCourseBtn) {
  createCourseBtn.addEventListener("click", async () => {
    if (!authToken || !authUser) {
      setStatus("Нужна авторизация.");
      return;
    }
    if (!isAuthor()) {
      setStatus("Чтобы опубликовать курс, станьте автором.");
      return;
    }

    const title = titleInput ? titleInput.value.trim() : "";
    const description = descriptionInput ? descriptionInput.value.trim() : "";
    const visibility = visibilitySelect ? visibilitySelect.value : "public";
    const tags = parseTags(tagsInput ? tagsInput.value : "");

    if (!title) {
      setStatus("Укажи название курса.");
      return;
    }

    try {
      createCourseBtn.disabled = true;

      let coverImagePath = "";
      if (selectedCoverFile) {
        setStatus("Загружаю картинку...");
        const uploadPayload = await api.uploadCourseCover(authToken, selectedCoverFile);
        coverImagePath = String(uploadPayload.cover_image_path || "");
      }

      setStatus("Создаю курс...");
      const payload = await api.createCourse(authToken, {
        title,
        description,
        visibility,
        tags,
        coverImagePath,
      });

      const course = payload.course || {};
      setStatus(`Курс опубликован: ${course.title || title}`);
      window.setTimeout(() => {
        window.location.href = "/courses";
      }, 800);
    } catch (error) {
      setStatus(`Ошибка создания курса: ${getErrorMessage(error)}`);
    } finally {
      createCourseBtn.disabled = false;
    }
  });
}

async function init() {
  await initTopAuthWidget({
    onAuthChanged: async ({ token, user }) => {
      authToken = token || "";
      authUser = user || null;
      applyAccessUi();
    },
  });

  applyAccessUi();
}

init();
