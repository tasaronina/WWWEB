import axios from "axios";

// глобальные настройки
axios.defaults.withCredentials = true;
axios.defaults.headers.common["X-Requested-With"] = "XMLHttpRequest";

// ---- CSRF helper ----
function getCookie(name) {
  if (typeof document === "undefined") return null;
  const m = document.cookie.match(new RegExp("(^|; )" + name + "=([^;]*)"));
  return m ? decodeURIComponent(m[2]) : null;
}

function attachCsrf(config) {
  const method = (config?.method || "get").toLowerCase();
  if (["post", "put", "patch", "delete"].includes(method)) {
    config.headers ||= {};
    if (!config.headers["X-CSRFToken"]) {
      const token = getCookie("csrftoken");
      if (token) config.headers["X-CSRFToken"] = token;
    }
  }
  return config;
}

// подставляем CSRF для ЛЮБЫХ axios-запросов
axios.interceptors.request.use(attachCsrf);

// инстанс (если где-то импортируют именно api)
const api = axios.create({});
api.interceptors.request.use(attachCsrf);

export async function ensureCsrf() {
  await axios.get("/api/csrf/");
}

export async function downloadExport(resource, params = {}, type = "excel", filenameBase = "export") {
  const { data, headers } = await axios.get(`/api/${resource}/export/`, {
    params: { ...params, type },
    responseType: "blob",
  });

  // имя файла берём из Content-Disposition, если есть
  let filename = filenameBase;
  const dispo = headers["content-disposition"] || headers["Content-Disposition"] || "";
  const m = /filename\*=UTF-8''([^;]+)|filename="?([^"]+)"?/i.exec(dispo);
  if (m) {
    filename = decodeURIComponent((m[1] || m[2] || "").trim());
  } else {
    filename += type === "word" ? ".doc" : ".csv";
  }

  const url = URL.createObjectURL(data);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export default api;
