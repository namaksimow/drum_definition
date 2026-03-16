import * as api from "../services/api.js?v=9";
import { initTopAuthWidget } from "../services/top_auth_widget.js?v=8";

const AUTH_TOKEN_KEY = "drum_auth_token";
const statusEl = document.getElementById("status");
const fileInput = document.getElementById("fileInput");
const titleInput = document.getElementById("titleInput");
const visibilitySelect = document.getElementById("visibilitySelect");
const createBtn = document.getElementById("createBtn");
const saveBtn = document.getElementById("saveBtn");
const pdfBtn = document.getElementById("pdfBtn");
const jsonBtn = document.getElementById("jsonBtn");
const jobIdText = document.getElementById("jobIdText");
const jsonView = document.getElementById("jsonView");
const progressOverlay = document.getElementById("progressOverlay");
const progressFill = document.getElementById("progressFill");
const progressPercent = document.getElementById("progressPercent");
const progressText = document.getElementById("progressText");

let jobId = "";
let authToken = "";
let currentProgress = 0;
let progressTimer = null;

function ensureCoursesMenuButton() {
  const menu = document.querySelector(".menu");
  if (!menu) return;
  const existing = menu.querySelector('a.menu__btn[href="/courses"]');
  if (existing) return;

  const link = document.createElement("a");
  link.className = "menu__btn";
  link.href = "/courses";
  link.textContent = "Курсы";
  menu.appendChild(link);
}

async function waitForPersonalRowByJobId(targetJobId, maxAttempts = 12, delayMs = 2500) {
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const listPayload = await api.fetchPersonalTablatures(authToken);
    const items = Array.isArray(listPayload.items) ? listPayload.items : [];
    const row = items.find((x) => String(x.task_id) === String(targetJobId));
    if (row) return row;
    if (attempt < maxAttempts) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }
  return null;
}

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

function isMp3(file) {
  if (!file || !file.name) return false;
  return file.name.toLowerCase().endsWith(".mp3");
}

function setBusy(isBusy) {
  if (createBtn) createBtn.disabled = isBusy;
  if (saveBtn) saveBtn.disabled = isBusy || !authToken;
  if (pdfBtn) pdfBtn.disabled = isBusy;
  if (jsonBtn) jsonBtn.disabled = isBusy;
}

function updateJobId(value) {
  jobId = value || "";
  if (jobIdText) jobIdText.textContent = jobId || "-";
}

function setProgress(value, message) {
  currentProgress = Math.max(0, Math.min(100, Number(value) || 0));
  if (progressFill) progressFill.style.width = `${currentProgress}%`;
  if (progressPercent) progressPercent.textContent = `${Math.round(currentProgress)}%`;
  if (progressText && message) progressText.textContent = message;
}

function startProgressTimer() {
  if (progressTimer) return;
  progressTimer = setInterval(() => {
    if (currentProgress < 92) {
      setProgress(currentProgress + 1);
    }
  }, 900);
}

function stopProgressTimer() {
  if (!progressTimer) return;
  clearInterval(progressTimer);
  progressTimer = null;
}

function openProgressOverlay() {
  if (progressOverlay) progressOverlay.classList.remove("is-hidden");
}

function closeProgressOverlay() {
  if (progressOverlay) progressOverlay.classList.add("is-hidden");
}

function statusToText(status) {
  if (status === "queued") return "Файл в очереди на обработку...";
  if (status === "processing") return "Идёт обработка аудио и построение табулатуры...";
  if (status === "done") return "Табулатура готова.";
  if (status === "failed") return "Обработка завершилась ошибкой.";
  return "Получаю статус обработки...";
}

function statusToProgressFloor(status) {
  if (status === "queued") return 20;
  if (status === "processing") return 45;
  if (status === "done") return 100;
  if (status === "failed") return 100;
  return 10;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitUntilJobFinished(targetJobId) {
  openProgressOverlay();
  setProgress(8, "Задача создана. Подготавливаю обработку...");
  startProgressTimer();

  const maxAttempts = 300;
  const delayMs = 2000;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    let status = "queued";
    try {
      const payload = await api.fetchJobById(targetJobId);
      status = String(payload?.job?.status || "queued").toLowerCase();
    } catch {
      if (attempt % 5 === 0) {
        setProgress(currentProgress, "Проверяю состояние задачи...");
      }
      await sleep(delayMs);
      continue;
    }

    const floor = statusToProgressFloor(status);
    if (floor > currentProgress) {
      setProgress(floor, statusToText(status));
    } else {
      setProgress(currentProgress, statusToText(status));
    }

    if (status === "done") {
      stopProgressTimer();
      setProgress(100, "Табулатура готова.");
      await sleep(500);
      closeProgressOverlay();
      return;
    }
    if (status === "failed") {
      stopProgressTimer();
      setProgress(100, "Ошибка обработки.");
      await sleep(500);
      closeProgressOverlay();
      throw new Error("Обработка завершилась со статусом failed");
    }

    await sleep(delayMs);
  }

  stopProgressTimer();
  closeProgressOverlay();
  throw new Error("Превышено время ожидания завершения обработки");
}

if (fileInput) {
  fileInput.addEventListener("change", () => {
    const file = fileInput.files && fileInput.files[0] ? fileInput.files[0] : null;
    if (!file) return;
    if (!isMp3(file)) {
      setStatus("Выбран неверный файл. Разрешены только .mp3");
      fileInput.value = "";
    }
  });
}

if (createBtn) {
  createBtn.addEventListener("click", async () => {
    const file = fileInput && fileInput.files ? fileInput.files[0] : null;
    if (!file) {
      setStatus("Выбери MP3 файл.");
      return;
    }
    if (!isMp3(file)) {
      setStatus("Разрешены только файлы с расширением .mp3");
      return;
    }

    const tablatureName = titleInput ? titleInput.value.trim() : "";
    try {
      setBusy(true);
      setStatus("Создание задачи...");
      const payload = await api.uploadAudio(file, authToken, tablatureName);
      const job = payload.job || {};
      updateJobId(job.id ? String(job.id) : "");
      if (!jobId) {
        throw new Error("В ответе сервиса не найден job_id");
      }
      await waitUntilJobFinished(jobId);
      setStatus(`Табулатура успешно создана.\njob_id: ${jobId}\nstatus: done`);
    } catch (error) {
      setStatus(`Ошибка создания:\n${getErrorMessage(error)}`);
    } finally {
      stopProgressTimer();
      closeProgressOverlay();
      setBusy(false);
    }
  });
}

if (saveBtn) {
  saveBtn.addEventListener("click", async () => {
    if (!jobId) {
      setStatus("Сначала создай табулатуру, чтобы получить job_id.");
      return;
    }
    if (!authToken) {
      setStatus("Сохранение в личную библиотеку доступно только зарегистрированному пользователю.");
      return;
    }

    const newName = titleInput ? titleInput.value.trim() : "";
    const visibility = visibilitySelect ? visibilitySelect.value : "private";
    try {
      setBusy(true);
      setStatus("Ожидаю появление табулатуры в личной библиотеке...");
      const row = await waitForPersonalRowByJobId(jobId);
      if (!row) {
        setStatus("Табулатура еще не готова. Подожди завершения обработки и повтори.");
        return;
      }

      const detailPayload = await api.fetchPersonalTablatureById(authToken, row.id);
      const existing = detailPayload && detailPayload.tablature ? detailPayload.tablature : null;
      const existingName = String(existing?.track_file_name || "").trim().toLowerCase();
      const existingVisibility = String(existing?.visibility || "private").trim().toLowerCase();
      const targetName = String(newName || existing?.track_file_name || "").trim().toLowerCase();
      const targetVisibility = String(visibility || "private").trim().toLowerCase();

      if (existingName && existingName === targetName && existingVisibility === targetVisibility) {
        setStatus("Уже существует табулатура с таким названием.");
        return;
      }

      await api.updatePersonalTablature(authToken, row.id, {
        trackFileName: newName || undefined,
        visibility: visibility || undefined,
      });
      setStatus(`Табулатура #${row.id} сохранена. visibility=${visibility}`);
    } catch (error) {
      const message = getErrorMessage(error);
      if (message.toLowerCase().includes("already exists")) {
        setStatus("Табулатура не сохранена: уже существует табулатура с таким названием.");
      } else {
        setStatus(`Ошибка сохранения:\n${message}`);
      }
    } finally {
      setBusy(false);
    }
  });
}

if (pdfBtn) {
  pdfBtn.addEventListener("click", async () => {
    if (!jobId) {
      setStatus("Сначала создай табулатуру.");
      return;
    }
    try {
      setBusy(true);
      const blob = await api.fetchPdfByJobId(jobId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `tablature-${jobId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setStatus("PDF скачан.");
    } catch (error) {
      setStatus(`Ошибка получения PDF:\n${getErrorMessage(error)}`);
    } finally {
      setBusy(false);
    }
  });
}

if (jsonBtn) {
  jsonBtn.addEventListener("click", async () => {
    if (!jobId) {
      setStatus("Сначала создай табулатуру.");
      return;
    }
    try {
      setBusy(true);
      const payload = await api.fetchTablatureByJobId(jobId);
      if (jsonView) jsonView.textContent = JSON.stringify(payload, null, 2);
      setStatus("JSON загружен.");
    } catch (error) {
      setStatus(`Ошибка получения JSON:\n${getErrorMessage(error)}`);
    } finally {
      setBusy(false);
    }
  });
}

async function init() {
  ensureCoursesMenuButton();
  await initTopAuthWidget({
    onAuthChanged: async ({ token, user }) => {
      authToken = token || "";
      if (!authToken) {
        localStorage.removeItem(AUTH_TOKEN_KEY);
      }
      if (saveBtn) {
        saveBtn.disabled = !authToken;
      }
      setStatus(
        user
          ? "Авторизованный режим: можно сохранить в личную библиотеку."
          : "Гостевой режим. Создание доступно, сохранение в библиотеку отключено."
      );
    },
  });
}

init();
