import axios from "axios";

const http = axios.create({ baseURL: "/api/v1" });

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function login(username, password) {
  const { data } = await http.post("/auth/login", { username, password });
  return data;
}

export async function register(username, password) {
  const { data } = await http.post("/auth/register", { username, password });
  return data;
}
