const USER_ID = 1;

document.addEventListener('DOMContentLoaded', async () => {
  const form = document.getElementById('profile-form');
  const bioInput = document.getElementById('bio');
  const linksInput = document.getElementById('links');
  const avatarInput = document.getElementById('avatar-input');
  const chemTbody = document.querySelector('#chemistry-table tbody');

  try {
    const res = await fetch(`/api/user-settings/profile/${USER_ID}`);
    if (res.ok) {
      const data = await res.json();
      bioInput.value = data.bio || '';
      linksInput.value = (data.links || []).join(', ');
    }
  } catch (e) {
    // ignore load errors
  }

  try {
    const chemRes = await fetch(`/chemistry/${USER_ID}`);
    if (chemRes.ok) {
      const pairs = await chemRes.json();
      pairs.forEach((p) => {
        const other = p.player_a_id === USER_ID ? p.player_b_id : p.player_a_id;
        const tr = document.createElement('tr');
        if (p.score >= 80) tr.classList.add('chem-high');
        else if (p.score <= 20) tr.classList.add('chem-low');
        tr.innerHTML = `<td>${other}</td><td>${p.score}</td>`;
        chemTbody.appendChild(tr);
      });
    }
  } catch (e) {
    // ignore chemistry errors
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const bio = bioInput.value;
    const links = linksInput.value
      .split(',')
      .map((l) => l.trim())
      .filter((l) => l);

    await fetch(`/api/user-settings/profile/${USER_ID}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bio, links }),
    });

    const file = avatarInput.files[0];
    if (file) {
      const fd = new FormData();
      fd.append('file', file);
      await fetch('/api/avatars', { method: 'POST', body: fd });
    }
  });
});
