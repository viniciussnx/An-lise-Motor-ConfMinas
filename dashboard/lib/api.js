/**
 * Cliente HTTP central — anexa token Bearer e expulsa para /login se 401.
 */

export const API =
  (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_URL) ||
  'http://localhost:8000';

const TOKEN_KEY = 'confiminas_token';
const USER_KEY = 'confiminas_user';

export function getToken() {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getUser() {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveSession({ token, username, expires_at }) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(TOKEN_KEY, token);
  window.localStorage.setItem(
    USER_KEY,
    JSON.stringify({ username, expires_at }),
  );
}

export function clearSession() {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

export function isAuthenticated() {
  const token = getToken();
  const user = getUser();
  if (!token || !user) return false;
  if (user.expires_at && Date.now() / 1000 > user.expires_at) {
    clearSession();
    return false;
  }
  return true;
}

export async function apiFetch(path, opts = {}) {
  const headers = new Headers(opts.headers || {});
  if (!headers.has('Content-Type') && opts.body) {
    headers.set('Content-Type', 'application/json');
  }
  const token = getToken();
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  const url = path.startsWith('http') ? path : `${API}${path}`;
  const res = await fetch(url, { ...opts, headers });

  if (res.status === 401) {
    clearSession();
    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
      const next = encodeURIComponent(window.location.pathname + window.location.search);
      window.location.href = `/login?next=${next}`;
    }
    throw new Error('Sessão expirada');
  }
  return res;
}

export async function login(username, password) {
  const res = await fetch(`${API}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Falha no login');
  }
  const data = await res.json();
  saveSession(data);
  return data;
}

export function logout() {
  clearSession();
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}
