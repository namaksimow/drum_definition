import * as api from "../services/api.js?v=12";
import { initTopAuthWidget } from "../services/top_auth_widget.js?v=12";

const subtitleEl = document.getElementById("subtitle");
const statusEl = document.getElementById("status");

const authorGuard = document.getElementById("authorGuard");
const editPanel = document.getElementById("editPanel");

const titleInput = document.getElementById("courseTitleInput");
const descriptionInput = document.getElementById("courseDescriptionInput");
const tagsInput = document.getElementById("courseTagsInput");
const visibilitySelect = document.getElementById("courseVisibilitySelect");
const coverFileInput = document.getElementById("coverFileInput");
const coverPreview = document.getElementById("coverPreview");
const currentCoverPreview = document.getElementById("currentCoverPreview");
const saveCourseBtn = document.getElementById("saveCourseBtn");
const deleteCourseBtn = document.getElementById("deleteCourseBtn");

let authToken = "";
let authUser = null;
let selectedCoverFile = null;
let currentCourse = null;

function setStatus(message) {
  if (statusEl) statusEl.textContent = message;
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
  if (parts.length < 3) return null;
  const value = Number(parts[2]);
  if (!Number.isInteger(value) || value <= 0) return null;
  return value;
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
  if (editPanel) editPanel.classList.toggle("is-hidden", !allowed);

  if (!subtitleEl) return;
  if (!authUser) {
    subtitleEl.innerHTML = "Для редактирования курса нужен вход под пользователем с ролью <code>автор</code>.";
    return;
  }
  const role = String(authUser.role || "").toLowerCase();
  const roleLabel = role === "author" ? "автор" : role === "admin" ? "администратор" : "пользователь";
  subtitleEl.innerHTML = `Вход выполнен: ${authUser.nickname || authUser.email}. Роль: ${roleLabel}.`;
}

function fillForm(course) {
  currentCourse = course;
  if (!course) return;
  if (titleInput) titleInput.value = course.title || "";
  if (descriptionInput) descriptionInput.value = course.description || "";
  if (tagsInput) tagsInput.value = Array.isArray(course.tags) ? course.tags.join(", ") : "";
  if (visibilitySelect) visibilitySelect.value = course.visibility || "private";

  if (subtitleEl) {
    subtitleEl.textContent = `Редактирование курса: ${course.title || `#${course.id}`} • Обновлен: ${formatDateTime(course.updated_at)}`;
  }

  if (currentCoverPreview) {
    const cover = String(course.cover_image_path || "");
    if (cover) {
      currentCoverPreview.src = cover;
      currentCoverPreview.classList.remove("is-hidden");
    } else {
      currentCoverPreview.src = "";
      currentCoverPreview.classList.add("is-hidden");
    }
  }
}

async function loadCourse() {
  const courseId = getCourseIdFromPath();
  if (!courseId) {
    setStatus("Некорректный id курса в URL.");
    return;
  }
  if (!authToken || !isAuthor()) {
    return;
  }

  try {
    setStatus("Загружаю курс...");
    const payload = await api.fetchPersonalCourses(authToken, String(courseId), { limit: 200, offset: 0 });
    const items = Array.isArray(payload.items) ? payload.items : [];
    const match = items.find((item) => Number(item.id) === Number(courseId)) || null;
    if (!match) {
      setStatus("Курс не найден или недоступен.");
      if (editPanel) editPanel.classList.add("is-hidden");
      if (authorGuard) authorGuard.classList.remove("is-hidden");
      return;
    }
    fillForm(match);
    setStatus("Курс загружен.");
  } catch (error) {
    setStatus(`Ошибка загрузки курса: ${getErrorMessage(error)}`);
  }
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

if (saveCourseBtn) {
  saveCourseBtn.addEventListener("click", async () => {
    const courseId = getCourseIdFromPath();
    if (!courseId || !authToken || !isAuthor()) {
      setStatus("Недостаточно прав.");
      return;
    }

    const title = titleInput ? titleInput.value.trim() : "";
    const description = descriptionInput ? descriptionInput.value.trim() : "";
    const visibility = visibilitySelect ? visibilitySelect.value : "private";
    const tags = parseTags(tagsInput ? tagsInput.value : "");

    if (!title) {
      setStatus("Укажи название курса.");
      return;
    }

    try {
      saveCourseBtn.disabled = true;
      if (deleteCourseBtn) deleteCourseBtn.disabled = true;

      let coverImagePath = undefined;
      if (selectedCoverFile) {
        setStatus("Загружаю новую обложку...");
        const uploadPayload = await api.uploadCourseCover(authToken, selectedCoverFile);
        coverImagePath = String(uploadPayload.cover_image_path || "");
      }

      setStatus("Сохраняю изменения...");
      const payload = await api.updatePersonalCourse(authToken, courseId, {
        title,
        description,
        visibility,
        tags,
        coverImagePath,
      });
      const course = payload && payload.course ? payload.course : null;
      if (course) fillForm(course);
      setStatus(
        course && course.updated_at
          ? `Курс обновлен: ${formatDateTime(course.updated_at)}`
          : "Курс обновлен."
      );
    } catch (error) {
      setStatus(`Ошибка сохранения курса: ${getErrorMessage(error)}`);
    } finally {
      saveCourseBtn.disabled = false;
      if (deleteCourseBtn) deleteCourseBtn.disabled = false;
    }
  });
}

if (deleteCourseBtn) {
  deleteCourseBtn.addEventListener("click", async () => {
    const courseId = getCourseIdFromPath();
    if (!courseId || !authToken || !isAuthor()) {
      setStatus("Недостаточно прав.");
      return;
    }
    const shouldDelete = window.confirm("Удалить курс без возможности восстановления?");
    if (!shouldDelete) return;

    try {
      deleteCourseBtn.disabled = true;
      if (saveCourseBtn) saveCourseBtn.disabled = true;
      setStatus("Удаляю курс...");
      await api.deletePersonalCourse(authToken, courseId);
      setStatus("Курс удален.");
      window.setTimeout(() => {
        window.location.href = "/account";
      }, 400);
    } catch (error) {
      setStatus(`Ошибка удаления курса: ${getErrorMessage(error)}`);
    } finally {
      deleteCourseBtn.disabled = false;
      if (saveCourseBtn) saveCourseBtn.disabled = false;
    }
  });
}

async function init() {
  await initTopAuthWidget({
    onAuthChanged: async ({ token, user }) => {
      authToken = token || "";
      authUser = user || null;
      applyAccessUi();
      if (isAuthor()) {
        await loadCourse();
      }
    },
  });

  applyAccessUi();
}

init();
