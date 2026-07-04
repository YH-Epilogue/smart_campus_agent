<template>
  <div class="header">
    <div class="header-left">
      <div class="status-dot"></div>
      <span class="title">Smart Campus Agent</span>
    </div>
    <div class="header-right">
      <div class="user-info">
        <div class="avatar">{{ (userStore.user?.username || "U")[0].toUpperCase() }}</div>
        <span class="username">{{ userStore.user?.username || "未登录" }}</span>
      </div>
      <button class="logout-btn" @click="handleLogout">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
        </svg>
        退出
      </button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";
import { useUserStore } from "../../stores/userStore";

const router = useRouter();
const userStore = useUserStore();

function handleLogout() {
  userStore.logout();
  router.push("/login");
}
</script>

<style scoped>
.header {
  height: 56px; display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px; position: relative; z-index: 5;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  background: rgba(8,11,18,0.4); backdrop-filter: blur(30px) saturate(130%);
  -webkit-backdrop-filter: blur(30px) saturate(130%);
}
.header-left { display: flex; align-items: center; gap: 10px; }
.status-dot {
  width: 8px; height: 8px; background: #00f2fe; border-radius: 50%;
  box-shadow: 0 0 12px rgba(0,242,254,0.5);
  animation: dotPulse 3s ease-in-out infinite;
}
@keyframes dotPulse {
  0%, 100% { box-shadow: 0 0 12px rgba(0,242,254,0.5); }
  50% { box-shadow: 0 0 20px rgba(0,242,254,0.8); }
}
.title {
  font-size: 15px; font-weight: 600; color: #ffffff; letter-spacing: 0.5px;
}
.header-right { display: flex; align-items: center; gap: 16px; }
.user-info { display: flex; align-items: center; gap: 10px; }
.avatar {
  width: 30px; height: 30px; border-radius: 10px;
  background: rgba(0,242,254,0.08); border: 1px solid rgba(0,242,254,0.2);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600; color: #00f2fe;
  transition: all 0.3s;
}
.avatar:hover { background: rgba(0,242,254,0.12); }
.username { font-size: 13px; color: rgba(255,255,255,0.5); }
.logout-btn {
  display: flex; align-items: center; gap: 6px; padding: 7px 14px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px; color: rgba(255,255,255,0.5); font-size: 12px;
  cursor: pointer; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.logout-btn:hover { background: rgba(250,112,154,0.08); color: #fa709a; border-color: rgba(250,112,154,0.2); transform: translateY(-1px); }
</style>
