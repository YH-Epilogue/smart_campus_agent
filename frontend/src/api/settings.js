/**
 * 系统设置 API 接口（管理员专用）
 *
 * 提供与后端 /api/v1/settings 端点交互的函数：
 * - getSettings: 获取当前系统设置（API Key、模型配置等）
 * - updateSettings: 更新系统设置
 *
 * 权限：仅管理员（admin）可调用
 * 设置内容包括：DeepSeek API Key、LLM 模型名称、温度参数等
 */
import http from "./http";

/**
 * 获取系统当前设置
 * @returns {object} 设置对象，包含 api_key/model/temperature 等配置项
 */
export async function getSettings() {
  const { data } = await http.get("/settings/");
  return data;
}

/**
 * 更新系统设置
 * @param {object} payload - 要更新的设置字段（部分更新，仅传需要修改的字段）
 */
export async function updateSettings(payload) {
  const { data } = await http.put("/settings/", payload);
  return data;
}
