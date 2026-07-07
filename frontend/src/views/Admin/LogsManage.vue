<template>
  <div class="page-container">
    <div class="page-header">
      <h2>日志管理</h2>
      <div class="header-actions">
        <el-button @click="handleExport" size="small">导出 CSV</el-button>
        <el-popconfirm title="确定清理30天前的日志？" @confirm="handleCleanup">
          <template #reference>
            <el-button type="danger" size="small">清理旧日志</el-button>
          </template>
        </el-popconfirm>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input v-model="filters.keyword" placeholder="搜索关键词" clearable size="small" style="width: 200px" @keyup.enter="loadLogs" />
      <el-select v-model="filters.role" placeholder="角色" clearable size="small" style="width: 100px">
        <el-option label="用户" value="user" />
        <el-option label="助手" value="assistant" />
      </el-select>
      <el-input v-model="filters.session_id" placeholder="会话ID" clearable size="small" style="width: 160px" />
      <el-button type="primary" size="small" @click="loadLogs">查询</el-button>
    </div>

    <el-card>
    <el-table :data="logs" stripe style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="role" label="角色" width="80">
        <template #default="{ row }">
          <el-tag :type="row.role === 'assistant' ? 'success' : 'primary'" size="small">
            {{ row.role === 'assistant' ? 'AI' : '用户' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="content" label="内容" show-overflow-tooltip />
      <el-table-column prop="session_id" label="会话" width="140" show-overflow-tooltip />
      <el-table-column prop="created_at" label="时间" width="170">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
    </el-table>

      <!-- 分页 -->
      <div class="pagination" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadLogs"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
/**
 * LogsManage - 日志管理页面
 * 职责：查看、搜索、导出、清理聊天日志
 * 功能：关键词搜索、角色筛选、会话 ID 筛选、分页、CSV 导出、旧日志清理
 * 权限：仅 admin 可访问
 */
import { ref, onMounted } from "vue";
import { getLogs, exportLogs, cleanupLogs } from "../../api/logs";
import { ElMessage } from "element-plus";

const logs = ref([]);         // 日志列表
const loading = ref(false);   // 加载状态
const total = ref(0);         // 总条数（用于分页）
const currentPage = ref(1);   // 当前页码
const pageSize = 20;          // 每页条数
const filters = ref({ keyword: "", role: "", session_id: "" }); // 筛选条件

/** 加载日志列表：支持分页和多条件筛选 */
async function loadLogs() {
  loading.value = true;
  try {
    const params = { page: currentPage.value, page_size: pageSize };
    if (filters.value.keyword) params.keyword = filters.value.keyword;
    if (filters.value.role) params.role = filters.value.role;
    if (filters.value.session_id) params.session_id = filters.value.session_id;
    const data = await getLogs(params);
    logs.value = data.items || data;
    total.value = data.total || logs.value.length;
  } catch (e) {
    ElMessage.error("加载日志失败");
  }
  loading.value = false;
}

/** 格式化时间为中文本地化格式 */
function formatDate(d) {
  if (!d) return "-";
  return new Date(d).toLocaleString("zh-CN");
}

/** 导出日志为 CSV 文件：创建 Blob 下载 */
async function handleExport() {
  try {
    const blob = await exportLogs();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "chat_logs.csv"; a.click();
    URL.revokeObjectURL(url);
    ElMessage.success("导出成功");
  } catch (e) {
    ElMessage.error("导出失败");
  }
}

/** 清理 30 天前的旧日志（带二次确认） */
async function handleCleanup() {
  try {
    const result = await cleanupLogs(30);
    ElMessage.success(result.detail || "清理完成");
    loadLogs();
  } catch (e) {
    ElMessage.error("清理失败");
  }
}

onMounted(loadLogs);
</script>

<style scoped>
.page-container { padding: 24px 32px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #f0ebe5; }
.header-actions { display: flex; gap: 8px; }
.filter-bar { display: flex; gap: 10px; margin-bottom: 16px; align-items: center; }
.pagination { display: flex; justify-content: center; margin-top: 16px; }

:deep(.el-table) {
  background: transparent !important;
}
:deep(.el-table th) {
  background: rgba(0, 242, 254, 0.08) !important;
  color: #00f2fe !important;
  border-bottom: 1px solid rgba(0, 242, 254, 0.15) !important;
}
:deep(.el-table td) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
  color: #c8d6e5 !important;
}
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: rgba(0, 242, 254, 0.03) !important;
}
:deep(.el-table__row:hover > td) {
  background: rgba(0, 242, 254, 0.06) !important;
}
</style>
