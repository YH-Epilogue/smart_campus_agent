/**
 * 认证相关 API 接口
 *
 * 提供与后端 /api/v1/auth 端点交互的函数：
 * - login: 用户登录，获取 JWT token
 * - register: 新用户注册
 *
 * 注意：此文件用于认证（登录/注册），用户管理（增删改查）请使用 users.js
 */
import http from "./http";

/**
 * 用户登录
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @returns {object} { access_token: JWT token, role: 用户角色 }
 */
export async function login(username, password) {
  const { data } = await http.post("/auth/login", { username, password });
  return data;
}

/**
 * 新用户注册
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @param {string} role - 用户角色（默认 "student"，可选 "teacher"/"admin"）
 * @returns {object} 注册结果信息
 */
export async function register(username, password, role = "student") {
  const { data } = await http.post("/auth/register", { username, password, role });
  return data;
}
