/**
 * 聊天状态管理（Pinia Store）
 *
 * 功能：
 * - 管理对话列表（conversations）、当前会话消息（messages）
 * - 提供创建会话、发送消息、加载历史、删除会话等操作
 * - 发送消息时自动更新会话标题（取用户第一条消息的前30字符）
 * - loading 状态用于控制前端消息加载动画
 *
 * 消息结构：{ role: "user"|"assistant", content, sources?, file_name?, supplement? }
 * 会话结构：{ id, title, message_count, latest_time }
 */
import { defineStore } from "pinia";
import { ref } from "vue";
import { sendMessage as apiSendMessage, getHistory, getSessions, deleteSession as apiDeleteSession } from "../api/chat";

export const useChatStore = defineStore("chat", () => {
  // 对话列表（侧边栏显示的所有会话）
  const conversations = ref([]);
  // 当前正在查看的会话 ID
  const currentSessionId = ref("");
  // 当前会话的消息列表（包含 user 和 assistant 消息）
  const messages = ref([]);
  // 消息发送中的加载状态，控制发送按钮禁用和加载动画
  const loading = ref(false);

  /**
   * 从后端加载所有对话列表（侧边栏用）
   * 后端返回 sessions 数组，前端映射为前端需要的字段格式
   */
  async function loadSessions() {
    try {
      const sessions = await getSessions();
      conversations.value = sessions.map((s) => ({
        id: s.session_id,
        title: s.title,
        message_count: s.message_count,
        latest_time: s.latest_time,
      }));
    } catch (e) {
      console.error("Failed to load sessions:", e);
    }
  }

  /**
   * 创建新会话（前端本地创建，不调用后端）
   * 使用时间戳作为临时 ID，首次发消息后后端会生成真正的 session_id
   */
  function createSession() {
    const id = "session_" + Date.now();
    conversations.value.unshift({ id, title: "新对话", message_count: 0 });
    currentSessionId.value = id;
    messages.value = [];
    return id;
  }

  /**
   * 发送消息并获取 AI 回复
   * @param {string} query - 用户输入的问题
   * @param {string} kbId - 关联的知识库 ID（可选，为空则使用全局对话）
   * @param {string} fileName - 附件文件名（可选）
   * @param {string} supplementText - 补充说明文字（可选）
   */
  async function sendMessage(query, kbId, fileName, supplementText) {
    // 没有当前会话时自动创建新会话
    if (!currentSessionId.value) createSession();

    // 先将用户消息加入消息列表（乐观更新，立即显示）
    messages.value.push({ role: "user", content: query, file_name: fileName || null, supplement: supplementText || null });
    loading.value = true;

    try {
      // 调用后端 chat API 获取 AI 回复
      const res = await apiSendMessage(currentSessionId.value, kbId, query);
      messages.value.push({
        role: "assistant",
        content: res.answer,
        sources: res.sources, // RAG 检索来源（知识库文档引用）
      });
      // 首条消息发送后，用消息内容更新会话标题（取前30字）
      const conv = conversations.value.find((c) => c.id === currentSessionId.value);
      if (conv && conv.title === "新对话") {
        conv.title = query.slice(0, 30);
      }
    } catch (e) {
      // 错误时在消息列表中显示错误提示（红色提示）
      messages.value.push({
        role: "assistant",
        content: "抱歉，发生了错误：" + e.message,
      });
    } finally {
      loading.value = false;
    }
  }

  /**
   * 加载指定会话的历史消息（点击侧边栏会话时调用）
   * 设置 currentSessionId 并从后端拉取消息列表
   */
  async function loadHistory(sessionId) {
    currentSessionId.value = sessionId;
    messages.value = await getHistory(sessionId);
  }

  /**
   * 删除会话：调用后端删除 + 前端移除列表项
   * 如果删除的是当前会话，自动清空消息列表
   */
  async function deleteSession(sessionId) {
    try {
      await apiDeleteSession(sessionId);
      conversations.value = conversations.value.filter((c) => c.id !== sessionId);
      if (currentSessionId.value === sessionId) {
        currentSessionId.value = "";
        messages.value = [];
      }
    } catch (e) {
      console.error("Failed to delete session:", e);
    }
  }

  return {
    conversations,
    currentSessionId,
    messages,
    loading,
    loadSessions,
    createSession,
    sendMessage,
    loadHistory,
    deleteSession,
  };
});
