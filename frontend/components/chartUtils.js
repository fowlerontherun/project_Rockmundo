export function renderBarChart(canvas, labels, data) {
  if (!canvas) return;
  if (canvas._chart) canvas._chart.destroy();
  canvas._chart = new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: { labels, datasets: [{ label: 'Hours', data }] },
  });
}

export function renderLineChart(canvas, labels, data) {
  if (!canvas) return;
  if (canvas._chart) canvas._chart.destroy();
  canvas._chart = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: { labels, datasets: [{ label: 'Rest', data }] },
  });
}

export default { renderBarChart, renderLineChart };
