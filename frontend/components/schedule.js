import { fetchSchedule, saveSchedule } from './scheduleApi.js';
import { renderSchedule } from './scheduleRenderer.js';

export function initSchedulePage() {
  const form = document.getElementById('scheduleForm');
  const hourlyFields = document.getElementById('hourlyFields');
  const categoryField = document.getElementById('categoryField');
  const display = document.getElementById('scheduleDisplay');

  function buildHourlyInputs() {
    hourlyFields.innerHTML = '';
    for (let i = 0; i < 24; i++) {
      const label = document.createElement('label');
      label.textContent = `${String(i).padStart(2, '0')}:00 `;
      const input = document.createElement('input');
      input.type = 'text';
      input.name = `h${i}`;
      label.appendChild(input);
      hourlyFields.appendChild(label);
    }
  }

  function switchMode(mode) {
    if (mode === 'hourly') {
      hourlyFields.style.display = '';
      categoryField.style.display = 'none';
    } else {
      hourlyFields.style.display = 'none';
      categoryField.style.display = '';
    }
  }

  form.mode.forEach((radio) => {
    radio.addEventListener('change', () => switchMode(radio.value));
  });

  buildHourlyInputs();
  switchMode(form.mode.value);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = new FormData(form);
    const mode = data.get('mode');
    let payload;
    if (mode === 'hourly') {
      const entries = {};
      for (let i = 0; i < 24; i++) {
        const val = data.get(`h${i}`);
        if (val) entries[`${String(i).padStart(2, '0')}:00`] = val;
      }
      payload = { mode: 'hourly', entries };
    } else {
      payload = { mode: 'category', category: data.get('category') };
    }
    const result = await saveSchedule(payload).catch(() => null);
    renderSchedule(display, result || payload);
  });

  fetchSchedule()
    .then((sched) => {
      if (sched.mode === 'hourly') {
        form.mode.value = 'hourly';
        switchMode('hourly');
        Object.entries(sched.entries || {}).forEach(([h, val]) => {
          const idx = parseInt(h);
          const input = form.querySelector(`[name="h${idx}"]`);
          if (input) input.value = val;
        });
      } else if (sched.mode === 'category') {
        form.mode.value = 'category';
        switchMode('category');
        const select = document.getElementById('categorySelect');
        if (select) select.value = sched.category;
      }
      renderSchedule(display, sched);
    })
    .catch(() => {});
}

if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', initSchedulePage);
}

export default { initSchedulePage };
