export function getToken() {
  return localStorage.getItem('jwt');
}

export function setToken(token) {
  localStorage.setItem('jwt', token);
}

export function getSelectedCharacterId() {
  const value = localStorage.getItem('rockmundo.selectedCharacterId');
  if (!value) return null;
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

export function setSelectedCharacterId(characterId) {
  const next = Number.parseInt(characterId, 10);
  if (!Number.isFinite(next) || next <= 0) {
    localStorage.removeItem('rockmundo.selectedCharacterId');
  } else {
    localStorage.setItem('rockmundo.selectedCharacterId', String(next));
  }
  window.dispatchEvent(new CustomEvent('rockmundo:character-changed', { detail: { characterId: getSelectedCharacterId() } }));
}

export async function authFetch(input, init = {}) {
  const token = getToken();
  const headers = new Headers(init.headers || {});
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  const characterId = getSelectedCharacterId();
  if (characterId) {
    headers.set('X-Character-ID', String(characterId));
  }
  return fetch(input, { ...init, headers });
}
