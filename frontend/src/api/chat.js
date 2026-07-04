import axios from "axios";

const http = axios.create({ baseURL: "/api/v1" });

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function sendMessage(sessionId, kbId, query) {
  const payload = { session_id: sessionId, query };
  if (kbId) {
    payload.kb_id = kbId;
  }
  const { data } = await http.post("/chat/", payload);
  return data;
}

export async function getHistory(sessionId) {
  const { data } = await http.get(`/chat/${sessionId}`);
  return data;
}

export async function getSessions() {
  const { data } = await http.get("/logs/sessions");
  return data;
}

export async function deleteSession(sessionId) {
  const { data } = await http.delete(`/chat/${sessionId}`);
  return data;
}
