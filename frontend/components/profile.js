import { authFetch, getToken } from '../utils/auth.js';

document.addEventListener('DOMContentLoaded', async () => {
  const token = getToken();
  if (!token) {
    window.location.href = 'login.html';
    return;
  }

  let USER_ID;
  let username;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    USER_ID = payload.sub || payload.user_id;
    username = payload.username || payload.sub;
    const header = document.querySelector('h1');
    if (header && username) header.textContent = `Profile - ${username}`;
  } catch (e) {
    // ignore parse errors
  }

  const form = document.getElementById('profile-form');
  const bioInput = document.getElementById('bio');
  const linksInput = document.getElementById('links');
  const avatarInput = document.getElementById('avatar-input');
  const chemTbody = document.querySelector('#chemistry-table tbody');

  try {
    const res = await authFetch(`/api/user-settings/profile/${USER_ID}`);
    if (res && res.ok) {
      const data = await res.json();
      bioInput.value = data.bio || '';
      linksInput.value = (data.links || []).join(', ');
    }
  } catch (e) {
    // ignore load errors
  }

  try {
    const chemRes = await authFetch(`/chemistry/${USER_ID}`);
    if (chemRes && chemRes.ok) {
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

    await authFetch(`/api/user-settings/profile/${USER_ID}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bio, links }),
    });

    const file = avatarInput.files[0];
    if (file) {
      const fd = new FormData();
      fd.append('file', file);
      await authFetch('/api/avatars', { method: 'POST', body: fd });
    }
  });
});
