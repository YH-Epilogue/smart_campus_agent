/**
 * 用户状态管理（Pinia Store）
 *
 * 功能：
 * - 管理 JWT token 和用户信息的全局状态
 * - 提供登录/登出操作，与后端认证 API 交互
 * - 持久化 token 到 localStorage，刷新页面后自动恢复登录状态
 * - 提供角色判断的计算属性（isAdmin/isTeacher/isStudent），供路由守卫和组件使用
 *
 * 使用方式：在组件中调用 useUserStore() 获取 store 实例
 */
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { login as apiLogin } from "../api/user";
import { decodeToken } from "../utils/jwt";

export const useUserStore = defineStore("user", () => {
  // JWT token，页面刷新时从 localStorage 自动恢复
  const token = ref(localStorage.getItem("token") || "");
  // 当前登录用户信息（id/username/role），从 token 中解析得出
  const user = ref(loadUserFromToken());

  // 是否已登录（token 非空即为已登录）
  const isLoggedIn = computed(() => !!token.value);
  // 角色判断：学生
  const isStudent = computed(() => user.value?.role === "student");
  // 角色判断：老师（可查看知识库/文档/请假管理）
  const isTeacher = computed(() => user.value?.role === "teacher");
  // 角色判断：管理员（可访问全部管理页面）
  const isAdmin = computed(() => user.value?.role === "admin");

  /**
   * 从 localStorage 中读取 token 并解析用户信息
   * token 过期或格式错误时返回 null，用户需重新登录
   */
  function loadUserFromToken() {
    const t = localStorage.getItem("token");
    if (!t) return null;
    const payload = decodeToken(t);
    if (!payload) return null;
    // JWT payload 中 sub=username, role 决定权限等级
    return { id: payload.sub, username: payload.username, role: payload.role || "student" };
  }

  /**
   * 登录：调用后端 /api/v1/auth/login 接口
   * 成功后将 token 和用户信息写入响应式状态和 localStorage
   */
  async function login(username, password) {
    const res = await apiLogin(username, password);
    token.value = res.access_token;
    user.value = { username, role: res.role };
    localStorage.setItem("token", res.access_token);
    return res;
  }

  /**
   * 登出：清空所有用户状态，移除 localStorage 中的 token
   * 调用后路由守卫会自动跳转到 /login
   */
  function logout() {
    token.value = "";
    user.value = null;
    localStorage.removeItem("token");
  }

  return { token, user, isLoggedIn, isStudent, isTeacher, isAdmin, login, logout };
});
