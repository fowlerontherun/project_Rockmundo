import { fetchSchedule, saveSchedule } from './scheduleApi.js';
import { renderSchedule } from './scheduleRenderer.js';

export function buildMobileForm() {
  const form = document.createElement('form');
  const time = document.createElement('input');
  time.type = 'time';
  time.name = 'time';
  const value = document.createElement('input');
  value.type = 'text';
  value.name = 'value';
  value.placeholder = 'Activity';
  const submit = document.createElement('button');
  submit.type = 'submit';
  submit.textContent = 'Add';
  form.append(time, value, submit);
  return form;
}

export function initMobilePlanner() {
  const container = document.getElementById('mobilePlanner');
  if (!container) return;

  const form = buildMobileForm();
  const display = document.createElement('div');
  display.id = 'mobileDisplay';
  container.append(form, display);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = new FormData(form);
    const time = data.get('time');
    const value = data.get('value');
    if (!time || !value) return;
    const payload = { mode: 'hourly', entries: { [time]: value } };
    const result = await saveSchedule(payload).catch(() => null);
    renderSchedule(display, result || payload);
    form.reset();
  });

  fetchSchedule()
    .then((sched) => {
      if (sched) renderSchedule(display, sched);
    })
    .catch(() => {});
}

if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', initMobilePlanner);
}

export default { initMobilePlanner, buildMobileForm };
