import { renderBarChart, renderLineChart } from './chartUtils.js';

export function initScheduleAnalytics() {
  const container = document.getElementById('scheduleAnalytics');
  if (!container) return;
  const userInput = container.querySelector('#analyticsUserId');
  const weekInput = container.querySelector('#analyticsWeek');
  const btn = container.querySelector('#analyticsBtn');
  const categoryCanvas = container.querySelector('#categoryChart');
  const restCanvas = container.querySelector('#restChart');

  btn.addEventListener('click', async () => {
    const uid = userInput.value;
    const week = weekInput.value;
    if (!uid || !week) return;
    try {
      const res = await fetch(`/schedule/analytics/${uid}/${week}`);
      const data = await res.json();
      const labels = Object.keys(data.totals);
      const values = Object.values(data.totals);
      renderBarChart(categoryCanvas, labels, values);
      const restLabels = data.rest.map(r => r.date);
      const restValues = data.rest.map(r => r.rest_hours);
      renderLineChart(restCanvas, restLabels, restValues);
    } catch {
      // ignore errors
    }
  });
}

if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', initScheduleAnalytics);
}

export default { initScheduleAnalytics };
