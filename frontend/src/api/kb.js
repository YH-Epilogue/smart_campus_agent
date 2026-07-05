import axios from "axios";

const http = axios.create({ baseURL: "/api/v1" });

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function listKBs(params = {}) {
  const { data } = await http.get("/kb/", { params });
  return data;
}

export async function createKB(name, description, department) {
  const { data } = await http.post("/kb/", { name, description, department });
  return data;
}

export async function deleteKB(kbId) {
  const { data } = await http.delete(`/kb/${kbId}`);
  return data;
}

export async function updateKB(kbId, name, description) {
  const { data } = await http.put(`/kb/${kbId}`, { name, description });
  return data;
}

export async function cloneKB(kbId) {
  const { data } = await http.post(`/kb/${kbId}/clone`);
  return data;
}
