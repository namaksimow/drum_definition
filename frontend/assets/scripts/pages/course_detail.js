import * as api from "../services/api.js?v=15";
import { initTopAuthWidget } from "../services/top_auth_widget.js?v=8";

const titleEl = document.getElementById("courseTitle");
const subtitleEl = document.getElementById("courseSubtitle");
const statusEl = document.getElementById("status");
const lessonEditorPanel = document.getElementById("lessonEditorPanel");
const lessonsList = document.getElementById("lessonsList");

const newLessonTitle = document.getElementById("newLessonTitle");
const newLessonContent = document.getElementById("newLessonContent");
const newLessonPosition = document.getElementById("newLessonPosition");
const addLessonBtn = document.getElementById("addLessonBtn");

let authToken = "";
let authUser = null;
let courseId = null;
let editableRequested = false;
let editableMode = false;
let lastProgressErrorMessage = "";
let lastCourseUpdatedAtText = "";
let courseVisitTracked = false;

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

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function getCourseIdFromPath() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  const last = Number(parts[parts.length - 1]);
  if (!Number.isInteger(last) || last <= 0) return null;
  return last;
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

function formatUpdatedAt(value) {
  return formatCreatedAt(value);
}

function canEditRequestedLessons() {
  return editableRequested && !!authToken && String(authUser?.role || "").toLowerCase() === "author";
}

function setEditorVisible(visible) {
  if (!lessonEditorPanel) return;
  lessonEditorPanel.classList.toggle("is-hidden", !visible);
}

async function loadCourseMeta() {
  if (!courseId) return;
  try {
    const payload = editableMode
      ? await api.fetchPersonalCourses(authToken, String(courseId), { limit: 200, offset: 0 })
      : await api.fetchCourses(String(courseId), { limit: 200, offset: 0 });
    const items = Array.isArray(payload.items) ? payload.items : [];
    const course = items.find((item) => Number(item.id) === Number(courseId)) || null;
    if (!course) {
      if (titleEl) titleEl.textContent = `Курс #${courseId}`;
      if (subtitleEl) subtitleEl.textContent = "Курс не найден.";
      return;
    }
    if (titleEl) titleEl.textContent = course.title || `Курс #${courseId}`;
    lastCourseUpdatedAtText = formatUpdatedAt(course.updated_at);
    if (subtitleEl) {
      let mode = editableMode ? "Режим редактирования уроков" : "Режим просмотра уроков";
      if (!editableMode && authToken) {
        mode = "Режим просмотра уроков (можно отмечать пройденные)";
      }
      subtitleEl.textContent = `Автор: ${course.author || "unknown"} • Обновлен: ${lastCourseUpdatedAtText} • ${mode}`;
    }
  } catch {
    lastCourseUpdatedAtText = "";
    if (titleEl) titleEl.textContent = `Курс #${courseId}`;
    if (subtitleEl) subtitleEl.textContent = editableMode ? "Редактирование уроков" : "Просмотр уроков";
  }
}

function mergeProgressIntoLessons(lessons, progressItems) {
  const progressByLessonId = new Map();
  for (const item of progressItems) {
    if (!item || typeof item !== "object") continue;
    const lessonId = Number(item.lesson_id);
    if (!Number.isFinite(lessonId)) continue;
    progressByLessonId.set(lessonId, Boolean(item.is_completed));
  }
  return lessons.map((item) => {
    const lessonId = Number(item.id);
    return {
      ...item,
      is_completed: progressByLessonId.get(lessonId) === true,
    };
  });
}

function renderLessons(items) {
  if (!lessonsList) return;
  if (!items.length) {
    lessonsList.innerHTML = `
      <article class="lesson">
        <h3 class="lesson__title">Уроков пока нет</h3>
        <p class="lesson__content">Список уроков пуст.</p>
      </article>
    `;
    return;
  }

  if (!editableMode) {
    const canTrack = Boolean(authToken);
    lessonsList.innerHTML = items
      .map(
        (item) => `
          <article class="lesson ${item.is_completed ? "lesson--completed" : ""}">
            <h3 class="lesson__title">${escapeHtml(item.title || "Без названия")}</h3>
            <p class="lesson__meta">Позиция: ${Number(item.position) || 1} • Обновлен: ${formatCreatedAt(item.updated_at)}</p>
            <p class="lesson__content">${escapeHtml(item.content || "")}</p>
            <div class="lesson__progress">
              <label class="lesson__progress-label">
                <input
                  type="checkbox"
                  data-progress-lesson-id="${item.id}"
                  ${item.is_completed ? "checked" : ""}
                  ${canTrack ? "" : "disabled"}
                />
                Пройдено
              </label>
            </div>
          </article>
        `
      )
      .join("");
    return;
  }

  lessonsList.innerHTML = items
    .map(
      (item) => `
        <article class="lesson" data-lesson-id="${item.id}">
          <label class="field-label" for="lesson-title-${item.id}">Название урока</label>
          <input class="field-input" id="lesson-title-${item.id}" data-lesson-title value="${escapeHtml(item.title || "")}" />
          <label class="field-label" for="lesson-content-${item.id}">Содержание</label>
          <textarea class="field-input field-textarea" id="lesson-content-${item.id}" data-lesson-content>${escapeHtml(item.content || "")}</textarea>
          <label class="field-label" for="lesson-position-${item.id}">Позиция</label>
          <input class="field-input" id="lesson-position-${item.id}" data-lesson-position type="number" min="1" step="1" value="${Number(item.position) || 1}" />
          <div class="lesson__actions">
            <button class="btn btn--primary" type="button" data-lesson-save-id="${item.id}">Сохранить</button>
            <button class="btn btn--secondary" type="button" data-lesson-delete-id="${item.id}">Удалить</button>
          </div>
        </article>
      `
    )
    .join("");
}

async function loadLessonsAndRender() {
  if (!courseId) return;
  editableMode = false;

  try {
    let payload;
    if (canEditRequestedLessons()) {
      try {
        payload = await api.fetchPersonalCourseLessons(authToken, courseId);
        editableMode = true;
      } catch (error) {
        editableMode = false;
        setStatus(`Редактирование недоступно: ${getErrorMessage(error)}. Показан режим просмотра.`);
        payload = await api.fetchPublicCourseLessons(courseId);
      }
    } else {
      payload = await api.fetchPublicCourseLessons(courseId);
    }

    let items = Array.isArray(payload.items) ? payload.items : [];
    lastProgressErrorMessage = "";
    if (!editableMode && authToken) {
      try {
        const progressPayload = await api.fetchPersonalCourseLessonProgress(authToken, courseId);
        const progressItems = Array.isArray(progressPayload.items) ? progressPayload.items : [];
        items = mergeProgressIntoLessons(items, progressItems);
      } catch (error) {
        lastProgressErrorMessage = getErrorMessage(error);
      }
    }
    renderLessons(items);
    setEditorVisible(editableMode);
    await loadCourseMeta();
    if (!editableMode && authToken && !courseVisitTracked) {
      try {
        await api.trackPersonalCourseVisit(authToken, courseId);
        courseVisitTracked = true;
      } catch {
        // Статистика посещений не должна ломать просмотр курса.
      }
    }
    if (lastProgressErrorMessage) {
      setStatus(`Уроки загружены, но прогресс недоступен: ${lastProgressErrorMessage}`);
    } else if (!statusEl || statusEl.textContent === "Готово к работе.") {
      setStatus(`Загружено уроков: ${items.length}`);
    }
  } catch (error) {
    renderLessons([]);
    setEditorVisible(false);
    await loadCourseMeta();
    setStatus(`Ошибка загрузки уроков: ${getErrorMessage(error)}`);
  }
}

if (addLessonBtn) {
  addLessonBtn.addEventListener("click", async () => {
    if (!editableMode || !authToken || !courseId) {
      setStatus("Редактирование уроков недоступно.");
      return;
    }
    const title = newLessonTitle ? newLessonTitle.value.trim() : "";
    if (!title) {
      setStatus("Укажи название урока.");
      return;
    }
    const content = newLessonContent ? newLessonContent.value.trim() : "";
    const rawPosition = newLessonPosition ? newLessonPosition.value.trim() : "";
    const position = rawPosition ? Number(rawPosition) : undefined;

    try {
      addLessonBtn.disabled = true;
      await api.createPersonalCourseLesson(authToken, courseId, {
        title,
        content,
        position: Number.isFinite(position) ? position : undefined,
      });
      if (newLessonTitle) newLessonTitle.value = "";
      if (newLessonContent) newLessonContent.value = "";
      if (newLessonPosition) newLessonPosition.value = "";
      await loadLessonsAndRender();
      setStatus(
        lastCourseUpdatedAtText
          ? `Урок добавлен. Курс обновлен: ${lastCourseUpdatedAtText}`
          : "Урок добавлен."
      );
    } catch (error) {
      setStatus(`Ошибка добавления урока: ${getErrorMessage(error)}`);
    } finally {
      addLessonBtn.disabled = false;
    }
  });
}

if (lessonsList) {
  lessonsList.addEventListener("change", async (event) => {
    if (editableMode || !authToken || !courseId) return;
    const target = event.target;
    if (!(target instanceof HTMLInputElement)) return;
    if (!target.matches("[data-progress-lesson-id]")) return;

    const lessonId = Number(target.getAttribute("data-progress-lesson-id"));
    if (!Number.isFinite(lessonId)) return;

    const lessonCard = target.closest(".lesson");
    const completed = target.checked;
    if (lessonCard) {
      lessonCard.classList.toggle("lesson--completed", completed);
    }
    target.disabled = true;
    try {
      await api.setPersonalCourseLessonProgress(authToken, courseId, lessonId, completed);
      setStatus(completed ? "Урок отмечен как пройденный." : "Отметка о прохождении снята.");
    } catch (error) {
      target.checked = !completed;
      if (lessonCard) {
        lessonCard.classList.toggle("lesson--completed", !completed);
      }
      setStatus(`Ошибка обновления прогресса: ${getErrorMessage(error)}`);
    } finally {
      target.disabled = false;
    }
  });

  lessonsList.addEventListener("click", async (event) => {
    if (!editableMode || !authToken || !courseId) return;
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;

    const saveBtn = target.closest("[data-lesson-save-id]");
    if (saveBtn) {
      const lessonId = Number(saveBtn.getAttribute("data-lesson-save-id"));
      const lessonCard = saveBtn.closest("[data-lesson-id]");
      if (!Number.isFinite(lessonId) || !lessonCard) return;
      const titleInput = lessonCard.querySelector("[data-lesson-title]");
      const contentInput = lessonCard.querySelector("[data-lesson-content]");
      const positionInput = lessonCard.querySelector("[data-lesson-position]");

      const title = titleInput instanceof HTMLInputElement ? titleInput.value.trim() : "";
      const content = contentInput instanceof HTMLTextAreaElement ? contentInput.value.trim() : "";
      const rawPosition = positionInput instanceof HTMLInputElement ? positionInput.value.trim() : "";
      const position = rawPosition ? Number(rawPosition) : undefined;

      if (!title) {
        setStatus("Название урока не может быть пустым.");
        return;
      }
      try {
        await api.updatePersonalCourseLesson(authToken, courseId, lessonId, {
          title,
          content,
          position: Number.isFinite(position) ? position : undefined,
        });
        await loadLessonsAndRender();
        setStatus(
          lastCourseUpdatedAtText
            ? `Урок сохранен. Курс обновлен: ${lastCourseUpdatedAtText}`
            : "Урок сохранен."
        );
      } catch (error) {
        setStatus(`Ошибка сохранения урока: ${getErrorMessage(error)}`);
      }
      return;
    }

    const deleteBtn = target.closest("[data-lesson-delete-id]");
    if (!deleteBtn) return;
    const lessonId = Number(deleteBtn.getAttribute("data-lesson-delete-id"));
    if (!Number.isFinite(lessonId)) return;
    if (!window.confirm("Удалить урок?")) return;

    try {
      await api.deletePersonalCourseLesson(authToken, courseId, lessonId);
      setStatus("Урок удален.");
      await loadLessonsAndRender();
    } catch (error) {
      setStatus(`Ошибка удаления урока: ${getErrorMessage(error)}`);
    }
  });
}

async function init() {
  courseId = getCourseIdFromPath();
  if (!courseId) {
    setStatus("Некорректный id курса.");
    return;
  }
  courseVisitTracked = false;

  const params = new URLSearchParams(window.location.search || "");
  editableRequested = String(params.get("editable") || "").toLowerCase() === "1";

  await initTopAuthWidget({
    onAuthChanged: async ({ token, user }) => {
      authToken = token || "";
      authUser = user || null;
      await loadLessonsAndRender();
    },
  });

  await loadLessonsAndRender();
}

init();
