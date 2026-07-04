<template>
  <div class="page-container">
    <div class="page-header">
      <h2>数据统计</h2>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom: 32px">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon">📚</div>
            <div class="stat-value">{{ stats.total_kb }}</div>
            <div class="stat-label">知识库</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon">📄</div>
            <div class="stat-value">{{ stats.total_docs }}</div>
            <div class="stat-label">文档</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon">💬</div>
            <div class="stat-value">{{ stats.total_messages }}</div>
            <div class="stat-label">消息总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon">🗂️</div>
            <div class="stat-value">{{ stats.total_sessions }}</div>
            <div class="stat-label">会话数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20">
      <!-- 热门关键词 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span class="card-title">热门关键词</span>
          </template>
          <div class="chart-area">
            <div v-for="item in analytics.top_words" :key="item.word" class="bar-item">
              <span class="bar-label">{{ item.word }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: getBarWidth(item.count) + '%' }"></div>
              </div>
              <span class="bar-value">{{ item.count }}</span>
            </div>
            <div v-if="!analytics.top_words?.length" class="empty-chart">暂无数据</div>
          </div>
        </el-card>
      </el-col>

      <!-- 每日消息量 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span class="card-title">每日消息量</span>
          </template>
          <div class="chart-area">
            <div v-for="item in analytics.daily_stats" :key="item.date" class="bar-item">
              <span class="bar-label">{{ item.date.slice(5) }}</span>
              <div class="bar-track">
                <div class="bar-fill daily" :style="{ width: getDailyBarWidth(item.count) + '%' }"></div>
              </div>
              <span class="bar-value">{{ item.count }}</span>
            </div>
            <div v-if="!analytics.daily_stats?.length" class="empty-chart">暂无数据</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "axios";

const stats = ref({ total_kb: 0, total_docs: 0, total_messages: 0, total_sessions: 0 });
const analytics = ref({ top_words: [], daily_stats: [] });

function getBarWidth(count) {
  if (!analytics.value.top_words?.length) return 0;
  const max = Math.max(...analytics.value.top_words.map(w => w.count));
  return max > 0 ? (count / max) * 100 : 0;
}

function getDailyBarWidth(count) {
  if (!analytics.value.daily_stats?.length) return 0;
  const max = Math.max(...analytics.value.daily_stats.map(d => d.count));
  return max > 0 ? (count / max) * 100 : 0;
}

onMounted(async () => {
  try {
    const token = localStorage.getItem("token");
    const headers = { Authorization: `Bearer ${token}` };

    const [statsRes, analyticsRes] = await Promise.all([
      axios.get("/api/v1/logs/stats", { headers }),
      axios.get("/api/v1/logs/analytics", { headers }),
    ]);

    stats.value = statsRes.data;
    analytics.value = analyticsRes.data;
  } catch (e) {
    console.error("Failed to load stats:", e);
  }
});
</script>

<style scoped>
.page-container {
  padding: 24px 32px;
  background: transparent;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: #f0ebe5;
}

.stat-card {
  text-align: center;
  padding: 24px 16px;
}

.stat-icon {
  font-size: 28px;
  margin-bottom: 12px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #d4aa50;
  line-height: 1;
}

.stat-label {
  margin-top: 8px;
  color: rgba(200, 190, 175, 0.5);
  font-size: 13px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #f0ebe5;
}

.chart-area {
  padding: 16px 0;
}

.bar-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.bar-label {
  width: 80px;
  font-size: 12px;
  color: var(--text-secondary);
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-track {
  flex: 1;
  height: 20px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #d4aa50, #e0b860);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.bar-fill.daily {
  background: linear-gradient(90deg, #64b4ff, #80c4ff);
}

.bar-value {
  width: 40px;
  font-size: 12px;
  color: var(--text-muted);
  text-align: right;
}

.empty-chart {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}
</style>
