/**
 * 用户管理 API 接口（管理员专用）
 *
 * 提供与后端 /api/v1/users 端点交互的函数：
 * - getUsers: 获取所有用户列表
 * - updateUser: 更新用户信息（角色、密码等）
 * - deleteUser: 删除用户
 *
 * 权限：仅管理员（admin）可调用这些接口
 */
import http from "./http";

/**
 * 获取所有用户列表（管理页面表格数据源）
 * @returns {Array} 用户数组，包含 id/username/role/created_at 等字段
 */
export async function getUsers() {
  const { data } = await http.get("/users/");
  return data;
}

/**
 * 更新指定用户的信息
 * @param {string|number} userId - 用户 ID
 * @param {object} payload - 要更新的字段（如 { role: "teacher" } 或 { password: "new" }）
 */
export async function updateUser(userId, payload) {
  const { data } = await http.put(`/users/${userId}`, payload);
  return data;
}

/**
 * 删除指定用户
 * @param {string|number} userId - 用户 ID
 */
export async function deleteUser(userId) {
  const { data } = await http.delete(`/users/${userId}`);
  return data;
}
