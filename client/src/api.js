

import axios from "axios";
import Cookies from "js-cookie";


axios.defaults.withCredentials = true;
axios.defaults.xsrfCookieName = "csrftoken";
axios.defaults.xsrfHeaderName = "X-CSRFToken";


const api = axios.create({
  baseURL: "/api/",
  withCredentials: true,
});


function attachCSRF(config) {
  const token = Cookies.get("csrftoken");
  if (token) {
    config.headers = config.headers || {};
    if (!("X-CSRFToken" in config.headers)) {
      config.headers["X-CSRFToken"] = token;
    }
  }
  return config;
}
axios.interceptors.request.use(attachCSRF);
api.interceptors.request.use(attachCSRF);


let notify = null;

export function setNotifier(fn) { notify = fn; }


function handleError(error) {
  const status = error?.response?.status;

  const detail =
    error?.response?.data?.detail ||
    error?.response?.data?.message ||
    "";

  if (status === 403) {
    notify?.("У вас нет прав на это действие.", "warning");
  } else if (status === 401) {
    notify?.("Необходимо войти в систему.", "warning");
  } else if (status >= 500) {
    notify?.("Ошибка сервера. Попробуйте позже.", "danger");
  } else if (detail) {
    notify?.(String(detail), "danger");
  }
  return Promise.reject(error);
}
axios.interceptors.response.use(r => r, handleError);
api.interceptors.response.use(r => r, handleError);


function normalize(url) {
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  if (url.startsWith("/api/")) return url.slice(5);
  return url;
}
export async function apiGet(url, config) {
  const res = await api.get(normalize(url), config);
  return res.data;
}
export async function apiPost(url, data, config) {
  const res = await api.post(normalize(url), data, config);
  return res.data;
}
export async function apiPatch(url, data, config) {
  const res = await api.patch(normalize(url), data, config);
  return res.data;
}
export async function apiDelete(url, config) {
  const res = await api.delete(normalize(url), config);
  return res.status === 200 || res.status === 204;
}


export const getCSRF    = () => api.get("csrf/");
export const authLogin  = (u, p) => api.post("auth/login/", { username: u, password: p });
export const authLogout = () => api.post("auth/logout/");
export const authMe     = () => api.get("auth/me/");

export default api;
