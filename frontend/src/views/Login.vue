<template>
  <div class="landing">
    <!-- Liquid Aurora background -->
    <div class="light-engine">
      <div class="orb orb-1" id="orb1"></div>
      <div class="orb orb-2" id="orb2"></div>
      <div class="orb orb-3" id="orb3"></div>
    </div>

    <!-- Frosted glass overlay -->
    <div class="glass-overlay"></div>

    <!-- Mouse tracking glow -->
    <div class="mouse-glow" id="mouseGlow"></div>

    <!-- 3D Geometric core -->
    <div class="geometric-core">
      <div class="ring ring-outer"></div>
      <div class="ring ring-inner"></div>
    </div>

    <!-- UI Layer -->
    <div class="ui-layer">
      <!-- Navigation -->
      <header class="header" :class="{ scrolled: isScrolled }">
        <div class="brand">SMART CAMPUS.</div>
        <nav class="nav-links">
          <a href="#about">ABOUT</a>
          <a href="#features">FEATURES</a>
          <a href="#tech">TECH</a>
        </nav>
      </header>

      <!-- Hero -->
      <main class="hero">
        <div class="badge">INTELLIGENT CAMPUS AGENT</div>
        <h1 class="title" id="mainTitle">
          <span>SMART</span><br>
          <span>CAMPUS</span>
        </h1>
        <p class="desc">
          基于 RAG 检索增强生成的校园智能问答与事务处理平台。<br>
          重新定义校园智能体验。
        </p>
        <div class="hero-actions">
          <button class="btn-glow" @click="scrollToLogin">开始使用</button>
          <a href="#about" class="btn-outline">了解更多</a>
        </div>

        <!-- Scroll down indicator -->
        <div class="scroll-down" @click="scrollToAbout">
          <div class="scroll-down-line"></div>
          <span>SCROLL</span>
        </div>
      </main>
    </div>

    <!-- Footer data panels - fixed at bottom, outside ui-layer -->
    <footer class="footer">
      <div class="data-box">
        <div class="data-label">TECH STACK</div>
        <div class="data-value">RAG + DEEPSEEK + CHROMADB</div>
      </div>
      <div class="data-box right">
        <div class="data-label">SYSTEM STATUS</div>
        <div class="data-value">ACTIVE</div>
      </div>
    </footer>

    <!-- Scrollable sections -->
    <div class="scroll-content">
      <!-- About -->
      <section id="about" class="section">
        <div class="section-inner">
          <div class="section-tag">ABOUT</div>
          <div class="about-grid">
            <div class="about-left">
              <h2 class="section-title">重新定义<br/>校园智能体验</h2>
            </div>
            <div class="about-right">
              <p class="about-text">
                Smart Campus Agent 是一款基于 RAG（检索增强生成）技术的校园智能平台。
                它将分散在各类系统中的知识资产——学生手册、校园新闻、事务流程——
                通过 AI 对话的方式统一呈现，为师生提供便捷的信息查询和事务办理服务。
              </p>
              <p class="about-text">
                平台支持多轮对话、多知识库检索、参考来源溯源，
                让每一次交互都精准、高效、可追溯。
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- Features -->
      <section id="features" class="section">
        <div class="section-inner">
          <div class="about-grid">
            <div class="about-left">
              <div class="section-tag">CAPABILITIES</div>
              <h2 class="section-title">核心能力</h2>
            </div>
            <div class="about-right">
              <div class="features-list">
                <div class="feature-item" v-for="f in features" :key="f.title">
                  <div class="feature-icon" v-html="f.icon"></div>
                  <div class="feature-text">
                    <h3>{{ f.title }}</h3>
                    <p>{{ f.desc }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Tech -->
      <section id="tech" class="section">
        <div class="section-inner">
          <div class="about-grid">
            <div class="about-left">
              <div class="section-tag">TECHNOLOGY</div>
              <h2 class="section-title">技术架构</h2>
            </div>
            <div class="about-right">
              <div class="tech-list">
                <div class="tech-item" v-for="t in techs" :key="t.name">
                  <div class="tech-name">{{ t.name }}</div>
                  <div class="tech-desc">{{ t.desc }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Login trigger -->
      <section class="section login-trigger-section">
        <div class="section-inner centered">
          <div class="section-tag">GET STARTED</div>
          <h2 class="section-title centered">开始使用</h2>
          <p class="login-trigger-desc">登录后即可体验完整的校园智能问答服务</p>
          <button class="btn-glow large" @click="showLogin = true">
            进入系统
          </button>
        </div>
      </section>
    </div>

    <!-- Login Modal -->
    <div class="login-overlay" ref="loginSection" v-show="showLogin">
      <div class="login-modal" @click.self="showLogin = false">
        <div class="login-card">
          <button class="close-btn" @click="showLogin = false">&times;</button>
          <div class="login-header">
            <h3>登录</h3>
            <p>输入您的凭据以继续</p>
          </div>
          <form @submit.prevent="handleLogin">
            <div class="field">
              <label>USERNAME</label>
              <input v-model="form.username" type="text" placeholder="请输入用户名" required />
            </div>
            <div class="field">
              <label>PASSWORD</label>
              <div class="password-wrap">
                <input
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="请输入密码"
                  required
                />
                <button type="button" class="eye-btn" @click="showPassword = !showPassword">
                  {{ showPassword ? '🙈' : '👁' }}
                </button>
              </div>
            </div>
            <button type="submit" class="submit-btn" :disabled="loading">
              {{ loading ? '登录中...' : '登 录' }}
            </button>
          </form>
          <div class="login-footer">
            还没有账号？ <a href="#" @click.prevent="handleRegister">立即注册</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "../stores/userStore";
import { register } from "../api/user";
import { ElMessage } from "element-plus";

const router = useRouter();
const userStore = useUserStore();
const loading = ref(false);
const showPassword = ref(false);
const showLogin = ref(false);
const form = reactive({ username: "", password: "" });
const loginSection = ref(null);

async function handleLogin() {
  loading.value = true;
  try {
    await userStore.login(form.username, form.password);
    router.push("/");
  } catch (e) {
    ElMessage.error("登录失败：" + (e.response?.data?.detail || e.message));
  } finally {
    loading.value = false;
  }
}

async function handleRegister() {
  if (!form.username || !form.password) {
    ElMessage.warning("请先输入用户名和密码");
    return;
  }
  try {
    await register(form.username, form.password);
    ElMessage.success("注册成功，请登录");
  } catch (e) {
    ElMessage.error("注册失败：" + (e.response?.data?.detail || e.message));
  }
}

function scrollToLogin() {
  showLogin.value = true;
}

function scrollToAbout() {
  document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' });
}

// Glitch effect placeholder (handled in onMounted)
function glitchEffect() {}

const features = [
  {
    icon: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    title: "智能检索",
    desc: "基于 RAG 检索增强生成技术，从知识库中精准定位相关信息，提供准确回答。"
  },
  {
    icon: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    title: "多轮对话",
    desc: "支持上下文关联，理解追问意图，实现自然流畅的连续对话体验。"
  },
  {
    icon: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    title: "文档管理",
    desc: "支持 PDF、Word、TXT 等多格式文档上传，自动解析、切分、向量化。"
  },
  {
    icon: '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    title: "安全可靠",
    desc: "JWT 认证、角色权限控制、敏感词过滤，保障数据安全与合规。"
  }
];

const techs = [
  { name: "FastAPI", desc: "高性能异步后端框架" },
  { name: "Vue 3", desc: "响应式前端框架" },
  { name: "ChromaDB", desc: "向量数据库" },
  { name: "DeepSeek", desc: "大语言模型 API" },
  { name: "sentence-transformers", desc: "文本向量化模型" },
  { name: "Element Plus", desc: "UI 组件库" },
];

onMounted(() => {
  const orb1 = document.getElementById('orb1');
  const orb2 = document.getElementById('orb2');
  const orb3 = document.getElementById('orb3');
  const mainTitle = document.getElementById('mainTitle');
  const mouseGlow = document.getElementById('mouseGlow');

  // Mouse tracking - parallax orbs + 3D title tilt + glow
  document.addEventListener('mousemove', (e) => {
    const x = e.clientX / window.innerWidth - 0.5;
    const y = e.clientY / window.innerHeight - 0.5;

    // Orb parallax movement
    if (orb1) orb1.style.transform = `translate(${x * 80}px, ${y * 80}px)`;
    if (orb2) orb2.style.transform = `translate(${-x * 80}px, ${-y * 80}px)`;
    if (orb3) orb3.style.transform = `translate(${x * 40}px, ${-y * 40}px)`;

    // Title 3D tilt
    if (mainTitle) {
      mainTitle.style.transform = `perspective(1000px) rotateY(${x * 20}deg) rotateX(${-y * 20}deg)`;
    }

    // Mouse glow follows cursor
    if (mouseGlow) {
      mouseGlow.style.left = e.clientX + 'px';
      mouseGlow.style.top = e.clientY + 'px';
    }
  });

  // Glitch effect on data-box click
  document.querySelectorAll('.data-box').forEach(box => {
    box.addEventListener('click', () => {
      const val = box.querySelector('.data-value');
      if (!val) return;
      const orig = val.textContent;
      val.textContent = "PROCESSING...";
      val.style.color = "rgba(0, 242, 254, 0.9)";
      setTimeout(() => {
        val.textContent = "SYNCHRONIZED";
        val.style.color = "#fff";
        setTimeout(() => { val.textContent = orig; }, 800);
      }, 600);
    });
  });

  // Section scroll entrance animation
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('section-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('.section').forEach(s => observer.observe(s));
});

onUnmounted(() => {
  // Cleanup handled by page unload
});
</script>

<style scoped>
/* ==================== BASE ==================== */
.landing {
  background: #080b12;
  color: #ffffff;
  font-family: 'Montserrat', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  overflow-x: hidden;
  cursor: crosshair;
  /* Film grain noise */
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E");
}

/* ==================== LIQUID AURORA ==================== */
.light-engine {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  z-index: 0; overflow: hidden;
}
.orb {
  position: absolute; border-radius: 50%;
  filter: blur(90px); opacity: 0.8;
  animation: float 20s infinite ease-in-out alternate;
}
.orb-1 {
  width: 60vw; height: 60vw;
  background: linear-gradient(135deg, #00f2fe, #4facfe);
  top: -20%; left: -10%;
  animation-duration: 25s;
}
.orb-2 {
  width: 50vw; height: 50vw;
  background: linear-gradient(135deg, #43e97b, #38f9d7);
  bottom: -20%; right: -10%;
  animation-duration: 22s;
  animation-direction: alternate-reverse;
}
.orb-3 {
  width: 45vw; height: 45vw;
  background: linear-gradient(135deg, #fa709a, #fee140);
  top: 20%; left: 30%;
  animation-duration: 28s;
  mix-blend-mode: screen;
}

@keyframes float {
  0% { transform: translate(0, 0) scale(1) rotate(0deg); }
  50% { transform: translate(10vw, 15vh) scale(1.1) rotate(180deg); }
  100% { transform: translate(-10vw, -10vh) scale(0.9) rotate(360deg); }
}

/* ==================== FROSTED GLASS OVERLAY ==================== */
.glass-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100vh;
  backdrop-filter: blur(40px) saturate(160%);
  -webkit-backdrop-filter: blur(40px) saturate(160%);
  background: rgba(8, 11, 18, 0.15);
  z-index: 1; pointer-events: none;
}

/* ==================== MOUSE GLOW ==================== */
.mouse-glow {
  position: fixed;
  width: 400px; height: 400px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0, 242, 254, 0.12) 0%, transparent 70%);
  pointer-events: none;
  z-index: 3;
  transform: translate(-50%, -50%);
  transition: left 0.15s ease-out, top 0.15s ease-out;
  mix-blend-mode: screen;
}

/* ==================== 3D GEOMETRIC CORE ==================== */
.geometric-core {
  position: fixed;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 500px; height: 500px;
  z-index: 2;
  display: flex; justify-content: center; align-items: center;
  pointer-events: none; opacity: 0.3;
}
.ring {
  position: absolute; border-radius: 50%;
  border: 1px dashed rgba(255, 255, 255, 0.5);
}
.ring-outer {
  width: 100%; height: 100%;
  animation: spinRotate 40s linear infinite;
}
.ring-inner {
  width: 70%; height: 70%;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-top: 2px solid #fff;
  animation: spinRotateReverse 20s linear infinite;
}

@keyframes spinRotate {
  0% { transform: rotateX(60deg) rotateY(20deg) rotateZ(0deg); }
  100% { transform: rotateX(60deg) rotateY(20deg) rotateZ(360deg); }
}
@keyframes spinRotateReverse {
  0% { transform: rotateX(40deg) rotateY(-20deg) rotateZ(360deg); }
  100% { transform: rotateX(40deg) rotateY(-20deg) rotateZ(0deg); }
}

/* ==================== UI LAYER ==================== */
.ui-layer {
  position: relative; z-index: 10; display: flex; flex-direction: column;
}

/* Header */
.header {
  position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
  padding: 24px 60px; display: flex;
  justify-content: space-between; align-items: center;
  background: transparent;
  transition: background 0.3s;
}
.header.scrolled {
  background: rgba(8,11,18,0.85);
  backdrop-filter: blur(20px);
}
.brand {
  font-weight: 700; font-size: 14px;
  letter-spacing: 6px; text-transform: uppercase;
}
.nav-links { display: flex; gap: 50px; }
.nav-links a {
  color: #fff; text-decoration: none;
  font-family: 'Space Mono', monospace;
  font-size: 11px; letter-spacing: 2px;
  position: relative; padding-bottom: 4px;
  transition: opacity 0.3s;
}
.nav-links a::after {
  content: ''; position: absolute; bottom: 0; left: 0;
  width: 0; height: 1px; background: #fff;
  transition: width 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.nav-links a:hover::after { width: 100%; }
.nav-links a:hover { opacity: 1; }
.nav-links a:not(:hover) { opacity: 0.6; }

/* Hero */
.hero {
  height: 100vh; display: flex; flex-direction: column;
  justify-content: center; align-items: center;
  text-align: center; padding: 0 20px;
  position: relative; z-index: 10;
}
.hero-content {
  position: relative; z-index: 11;
}
.badge {
  font-family: 'Space Mono', monospace;
  font-size: 10px; letter-spacing: 4px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 8px 16px; border-radius: 30px;
  margin-bottom: 40px; backdrop-filter: blur(10px);
  animation: fadeIn 2s ease forwards;
}
.title {
  font-size: 6vw; font-weight: 700; letter-spacing: -2px;
  line-height: 1; margin-bottom: 30px;
  text-shadow: 0 10px 30px rgba(0,0,0,0.3);
  animation: scaleUp 1.5s cubic-bezier(0.16, 1, 0.3, 1);
  transform: perspective(1000px) rotateY(0deg) rotateX(0deg);
  transition: transform 0.2s ease-out, filter 0.3s;
  will-change: transform;
}
.title span {
  background: linear-gradient(180deg, #ffffff 0%, rgba(255,255,255,0.4) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.desc {
  font-family: 'Space Mono', monospace;
  font-size: 13px; letter-spacing: 1px; line-height: 1.8;
  color: rgba(255, 255, 255, 0.7);
  max-width: 500px; margin-bottom: 40px;
  animation: fadeIn 2s 0.5s ease forwards; opacity: 0;
}
.hero-actions {
  display: flex; gap: 20px;
  animation: fadeIn 2s 0.8s ease forwards; opacity: 0;
}
.btn-glow {
  padding: 14px 40px; background: #fff; border: none;
  color: #080b12; font-size: 12px; font-weight: 700;
  letter-spacing: 3px; text-transform: uppercase;
  cursor: pointer; transition: all 0.4s;
  font-family: 'Montserrat', sans-serif;
}
.btn-glow:hover {
  box-shadow: 0 0 30px rgba(255,255,255,0.3);
  transform: translateY(-2px);
}
.btn-outline {
  padding: 14px 40px; border: 1px solid rgba(255,255,255,0.3);
  color: rgba(255,255,255,0.7); text-decoration: none;
  font-size: 12px; letter-spacing: 3px; text-transform: uppercase;
  transition: all 0.3s; font-family: 'Montserrat', sans-serif;
}
.btn-outline:hover { border-color: #fff; color: #fff; }

/* Scroll down indicator */
.scroll-down {
  position: absolute; bottom: 80px; left: 50%;
  transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center;
  gap: 12px; cursor: pointer;
  animation: fadeIn 2s 1.2s ease forwards; opacity: 0;
}
.scroll-down span {
  font-family: 'Space Mono', monospace;
  font-size: 9px; letter-spacing: 4px;
  color: rgba(255,255,255,0.4);
}
.scroll-down-line {
  width: 1px; height: 40px;
  background: linear-gradient(180deg, transparent, rgba(255,255,255,0.6));
  animation: scrollPulse 2s ease-in-out infinite;
}
@keyframes scrollPulse {
  0%, 100% { opacity: 0.3; transform: scaleY(1); }
  50% { opacity: 1; transform: scaleY(1.3); }
}

/* Footer */
.footer {
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 9998;
  padding: 20px 60px; display: flex;
  justify-content: space-between; align-items: flex-end;
  pointer-events: none;
}
.data-box {
  background: rgba(255, 255, 255, 0.03);
  border-left: 2px solid rgba(255, 255, 255, 0.5);
  padding: 15px 20px;
  transition: all 0.3s; cursor: pointer;
  pointer-events: auto;
}
.data-box:hover {
  background: rgba(255, 255, 255, 0.08);
  border-left-color: #fff;
}
.data-box:active {
  transform: scale(0.98);
  background: rgba(255, 255, 255, 0.12);
}
.data-box.right {
  border-left: none; border-right: 2px solid rgba(255, 255, 255, 0.5); text-align: right;
}
.data-label {
  font-family: 'Space Mono', monospace;
  font-size: 9px; color: rgba(255,255,255,0.5); letter-spacing: 2px; margin-bottom: 5px;
}
.data-value { font-size: 14px; font-weight: 700; letter-spacing: 1px; }

/* ==================== LOGIN MODAL ==================== */
.login-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  z-index: 1000; display: flex; align-items: center; justify-content: center;
  background: rgba(0, 0, 0, 0.5); backdrop-filter: blur(10px);
  animation: fadeIn 0.3s ease;
}
.login-modal { position: relative; }
.login-card {
  width: 400px; padding: 48px;
  background: rgba(25, 30, 45, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  backdrop-filter: blur(20px);
  position: relative;
}
.close-btn {
  position: absolute; top: 16px; right: 16px;
  background: none; border: none; color: rgba(255,255,255,0.4);
  font-size: 24px; cursor: pointer; transition: color 0.3s;
}
.close-btn:hover { color: #fff; }
.login-header { text-align: center; margin-bottom: 36px; }
.login-header h3 {
  font-size: 20px; font-weight: 600; margin-bottom: 8px;
  letter-spacing: 2px;
}
.login-header p {
  font-size: 12px; color: rgba(255,255,255,0.5); letter-spacing: 1px;
}
.field { margin-bottom: 20px; }
.field label {
  display: block; font-size: 10px; color: rgba(255,255,255,0.4);
  margin-bottom: 8px; letter-spacing: 2px;
  font-family: 'Space Mono', monospace;
}
.field input {
  width: 100%; padding: 14px 16px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 2px; color: #fff; font-size: 14px;
  outline: none; transition: all 0.3s;
}
.field input::placeholder { color: rgba(255,255,255,0.25); }
.field input:focus {
  border-color: rgba(255,255,255,0.3);
  box-shadow: 0 0 0 3px rgba(255,255,255,0.05);
}
.password-wrap { position: relative; }
.password-wrap input { padding-right: 48px; }
.eye-btn {
  position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
  background: none; border: none; cursor: pointer; font-size: 16px;
  opacity: 0.4; transition: opacity 0.3s;
}
.eye-btn:hover { opacity: 0.8; }
.submit-btn {
  width: 100%; padding: 14px; background: #fff;
  border: none; border-radius: 2px; color: #080b12;
  font-size: 11px; font-weight: 700; cursor: pointer;
  transition: all 0.3s; margin-top: 8px;
  letter-spacing: 4px; text-transform: uppercase;
  font-family: 'Montserrat', sans-serif;
}
.submit-btn:hover:not(:disabled) {
  box-shadow: 0 0 20px rgba(255,255,255,0.2);
  transform: translateY(-1px);
}
.submit-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.login-footer {
  text-align: center; margin-top: 24px; font-size: 12px;
  color: rgba(255,255,255,0.4);
}
.login-footer a {
  color: rgba(255,255,255,0.7); text-decoration: none;
}
.login-footer a:hover { color: #fff; }

/* ==================== SCROLL CONTENT SECTIONS ==================== */
.scroll-content {
  position: relative;
  background: linear-gradient(180deg,
    transparent 0%,
    rgba(8,11,18,0.7) 8%,
    rgba(8,11,18,0.85) 20%,
    rgba(8,11,18,0.9) 50%,
    rgba(8,11,18,0.85) 80%,
    rgba(8,11,18,0.7) 92%,
    transparent 100%);
  z-index: 5;
  will-change: transform;
  transform: translateZ(0);
}
.section {
  padding: 160px 60px;
  position: relative;
  border-top: 1px solid rgba(255,255,255,0.04);
  opacity: 0;
  transform: translateY(40px);
  transition: opacity 0.8s ease, transform 0.8s ease;
}
.section.section-visible {
  opacity: 1;
  transform: translateY(0);
}
.section-inner {
  max-width: 1200px; margin: 0 auto;
  position: relative; z-index: 6;
}
.section-inner.centered { text-align: center; }
.section-tag {
  font-family: 'Space Mono', monospace;
  font-size: 10px; letter-spacing: 6px; color: rgba(255,255,255,0.35);
  margin-bottom: 24px;
}
.section-title {
  font-size: clamp(32px, 5vw, 56px); font-weight: 200; line-height: 1.2;
  color: rgba(255,255,255,0.95); margin-bottom: 48px; letter-spacing: -1px;
}
.section-title.centered { text-align: center; }

/* About */
.about-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 80px;
  align-items: start;
}
.about-text {
  font-family: 'Space Mono', monospace;
  font-size: 14px; line-height: 2; color: rgba(255,255,255,0.45);
  margin-bottom: 24px;
}

/* Features - list style like About */
.features-list {
  display: flex; flex-direction: column; gap: 32px;
  position: relative; z-index: 7;
}
.feature-item {
  display: flex; gap: 20px; align-items: flex-start;
}
.feature-icon {
  color: rgba(255,255,255,0.6); flex-shrink: 0; margin-top: 2px;
}
.feature-text h3 {
  font-size: 16px; font-weight: 500; color: rgba(255,255,255,0.95);
  margin-bottom: 8px; letter-spacing: 0.5px;
}
.feature-text p {
  font-family: 'Space Mono', monospace;
  font-size: 13px; line-height: 1.8; color: rgba(255,255,255,0.6);
}

/* Tech - list style like About */
.tech-list {
  display: flex; flex-direction: column; gap: 24px;
  position: relative; z-index: 7;
}
.tech-item {
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.tech-name {
  font-size: 16px; font-weight: 500; color: rgba(255,255,255,0.95);
  margin-bottom: 6px; letter-spacing: 0.5px;
}
.tech-desc {
  font-family: 'Space Mono', monospace;
  font-size: 13px; color: rgba(255,255,255,0.6);
}
.about-text {
  font-family: 'Space Mono', monospace;
  font-size: 14px; line-height: 2; color: rgba(255,255,255,0.4);
  margin-bottom: 24px;
}

/* Features */
.features-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px;
  margin-top: 64px;
}
.feature-card {
  padding: 32px; border: 1px solid rgba(255,255,255,0.08);
  border-radius: 2px; background: rgba(255,255,255,0.04);
  transition: all 0.4s ease;
}
.feature-card:hover {
  border-color: rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.04);
  transform: translateY(-4px);
}
.feature-icon { color: rgba(255,255,255,0.3); margin-bottom: 24px; }
.feature-card h3 {
  font-size: 15px; font-weight: 500; color: rgba(255,255,255,0.9);
  margin-bottom: 12px; letter-spacing: 0.5px;
}
.feature-card p {
  font-family: 'Space Mono', monospace;
  font-size: 12px; line-height: 1.8; color: rgba(255,255,255,0.45);
}

/* Tech */
.tech-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 0;
  margin-top: 64px;
}
.tech-item {
  padding: 28px; border-bottom: 1px solid rgba(255,255,255,0.06);
}
.tech-name {
  font-size: 16px; font-weight: 500; color: rgba(255,255,255,0.9);
  margin-bottom: 8px; letter-spacing: 0.5px;
}
.tech-desc {
  font-family: 'Space Mono', monospace;
  font-size: 12px; color: rgba(255,255,255,0.45);
}

/* Login trigger section */
.login-trigger-section { text-align: center; }
.login-trigger-desc {
  font-family: 'Space Mono', monospace;
  font-size: 14px; color: rgba(255,255,255,0.5);
  margin-bottom: 40px;
}
.btn-glow.large {
  padding: 18px 60px; font-size: 13px;
}
.btn-glow {
  padding: 14px 40px; background: #fff; border: none;
  color: #080b12; font-size: 12px; font-weight: 700;
  letter-spacing: 3px; text-transform: uppercase;
  cursor: pointer; transition: all 0.4s;
  font-family: 'Montserrat', sans-serif;
}
.btn-glow:hover {
  box-shadow: 0 0 30px rgba(255,255,255,0.3);
  transform: translateY(-2px);
}

/* ==================== ANIMATIONS ==================== */
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-30px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes scaleUp {
  from { opacity: 0; transform: scale(0.9) translateY(20px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
