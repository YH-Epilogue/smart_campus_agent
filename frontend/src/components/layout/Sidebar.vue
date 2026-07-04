<template>
  <div class="sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <div v-if="!collapsed" class="header-title">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span>会话</span>
      </div>
      <button v-if="!collapsed" class="new-btn" @click="handleNew">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        新对话
      </button>
    </div>

    <div v-if="!collapsed" class="session-list">
      <div
        v-for="conv in chatStore.conversations"
        :key="conv.id"
        class="session-item"
        :class="{ active: conv.id === chatStore.currentSessionId }"
        @click="chatStore.loadHistory(conv.id)"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="flex-shrink:0;opacity:0.5">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span class="session-title">{{ conv.title }}</span>
        <button class="del-btn" @click.stop="handleDelete(conv.id)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <div v-if="!chatStore.conversations.length" class="empty-state">
        <p>暂无会话</p>
      </div>
    </div>

    <div v-if="!collapsed" class="sidebar-footer">
      <router-link to="/admin/kb" class="nav-link">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
        </svg>
        知识库管理
      </router-link>
      <router-link to="/admin/doc" class="nav-link">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
        </svg>
        文档管理
      </router-link>
    </div>

    <button class="toggle-btn" @click="collapsed = !collapsed">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
        :style="{ transform: collapsed ? 'rotate(180deg)' : '' }">
        <polyline points="9 18 15 12 9 6"/>
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useChatStore } from "../../stores/chatStore";
import { ElMessageBox } from "element-plus";

const chatStore = useChatStore();
const collapsed = ref(false);

function handleNew() { chatStore.createSession(); }

async function handleDelete(id) {
  try {
    await ElMessageBox.confirm("确定删除此会话？", "确认", {
      confirmButtonText: "确定", cancelButtonText: "取消", type: "warning",
    });
    await chatStore.deleteSession(id);
  } catch (e) {}
}

onMounted(() => { chatStore.loadSessions(); });
</script>

<style scoped>
.sidebar {
  width: 260px; background: rgba(8,11,18,0.4);
  border-right: 1px solid rgba(255,255,255,0.06);
  display: flex; flex-direction: column;
  transition: width 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative; flex-shrink: 0; z-index: 3;
  backdrop-filter: blur(40px) saturate(130%);
  -webkit-backdrop-filter: blur(40px) saturate(130%);
}
.sidebar.collapsed { width: 52px; }

.sidebar-header {
  padding: 20px 16px 16px; display: flex;
  justify-content: space-between; align-items: center;
}
.header-title {
  display: flex; align-items: center; gap: 8px;
  color: rgba(0,242,254,0.7); font-size: 13px; font-weight: 600;
}
.new-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 7px 14px; background: rgba(0,242,254,0.06);
  border: 1px solid rgba(0,242,254,0.2); border-radius: 10px;
  color: #00f2fe; font-size: 12px; cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.new-btn:hover {
  background: rgba(0,242,254,0.12); border-color: rgba(0,242,254,0.35);
  transform: translateY(-1px);
}

.session-list { flex: 1; overflow-y: auto; padding: 4px 10px; }

.session-item {
  display: flex; align-items: center; gap: 10px;
  padding: 11px 12px; margin: 3px 0; border-radius: 12px;
  cursor: pointer; font-size: 13px; color: rgba(255,255,255,0.5);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); border: 1px solid transparent;
}
.session-item:hover {
  background: rgba(255,255,255,0.04); color: rgba(255,255,255,0.85);
  border-color: rgba(255,255,255,0.06);
}
.session-item.active {
  background: rgba(0,242,254,0.06); color: #00f2fe;
  border-color: rgba(0,242,254,0.15);
}
.session-title {
  flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.del-btn {
  opacity: 0; background: none; border: none; color: rgba(255,255,255,0.25);
  cursor: pointer; padding: 4px; border-radius: 6px; transition: all 0.2s;
  display: flex; align-items: center;
}
.session-item:hover .del-btn { opacity: 1; }
.del-btn:hover { color: #fa709a; background: rgba(250,112,154,0.08); }

.empty-state { text-align: center; padding: 40px 20px; color: rgba(255,255,255,0.25); font-size: 13px; }

.sidebar-footer {
  padding: 12px; border-top: 1px solid rgba(255,255,255,0.06);
  display: flex; flex-direction: column; gap: 4px;
}
.nav-link {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px;
  border-radius: 12px; color: rgba(255,255,255,0.45); text-decoration: none;
  font-size: 13px; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.nav-link:hover { background: rgba(255,255,255,0.04); color: #00f2fe; }

.toggle-btn {
  position: absolute; top: 50%; right: -14px; transform: translateY(-50%);
  width: 28px; height: 56px; border-radius: 0 12px 12px 0;
  background: rgba(8,11,18,0.6); border: 1px solid rgba(255,255,255,0.06);
  border-left: none; color: rgba(0,242,254,0.4); cursor: pointer;
  display: flex; align-items: center; justify-content: center; z-index: 10;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  backdrop-filter: blur(20px);
}
.toggle-btn:hover { background: rgba(0,242,254,0.06); color: #00f2fe; }
.toggle-btn svg { transition: transform 0.3s; }
</style>
