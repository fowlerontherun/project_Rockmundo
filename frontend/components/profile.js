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

  const bandForm = document.getElementById('band-form');
  const bandNameInput = document.getElementById('band-name');
  const bandGenreInput = document.getElementById('band-genre');
  const bandFounderInput = document.getElementById('band-founder');
  const bandError = document.getElementById('band-error');

  if (bandFounderInput && USER_ID) bandFounderInput.value = USER_ID;

  const avatarForm = document.getElementById('avatar-form');
  const avatarError = document.getElementById('avatar-error');

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

  if (bandForm) {
    bandForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (bandError) bandError.textContent = '';
      const payload = {
        name: bandNameInput.value,
        genre: bandGenreInput.value,
        founder_id: parseInt(bandFounderInput.value, 10),
      };
      const res = await authFetch('/api/bands', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        bandForm.reset();
        if (bandFounderInput && USER_ID) bandFounderInput.value = USER_ID;
      } else {
        let errText = 'Failed to create band';
        try {
          const data = await res.json();
          if (Array.isArray(data.detail)) {
            errText = data.detail.map((d) => d.msg).join(', ');
          } else if (data.detail) {
            errText = data.detail;
          }
        } catch (err) {
          // ignore parse errors
        }
        if (bandError) bandError.textContent = errText;
      }
    });
  }

  if (avatarForm) {
    avatarForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (avatarError) avatarError.textContent = '';
      const payload = {
        character_id: parseInt(document.getElementById('avatar-character-id').value, 10),
        nickname: document.getElementById('avatar-nickname').value,
        body_type: document.getElementById('avatar-body').value,
        skin_tone: document.getElementById('avatar-skin').value,
        face_shape: document.getElementById('avatar-face').value,
        hair_style: document.getElementById('avatar-hair-style').value,
        hair_color: document.getElementById('avatar-hair-color').value,
        top_clothing: document.getElementById('avatar-top').value,
        bottom_clothing: document.getElementById('avatar-bottom').value,
        shoes: document.getElementById('avatar-shoes').value,
      };
      const res = await authFetch('/api/avatars', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        avatarForm.reset();
      } else {
        let errText = 'Failed to create avatar';
        try {
          const data = await res.json();
          if (Array.isArray(data.detail)) {
            errText = data.detail.map((d) => d.msg).join(', ');
          } else if (data.detail) {
            errText = data.detail;
          }
        } catch (err) {
          // ignore parse errors
        }
        if (avatarError) avatarError.textContent = errText;
      }
    });
  }
});
