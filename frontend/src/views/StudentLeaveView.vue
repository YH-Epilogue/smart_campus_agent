<template>
  <div class="page-container">
    <div class="page-header">
      <h2>我的请假记录</h2>
    </div>

    <el-table :data="list" stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="编号" width="70" />
      <el-table-column label="请假时间" width="200">
        <template #default="{ row }">{{ row.start_date }} 至 {{ row.end_date }}</template>
      </el-table-column>
      <el-table-column prop="reason" label="请假原因" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="提交时间" width="170">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
    </el-table>

    <div v-if="!loading && list.length === 0" class="empty-state">
      暂无请假记录
    </div>
  </div>
</template>

<script setup>
/**
 * StudentLeaveView - 学生请假记录查看页
 * 职责：展示当前登录学生的请假历史记录列表
 * 角色：仅学生可见，教师/管理员使用 LeaveManage.vue
 * 数据：通过 getLeaveList 接口获取（后端按 user_id 过滤）
 */
import { ref, onMounted } from "vue";
import { getLeaveList } from "../api/leave";
import { ElMessage } from "element-plus";

const list = ref([]);       // 请假记录列表
const loading = ref(false); // 加载状态

/** 将状态码映射为 Element Plus Tag 的类型（颜色） */
function statusType(s) {
  return { pending: "warning", approved: "success", rejected: "danger" }[s] || "info";
}

/** 将状态码映射为中文标签文本 */
function statusLabel(s) {
  return { pending: "审批中", approved: "已批准", rejected: "已驳回" }[s] || s;
}

/** 格式化日期为中文本地化格式 */
function formatDate(d) {
  if (!d) return "-";
  return new Date(d).toLocaleString("zh-CN");
}

onMounted(async () => {
  loading.value = true;
  try {
    list.value = await getLeaveList();
  } catch (e) {
    ElMessage.error("加载失败");
  }
  loading.value = false;
});
</script>

<style scoped>
.page-container { padding: 24px 32px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #f0ebe5; }
.empty-state { text-align: center; padding: 60px; color: rgba(255,255,255,0.3); font-size: 14px; }
</style>
