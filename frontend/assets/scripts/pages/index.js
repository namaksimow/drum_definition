import { fetchPdfByJobId, uploadAudio } from "../services/api.js";

const statusEl = document.getElementById("status");
const uploadBtn = document.getElementById("uploadBtn");
const pdfBtn = document.getElementById("pdfBtn");
const fileInput = document.getElementById("songFile");
const jobIdInput = document.getElementById("jobId");
const pdfFrame = document.getElementById("pdfFrame");

function setStatus(message) {
  statusEl.textContent = message;
}

function setBusy(isBusy) {
  uploadBtn.disabled = isBusy;
  pdfBtn.disabled = isBusy;
}

uploadBtn.addEventListener("click", async () => {
  const file = fileInput.files?.[0];
  if (!file) {
    setStatus("Выбери файл перед загрузкой.");
    return;
  }

  try {
    setBusy(true);
    setStatus("Отправка файла в backend...");

    const payload = await uploadAudio(file);
    const job = payload.job || {};
    setStatus(`Файл отправлен.\njob_id: ${job.id}\nstatus: ${job.status}`);

    if (job.id) {
      jobIdInput.value = job.id;
    }
  } catch (error) {
    setStatus(`Ошибка загрузки:\n${error.message}`);
  } finally {
    setBusy(false);
  }
});

pdfBtn.addEventListener("click", async () => {
  const jobId = jobIdInput.value.trim();
  if (!jobId) {
    setStatus("Введи job_id.");
    return;
  }

  try {
    setBusy(true);
    setStatus("Проверяю готовый PDF...");

    const pdfBlob = await fetchPdfByJobId(jobId);
    const pdfUrl = URL.createObjectURL(pdfBlob);
    pdfFrame.src = pdfUrl;
    setStatus(`PDF открыт для job_id: ${jobId}`);
  } catch (error) {
    setStatus(`Ошибка получения PDF:\n${error.message}`);
  } finally {
    setBusy(false);
  }
});

