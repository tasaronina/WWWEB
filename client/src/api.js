
import axios from "axios";

axios.defaults.withCredentials = true;

export const api = axios.create({
  baseURL: "/",
  withCredentials: true,
});


api.defaults.xsrfCookieName = "csrftoken";
api.defaults.xsrfHeaderName = "X-CSRFToken";

export async function ensureCsrf() {
  try { await api.get("/api/csrf/"); } catch {}
}

export async function getMe() {
  const { data } = await api.get("/api/auth/me/");
  return data;
}

export async function doLogin(username, password) {

  await ensureCsrf();
  const { data } = await api.post("/api/auth/login/", { username, password });
  return data;
}

export async function doLogout() {
  await ensureCsrf();
  await api.post("/api/auth/logout/");
}


export async function downloadExport(arg1, arg2, arg3) {
  let path, params, filename;
  if (typeof arg1 === "string") {
    path = arg1;
    params = (arg2 && typeof arg2 === "object") ? arg2 : {};
    filename = typeof arg3 === "string" ? arg3 : "export.csv";
  } else if (arg1 && typeof arg1 === "object") {
    path = arg1.path || "/api/order-items/";
    params = arg1.params || {};
    filename = arg1.filename || "export.csv";
  } else {
    path = "/api/order-items/";
    params = {};
    filename = "export.csv";
  }
  if (!path.startsWith("/")) path = "/" + path;

  const resp = await api.get(path, { params, responseType: "blob" });
  const ct = resp.headers["content-type"] || "";

  // если сервер дал файл — скачиваем
  if (!ct.includes("application/json")) {
    const blob = resp.data instanceof Blob ? resp.data : new Blob([resp.data]);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    return;
  }

  // иначе это JSON — попробуем превратить в CSV
  const text = await resp.data.text();
  let rows;
  try { rows = JSON.parse(text); } catch {
    const blob = new Blob([text], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename.replace(/\.csv$/i, ".json");
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
    return;
  }
  const arr = Array.isArray(rows) ? rows : (Array.isArray(rows?.results) ? rows.results : [rows]);
  if (!arr.length) {
    const blob = new Blob([""], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    return;
  }
  const headers = Array.from(new Set(arr.flatMap(o => Object.keys(o))));
  const csvLines = [
    headers.join(","),
    ...arr.map(o => headers.map(h => {
      const v = o[h] ?? "";
      const s = typeof v === "object" ? JSON.stringify(v) : String(v);
      return `"${s.replace(/"/g, '""')}"`;
    }).join(",")),
  ];
  const blob = new Blob([csvLines.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
}


export default api;
