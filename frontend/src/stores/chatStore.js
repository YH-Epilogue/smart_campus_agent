import { defineStore } from "pinia";
import { ref } from "vue";
import { sendMessage as apiSendMessage, getHistory, getSessions, deleteSession as apiDeleteSession } from "../api/chat";

export const useChatStore = defineStore("chat", () => {
  const conversations = ref([]);
  const currentSessionId = ref("");
  const messages = ref([]);
  const loading = ref(false);

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

  function createSession() {
    const id = "session_" + Date.now();
    conversations.value.unshift({ id, title: "新对话", message_count: 0 });
    currentSessionId.value = id;
    messages.value = [];
    return id;
  }

  async function sendMessage(query, kbId, fileName, supplementText) {
    if (!currentSessionId.value) createSession();

    messages.value.push({ role: "user", content: query, file_name: fileName || null, supplement: supplementText || null });
    loading.value = true;

    try {
      const res = await apiSendMessage(currentSessionId.value, kbId, query);
      messages.value.push({
        role: "assistant",
        content: res.answer,
        sources: res.sources,
      });
      // Update session title if first message
      const conv = conversations.value.find((c) => c.id === currentSessionId.value);
      if (conv && conv.title === "新对话") {
        conv.title = query.slice(0, 30);
      }
    } catch (e) {
      messages.value.push({
        role: "assistant",
        content: "抱歉，发生了错误：" + e.message,
      });
    } finally {
      loading.value = false;
    }
  }

  async function loadHistory(sessionId) {
    currentSessionId.value = sessionId;
    messages.value = await getHistory(sessionId);
  }

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
