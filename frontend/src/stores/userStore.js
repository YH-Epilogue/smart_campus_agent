import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { login as apiLogin } from "../api/user";
import { decodeToken } from "../utils/jwt";

export const useUserStore = defineStore("user", () => {
  const token = ref(localStorage.getItem("token") || "");
  const user = ref(loadUserFromToken());

  const isLoggedIn = computed(() => !!token.value);

  function loadUserFromToken() {
    const t = localStorage.getItem("token");
    if (!t) return null;
    const payload = decodeToken(t);
    if (!payload) return null;
    return { id: payload.sub, username: payload.username, role: payload.role || "user" };
  }

  async function login(username, password) {
    const res = await apiLogin(username, password);
    token.value = res.access_token;
    user.value = { username, role: res.role };
    localStorage.setItem("token", res.access_token);
  }

  function logout() {
    token.value = "";
    user.value = null;
    localStorage.removeItem("token");
  }

  return { token, user, isLoggedIn, login, logout };
});
