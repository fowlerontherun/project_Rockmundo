export function renderSchedule(container, sched) {
  container.innerHTML = '';
  if (!sched) return;
  if (sched.mode === 'hourly') {
    const ul = document.createElement('ul');
    const entries = sched.entries || {};
    Object.keys(entries).sort().forEach(hour => {
      const li = document.createElement('li');
      li.textContent = `${hour}: ${entries[hour]}`;
      ul.appendChild(li);
    });
    container.appendChild(ul);
  } else if (sched.mode === 'category') {
    const p = document.createElement('p');
    p.textContent = `Category: ${sched.category}`;
    container.appendChild(p);
  }
}

export default { renderSchedule };
