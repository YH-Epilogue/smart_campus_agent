/**
 * 全局 HTTP 请求实例
 *
 * 功能：
 * - 创建统一的 axios 实例，所有 API 模块共享此实例
 * - 设置 API 基础路径为 /api/v1
 * - 请求拦截器自动附加 JWT token 到 Authorization 头
 * - 避免每个 API 文件重复创建 axios 实例和拦截器
 *
 * 使用方式：import http from "./http"，然后调用 http.get/post/put/delete
 */
import axios from "axios";

// 创建 axios 实例，统一设置 API 基础路径（对应后端 FastAPI 的 /api/v1 路由前缀）
const http = axios.create({ baseURL: "/api/v1" });

// 请求拦截器：每次发请求前自动从 localStorage 读取 token 并附加到请求头
http.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default http;
