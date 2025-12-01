

import axios from "axios";

const api = axios.create({
  baseURL: "/api/",
  withCredentials: true,
});


export const apiGet = (url, params = {}) =>
  api.get(url, { params }).then((r) => r.data);

export const apiPost = (url, data = {}) =>
  api.post(url, data).then((r) => r.data);

export const apiPatch = (url, data = {}) =>
  api.patch(url, data).then((r) => r.data);

export const apiDelete = (url) =>
  api.delete(url).then((r) => r.data);

export async function exportFile(entity, params = {}, type = "excel") {
  const q = new URLSearchParams({ ...(params || {}), type }).toString();
  const url = `${entity}/export/?${q}`;
  const res = await api.get(url, { responseType: "blob" });
  return res.data; // Blob
}

export async function downloadExport(
  entity,
  params = {},
  type = "excel",
  filename = "export"
) {
  const data = await exportFile(entity, params, type);
  const blob = new Blob([data], {
    type:
      type === "word"
        ? "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  });

  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename + (type === "word" ? ".docx" : ".xlsx"));
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}


export const fetchOrders = (params = {}) => apiGet("orders/", params);
export const fetchOrderItems = (params = {}) => apiGet("order-items/", params);

export default api;
