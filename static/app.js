const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ALLOWED_EXTENSIONS = [".pdf", ".docx"];
const RISK_ORDER = { High: 0, Medium: 1, Low: 2 };
const STATUS_LABELS = {
    
  quote_verified: "Yes – source found",
  unverified: "Unverified – please check manually",
  possibly_present: "Possibly present, check manually",
  not_found: "No",
};
const LANGUAGE_NAMES = { en: "English", es: "Spanish", zh: "Chinese" };

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
const resultsLanguage = document.getElementById("results-language");

explainToggle.addEventListener("change", () => {
  table.classList.toggle("show-plain", explainToggle.checked);
});

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
}

function checkFile(file) {
  if (!file) return "Please choose a file.";
  const name = file.name.toLowerCase();
  if (!ALLOWED_EXTENSIONS.some((extension) => name.endsWith(extension))) {
    return "Only PDF and DOCX files are supported.";
  }
  if (file.size === 0) return "The file is empty.";
  if (file.size > MAX_FILE_SIZE) return "The file is too large. The limit is 10 MB.";
  return null;
}

function textCell(text) {
  const cell = document.createElement("td");
  cell.textContent = text;
  return cell;
}

function riskCell(risk) {
  const cell = textCell(risk);
  cell.className = `risk risk-${risk.toLowerCase()}`;
  return cell;
}

function formatLocation(location) {
  const kind = location.kind === "page" ? "Page" : "Paragraph";
  return `${kind} ${location.number}`;
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
    caption.textContent = formatLocation(quote.location);
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

function renderResults(findings) {
  const sorted = [...findings].sort((a, b) => RISK_ORDER[a.risk] - RISK_ORDER[b.risk]);
  for (const finding of sorted) {
    const row = document.createElement("tr");
    row.append(
      textCell(finding.label),
      textCell(STATUS_LABELS[finding.status] || finding.status),
      riskCell(finding.risk),
      textCell(finding.explanation),
      quotesCell(finding.quotes),
      plainCell(finding.plain_language),
    );
    tableBody.append(row);
  }

  const highRisk = findings.filter((finding) => finding.risk === "High").length;
  const toCheck = findings.filter(
    (finding) => finding.status === "unverified" || finding.status === "possibly_present",
  ).length;
  summary.textContent = `${findings.length} items checked · ${highRisk} high risk · ${toCheck} to check manually`;
    contactSection.classList.toggle("highlight", highRisk > 0);
  contactHighlight.hidden = highRisk === 0;
  results.hidden = false;
}

async function sendForm() {
  try {
    return await fetch("/api/check", { method: "POST", body: new FormData(form) });
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

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearPage();

  const problem = checkFile(fileInput.files[0]);
  if (problem) {
    showError(problem);
    return;
  }

  button.disabled = true;
  statusText.textContent = "Checking the contract… this can take up to a minute.";
  const response = await sendForm();
  button.disabled = false;
  statusText.textContent = "";

  if (!response) {
    showError("Could not reach the server. Please try again.");
    return;
  }

  const data = await readJson(response);
  if (!data) {
    showError("Something went wrong on the server. Please try again.");
    return;
  }

  if (!response.ok) {
    showError(typeof data.detail === "string" ? data.detail : "Something went wrong. Please try again.");
    return;
  }
  lastCheck = data;
    resultsLanguage.textContent = `Results are in ${LANGUAGE_NAMES[data.language] || "English"}.`;
  renderResults(data.results);
});

const contactForm = document.getElementById("contact-form");
const contactButton = contactForm.querySelector("button");
const contactSection = document.getElementById("contact");
const contactHighlight = document.getElementById("contact-highlight");
const contactStatus = document.getElementById("contact-status");
const contactError = document.getElementById("contact-error");
let lastCheck = null;

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
    summary: includeSummary
      ? lastCheck.results.map((finding) => ({ label: finding.label, status: finding.status, risk: finding.risk }))
      : [],
  };

  contactButton.disabled = true;
  contactStatus.textContent = "Sending…";
  let response = null;
  try {
    response = await fetch("/api/contact", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    response = null;
  }
  contactButton.disabled = false;
  contactStatus.textContent = "";

  if (!response) {
    showContactError("Could not reach the server. Please try again.");
    return;
  }
  if (response.ok) {
    contactStatus.textContent = "Message sent. You'll get a reply by email.";
    contactForm.reset();
    return;
  }
  if (response.status === 422) {
    showContactError("Please check your name, email and message, and tick the consent box.");
    return;
  }
  const data = await readJson(response);
  showContactError(data && typeof data.detail === "string" ? data.detail : "Something went wrong. Please try again.");
});