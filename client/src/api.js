// client/src/api.js
// ЕДИНАЯ точка входа для всех запросов на API (Vue + Vite + DRF)
import axios from "axios";
import Cookies from "js-cookie";

// Можно переопределить через VITE_API_BASE, по умолчанию — /api/
const baseURL = (import.meta?.env && import.meta.env.VITE_API_BASE) || "/api/";

const api = axios.create({
  baseURL,
  withCredentials: true,       // отправляем сессионные куки Django
  xsrfCookieName: "csrftoken", // имя cookie с CSRF
  xsrfHeaderName: "X-CSRFToken",
});

// Проставляем CSRF и Content-Type (если не FormData)
api.interceptors.request.use((config) => {
  const token = Cookies.get("csrftoken");
  if (token) config.headers["X-CSRFToken"] = token;

  if (
    !config.headers["Content-Type"] &&
    config.data &&
    !(config.data instanceof FormData)
  ) {
    config.headers["Content-Type"] = "application/json";
  }
  return config;
});

// Нормализуем ошибки
api.interceptors.response.use(
  (resp) => resp,
  (err) => {
    if (err.response) {
      const { status, statusText, data } = err.response;
      const message =
        (data && (data.detail || data.message)) ||
        `${status} ${statusText || "Error"}`;
      return Promise.reject(new Error(message));
    }
    return Promise.reject(err);
  }
);

// --- Вызовы в прежном стиле (совместимо с твоими страницами) ---

export async function apiGet(url) {
  const r = await api.get(url);
  return r.data;
}

export async function apiPost(url, data) {
  const isFD = data instanceof FormData;
  const r = await api.post(url, isFD ? data : JSON.stringify(data), {
    headers: isFD ? { "Content-Type": "multipart/form-data" } : undefined,
  });
  return r.data;
}

export async function apiPatch(url, data) {
  const isFD = data instanceof FormData;
  const r = await api.patch(url, isFD ? data : JSON.stringify(data), {
    headers: isFD ? { "Content-Type": "multipart/form-data" } : undefined,
  });
  return r.data;
}

export async function apiDelete(url) {
  const r = await api.delete(url);
  return r.status === 204 || r.status === 200;
}

// ----- ВАЖНО: инициализация CSRF (выставляет csrftoken cookie) -----
export async function initCsrf() {
  try {
    // этот GET вернёт 200 и установит csrftoken
    await api.get("csrf/");
  } catch {
    // тихо проглатываем — повторим позже
  }
}

export default api;
