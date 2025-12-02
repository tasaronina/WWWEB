import axios from "axios";

// ВАЖНО: используем ТОТ ЖЕ ХОСТ, что и у фронта (127.0.0.1), иначе кука сессии не поедет.
export const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  withCredentials: true,
  headers: { "X-Requested-With": "XMLHttpRequest" },
});

function getCookie(name) {
  if (typeof document === "undefined") return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

export async function ensureCsrf() {
  // получаем CSRF cookie и прокидываем в заголовки
  await api.get("/api/csrf/");
  const csrftoken = getCookie("csrftoken");
  if (csrftoken) api.defaults.headers.common["X-CSRFToken"] = csrftoken;
}

export async function login(username, password) {
  await ensureCsrf();
  await api.post("/api/auth/login/", { username, password });
  // Сразу проверяем, приклеилась ли сессия
  const { data } = await api.get("/api/auth/me/");
  return data; // { authenticated, user, otp_ttl }
}

export async function logout() {
  await ensureCsrf();
  await api.post("/api/auth/logout/");
}

export default api;
