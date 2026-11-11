// Shared translation logic for every page.
const SUPPORTED_LANGUAGES = ["en", "es", "zh"];
const STORAGE_KEY = "language";

let translations = {};
let englishTranslations = {};
let currentLanguage = "en";

const languageSelect = document.getElementById("ui-language");

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

function locale() {
  return currentLanguage === "zh" ? "zh-CN" : currentLanguage;
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
  document.title = t(document.body.dataset.titleKey || "page.title");
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
  if (languageSelect) languageSelect.value = language;
  document.documentElement.lang = locale();
  applyTranslations();
  document.dispatchEvent(new CustomEvent("i18n:change", { detail: { language } }));
}

async function initLanguage() {
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

if (languageSelect) {
  languageSelect.addEventListener("change", () => {
    setLanguage(languageSelect.value).catch(() => {});
  });
}

initLanguage();