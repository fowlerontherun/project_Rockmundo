export async function fetchSchedule() {
  const res = await fetch('/api/schedule');
  if (!res.ok) {
    throw new Error('Failed to fetch schedule');
  }
  return res.json();
}

export async function saveSchedule(data) {
  const res = await fetch('/api/schedule', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    throw new Error('Failed to save schedule');
  }
  return res.json();
}

export default { fetchSchedule, saveSchedule };
