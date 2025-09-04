let plannerGrid;
let summaryPanel;

async function updateSummary() {
  if (!summaryPanel || !plannerGrid) return;
  const entries = [];
  plannerGrid.querySelectorAll('.slot').forEach((s) => {
    if (s.dataset.activityId) {
      entries.push({ activity_id: parseInt(s.dataset.activityId, 10) });
    }
  });
  if (entries.length === 0) {
    summaryPanel.textContent = '';
    return;
  }
  try {
    const res = await fetch('/schedule/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: 1, entries })
    });
    if (res.ok) {
      const data = await res.json();
      summaryPanel.textContent = `Projected XP: ${data.xp}, Energy: ${data.energy}`;
    }
  } catch {
    /* ignore */
  }
}

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

  plannerGrid = document.createElement('div');
  plannerGrid.id = 'plannerGrid';
  plannerGrid.style.display = 'grid';
  plannerGrid.style.gridTemplateColumns = 'repeat(8, 1fr)';
  plannerGrid.style.gap = '2px';

  for (let h = 0; h < 24; h++) {
    for (let q = 0; q < 4; q++) {
      const slot = document.createElement('div');
      const minutes = q * 15;
      const time = `${String(h).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
      const d = new Date();
      d.setHours(h, minutes, 0, 0);
      const label = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      slot.className = 'slot';
      slot.draggable = true;
      slot.dataset.time = time;
      slot.textContent = label;
      slot.addEventListener('dragstart', (e) => {
        e.dataTransfer.setData('text/plain', time);
      });
      slot.addEventListener('drop', async (e) => {
        e.preventDefault();
        const text = e.dataTransfer.getData('text/plain');
        await updateSlot(time, text);
      });
      slot.addEventListener('dragover', (e) => e.preventDefault());
      plannerGrid.appendChild(slot);
    }
  }

  container.appendChild(plannerGrid);

  summaryPanel = document.createElement('div');
  summaryPanel.id = 'planSummary';
  summaryPanel.style.marginTop = '1rem';
  container.appendChild(summaryPanel);

  fetchSchedule()
    .then((sched) => {
      Object.entries(sched || {}).forEach(([time, val]) => {
        const slot = plannerGrid.querySelector(`[data-time="${time}"]`);
        if (!slot) return;
        if (val && typeof val === 'object') {
          slot.textContent = val.label || val.value || '';
          if (val.activity_id) slot.dataset.activityId = val.activity_id;
          if (val.durationDays && val.durationDays > 1) {
            slot.style.gridColumn = `span ${val.durationDays}`;
          }
        } else {
          slot.textContent = val;
        }
      });
      updateSummary();
    })
    .catch(() => {});
}

export async function updateSlot(time, value, durationDays = 1) {
  const slot = document.querySelector(`[data-time="${time}"]`);
  if (slot) {
    if (typeof value === 'object') {
      slot.textContent = value.label || value.value || '';
      if (value.activity_id) slot.dataset.activityId = value.activity_id;
      if (value.durationDays && value.durationDays > 1) {
        slot.style.gridColumn = `span ${value.durationDays}`;
      }
    } else {
      slot.textContent = value;
      delete slot.dataset.activityId;
    }
  }
  const res = await saveSlot(time, value, durationDays);
  updateSummary();
  return res;
}

if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', initAdvancedPlanner);
}

export default { initAdvancedPlanner, fetchSchedule, saveSlot, deleteSlot, updateSlot };
