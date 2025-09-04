export async function fetchSchedule() {
  const res = await fetch('/api/schedule');
  if (!res.ok) {
    throw new Error('Failed to fetch schedule');
  }
  return res.json();
}

export async function saveSlot(time, value, durationDays = 1) {
  const res = await fetch(`/api/schedule/${encodeURIComponent(time)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ value, durationDays })
  });
  if (!res.ok) {
    throw new Error('Failed to save slot');
  }
  return res.json();
}

export async function deleteSlot(time) {
  const res = await fetch(`/api/schedule/${encodeURIComponent(time)}`, {
    method: 'DELETE'
  });
  if (!res.ok) {
    throw new Error('Failed to delete slot');
  }
  return res.json();
}

export function initAdvancedPlanner() {
  const container = document.getElementById('advancedPlanner');
  if (!container) return;

  const grid = document.createElement('div');
  grid.id = 'plannerGrid';
  grid.style.display = 'grid';
  grid.style.gridTemplateColumns = 'repeat(8, 1fr)';
  grid.style.gap = '2px';

  for (let h = 0; h < 24; h++) {
    for (let q = 0; q < 4; q++) {
      const slot = document.createElement('div');
      const minutes = q * 15;
      const time = `${String(h).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
      slot.className = 'slot';
      slot.draggable = true;
      slot.dataset.time = time;
      slot.textContent = time;
      slot.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', time);
      });
      slot.addEventListener('drop', async (e) => {
        e.preventDefault();
        const text = e.dataTransfer.getData('text/plain');
        await updateSlot(time, text);
      });
      slot.addEventListener('dragover', (e) => e.preventDefault());
      grid.appendChild(slot);
    }
  }

  container.appendChild(grid);

  fetchSchedule()
    .then((sched) => {
      Object.entries(sched || {}).forEach(([time, val]) => {
        const slot = grid.querySelector(`[data-time="${time}"]`);
        if (!slot) return;
        if (val && typeof val === 'object') {
          slot.textContent = val.label || val.value || '';
          if (val.durationDays && val.durationDays > 1) {
            slot.style.gridColumn = `span ${val.durationDays}`;
          }
        } else {
          slot.textContent = val;
        }
      });
    })
    .catch(() => {});
}

export async function updateSlot(time, value, durationDays = 1) {
  const slot = document.querySelector(`[data-time="${time}"]`);
  if (slot) {
    if (typeof value === 'object') {
      slot.textContent = value.label || value.value || '';
      if (value.durationDays && value.durationDays > 1) {
        slot.style.gridColumn = `span ${value.durationDays}`;
      }
    } else {
      slot.textContent = value;
    }
  }
  return saveSlot(time, value, durationDays);
}

if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', initAdvancedPlanner);
}

export default { initAdvancedPlanner, fetchSchedule, saveSlot, deleteSlot, updateSlot };
