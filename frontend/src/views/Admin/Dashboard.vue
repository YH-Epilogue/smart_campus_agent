<template>
  <div class="page-container">
    <div class="page-header">
      <h2>数据统计</h2>
    </div>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon kb-icon">📚</div>
            <div class="stat-value">{{ stats.kbCount }}</div>
            <div class="stat-label">知识库</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon doc-icon">📄</div>
            <div class="stat-value">{{ stats.docCount }}</div>
            <div class="stat-label">文档</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon chat-icon">💬</div>
            <div class="stat-value">{{ stats.chatCount }}</div>
            <div class="stat-label">对话</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { listKBs } from "../../api/kb";
import axios from "axios";

const stats = ref({ kbCount: 0, docCount: 0, chatCount: 0 });

onMounted(async () => {
  const kbs = await listKBs();
  stats.value.kbCount = kbs.length;
  stats.value.docCount = kbs.reduce((sum, kb) => sum + kb.document_count, 0);

  try {
    const token = localStorage.getItem("token");
    const { data } = await axios.get("/api/v1/logs/stats", {
      headers: { Authorization: `Bearer ${token}` },
    });
    stats.value.chatCount = data.total_messages || 0;
  } catch (e) {
    console.error("Failed to load chat stats:", e);
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
  padding: 32px 20px;
}

.stat-icon {
  font-size: 28px;
  margin-bottom: 16px;
  opacity: 0.9;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  color: #d4aa50;
  line-height: 1;
}

.stat-label {
  margin-top: 8px;
  color: rgba(200, 190, 175, 0.5);
  font-size: 13px;
}
</style>
