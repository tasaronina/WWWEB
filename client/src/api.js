// client/src/api.js
// Простой помощник для запросов к API

import axios from "axios";

// Базовый URL для API
const BASE_URL = "/api/";

// Собираем URL аккуратно
function buildUrl(url) {
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }
  if (url.startsWith("/api/")) {
    return url;
  }
  if (url.startsWith("/")) {
    return `/api${url}`;
  }
  return BASE_URL + url;
}

export async function apiGet(url) {
  const response = await axios.get(buildUrl(url));
  return response.data;
}

export async function apiPost(url, data) {
  const response = await axios.post(buildUrl(url), data);
  return response.data;
}

export async function apiPatch(url, data) {
  const response = await axios.patch(buildUrl(url), data);
  return response.data;
}

export async function apiDelete(url) {
  const response = await axios.delete(buildUrl(url));
  return response.status === 200 || response.status === 204;
}

// По умолчанию экспортируем axios, чтобы можно было использовать как раньше
export default axios;
