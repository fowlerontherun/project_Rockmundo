export function getToken() {
  return localStorage.getItem('jwt');
}

export function setToken(token) {
  localStorage.setItem('jwt', token);
}

export async function authFetch(input, init = {}) {
  const token = getToken();
  const headers = new Headers(init.headers || {});
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return fetch(input, { ...init, headers });
}
