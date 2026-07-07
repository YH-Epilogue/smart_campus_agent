<template>
  <div class="dashboard">
    <!-- 背景 -->
    <div class="bg-layer"></div>
    <canvas ref="networkCanvas" class="bg-canvas"></canvas>

    <!-- 顶部标题栏 -->
    <header class="dash-header">
      <div class="header-left">
        <span class="status-dot"></span>
        <span class="status-text">实时系统状态：正常</span>
      </div>
      <h1 class="header-title">数据统计</h1>
      <div class="header-right">
        <div class="clock-ring">
          <svg viewBox="0 0 40 40">
            <circle cx="20" cy="20" r="18" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="1.5"/>
            <line x1="20" y1="20" :x2="clockHourX" :y2="clockHourY" stroke="rgba(255,255,255,0.6)" stroke-width="1.5" stroke-linecap="round"/>
            <line x1="20" y1="20" :x2="clockMinX" :y2="clockMinY" stroke="rgba(0,242,254,0.8)" stroke-width="1" stroke-linecap="round"/>
            <circle cx="20" cy="20" r="1.5" fill="#00f2fe"/>
          </svg>
        </div>
      </div>
    </header>

    <!-- 顶部指标卡片 -->
    <div class="stat-cards">
      <div class="stat-card" v-for="(card, i) in statCards" :key="i">
        <div class="card-icon-box">
          <div class="card-icon-3d" :class="'icon-style-' + i">
            <div class="geo-shape" v-if="i === 0">
              <div class="hexagon"></div>
              <div class="hexagon-inner"></div>
            </div>
            <div class="doc-stack" v-else-if="i === 1">
              <div class="doc-page" v-for="n in 4" :key="n" :style="{ transform: `translateY(${-n * 3}px) rotate(${n * 2 - 4}deg)` }"></div>
            </div>
            <div class="human-particle" v-else-if="i === 2">
              <svg viewBox="0 0 60 70" fill="none">
                <circle cx="30" cy="14" r="8" stroke="rgba(0,242,254,0.6)" stroke-width="1" fill="rgba(0,242,254,0.05)"/>
                <path d="M15 35 C15 25 45 25 45 35 L48 60 C48 65 12 65 12 60 Z" stroke="rgba(0,242,254,0.4)" stroke-width="1" fill="rgba(0,242,254,0.03)"/>
                <line x1="30" y1="35" x2="30" y2="55" stroke="rgba(0,242,254,0.3)" stroke-width="0.5"/>
                <line x1="15" y1="40" x2="45" y2="40" stroke="rgba(0,242,254,0.3)" stroke-width="0.5"/>
                <circle cx="22" cy="42" r="1" fill="rgba(0,242,254,0.6)"/>
                <circle cx="38" cy="42" r="1" fill="rgba(0,242,254,0.6)"/>
                <circle cx="30" cy="50" r="1" fill="rgba(0,242,254,0.6)"/>
                <circle cx="25" cy="45" r="0.8" fill="rgba(0,242,254,0.4)"/>
                <circle cx="35" cy="45" r="0.8" fill="rgba(0,242,254,0.4)"/>
                <circle cx="30" cy="48" r="0.8" fill="rgba(0,242,254,0.4)"/>
              </svg>
            </div>
            <div class="network-sphere" v-else-if="i === 3">
              <svg viewBox="0 0 60 60" fill="none">
                <circle cx="30" cy="30" r="22" stroke="rgba(167,139,250,0.2)" stroke-width="0.5" stroke-dasharray="3 3"/>
                <circle cx="30" cy="30" r="16" stroke="rgba(167,139,250,0.3)" stroke-width="0.5"/>
                <circle cx="30" cy="30" r="8" stroke="rgba(167,139,250,0.4)" stroke-width="0.5"/>
                <line v-for="(l,i) in sphereLines" :key="'l'+i" :x1="l.x1" :y1="l.y1" :x2="l.x2" :y2="l.y2" stroke="rgba(167,139,250,0.3)" stroke-width="0.5"/>
                <circle v-for="(p,i) in spherePoints" :key="'p'+i" :cx="p.x" :cy="p.y" :r="p.r" :fill="p.fill"/>
              </svg>
            </div>
          </div>
        </div>
        <div class="card-data">
          <div class="card-number">{{ card.value }}</div>
          <div class="card-label">{{ card.label }}</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="chart-section">
      <!-- 左侧：文档关键词 桑基流图 -->
      <div class="chart-panel left-panel">
        <div class="panel-title-bar">
          <span class="title-accent"></span>
          <span class="panel-title">文档关键词</span>
        </div>
        <div class="sankey-area">
          <div class="sankey-left-labels">
            <div v-for="(item, i) in sankeyData" :key="i" class="sankey-label-row">
              <span class="sankey-label">{{ item.word }}</span>
              <span class="sankey-dot" :style="{ background: item.color }"></span>
            </div>
          </div>
          <div class="sankey-flow">
            <svg :viewBox="'0 0 400 ' + sankeyHeight" preserveAspectRatio="none" class="sankey-svg">
              <defs>
                <linearGradient v-for="(item, i) in sankeyData" :key="'g'+i" :id="'flowGrad'+i" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" :stop-color="item.color" stop-opacity="0.6"/>
                  <stop offset="100%" :stop-color="item.color" stop-opacity="0.9"/>
                </linearGradient>
              </defs>
              <path v-for="(item, i) in sankeyFlows" :key="'f'+i" :d="item.d" :fill="'url(#flowGrad'+i+')'" class="sankey-path"
                @mouseenter="hoveredSankey = i" @mouseleave="hoveredSankey = null" />
            </svg>
          </div>
          <div class="sankey-right-labels">
            <div v-for="(item, i) in sankeyData" :key="i" class="sankey-right-row">
              <span class="sankey-count" :style="{ color: item.color }">{{ item.count }}</span>
            </div>
          </div>
          <!-- 悬浮提示 -->
          <div v-if="hoveredSankey !== null" class="sankey-tooltip">
            <span class="tooltip-title">文档关键词</span>
            <span class="tooltip-item">● {{ sankeyData[hoveredSankey]?.word }}：{{ sankeyData[hoveredSankey]?.count }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧：每日新增 趋势图 -->
      <div class="chart-panel right-panel">
        <div class="panel-title-bar">
          <span class="title-accent"></span>
          <span class="panel-title">每日新增</span>
        </div>
        <div class="trend-area">
          <div class="trend-y-axis">
            <span v-for="y in yLabels" :key="y" class="y-label">{{ y }}</span>
          </div>
          <div class="trend-chart">
            <svg :viewBox="'0 0 ' + trendWidth + ' ' + trendHeight" preserveAspectRatio="none" class="trend-svg">
              <defs>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#00f2fe" stop-opacity="0.4"/>
                  <stop offset="100%" stop-color="#00f2fe" stop-opacity="0"/>
                </linearGradient>
              </defs>
              <!-- 网格线 -->
              <line v-for="y in gridLines" :key="y" x1="0" :y1="y" :x2="trendWidth" :y2="y" stroke="rgba(255,255,255,0.04)" stroke-width="0.5"/>
              <!-- 面积 -->
              <path :d="areaPath" fill="url(#areaGrad)" class="area-fill"/>
              <!-- 曲线 -->
              <path :d="linePath" fill="none" stroke="#00f2fe" stroke-width="2.5" class="trend-line"/>
              <!-- 节点 -->
              <g v-for="(pt, i) in trendPoints" :key="i" class="trend-node"
                @mouseenter="hoveredTrend = i" @mouseleave="hoveredTrend = null">
                <circle :cx="pt.x" :cy="pt.y" r="8" fill="rgba(0,242,254,0.15)"/>
                <circle :cx="pt.x" :cy="pt.y" r="4" fill="#00f2fe" stroke="#060a14" stroke-width="2"/>
              </g>
              <!-- X轴日期 -->
              <text v-for="(pt, i) in trendPoints" :key="'t'+i" :x="pt.x" :y="trendHeight - 4" text-anchor="middle" fill="rgba(255,255,255,0.25)" font-size="10" font-family="monospace">
                {{ analytics.daily_stats[i]?.date?.slice(5) }}
              </text>
            </svg>
            <!-- 悬浮提示 -->
            <div v-if="hoveredTrend !== null" class="trend-tooltip"
              :style="{ left: trendPoints[hoveredTrend]?.x + 'px' }">
              <div class="tt-date">{{ analytics.daily_stats[hoveredTrend]?.date }}</div>
              <div class="tt-item">● {{ analytics.daily_stats[hoveredTrend]?.date }}：{{ analytics.daily_stats[hoveredTrend]?.count }}</div>
              <div class="tt-item">● 每日新增：{{ analytics.daily_stats[hoveredTrend]?.count }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部区域 -->
    <div class="bottom-section">
      <!-- 角色比例 -->
      <div class="chart-panel bottom-left">
        <div class="panel-title-bar">
          <span class="title-accent"></span>
          <span class="panel-title">角色比例</span>
        </div>
        <div class="role-bars">
          <div v-for="(item, i) in roleData" :key="i" class="role-row">
            <span class="role-date">{{ item.date }}</span>
            <div class="role-bar-track">
              <div v-for="(seg, j) in item.segments" :key="j" class="role-segment"
                :style="{ width: seg.pct + '%', background: seg.color }">
              </div>
            </div>
            <div class="role-legend">
              <span v-for="(seg, j) in item.segments" :key="j" class="legend-tag" :style="{ borderColor: seg.color, color: seg.color }">
                {{ seg.label }}
              </span>
            </div>
            <span class="role-pct">100%</span>
          </div>
        </div>
      </div>

      <!-- 用户详情 -->
      <div class="chart-panel bottom-right">
        <div class="panel-title-bar">
          <span class="title-accent"></span>
          <span class="panel-title">用户详情</span>
          <span class="panel-menu">☰</span>
        </div>
        <div class="user-detail-list">
          <div v-for="(user, i) in userList" :key="i" class="user-detail-row">
            <div class="user-avatar" :style="{ background: user.avatarBg }">
              {{ user.name[0] }}
            </div>
            <span class="user-detail-name">{{ user.name }}</span>
            <span class="user-status" :class="user.active ? 'active' : ''">
              <span class="status-dot-sm"></span>{{ user.active ? '主动' : '被动' }}
            </span>
            <span class="user-meta">上次登录</span>
            <span class="user-meta">上次登录数</span>
            <span class="user-msg-count" :style="{ color: user.count > 10 ? '#00f2fe' : '#c8d6e5' }">{{ user.count }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <footer class="dash-footer">
      <span class="footer-chip active">系统监控</span>
      <span class="footer-chip">文档数 ▾</span>
      <span class="footer-chip">注意 ▾</span>
      <span class="footer-chip">消息 ▾</span>
      <span class="footer-chip">请问问题 ▾</span>
    </footer>
  </div>
</template>

<script setup>
/**
 * Dashboard - 管理员数据统计仪表盘
 * 职责：展示系统运行数据的可视化面板，包括统计卡片、关键词桑基图、
 *        每日趋势图、角色比例、用户活跃度等
 * 设计：深色科技风面板，Canvas 网络背景动画 + SVG 图表
 * 数据：30 秒自动刷新，从 /logs/stats 和 /logs/analytics 获取
 */
import { ref, computed, onMounted, onUnmounted, nextTick } from "vue";
import http from "../../api/http";

/** 原始统计数据：知识库数、文档数、消息数、会话数 */
const stats = ref({ total_kb: 0, total_docs: 0, total_messages: 0, total_sessions: 0 });
/** 分析数据：关键词频率、每日新增、检索率、用户活跃度 */
const analytics = ref({ top_words: [], daily_stats: [], retrieval_rate: 0, daily_retrieval_rate: [], user_activity: [] });
const hoveredSankey = ref(null);   // 桑基图悬浮索引
const hoveredTrend = ref(null);    // 趋势图悬浮索引
const networkCanvas = ref(null);   // 背景网络 Canvas 引用

/** 时钟组件：每秒更新角度，驱动 SVG 时针/分针旋转 */
const clockAngle = ref(0);
let clockTimer;
function updateClock() {
  const now = new Date();
  const h = now.getHours() % 12;
  const m = now.getMinutes();
  clockAngle.value = (h * 30 + m * 0.5);
}
/** 时钟 SVG 坐标计算：角度 → SVG 像素坐标 */
const clockHourX = computed(() => 20 + 10 * Math.sin((clockAngle.value) * Math.PI / 180));
const clockHourY = computed(() => 20 - 10 * Math.cos((clockAngle.value) * Math.PI / 180));
const clockMinX = computed(() => 20 + 14 * Math.sin((clockAngle.value * 2) * Math.PI / 180));
const clockMinY = computed(() => 20 - 14 * Math.cos((clockAngle.value * 2) * Math.PI / 180));

/** 统计卡片数据：将 stats ref 映射为卡片展示格式 */
const statCards = computed(() => [
  { label: "项目数", value: stats.value.total_kb },
  { label: "文档数", value: stats.value.total_docs },
  { label: "用户数", value: stats.value.total_users },
  { label: "消息数", value: stats.value.total_messages },
]);

/**
 * 网络球体装饰图：12 个随机分布的点 + 连线
 * 用于统计卡片"消息数"的 icon 装饰
 */
const spherePoints = computed(() => {
  const pts = [];
  const n = 12;
  for (let i = 0; i < n; i++) {
    const angle = (i / n) * Math.PI * 2;
    const r = 14 + Math.sin(i * 1.7) * 8;
    pts.push({
      x: 30 + r * Math.cos(angle),
      y: 30 + r * Math.sin(angle),
      r: 1.2 + Math.random() * 0.8,
      fill: i % 3 === 0 ? "rgba(0,242,254,0.8)" : i % 3 === 1 ? "rgba(167,139,250,0.7)" : "rgba(250,112,154,0.6)",
    });
  }
  return pts;
});
/** 连线：每个点与相邻点和第三个点相连 */
const sphereLines = computed(() => {
  const lines = [];
  const pts = spherePoints.value;
  for (let i = 0; i < pts.length; i++) {
    const j = (i + 1) % pts.length;
    const k = (i + 3) % pts.length;
    lines.push({ x1: pts[i].x, y1: pts[i].y, x2: pts[j].x, y2: pts[j].y });
    lines.push({ x1: pts[i].x, y1: pts[i].y, x2: pts[k].x, y2: pts[k].y });
  }
  return lines;
});

/**
 * 桑基流图：展示文档关键词频率
 * 使用 SVG path 绘制贝塞尔曲线流，左侧标签 + 右侧数值
 */
const colors = ["#00f2fe", "#43e97b", "#a78bfa", "#f59e0b", "#fa709a", "#38f9d7", "#64b4ff", "#e879f9", "#fb923c", "#34d399"];
/** 关键词数据：取 top_words 前 9 个，分配颜色 */
const sankeyData = computed(() => {
  return analytics.value.top_words.slice(0, 9).map((w, i) => ({
    ...w, color: colors[i % colors.length],
  }));
});
const sankeyHeight = computed(() => Math.max(sankeyData.value.length * 32, 100));
/** 桑基流路径：贝塞尔曲线从左侧各关键词流向右侧中心点 */
const sankeyFlows = computed(() => {
  const data = sankeyData.value;
  const h = sankeyHeight.value;
  const n = data.length;
  const maxCount = Math.max(...data.map(d => d.count), 1);
  const barH = Math.min(22, (h - 10) / n);
  return data.map((item, i) => {
    const y = 10 + i * (h / n) + (h / n - barH) / 2;
    const flowH = Math.max(3, (item.count / maxCount) * barH);
    const midY = h / 2;
    return {
      d: `M 0 ${y + barH / 2 - flowH / 2} C 100 ${y + barH / 2 - flowH / 2} 250 ${midY - flowH / 2} 390 ${midY - flowH / 2 + i * 3} L 390 ${midY + flowH / 2 + i * 3} C 250 ${midY + flowH / 2} 100 ${y + barH / 2 + flowH / 2} 0 ${y + barH / 2 + flowH / 2} Z`,
    };
  });
});

/**
 * 每日新增趋势图：SVG 面积图 + 折线 + 节点
 * 展示近 7 天的文档/消息新增量趋势
 */
const trendWidth = 500;
const trendHeight = 200;
/** 趋势点：将 daily_stats 映射到 SVG 坐标 */
const trendPoints = computed(() => {
  const data = analytics.value.daily_stats || [];
  if (!data.length) return [];
  const max = Math.max(...data.map(d => d.count), 1);
  const padding = 40;
  const usable = trendWidth - padding * 2;
  return data.map((d, i) => ({
    x: padding + (i / Math.max(data.length - 1, 1)) * usable,
    y: 20 + (1 - d.count / max) * (trendHeight - 50),
  }));
});
/** 折线路径：点对点直线连接 */
const linePath = computed(() => {
  const pts = trendPoints.value;
  if (pts.length < 2) return "";
  return pts.map((p, i) => (i === 0 ? `M${p.x},${p.y}` : `L${p.x},${p.y}`)).join(" ");
});
/** 面积路径：折线 + 底部闭合，用于渐变填充 */
const areaPath = computed(() => {
  const pts = trendPoints.value;
  if (pts.length < 2) return "";
  const line = pts.map((p, i) => (i === 0 ? `M${p.x},${p.y}` : `L${p.x},${p.y}`)).join(" ");
  return `${line} L${pts[pts.length - 1].x},${trendHeight - 20} L${pts[0].x},${trendHeight - 20} Z`;
});
/** Y 轴刻度标签：最大值、一半、0 */
const yLabels = computed(() => {
  const data = analytics.value.daily_stats || [];
  const max = Math.max(...data.map(d => d.count), 1);
  return [max, Math.round(max / 2), 0];
});
const gridLines = computed(() => {
  return [40, 100, 160];
});

/**
 * 角色比例数据：基于最近 3 天的日统计生成
 * 目前为模拟数据（管理者 30% / 申请人 70%），后续可接入真实数据
 */
const roleData = computed(() => {
  const days = analytics.value.daily_stats?.slice(-3) || [];
  return days.map(d => ({
    date: d.date.slice(5),
    segments: [
      { label: "管理者", pct: 30, color: "rgba(0,242,254,0.6)" },
      { label: "申请人", pct: 70, color: "rgba(167,139,250,0.5)" },
    ],
  }));
});

/** 用户活跃列表：取最近 5 个活跃用户，前 2 个标记为"主动" */
const userList = computed(() => {
  return analytics.value.user_activity?.slice(0, 5).map((u, i) => ({
    name: u.username,
    count: u.count,
    active: i < 2,
    avatarBg: i % 2 === 0 ? "rgba(0,242,254,0.15)" : "rgba(167,139,250,0.15)",
  })) || [];
});

/**
 * 绘制背景网络 Canvas 动画
 * 40 个随机移动的节点，距离 < 150px 时绘制连线
 * 使用 requestAnimationFrame 驱动，通过 animFrameId 在 onUnmounted 清理
 */
let animFrameId;
function drawNetwork() {
  const canvas = networkCanvas.value;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  const nodes = [];
  for (let i = 0; i < 40; i++) {
    nodes.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: Math.random() * 2 + 0.5,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
    });
  }
  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    nodes.forEach(n => {
      n.x += n.vx; n.y += n.vy;
      if (n.x < 0 || n.x > canvas.width) n.vx *= -1;
      if (n.y < 0 || n.y > canvas.height) n.vy *= -1;
    });
    // Draw lines
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 150) {
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.strokeStyle = `rgba(0,242,254,${0.08 * (1 - dist / 150)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }
    // Draw nodes
    nodes.forEach(n => {
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(0,242,254,0.3)";
      ctx.fill();
    });
    animFrameId = requestAnimationFrame(animate);
  }
  animate();
}

let refreshTimer;  // 定时刷新句柄，onUnmounted 时清理

/**
 * 组件挂载流程：
 * 1. 启动时钟定时器
 * 2. 初始化 Canvas 网络动画
 * 3. 并行加载统计和分析数据
 * 4. 启动 30 秒自动刷新
 */
onMounted(async () => {
  updateClock();
  clockTimer = setInterval(updateClock, 1000);
  await nextTick();
  drawNetwork();
  try {
    const [s, a] = await Promise.all([
      http.get("/logs/stats"),
      http.get("/logs/analytics"),
    ]);
    stats.value = s.data;
    analytics.value = a.data;
  } catch (e) {
    console.error("Dashboard load error:", e);
  }
  refreshTimer = setInterval(async () => {
    try {
      const [s, a] = await Promise.all([
        http.get("/logs/stats"),
        http.get("/logs/analytics"),
      ]);
      stats.value = s.data;
      analytics.value = a.data;
    } catch (e) {}
  }, 30000);
});

onUnmounted(() => {
  clearInterval(clockTimer);
  clearInterval(refreshTimer);
  cancelAnimationFrame(animFrameId);
});
</script>

<style scoped>
.dashboard {
  min-height: 100vh; background: #0a0e1a; color: #c8d6e5; position: relative; overflow-x: hidden;
}
.bg-layer {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background:
    radial-gradient(ellipse 60% 50% at 25% 20%, rgba(0,80,180,0.08) 0%, transparent 70%),
    radial-gradient(ellipse 50% 40% at 75% 80%, rgba(80,30,140,0.06) 0%, transparent 70%);
}
.bg-canvas { position: fixed; inset: 0; z-index: 0; pointer-events: none; }

/* Header */
.dash-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 18px 32px; position: relative; z-index: 2;
}
.header-left { display: flex; align-items: center; gap: 8px; }
.status-dot {
  width: 8px; height: 8px; border-radius: 50%; background: #43e97b;
  box-shadow: 0 0 10px #43e97b; animation: blink 2s infinite;
}
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
.status-text { font-size: 13px; color: rgba(255,255,255,0.5); }
.header-title {
  font-size: 26px; font-weight: 800; letter-spacing: 4px;
  background: linear-gradient(135deg, #00f2fe 0%, #a78bfa 50%, #fa709a 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.header-right { display: flex; align-items: center; }
.clock-ring { width: 40px; height: 40px; }
.clock-ring svg { width: 100%; height: 100%; }

/* Stat cards */
.stat-cards {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
  padding: 0 32px; margin-bottom: 24px; position: relative; z-index: 2;
}
.stat-card {
  display: flex; align-items: center; gap: 16px; padding: 18px 20px;
  background: rgba(12,16,32,0.85); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px; backdrop-filter: blur(12px);
  transition: all 0.3s;
}
.stat-card:hover { border-color: rgba(0,242,254,0.15); transform: translateY(-2px); }
.card-icon-box { width: 80px; height: 70px; display: flex; align-items: center; justify-content: center; }
.card-icon-3d { width: 70px; height: 70px; position: relative; }
.card-data { flex: 1; }
.card-number {
  font-size: 36px; font-weight: 800; color: #00f2fe; font-family: monospace; line-height: 1;
  text-shadow: 0 0 20px rgba(0,242,254,0.3);
}
.card-label { font-size: 13px; color: rgba(255,255,255,0.35); margin-top: 4px; }

/* Geometric icon */
.geo-shape { width: 70px; height: 70px; position: relative; animation: geo-spin 12s linear infinite; }
@keyframes geo-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.hexagon {
  position: absolute; inset: 5px; border: 1.5px solid rgba(167,139,250,0.5);
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
}
.hexagon-inner {
  position: absolute; inset: 15px; border: 1px solid rgba(0,242,254,0.4);
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
  animation: geo-spin 8s linear infinite reverse;
}

/* Doc stack */
.doc-stack { position: relative; width: 50px; height: 60px; }
.doc-page {
  position: absolute; bottom: 0; left: 5px; width: 40px; height: 50px;
  background: rgba(0,242,254,0.08); border: 1px solid rgba(0,242,254,0.25);
  border-radius: 3px; transform-origin: bottom center;
}

/* Human particle */
.human-particle svg { width: 60px; height: 70px; }

/* Network sphere */
.network-sphere svg { width: 65px; height: 65px; }

/* Chart section */
.chart-section {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  padding: 0 32px; margin-bottom: 16px; position: relative; z-index: 2;
}
.chart-panel {
  background: rgba(12,16,32,0.85); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px; overflow: hidden;
}
.panel-title-bar {
  display: flex; align-items: center; gap: 8px; padding: 14px 18px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.title-accent { width: 3px; height: 14px; background: #00f2fe; border-radius: 2px; }
.panel-title { font-size: 14px; font-weight: 600; color: rgba(255,255,255,0.85); }
.panel-menu { margin-left: auto; color: rgba(255,255,255,0.2); cursor: pointer; font-size: 16px; }

/* Sankey */
.sankey-area { padding: 16px; display: flex; gap: 12px; min-height: 280px; position: relative; }
.sankey-left-labels { width: 90px; display: flex; flex-direction: column; justify-content: space-around; }
.sankey-label-row { display: flex; align-items: center; gap: 6px; }
.sankey-label { font-size: 11px; color: rgba(255,255,255,0.45); text-align: right; flex: 1;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sankey-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.sankey-flow { flex: 1; }
.sankey-svg { width: 100%; height: 100%; }
.sankey-path { opacity: 0.7; transition: opacity 0.3s; cursor: pointer; }
.sankey-path:hover { opacity: 1; }
.sankey-right-labels { width: 30px; display: flex; flex-direction: column; justify-content: space-around; }
.sankey-right-row { text-align: left; }
.sankey-count { font-size: 13px; font-weight: 700; font-family: monospace; }
.sankey-tooltip {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  background: rgba(10,14,26,0.95); border: 1px solid rgba(0,242,254,0.2);
  border-radius: 8px; padding: 10px 14px; z-index: 10;
  display: flex; flex-direction: column; gap: 4px;
}
.tooltip-title { font-size: 11px; color: rgba(255,255,255,0.5); }
.tooltip-item { font-size: 12px; color: #00f2fe; }

/* Trend chart */
.trend-area { padding: 16px; display: flex; gap: 8px; }
.trend-y-axis { display: flex; flex-direction: column; justify-content: space-between;
  padding: 0 4px 20px; font-size: 10px; color: rgba(255,255,255,0.2); font-family: monospace; }
.trend-chart { flex: 1; position: relative; }
.trend-svg { width: 100%; height: 200px; }
.trend-line { filter: drop-shadow(0 0 6px rgba(0,242,254,0.4)); }
.area-fill { animation: area-in 1.5s ease; }
@keyframes area-in { from { opacity: 0; } to { opacity: 1; } }
.trend-node { cursor: pointer; }
.trend-tooltip {
  position: absolute; top: 20px; transform: translateX(-50%);
  background: rgba(10,14,26,0.95); border: 1px solid rgba(0,242,254,0.2);
  border-radius: 8px; padding: 10px 14px; z-index: 10; white-space: nowrap;
}
.tt-date { font-size: 12px; color: rgba(255,255,255,0.6); margin-bottom: 4px; }
.tt-item { font-size: 11px; color: #00f2fe; }

/* Bottom section */
.bottom-section {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  padding: 0 32px; margin-bottom: 16px; position: relative; z-index: 2;
}

/* Role bars */
.role-bars { padding: 16px 18px; display: flex; flex-direction: column; gap: 14px; }
.role-row { display: flex; align-items: center; gap: 10px; }
.role-date { font-size: 11px; color: rgba(255,255,255,0.3); width: 40px; font-family: monospace; }
.role-bar-track {
  flex: 1; height: 20px; display: flex; border-radius: 4px; overflow: hidden;
  background: rgba(255,255,255,0.02);
}
.role-segment { height: 100%; transition: width 0.8s ease; }
.role-legend { display: flex; gap: 6px; margin-left: 8px; }
.legend-tag {
  font-size: 10px; padding: 2px 8px; border: 1px solid; border-radius: 4px;
  background: rgba(255,255,255,0.02); white-space: nowrap;
}
.role-pct { font-size: 11px; color: rgba(255,255,255,0.3); font-family: monospace; width: 40px; text-align: right; }

/* User detail list */
.user-detail-list { padding: 12px 18px; }
.user-detail-row {
  display: flex; align-items: center; gap: 12px; padding: 10px 0;
  border-bottom: 1px solid rgba(255,255,255,0.03);
}
.user-detail-row:last-child { border-bottom: none; }
.user-avatar {
  width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 700; color: rgba(255,255,255,0.6);
}
.user-detail-name { font-size: 13px; color: rgba(255,255,255,0.8); width: 60px; }
.user-status {
  display: flex; align-items: center; gap: 4px; font-size: 11px;
  color: rgba(255,255,255,0.25);
}
.user-status.active { color: #43e97b; }
.status-dot-sm { width: 5px; height: 5px; border-radius: 50%; background: currentColor; }
.user-meta { font-size: 11px; color: rgba(255,255,255,0.2); }
.user-msg-count {
  margin-left: auto; font-size: 16px; font-weight: 700; font-family: monospace;
}

/* Footer */
.dash-footer {
  display: flex; justify-content: center; gap: 12px; padding: 12px 32px 18px;
  position: relative; z-index: 2;
}
.footer-chip {
  padding: 6px 16px; border-radius: 20px; font-size: 11px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.3); cursor: pointer; transition: all 0.3s;
}
.footer-chip:hover, .footer-chip.active {
  background: rgba(0,242,254,0.08); border-color: rgba(0,242,254,0.2); color: #00f2fe;
}
</style>
