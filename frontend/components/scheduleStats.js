export function initScheduleStats() {
  const container = document.getElementById('scheduleStats');
  if (!container) return;
  const userInput = container.querySelector('#statsUserId');
  const dateInput = container.querySelector('#statsDate');
  const btn = container.querySelector('#statsBtn');
  const output = container.querySelector('#statsOutput');

  btn.addEventListener('click', async () => {
    const uid = userInput.value;
    const day = dateInput.value;
    if (!uid || !day) return;
    try {
      const res = await fetch(`/api/schedule/stats/${uid}/${day}`);
      const data = await res.json();
      output.textContent = `Completion: ${data.completion}%`;
    } catch {
      output.textContent = 'Error loading stats';
    }
  });
}

if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', initScheduleStats);
}

export default { initScheduleStats };
