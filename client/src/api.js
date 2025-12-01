// Единая точка работы с API: CSRF + withCredentials + удобные функции

import axiosBase from "axios";

const axios = axiosBase.create({
  baseURL: "",
  withCredentials: true,
});

// ---- CSRF helpers ----
function getCookie(name) {
  const m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
  return m ? decodeURIComponent(m.pop()) : "";
}

export async function ensureCsrf() {
  try {
    await axios.get("/api/csrf/");
  } catch {}
}

// автоматически подставляем X-CSRFToken
axios.interceptors.request.use((config) => {
  const method = (config.method || "get").toLowerCase();
  if (["post", "put", "patch", "delete"].includes(method)) {
    const token = getCookie("csrftoken");
    if (token) config.headers["X-CSRFToken"] = token;
  }
  return config;
});

// ---- API calls ----
export async function apiMe() {
  const { data } = await axios.get("/api/auth/me/");
  return data || {};
}

export async function apiLogin(username, password) {
  await ensureCsrf();
  const payload = { username, password };
  // сервер допускает и login, и username — отправим оба
  payload.login = username;
  await axios.post("/api/auth/login/", payload);
}

export async function apiLogout() {
  await ensureCsrf();
  await axios.post("/api/auth/logout/", {});
}

// Нужен для старых импортов, чтобы не падало
export async function downloadExport() {
  /* заглушка — ничего не делает */
}

export default axios;
