export async function apiFetch(input, init = {}) {
  const headers = new Headers(init.headers || {});
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('jwt') : null;
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (
    init.body &&
    !(init.body instanceof FormData) &&
    !(init.body instanceof URLSearchParams) &&
    typeof init.body !== 'string'
  ) {
    headers.set('Content-Type', 'application/json');
    init.body = JSON.stringify(init.body);
  }

  const API_BASE =
    (typeof process !== 'undefined' && process.env && process.env.REACT_APP_API_BASE) ||
    (typeof window !== 'undefined' && window.API_BASE) ||
    '';

  let url = typeof input === 'string' ? input : input.url;
  if (!/^https?:\/\//i.test(url)) {
    url = API_BASE + url;
  }

  const response = await fetch(url, { ...init, headers });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response;
}

if (typeof window !== 'undefined') {
  window.apiFetch = apiFetch;
}

