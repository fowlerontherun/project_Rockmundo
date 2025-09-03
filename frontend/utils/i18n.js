let translations = {};
let currentLocale = 'en';

export function getLocale() {
  return currentLocale;
}

export function t(key) {
  return key.split('.').reduce((obj, k) => (obj || {})[k], translations) || key;
}

export async function initI18n() {
  const res = await fetch('/api/locales');
  const { default: defaultLocale, locales } = await res.json();
  let locale = localStorage.getItem('locale');
  if (!locale || !locales.includes(locale)) {
    locale = defaultLocale;
    localStorage.setItem('locale', locale);
  }
  currentLocale = locale;

  translations = await (await fetch(`/locales/${locale}.json`)).json();

  document.querySelectorAll('[data-i18n]').forEach((el) => {
    const key = el.getAttribute('data-i18n');
    const text = t(key);
    if (text) el.textContent = text;
  });

  document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
    const key = el.getAttribute('data-i18n-placeholder');
    const text = t(key);
    if (text) el.setAttribute('placeholder', text);
  });

  const select = document.getElementById('locale-select');
  if (select) {
    select.innerHTML = '';
    locales.forEach((loc) => {
      const opt = document.createElement('option');
      opt.value = loc;
      opt.textContent = loc;
      if (loc === locale) opt.selected = true;
      select.appendChild(opt);
    });
    select.onchange = async () => {
      localStorage.setItem('locale', select.value);
      await initI18n();
    };
  }
}

const originalFetch = window.fetch.bind(window);
window.fetch = (resource, init = {}) => {
  const headers = new Headers(init.headers || {});
  headers.set('Accept-Language', localStorage.getItem('locale') || currentLocale);
  return originalFetch(resource, { ...init, headers });
};
