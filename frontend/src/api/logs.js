/**
 * 日志管理 API 接口（管理员专用）
 *
 * 提供与后端 /api/v1/logs 端点交互的函数：
 * - getLogs: 获取操作日志列表（支持分页和筛选）
 * - exportLogs: 导出日志为文件下载
 * - cleanupLogs: 清理指定天数之前的历史日志
 *
 * 权限：仅管理员（admin）可调用
 */
import http from "./http";

/**
 * 获取操作日志列表
 * @param {object} params - 查询参数（可选，如 status/username/days/page_size/page）
 * @returns {Array} 日志条目数组
 */
export async function getLogs(params = {}) {
  const { data } = await http.get("/logs/", { params });
  return data;
}

/**
 * 导出日志为文件（浏览器自动下载）
 * @returns {Blob} 日志文件的二进制数据（前端触发下载）
 */
export async function exportLogs() {
  const resp = await http.get("/logs/export", {
    responseType: "blob",
  });
  return resp.data;
}

/**
 * 清理历史日志
 * @param {number} days - 保留最近多少天的日志（默认30天，删除更早的记录）
 * @returns {object} 清理结果，包含删除的记录数
 */
export async function cleanupLogs(days = 30) {
  const { data } = await http.delete("/logs/cleanup", {
    params: { days },
  });
  return data;
}
