/**
 * 请假管理 API 接口
 *
 * 提供与后端 /api/v1/leave 端点交互的函数：
 * - getLeaveList: 获取请假列表（支持按状态筛选）
 * - getLeaveStats: 获取请假统计数据（各状态的数量）
 * - approveLeave: 审批通过请假申请
 * - rejectLeave: 审批拒绝请假申请
 *
 * 使用场景：
 * - 学生端：提交请假申请（通过 ChatView 中的对话提交）
 * - 管理端：查看/审批请假列表
 */
import http from "./http";

/**
 * 获取请假列表
 * @param {string} status - 按状态筛选（可选："pending"/"approved"/"rejected"，不传则返回全部）
 * @returns {Array} 请假记录数组，包含学生信息、请假原因、时间、状态等
 */
export async function getLeaveList(status) {
  const params = status ? { status } : {};
  const { data } = await http.get("/leave/", { params });
  return data;
}

/**
 * 获取请假统计数据（仪表盘和管理页面用）
 * @returns {object} { pending: 待审批数, approved: 已通过数, rejected: 已拒绝数, total: 总数 }
 */
export async function getLeaveStats() {
  const { data } = await http.get("/leave/stats");
  return data;
}

/**
 * 审批通过请假申请
 * @param {string|number} leaveId - 请假记录 ID
 */
export async function approveLeave(leaveId) {
  const { data } = await http.put(`/leave/${leaveId}/approve`);
  return data;
}

/**
 * 审批拒绝请假申请
 * @param {string|number} leaveId - 请假记录 ID
 */
export async function rejectLeave(leaveId) {
  const { data } = await http.put(`/leave/${leaveId}/reject`);
  return data;
}
