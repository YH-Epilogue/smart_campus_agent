import axios from "axios";

const http = axios.create({ baseURL: "/api/v1" });

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function uploadDoc(kbId, file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await http.post(`/doc/upload?kb_id=${kbId}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function listDocs(kbId) {
  const { data } = await http.get(`/doc/${kbId}`);
  return data;
}

export async function deleteDoc(docId) {
  const { data } = await http.delete(`/doc/${docId}`);
  return data;
}

export async function previewDoc(docId) {
  const { data } = await http.get(`/doc/${docId}/preview`);
  return data;
}
