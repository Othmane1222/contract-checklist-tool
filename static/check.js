// Upload, results and contact form for /check. Uses t(), currentLanguage and locale() from i18n.js.
const MAX_FILE_MB = 10;
const MAX_FILE_SIZE = MAX_FILE_MB * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".pdf", ".docx"];
const RISK_ORDER = { High: 0, Medium: 1, Low: 2 };
// Set to true after the PIPL review to require consent before each upload.
const REQUIRE_UPLOAD_CONSENT = false;

let lastCheck = null;
let quoteCount = 0;

// Upload form
const form = document.getElementById("upload-form");
const button = form.querySelector("button");
const fileInput = document.getElementById("file");
const statusText = document.getElementById("status");
const errorBox = document.getElementById("error");
const errorText = document.getElementById("error-message");
const uploadConsentField = document.getElementById("upload-consent-field");
const uploadConsent = document.getElementById("upload-consent");

// Results
const results = document.getElementById("results");
const summary = document.getElementById("summary");
const tableBody = document.getElementById("results-body");
const table = document.getElementById("results-table");
const explainToggle = document.getElementById("explain-toggle");
const languageNote = document.getElementById("results-language-note");
const languageNoteText = document.getElementById("results-language-text");
const recheckButton = document.getElementById("recheck");
const fileGoneNote = document.getElementById("file-gone-note");
const verdict = document.getElementById("verdict");
const verdictText = document.getElementById("verdict-text");
const verdictLink = document.getElementById("verdict-link");
const printButton = document.getElementById("print-button");
const printMeta = document.getElementById("print-meta");

// Contact
const contactSection = document.getElementById("contact");
const contactHighlight = document.getElementById("contact-highlight");
const contactIntro = document.getElementById("contact-intro");
const contactOpen = document.getElementById("contact-open");
const contactForm = document.getElementById("contact-form");
const contactButton = contactForm.querySelector("button");
const contactStatus = document.getElementById("contact-status");
const contactError = document.getElementById("contact-error");

if (REQUIRE_UPLOAD_CONSENT) {
  uploadConsentField.hidden = false;
  uploadConsent.required = true;
}

// Pre-select the contract type when arriving from a homepage card, e.g. /check?type=lease
const requestedType = new URLSearchParams(window.location.search).get("type");
if (requestedType && [...form.contract_type.options].some((option) => option.value === requestedType)) {
  form.contract_type.value = requestedType;
}

// ---------- Helpers ----------

function errorMessage(body) {
  if (body && typeof body.code === "string" && hasTranslation(`error.${body.code}`)) {
    return t(`error.${body.code}`, body.params || {});
  }
  if (body && typeof body.message === "string") return body.message;
  return t("error.generic");
}

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

function showError(message) {
  errorText.textContent = message;
  errorBox.hidden = false;
  errorBox.focus();
}

function clearPage() {
  statusText.textContent = "";
  errorText.textContent = "";
  errorBox.hidden = true;
  results.hidden = true;
  tableBody.replaceChildren();
  lastCheck = null;
  contactForm.hidden = true;
  contactOpen.hidden = false;
  contactOpen.setAttribute("aria-expanded", "false");
}

function checkFile(file) {
  if (!file) return t("error.choose_file");
  const name = file.name.toLowerCase();
  if (!ALLOWED_EXTENSIONS.some((extension) => name.endsWith(extension))) return t("error.unsupported_file_type");
  if (file.size === 0) return t("error.file_empty");
  if (file.size > MAX_FILE_SIZE) return t("error.file_too_large", { max_mb: MAX_FILE_MB });
  return null;
}

// ---------- Results ----------

function textCell(text, label) {
  const cell = document.createElement("td");
  cell.textContent = text;
  if (label) cell.dataset.label = label;
  return cell;
}

function riskCell(risk) {
  const cell = textCell("");
  cell.classList.add("risk-cell");
  const tag = document.createElement("span");
  tag.className = `risk risk-${risk.toLowerCase()}`;
  tag.textContent = t(`risk.${risk}`);
  cell.append(tag);
  return cell;
}

function quotesCell(quotes) {
  const cell = textCell(quotes.length === 0 ? "—" : "");
  if (quotes.length === 0) cell.classList.add("is-empty");
  for (const quote of quotes) {
    quoteCount += 1;
    const figure = document.createElement("figure");
    figure.className = "quote";

    const caption = document.createElement("figcaption");
    caption.textContent = t(`location.${quote.location.kind}`, { number: quote.location.number });

    const blockquote = document.createElement("blockquote");
    blockquote.id = `quote-${quoteCount}`;
    blockquote.textContent = quote.text;

    // "Show full clause" button, visible on phones only (see style.css)
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "quote-toggle no-print";
    toggle.setAttribute("aria-controls", blockquote.id);
    toggle.setAttribute("aria-expanded", "false");
    toggle.textContent = t("results.show_clause");
    toggle.addEventListener("click", () => {
      const open = figure.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
      toggle.textContent = t(open ? "results.hide_clause" : "results.show_clause");
    });

    figure.append(caption, blockquote, toggle);
    cell.append(figure);
  }
  return cell;
}

function plainCell(text) {
  const cell = textCell(text || "—");
  cell.classList.add("plain-column");
  if (!text) cell.classList.add("is-empty");
  return cell;
}

function updateLanguageNote(resultsLanguage) {
  const differs = resultsLanguage !== currentLanguage;
  languageNote.hidden = !differs;
  if (!differs) return;

  const hasFile = fileInput.files.length > 0;
  const newLanguage = t(`language.${currentLanguage}`);
  languageNoteText.textContent = t("results.language_note", { language: t(`language.${resultsLanguage}`) });
  recheckButton.textContent = t("results.recheck", { language: newLanguage });
  recheckButton.disabled = !hasFile;
  fileGoneNote.hidden = hasFile;
  fileGoneNote.textContent = hasFile ? "" : t("results.file_gone", { language: newLanguage });
}

function renderVerdict(findings) {
  const high = findings.filter((finding) => finding.risk === "High").length;
  const attention = findings.filter(
    (finding) =>
      finding.risk !== "High" &&
      (finding.risk === "Medium" || finding.status === "unverified" || finding.status === "possibly_present"),
  ).length;

  let level = "clear";
  let text = t("verdict.clear");
  if (high > 0) {
    level = "high";
    text = t("verdict.high", { count: high });
  } else if (attention > 0) {
    level = "attention";
    text = t("verdict.attention", { count: attention });
  }
  verdict.className = `verdict verdict-${level}`;
  verdictText.textContent = text;
  verdictLink.hidden = level !== "high";
}

function renderResults(data) {
  tableBody.replaceChildren();
  const findings = data.results;
  const sorted = [...findings].sort((a, b) => RISK_ORDER[a.risk] - RISK_ORDER[b.risk]);
  for (const finding of sorted) {
    const row = document.createElement("tr");
    row.className = `row-${finding.risk.toLowerCase()}`;
    const item = textCell(finding.label);
    item.classList.add("item");
    row.append(
      item,
      textCell(t(`found.${finding.status}`), t("table.found")),
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
  printMeta.textContent = t("print.meta", {
    date: new Intl.DateTimeFormat(locale(), { dateStyle: "long" }).format(new Date()),
  });

  contactSection.classList.toggle("highlight", high > 0);
  contactHighlight.hidden = high === 0;
  contactIntro.hidden = high > 0;

  renderVerdict(findings);
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

// Choosing a different file clears the old results immediately.
fileInput.addEventListener("change", () => {
  if (lastCheck) clearPage();
});

printButton.addEventListener("click", () => window.print());

explainToggle.addEventListener("change", () => {
  table.classList.toggle("show-plain", explainToggle.checked);
});

document.addEventListener("i18n:change", () => {
  if (lastCheck) renderResults(lastCheck);
});

// ---------- Contact form ----------

function openContactForm() {
  contactForm.hidden = false;
  contactOpen.hidden = true;
  contactOpen.setAttribute("aria-expanded", "true");
  document.getElementById("contact-name").focus();
}

function showContactError(message) {
  contactError.textContent = message;
  contactError.hidden = false;
}

contactOpen.addEventListener("click", openContactForm);
verdictLink.addEventListener("click", openContactForm);

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
});zzz