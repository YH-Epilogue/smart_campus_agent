/**
 * 聊天相关 API 接口
 *
 * 提供与后端 /api/v1/chat 端点交互的函数：
 * - sendMessage: 发送消息并获取 AI 回复（支持指定知识库 ID）
 * - getHistory: 获取指定会话的历史消息
 * - getSessions: 获取所有对话列表（从 logs 接口获取）
 * - deleteSession: 删除指定会话及其消息记录
 */
import http from "./http";

/**
 * 发送消息并获取 AI 回复
 * @param {string} sessionId - 会话 ID（首次发消息前由前端临时生成）
 * @param {string} kbId - 知识库 ID（可选，为空则使用全局对话，不走 RAG）
 * @param {string} query - 用户输入的问题文本
 * @returns {object} { answer: AI 回复, sources: RAG 检索来源 }
 */
export async function sendMessage(sessionId, kbId, query) {
  const payload = { session_id: sessionId, query };
  // 仅在指定了知识库时才传 kb_id，否则后端走全局对话模式
  if (kbId) {
    payload.kb_id = kbId;
  }
  const { data } = await http.post("/chat/", payload);
  return data;
}

/**
 * 获取指定会话的历史消息列表
 * @param {string} sessionId - 会话 ID
 * @returns {Array} 消息数组，每条包含 role/content/sources 等字段
 */
export async function getHistory(sessionId) {
  const { data } = await http.get(`/chat/${sessionId}`);
  return data;
}

/**
 * 获取当前用户的所有对话列表（侧边栏展示用）
 * 注意：此接口复用 /logs/sessions 端点获取会话摘要信息
 * @returns {Array} 会话数组，包含 session_id/title/message_count/latest_time
 */
export async function getSessions() {
  const { data } = await http.get("/logs/sessions");
  return data;
}

/**
 * 删除指定会话及其所有消息记录
 * @param {string} sessionId - 要删除的会话 ID
 */
export async function deleteSession(sessionId) {
  const { data } = await http.delete(`/chat/${sessionId}`);
  return data;
}
