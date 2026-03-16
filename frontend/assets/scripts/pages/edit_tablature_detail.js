import * as api from "../services/api.js?v=9";
import { initTopAuthWidget } from "../services/top_auth_widget.js?v=8";

const INSTRUMENTS = ["hihat", "snare", "kick"];
const INSTRUMENT_SYMBOLS = { hihat: "x", snare: "o", kick: "o" };

const backLinkEl = document.getElementById("backLink");
const pageTitleEl = document.getElementById("pageTitle");
const subtitleEl = document.getElementById("subtitle");
const statusEl = document.getElementById("status");
const nameInput = document.getElementById("nameInput");
const visibilitySelect = document.getElementById("visibilitySelect");
const tabHint = document.getElementById("tabHint");
const tabEditor = document.getElementById("tabEditor");
const saveBtn = document.getElementById("saveBtn");

let authToken = "";
let tablatureId = null;
let currentTabData = null;
let isPatternReadOnly = false;
let isMetadataOnlyMode = false;

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

function getQueryParam(name) {
  const params = new URLSearchParams(window.location.search || "");
  return params.get(name);
}

function setStatus(message) {
  if (statusEl) statusEl.textContent = message;
}

function getTablatureIdFromPath() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  const last = parts[parts.length - 1];
  const id = Number(last);
  return Number.isFinite(id) ? id : null;
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

function computeSlotsFromPattern(pattern, symbol) {
  const slots = [];
  for (let i = 0; i < pattern.length; i += 1) {
    if (pattern[i] === symbol) slots.push(i);
  }
  return slots;
}

function normalizePattern(pattern, slotCount, symbol) {
  const source = typeof pattern === "string" ? pattern : "";
  let result = "";
  for (let i = 0; i < slotCount; i += 1) {
    const char = source[i] || "-";
    result += char === symbol ? symbol : "-";
  }
  return result;
}

function normalizeTabData(raw) {
  const data = JSON.parse(JSON.stringify(raw || {}));
  if (!Array.isArray(data.lines)) data.lines = [];

  data.lines.forEach((line, lineIndex) => {
    if (!Array.isArray(line.bars)) line.bars = [];
    if (!line.line_number) line.line_number = lineIndex + 1;

    line.bars.forEach((bar, barIndex) => {
      if (!bar || typeof bar !== "object") {
        line.bars[barIndex] = { bar_number: barIndex + 1, slot_count: 16, instruments: {} };
      }
      const safeBar = line.bars[barIndex];
      if (!safeBar.instruments || typeof safeBar.instruments !== "object") {
        safeBar.instruments = {};
      }
      const slotCount = Number.isFinite(Number(safeBar.slot_count))
        ? Math.max(1, Number(safeBar.slot_count))
        : 16;
      safeBar.slot_count = slotCount;

      INSTRUMENTS.forEach((instrument) => {
        const symbol = INSTRUMENT_SYMBOLS[instrument];
        if (!safeBar.instruments[instrument] || typeof safeBar.instruments[instrument] !== "object") {
          safeBar.instruments[instrument] = { symbol, pattern: "-".repeat(slotCount), slots: [] };
        }
        const item = safeBar.instruments[instrument];
        item.symbol = symbol;
        item.pattern = normalizePattern(item.pattern, slotCount, symbol);
        item.slots = computeSlotsFromPattern(item.pattern, symbol);
      });
    });
  });

  return data;
}

function formatSec(value) {
  const num = Number(value);
  if (Number.isFinite(num)) return `${num.toFixed(3)}s`;
  return `${value}s`;
}

function renderPatternButtons(lineIndex, barIndex, instrument, pattern) {
  const chars = [];
  for (let slot = 0; slot < pattern.length; slot += 1) {
    const char = pattern[slot] || "-";
    const onClass = char !== "-" ? " tab-cell--on" : "";
    chars.push(
      `<button class="tab-cell${onClass}" type="button" data-line-index="${lineIndex}" data-bar-index="${barIndex}" data-instrument="${instrument}" data-slot="${slot}">${char}</button>`
    );
  }
  return chars.join("");
}

function renderTabEditor(tabData) {
  if (!tabEditor) return;
  if (!tabData || !Array.isArray(tabData.lines) || tabData.lines.length === 0) {
    tabEditor.textContent = "Нет данных табулатуры.";
    return;
  }

  tabEditor.classList.toggle("tab-editor--readonly", isPatternReadOnly);
  tabEditor.innerHTML = tabData.lines
    .map((line, lineIndex) => {
      const bars = Array.isArray(line.bars) ? line.bars : [];
      const rows = INSTRUMENTS.map((instrument) => {
        const barsHtml = bars
          .map((bar, barIndex) => {
            const pattern = bar?.instruments?.[instrument]?.pattern || "";
            return `<span class="tab-row__pipe">|</span>${renderPatternButtons(lineIndex, barIndex, instrument, pattern)}<span class="tab-row__pipe">|</span>`;
          })
          .join("");
        return `
          <div class="tab-row">
            <p class="tab-row__label">${instrument}</p>
            <div class="tab-row__pattern">${barsHtml}</div>
          </div>
        `;
      }).join("");

      return `
        <article class="tab-line">
          <p class="tab-line__meta">line ${line.line_number || lineIndex + 1} | bars ${line.first_bar || "?"}-${line.last_bar || "?"} | ${formatSec(line.start_sec)} - ${formatSec(line.end_sec)}</p>
          ${rows}
        </article>
      `;
    })
    .join("");
}

function toggleCell(lineIndex, barIndex, instrument, slotIndex) {
  if (!currentTabData || !Array.isArray(currentTabData.lines)) return;
  const line = currentTabData.lines[lineIndex];
  const bar = line?.bars?.[barIndex];
  const item = bar?.instruments?.[instrument];
  if (!line || !bar || !item || typeof item.pattern !== "string") return;

  const symbol = String(item.symbol || INSTRUMENT_SYMBOLS[instrument] || "o");
  if (slotIndex < 0 || slotIndex >= item.pattern.length) return;

  const chars = item.pattern.split("");
  chars[slotIndex] = chars[slotIndex] === symbol ? "-" : symbol;
  item.pattern = chars.join("");
  item.slots = computeSlotsFromPattern(item.pattern, symbol);
}

function renderTablature(row) {
  if (!row) return;
  const trackName = row.track_file_name || "Без названия";
  if (pageTitleEl) pageTitleEl.textContent = `Просмотр табулатуры: ${trackName}`;
  if (subtitleEl) subtitleEl.textContent = `#${row.id} • visibility=${row.visibility || "private"} • task_id=${row.task_id}`;
  if (nameInput) nameInput.value = trackName;
  const visibility = String(row.visibility || "private").toLowerCase();
  if (visibilitySelect) {
    visibilitySelect.value = visibility === "public" ? "public" : "private";
  }

  currentTabData = normalizeTabData(asTabData(row.json_format));
  renderTabEditor(currentTabData);
}

async function loadTablature() {
  if (!authToken || !tablatureId) return;
  try {
    const payload = await api.fetchPersonalTablatureById(authToken, tablatureId);
    renderTablature(payload.tablature || null);
    setStatus("Табулатура загружена.");
  } catch (error) {
    setStatus(`Ошибка загрузки: ${getErrorMessage(error)}`);
  }
}

if (saveBtn) {
  saveBtn.addEventListener("click", async () => {
    if (!authToken || !tablatureId) {
      setStatus("Нужна авторизация.");
      return;
    }
    const name = nameInput ? nameInput.value.trim() : "";
    const visibility = visibilitySelect ? visibilitySelect.value : "private";
    const payload = {
      trackFileName: name,
      visibility,
    };
    if (!isMetadataOnlyMode) {
      payload.jsonFormat = currentTabData || { lines: [] };
    }

    try {
      saveBtn.disabled = true;
      const response = await api.updatePersonalTablature(authToken, tablatureId, payload);
      renderTablature(response.tablature || null);
      setStatus("Изменения сохранены.");
    } catch (error) {
      const message = getErrorMessage(error);
      if (message.toLowerCase().includes("already exists")) {
        setStatus("Ошибка сохранения: уже существует табулатура с таким названием.");
      } else {
        setStatus(`Ошибка сохранения: ${message}`);
      }
    } finally {
      saveBtn.disabled = false;
    }
  });
}

if (tabEditor) {
  tabEditor.addEventListener("click", (event) => {
    if (isPatternReadOnly) return;
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const button = target.closest("[data-line-index][data-bar-index][data-instrument][data-slot]");
    if (!button) return;

    const lineIndex = Number(button.getAttribute("data-line-index"));
    const barIndex = Number(button.getAttribute("data-bar-index"));
    const slotIndex = Number(button.getAttribute("data-slot"));
    const instrument = String(button.getAttribute("data-instrument") || "");
    if (!Number.isFinite(lineIndex) || !Number.isFinite(barIndex) || !Number.isFinite(slotIndex)) return;
    if (!INSTRUMENTS.includes(instrument)) return;

    toggleCell(lineIndex, barIndex, instrument, slotIndex);
    renderTabEditor(currentTabData);
  });
}

async function init() {
  ensureCoursesMenuButton();
  tablatureId = getTablatureIdFromPath();
  isMetadataOnlyMode = String(getQueryParam("mode") || "").toLowerCase() === "view";
  isPatternReadOnly = isMetadataOnlyMode;
  const fromPersonal = String(getQueryParam("from") || "").toLowerCase() === "personal";

  if (backLinkEl) {
    if (fromPersonal) {
      backLinkEl.href = "/#personal";
      backLinkEl.textContent = "← К личной библиотеке";
    } else {
      backLinkEl.href = "/edit";
      backLinkEl.textContent = "← К списку табулатур";
    }
  }

  if (isMetadataOnlyMode) {
    if (tabHint) {
      tabHint.textContent = "В этом режиме доступен только просмотр табулатуры. Можно менять только название и видимость.";
    }
  } else if (tabHint) {
    tabHint.innerHTML = "Клик по символу включает/выключает удар: <code>x/o</code> ↔ <code>-</code>.";
  }

  await initTopAuthWidget({
    onAuthChanged: async ({ token, user }) => {
      authToken = token || "";
      if (!user || !authToken) {
        setStatus("Нужна авторизация. Войди на главной странице.");
        return;
      }
      if (!tablatureId) {
        setStatus("Некорректный id табулатуры.");
        return;
      }
      await loadTablature();
    },
  });
}

init();
