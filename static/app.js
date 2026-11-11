const SUPPORTED_LANGUAGES = ["en", "es", "zh"];
const STORAGE_KEY = "language";
const MAX_FILE_MB = 10;
const MAX_FILE_SIZE = MAX_FILE_MB * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".pdf", ".docx"];
const RISK_ORDER = { High: 0, Medium: 1, Low: 2 };

let translations = {};
let englishTranslations = {};
let currentLanguage = "en";
let lastCheck = null;

const languageSelect = document.getElementById("ui-language");
const form = document.getElementById("upload-form");
const button = form.querySelector("button");
const fileInput = document.getElementById("file");
const statusText = document.getElementById("status");
const errorBox = document.getElementById("error");
const results = document.getElementById("results");
const summary = document.getElementById("summary");
const tableBody = document.getElementById("results-body");
const table = document.getElementById("results-table");
const explainToggle = document.getElementById("explain-toggle");
const languageNote = document.getElementById("results-language-note");
const recheckButton = document.getElementById("recheck");
const reuploadNote = document.getElementById("reupload-note");
const contactForm = document.getElementById("contact-form");
const contactButton = contactForm.querySelector("button");
const contactSection = document.getElementById("contact");
const contactHighlight = document.getElementById("contact-highlight");
const contactStatus = document.getElementById("contact-status");
const contactError = document.getElementById("contact-error");

// ---------- Translations ----------

function has(object, key) {
  return Object.prototype.hasOwnProperty.call(object, key);
}

function format(template, params = {}) {
  return template.replace(/\{(\w+)\}/g, (match, name) => (has(params, name) ? String(params[name]) : match));
}

function hasTranslation(key) {
  return has(translations, key) || has(englishTranslations, key);
}

function t(key, params = {}) {
  const template = has(translations, key) ? translations[key] : has(englishTranslations, key) ? englishTranslations[key] : key;
  return format(template, params);
}

function readSavedLanguage() {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function saveLanguage(language) {
  try {
    localStorage.setItem(STORAGE_KEY, language);
  } catch {
    // Storage unavailable (private window, blocked cookies): the choice just isn't remembered.
  }
}

function detectLanguage() {
  const saved = readSavedLanguage();
  if (SUPPORTED_LANGUAGES.includes(saved)) return saved;
  const browserLanguages = navigator.languages || [navigator.language || ""];
  for (const tag of browserLanguages) {
    const base = tag.toLowerCase().split("-")[0]; // zh-TW and zh-HK also become "zh" (Simplified Chinese)
    if (SUPPORTED_LANGUAGES.includes(base)) return base;
  }
  return "en";
}

async function loadTranslations(language) {
  const response = await fetch(`/static/i18n/${language}.json`);
  if (!response.ok) throw new Error(`Missing translations: ${language}`);
  return response.json();
}

function applyTranslations() {
  document.title = t("page.title");
  for (const element of document.querySelectorAll("[data-i18n]")) {
    element.textContent = t(element.dataset.i18n);
  }
}

async function setLanguage(language) {
  if (!has(englishTranslations, "page.title")) {
    englishTranslations = await loadTranslations("en");
  }
  translations = language === "en" ? englishTranslations : await loadTranslations(language);
  currentLanguage = language;
  saveLanguage(language);
  languageSelect.value = language;
  document.documentElement.lang = language === "zh" ? "zh-CN" : language;
  applyTranslations();
  if (lastCheck) renderResults(lastCheck);
}

function errorMessage(body) {
  if (body && typeof body.code === "string" && hasTranslation(`error.${body.code}`)) {
    return t(`error.${body.code}`, body.params || {});
  }
  if (body && typeof body.message === "string") return body.message;
  return t("error.generic");
}

// ---------- Network helpers ----------

async function post(url, options) {
  try {
    return await fetch(url, { method: "POST", ...options });
  } catch {
    return null;
  }
}

async function readJson(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

// ---------- Upload and results ----------

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function clearPage() {
  statusText.textContent = "";
  errorBox.textContent = "";
  errorBox.hidden = true;
  results.hidden = true;
  tableBody.replaceChildren();
  lastCheck = null;
}

function checkFile(file) {
  if (!file) return t("error.choose_file");
  const name = file.name.toLowerCase();
  if (!ALLOWED_EXTENSIONS.some((extension) => name.endsWith(extension))) return t("error.unsupported_file_type");
  if (file.size === 0) return t("error.file_empty");
  if (file.size > MAX_FILE_SIZE) return t("error.file_too_large", { max_mb: MAX_FILE_MB });
  return null;
}

function textCell(text) {
  const cell = document.createElement("td");
  cell.textContent = text;
  return cell;
}

function riskCell(risk) {
  const cell = textCell(t(`risk.${risk}`));
  cell.className = `risk risk-${risk.toLowerCase()}`;
  return cell;
}

function quotesCell(quotes) {
  const cell = document.createElement("td");
  if (quotes.length === 0) {
    cell.textContent = "—";
    return cell;
  }
  for (const quote of quotes) {
    const figure = document.createElement("figure");
    const caption = document.createElement("figcaption");
    caption.textContent = t(`location.${quote.location.kind}`, { number: quote.location.number });
    const blockquote = document.createElement("blockquote");
    blockquote.textContent = quote.text;
    figure.append(caption, blockquote);
    cell.append(figure);
  }
  return cell;
}

function plainCell(text) {
  const cell = textCell(text || "—");
  cell.className = "plain-column";
  return cell;
}

function updateLanguageNote(resultsLanguage) {
  const differs = resultsLanguage !== currentLanguage;
  languageNote.hidden = !differs;
  recheckButton.hidden = true;
  reuploadNote.hidden = true;
  if (!differs) return;

  const newLanguage = t(`language.${currentLanguage}`);
  languageNote.textContent = t("results.language_note", { language: t(`language.${resultsLanguage}`) });
  if (fileInput.files.length > 0) {
    recheckButton.textContent = t("results.recheck", { language: newLanguage });
    recheckButton.hidden = false;
  } else {
    reuploadNote.textContent = t("results.reupload", { language: newLanguage });
    reuploadNote.hidden = false;
  }
}

function renderResults(data) {
  tableBody.replaceChildren();
  const findings = data.results;
  const sorted = [...findings].sort((a, b) => RISK_ORDER[a.risk] - RISK_ORDER[b.risk]);
  for (const finding of sorted) {
    const row = document.createElement("tr");
    row.append(
      textCell(finding.label),
      textCell(t(`found.${finding.status}`)),
      riskCell(finding.risk),
      textCell(finding.explanation),
      quotesCell(finding.quotes),
      plainCell(finding.plain_language),
    );
    tableBody.append(row);
  }

  const high = findings.filter((finding) => finding.risk === "High").length;
  const check = findings.filter(
    (finding) => finding.status === "unverified" || finding.status === "possibly_present",
  ).length;
  summary.textContent = t("results.summary", { total: findings.length, high, check });
  contactSection.classList.toggle("highlight", high > 0);
  contactHighlight.hidden = high === 0;
  updateLanguageNote(data.language);
  results.hidden = false;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearPage();

  const problem = checkFile(fileInput.files[0]);
  if (problem) {
    showError(problem);
    return;
  }

  button.disabled = true;
  recheckButton.disabled = true;
  statusText.textContent = t("status.checking");

  const body = new FormData(form);
  body.set("language", currentLanguage);
  const response = await post("/api/check", { body });

  button.disabled = false;
  recheckButton.disabled = false;
  statusText.textContent = "";

  if (!response) {
    showError(t("error.unreachable"));
    return;
  }
  const data = await readJson(response);
  if (!response.ok) {
    showError(errorMessage(data));
    return;
  }
  if (!data) {
    showError(t("error.server"));
    return;
  }

  lastCheck = data;
  renderResults(data);
});

recheckButton.addEventListener("click", () => form.requestSubmit());

explainToggle.addEventListener("change", () => {
  table.classList.toggle("show-plain", explainToggle.checked);
});

languageSelect.addEventListener("change", () => {
  setLanguage(languageSelect.value).catch(() => showError(t("error.generic")));
});

// ---------- Contact form ----------

function showContactError(message) {
  contactError.textContent = message;
  contactError.hidden = false;
}

contactForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  contactError.hidden = true;
  contactStatus.textContent = "";
  if (!lastCheck) return;

  const includeSummary = document.getElementById("contact-summary").checked;
  const payload = {
    name: document.getElementById("contact-name").value.trim(),
    email: document.getElementById("contact-email").value.trim(),
    description: document.getElementById("contact-description").value.trim(),
    contract_type: lastCheck.contract_type,
    consent: document.getElementById("contact-consent").checked,
    website: document.getElementById("contact-website").value,
    user_language: currentLanguage,
    summary: includeSummary
      ? lastCheck.results.map((finding) => ({ item_id: finding.item_id, status: finding.status, risk: finding.risk }))
      : [],
  };

  contactButton.disabled = true;
  contactStatus.textContent = t("contact.sending");
  const response = await post("/api/contact", {
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  contactButton.disabled = false;
  contactStatus.textContent = "";

  if (!response) {
    showContactError(t("error.unreachable"));
    return;
  }
  if (response.ok) {
    contactStatus.textContent = t("contact.sent");
    contactForm.reset();
    return;
  }
  showContactError(errorMessage(await readJson(response)));
});

// ---------- Start ----------

async function init() {
  try {
    await setLanguage(detectLanguage());
  } catch {
    try {
      await setLanguage("en");
    } catch {
      // Keep the English text already in the HTML.
    }
  }
}

init();