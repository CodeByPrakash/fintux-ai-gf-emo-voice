export const WS_URL = `ws://${window.location.hostname}:8000/ws/chat`;
export const API_BASE = '/api';

export async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function apiPut(path, data) {
  return apiFetch(path, { method: 'PUT', body: JSON.stringify(data) });
}

export async function apiPost(path, data = {}) {
  return apiFetch(path, { method: 'POST', body: JSON.stringify(data) });
}

export async function apiDelete(path) {
  return apiFetch(path, { method: 'DELETE' });
}
