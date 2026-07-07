<template>
  <div class="chat-layout">
    <!-- Aurora background -->
    <div class="chat-aurora">
      <div class="aurora-orb a-orb-1"></div>
      <div class="aurora-orb a-orb-2"></div>
      <div class="aurora-orb a-orb-3"></div>
    </div>
    <div class="chat-glass"></div>

    <Sidebar />
    <div class="chat-main">
      <Header />
      <div class="chat-messages" ref="messagesRef">
        <!-- Particle canvas -->
        <canvas ref="particleCanvas" class="particle-canvas"></canvas>

        <!-- Shooting stars -->
        <div class="shooting-star s1"></div>
        <div class="shooting-star s2"></div>
        <div class="shooting-star s3"></div>
        <div class="shooting-star s4"></div>
        <div class="shooting-star s5"></div>

        <!-- Welcome area -->
        <div v-if="chatStore.messages.length === 0" class="welcome-area">
          <div class="welcome-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <circle cx="24" cy="24" r="20" stroke="url(#cyanGrad)" stroke-width="2" fill="none" opacity="0.3"/>
              <path d="M24 8L28 20H36L30 28L32 40L24 32L16 40L18 28L12 20H20L24 8Z" fill="url(#cyanGrad)"/>
              <defs>
                <linearGradient id="cyanGrad" x1="0" y1="0" x2="48" y2="48">
                  <stop offset="0%" stop-color="#00f2fe"/>
                  <stop offset="100%" stop-color="#43e97b"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h2>Smart Campus Agent</h2>
          <p class="welcome-desc">基于知识库的智能问答助手</p>
          <div class="quick-grid">
            <div
              v-for="q in quickQuestions"
              :key="q"
              class="quick-card"
              @click="sendQuick(q)"
            >
              <span class="quick-text">{{ q }}</span>
              <span class="quick-arrow">→</span>
            </div>
          </div>
        </div>

        <!-- Messages -->
        <ChatBubble v-for="(msg, i) in chatStore.messages" :key="i" :message="msg" />

        <!-- Typing indicator -->
        <div v-if="chatStore.loading" class="typing-area">
          <div class="typing-avatar">✦</div>
          <div class="typing-dots">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>

      <!-- Input area -->
      <div class="input-dock">
        <div class="kb-selector" v-if="knowledgeBases.length > 1">
          <span class="kb-label">知识库:</span>
          <select v-model="selectedKB" class="kb-select">
            <option v-for="kb in knowledgeBases" :key="kb.id" :value="kb.id">{{ kb.name }}</option>
          </select>
        </div>
        <!-- File attachment tag -->
        <div v-if="uploadedFile" class="file-tag">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          <span>{{ uploadedFile.name }}</span>
          <span class="file-size">({{ (uploadedFile.size / 1024).toFixed(1) }}KB)</span>
          <button class="file-remove" @click="uploadedFile = null">×</button>
        </div>
        <div class="input-container">
          <button class="icon-btn" @click="triggerFileUpload" title="上传图片/文件">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
          </button>
          <input type="file" ref="fileInput" @change="handleFileUpload" accept="image/*,.pdf,.docx,.txt,.md" style="display:none" />
          <input
            v-model="inputText"
            class="chat-input"
            :placeholder="uploadedFile ? '文件已附加，可输入补充说明...' : '输入你的问题...'"
            @keyup.enter="handleSend"
            :disabled="chatStore.loading"
          />
          <button
            class="send-btn"
            @click="handleSend"
            :disabled="(!inputText.trim() && !uploadedFile) || chatStore.loading"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * ChatView - 主聊天界面
 * 职责：承载 AI 对话的完整交互流程，包括消息展示、输入、文件上传、知识库切换
 * 架构：粒子网络动画背景 + 欢迎区/消息区双态切换 + 底部输入停靠栏
 * 依赖：chatStore 管理会话状态，Sidebar/Header 提供布局框架
 */
import { ref, onMounted, onUnmounted } from "vue";
import { useChatStore } from "../stores/chatStore";
import Sidebar from "../components/layout/Sidebar.vue";
import Header from "../components/layout/Header.vue";
import ChatBubble from "../components/chat/ChatBubble.vue";
import http from "../api/http";

/** 状态管理：会话消息、用户输入、UI 状态 */
const chatStore = useChatStore();
const inputText = ref("");              // 用户当前输入文本
const messagesRef = ref(null);          // 消息区 DOM 引用，用于滚动控制
const quickQuestions = ref([]);         // 快捷提问列表（从 settings 获取）
const particleCanvas = ref(null);       // 粒子网络 Canvas 引用
const selectedKB = ref(null);           // 当前选中的知识库 ID
const knowledgeBases = ref([]);         // 可用知识库列表

/**
 * 组件挂载：初始化粒子网络动画、加载快捷提问和知识库
 * 粒子网络使用 requestAnimationFrame 驱动，注意未在 onUnmounted 清理（已知问题）
 */
/** 组件卸载时执行所有清理函数 */
const cleanupFns = [];
onUnmounted(() => cleanupFns.forEach(fn => fn()));

onMounted(() => {
  const canvas = particleCanvas.value;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let dots = [];
  const dotCount = 55;
  const maxDist = 130;
  const colors = [[0,242,254],[67,233,123],[250,112,154],[64,248,255]];

  function resize() {
    canvas.width = canvas.parentElement.offsetWidth;
    canvas.height = canvas.parentElement.offsetHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  for (let i = 0; i < dotCount; i++) {
    const c = colors[Math.floor(Math.random() * colors.length)];
    const a = Math.random() * Math.PI * 2;
    const s = Math.random() * 0.06 + 0.02;
    dots.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: Math.cos(a) * s, vy: Math.sin(a) * s,
      r: Math.random() * 2 + 1, c, p: Math.random() * 6.28,
    });
  }

  let animFrameId;
  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < dotCount; i++) {
      for (let j = i + 1; j < dotCount; j++) {
        const dx = dots[i].x - dots[j].x, dy = dots[i].y - dots[j].y;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d < maxDist) {
          const a = (1 - d / maxDist) * 0.15;
          const g = ctx.createLinearGradient(dots[i].x, dots[i].y, dots[j].x, dots[j].y);
          g.addColorStop(0, `rgba(${dots[i].c.join(",")},${a})`);
          g.addColorStop(1, `rgba(${dots[j].c.join(",")},${a})`);
          ctx.strokeStyle = g; ctx.lineWidth = 0.8;
          ctx.beginPath(); ctx.moveTo(dots[i].x, dots[i].y);
          ctx.lineTo(dots[j].x, dots[j].y); ctx.stroke();
        }
      }
    }
    dots.forEach(d => {
      d.p += 0.02;
      const gl = 0.35 + Math.sin(d.p) * 0.15;
      const [r, g, b] = d.c;
      const glow = ctx.createRadialGradient(d.x, d.y, 0, d.x, d.y, d.r * 4);
      glow.addColorStop(0, `rgba(${r},${g},${b},${gl * 0.4})`);
      glow.addColorStop(1, `rgba(${r},${g},${b},0)`);
      ctx.fillStyle = glow; ctx.beginPath();
      ctx.arc(d.x, d.y, d.r * 4, 0, 6.28); ctx.fill();
      const core = ctx.createRadialGradient(d.x, d.y, 0, d.x, d.y, d.r);
      core.addColorStop(0, `rgba(255,255,255,${gl})`);
      core.addColorStop(0.5, `rgba(${r},${g},${b},${gl})`);
      core.addColorStop(1, `rgba(${r},${g},${b},0)`);
      ctx.fillStyle = core; ctx.beginPath();
      ctx.arc(d.x, d.y, d.r, 0, 6.28); ctx.fill();
      d.x += d.vx; d.y += d.vy;
      if (d.x < -10) d.x = canvas.width + 10;
      if (d.x > canvas.width + 10) d.x = -10;
      if (d.y < -10) d.y = canvas.height + 10;
      if (d.y > canvas.height + 10) d.y = -10;
    });
    animFrameId = requestAnimationFrame(animate);
  }
  animate();
  animate();
  loadQuickQuestions();
  loadKnowledgeBases();

  // 注册清理函数
  cleanupFns.push(() => {
    cancelAnimationFrame(animFrameId);
    window.removeEventListener("resize", resize);
  });
});

/**
 * 从后端 /settings/ 接口获取快捷提问列表
 * 快捷提问在欢迎界面展示，点击后直接发送
 */
async function loadQuickQuestions() {
  try {
    const { data } = await http.get("/settings/");
    quickQuestions.value = data.quick_questions || [];
  } catch (e) {
    console.error(e);
  }
}

/**
 * 加载当前用户可见的知识库列表
 * 后端根据角色过滤：admin/teacher 看全部，普通用户只看自己的
 */
async function loadKnowledgeBases() {
  try {
    const { data } = await http.get("/kb/");
    knowledgeBases.value = data || [];
    if (data.length > 0 && !selectedKB.value) {
      selectedKB.value = data[0].id;
    }
  } catch (e) {
    console.error(e);
  }
}

/** 快捷提问：将问题填入输入框并触发发送 */
async function sendQuick(q) {
  inputText.value = q;
  await handleSend();
}

/** 文件上传相关状态 */
const fileInput = ref(null);          // 隐藏的 file input 引用
const uploadedFile = ref(null);       // 当前已选择待发送的文件

/** 触发隐藏 file input 的点击事件，弹出文件选择对话框 */
function triggerFileUpload() {
  fileInput.value?.click();
}

/**
 * 文件选择回调：暂存文件引用，显示文件标签
 * 实际上传在发送时触发，这里只是预览
 */
async function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  // Store file reference, show as tag above input
  uploadedFile.value = file;
  inputText.value = "";  // Clear input so user can type additional text
  event.target.value = "";
}

/**
 * 发送消息的核心逻辑
 * 两种模式：纯文本发送 / 文件+文本混合发送
 * 文件发送流程：先调用 /doc/multimodal 提取文本内容，再合并用户补充说明一起发送
 * 发送到 chatStore，由 store 管理消息列表和加载状态
 */
async function handleSend() {
  const userText = inputText.value.trim();
  const hasFile = !!uploadedFile.value;

  if (!userText && !hasFile) return;

  // If there's an uploaded file, process it first
  if (hasFile) {
    const fileName = uploadedFile.value.name;
    try {
      const formData = new FormData();
      formData.append("file", uploadedFile.value);
      chatStore.loading = true;
      const { data } = await http.post("/doc/multimodal", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      chatStore.loading = false;

      let fullQuery = data.text || "";
      if (userText) {
        fullQuery = fullQuery ? `${fullQuery}\n\n${userText}` : userText;
      }
      uploadedFile.value = null;
      inputText.value = "";

      if (fullQuery.trim()) {
        await chatStore.sendMessage(fullQuery, selectedKB.value || 1, fileName, userText);
      }
    } catch (e) {
      chatStore.loading = false;
      chatStore.messages.push({
        role: "assistant",
        content: "文件处理失败：" + (e.response?.data?.detail || e.message),
      });
      uploadedFile.value = null;
      inputText.value = "";
      return;
    }
  } else {
    // No file, just send text
    inputText.value = "";
    await chatStore.sendMessage(userText, selectedKB.value || 1);
  }
}
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: 100vh;
  background: #080b12;
  position: relative;
  overflow: hidden;
}

/* Aurora background orbs */
.chat-aurora {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  z-index: 0; overflow: hidden;
}
.aurora-orb {
  position: absolute; border-radius: 50%;
  filter: blur(90px); opacity: 0.6;
  animation: orbFloat 20s infinite ease-in-out alternate;
}
.a-orb-1 {
  width: 50vw; height: 50vw;
  background: linear-gradient(135deg, #00f2fe, #4facfe);
  top: -15%; left: -5%;
  animation-duration: 25s;
}
.a-orb-2 {
  width: 40vw; height: 40vw;
  background: linear-gradient(135deg, #43e97b, #38f9d7);
  bottom: -15%; right: -5%;
  animation-duration: 22s;
  animation-direction: alternate-reverse;
}
.a-orb-3 {
  width: 35vw; height: 35vw;
  background: linear-gradient(135deg, #fa709a, #fee140);
  top: 30%; left: 40%;
  animation-duration: 28s;
  mix-blend-mode: screen;
}
@keyframes orbFloat {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(8vw, 10vh) scale(1.1); }
  100% { transform: translate(-8vw, -8vh) scale(0.9); }
}

.chat-glass {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  backdrop-filter: blur(80px) saturate(130%);
  -webkit-backdrop-filter: blur(80px) saturate(130%);
  background: rgba(8, 11, 18, 0.55);
  z-index: 1; pointer-events: none;
}

.chat-main {
  flex: 1; display: flex; flex-direction: column; min-width: 0;
  position: relative; z-index: 2;
}
.chat-messages {
  flex: 1; overflow-y: auto; padding: 20px 40px; position: relative;
}
.particle-canvas {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  z-index: 0; pointer-events: none;
}

/* Shooting stars */
.shooting-star {
  position: absolute; width: 2px; height: 2px;
  background: linear-gradient(-45deg, #00f2fe, transparent);
  border-radius: 999px; filter: drop-shadow(0 0 6px #00f2fe);
  animation: starTail 8s ease-in-out infinite, starShoot 8s ease-in-out infinite;
  transform: rotate(-35deg); opacity: 0; z-index: 1; pointer-events: none;
}
.shooting-star::before {
  content: ''; position: absolute; top: 50%; transform: translateY(-50%);
  width: 100px; height: 1px;
  background: linear-gradient(90deg, rgba(0,242,254,0.9), transparent);
}
.s1 { top: 8%; right: 15%; }
.s2 { top: 22%; right: 42%; animation-delay: 1.8s; }
.s3 { top: 5%; right: 72%; animation-delay: 3.5s; }
.s4 { top: 30%; right: 28%; animation-delay: 5.2s; }
.s5 { top: 10%; right: 60%; animation-delay: 6.8s; }
@keyframes starTail { 0% { width: 0; } 25% { width: 150px; } 100% { width: 0; } }
@keyframes starShoot {
  0% { transform: translateX(0) translateY(0) rotate(-35deg); opacity: 0; }
  5% { opacity: 1; }
  30% { transform: translateX(-600px) translateY(420px) rotate(-35deg); opacity: 0; }
  100% { transform: translateX(-600px) translateY(420px) rotate(-35deg); opacity: 0; }
}

/* Welcome */
.welcome-area {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; height: 100%; position: relative; z-index: 2;
}
.welcome-icon { margin-bottom: 24px; filter: drop-shadow(0 0 20px rgba(0,242,254,0.4)); }
.welcome-area h2 {
  font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 8px;
  background: linear-gradient(135deg, #ffffff, #00f2fe);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.welcome-desc { color: rgba(255,255,255,0.4); font-size: 14px; margin-bottom: 48px; }
.quick-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; max-width: 560px; width: 100%;
}
.quick-card {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08); border-radius: 16px;
  cursor: pointer; transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  backdrop-filter: blur(12px);
}
.quick-card:hover {
  border-color: rgba(0,242,254,0.25); background: rgba(0,242,254,0.06);
  transform: translateY(-3px); box-shadow: 0 8px 30px rgba(0,242,254,0.1);
}
.quick-text { font-size: 13px; color: rgba(255,255,255,0.7); }
.quick-arrow { color: rgba(0,242,254,0.3); font-size: 16px; transition: transform 0.3s; }
.quick-card:hover .quick-arrow { transform: translateX(4px); color: #00f2fe; }

/* Typing */
.typing-area {
  display: flex; align-items: center; gap: 12px; padding: 12px 0; position: relative; z-index: 2;
}
.typing-avatar {
  width: 32px; height: 32px; border-radius: 10px;
  background: rgba(0,242,254,0.08); border: 1px solid rgba(0,242,254,0.2);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; color: #00f2fe;
}
.typing-dots { display: flex; gap: 5px; }
.typing-dots span {
  width: 6px; height: 6px; background: #00f2fe; border-radius: 50%;
  animation: typeBounce 1.4s infinite ease-in-out;
}
.typing-dots span:nth-child(2) { animation-delay: 0.16s; }
.typing-dots span:nth-child(3) { animation-delay: 0.32s; }
@keyframes typeBounce {
  0%,80%,100% { transform: scale(0.4); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* Input dock */
.input-dock {
  padding: 16px 40px 24px; position: relative; z-index: 2;
}
.kb-selector {
  display: flex; align-items: center; gap: 8px; margin-bottom: 10px;
  font-size: 12px; color: rgba(255,255,255,0.4);
}
.kb-label { font-family: 'Space Mono', monospace; letter-spacing: 1px; }
.kb-select {
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px; padding: 6px 12px; color: #fff; font-size: 12px;
  outline: none; cursor: pointer;
}
.kb-select option { background: #1a1d2e; color: #fff; }
.file-tag {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px; background: rgba(0,242,254,0.1);
  border: 1px solid rgba(0,242,254,0.2); border-radius: 8px;
  font-size: 12px; color: #00f2fe; margin-bottom: 10px;
}
.file-tag svg { flex-shrink: 0; }
.file-size { color: rgba(255,255,255,0.4); font-size: 11px; }
.file-remove {
  background: none; border: none; color: rgba(255,255,255,0.4);
  cursor: pointer; font-size: 14px; padding: 0 4px; margin-left: 4px;
}
.file-remove:hover { color: #fa709a; }
.input-container {
  display: flex; align-items: center; gap: 12px;
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px; padding: 6px 8px 6px 24px;
  backdrop-filter: blur(16px); transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.input-container:focus-within {
  border-color: rgba(0,242,254,0.25);
  box-shadow: 0 0 0 3px rgba(0,242,254,0.06), 0 8px 30px rgba(0,0,0,0.15);
  background: rgba(255,255,255,0.07);
}
.chat-input {
  flex: 1; background: transparent; border: none; outline: none;
  color: #ffffff; font-size: 14px; padding: 12px 0;
}
.chat-input::placeholder { color: rgba(255,255,255,0.3); }
.icon-btn {
  width: 40px; height: 40px; border-radius: 10px; border: none;
  background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.5);
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all 0.2s; flex-shrink: 0;
}
.icon-btn:hover { background: rgba(0,242,254,0.1); color: #00f2fe; }
.send-btn {
  width: 44px; height: 44px; border-radius: 14px; border: none;
  background: linear-gradient(135deg, #00f2fe, #00c4d4);
  color: #080b12; cursor: pointer; display: flex; align-items: center;
  justify-content: center; transition: all 0.3s ease; flex-shrink: 0;
}
.send-btn:hover:not(:disabled) {
  transform: scale(1.08); box-shadow: 0 4px 20px rgba(0,242,254,0.4);
}
.send-btn:disabled { opacity: 0.3; cursor: not-allowed; }
</style>
