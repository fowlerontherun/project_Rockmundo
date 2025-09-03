const USER_ID = 1;

document.addEventListener('DOMContentLoaded', async () => {
  const form = document.getElementById('profile-form');
  const bioInput = document.getElementById('bio');
  const linksInput = document.getElementById('links');
  const avatarInput = document.getElementById('avatar-input');

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
