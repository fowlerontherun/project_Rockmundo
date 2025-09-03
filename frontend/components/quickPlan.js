export async function fetchDefaultPlan() {
  const res = await fetch('/api/default-plan');
  if (!res.ok) {
    throw new Error('Failed to fetch default plan');
  }
  return res.json();
}

export async function saveDefaultPlan(plan) {
  const res = await fetch('/api/default-plan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(plan)
  });
  if (!res.ok) {
    throw new Error('Failed to save default plan');
  }
  return res.json();
}

export function initQuickPlan() {
  const container = document.getElementById('quickPlan');
  if (!container) return;

  const categories = ['practice', 'rest', 'travel'];
  const form = document.createElement('form');

  categories.forEach((cat) => {
    const label = document.createElement('label');
    const input = document.createElement('input');
    input.type = 'checkbox';
    input.name = cat;
    label.appendChild(input);
    label.append(` ${cat}`);
    form.appendChild(label);
  });

  const save = document.createElement('button');
  save.type = 'submit';
  save.textContent = 'Save';
  form.appendChild(save);
  container.appendChild(form);

  fetchDefaultPlan()
    .then((plan) => {
      categories.forEach((cat) => {
        const input = form.querySelector(`input[name="${cat}"]`);
        if (input) input.checked = !!plan[cat];
      });
    })
    .catch(() => {});

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const plan = {};
    categories.forEach((cat) => {
      const input = form.querySelector(`input[name="${cat}"]`);
      plan[cat] = !!(input && input.checked);
    });
    await saveDefaultPlan(plan).catch(() => {});
  });
}

if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', initQuickPlan);
}

export default { initQuickPlan, fetchDefaultPlan, saveDefaultPlan };
