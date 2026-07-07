<template>
  <div class="page-container">
    <div class="page-header">
      <h2>请假审批</h2>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-mini">
          <div class="stat-num pending">{{ stats.pending }}</div>
          <div class="stat-lbl">待审批</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-mini">
          <div class="stat-num approved">{{ stats.approved }}</div>
          <div class="stat-lbl">已批准</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-mini">
          <div class="stat-num rejected">{{ stats.rejected }}</div>
          <div class="stat-lbl">已驳回</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-mini">
          <div class="stat-num total">{{ stats.total }}</div>
          <div class="stat-lbl">总计</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选 -->
    <div class="filter-bar">
      <el-radio-group v-model="statusFilter" @change="loadList" size="small">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="pending">待审批</el-radio-button>
        <el-radio-button value="approved">已批准</el-radio-button>
        <el-radio-button value="rejected">已驳回</el-radio-button>
      </el-radio-group>
      <el-button size="small" @click="loadList">刷新</el-button>
    </div>

    <!-- 列表 -->
    <el-table :data="list" stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="student_name" label="姓名" width="80" />
      <el-table-column prop="student_id" label="学号" width="120" />
      <el-table-column prop="class_name" label="班级" width="120" />
      <el-table-column label="请假时间" width="200">
        <template #default="{ row }">{{ row.start_date }} 至 {{ row.end_date }}</template>
      </el-table-column>
      <el-table-column prop="reason" label="原因" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="提交时间" width="170">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" v-if="isAdmin">
        <template #default="{ row }">
          <template v-if="row.status === 'pending'">
            <el-button size="small" type="success" @click="handleApprove(row.id)">批准</el-button>
            <el-button size="small" type="danger" @click="handleReject(row.id)">驳回</el-button>
          </template>
          <span v-else class="action-done">已处理</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
/**
 * LeaveManage - 请假审批管理页面
 * 职责：管理员/教师查看和审批学生的请假申请
 * 权限：admin/kb_admin/teacher 可审批，普通用户只读
 * 流程：统计概览 → 状态筛选 → 列表展示 → 批准/驳回操作
 */
import { ref, onMounted, computed } from "vue";
import { getLeaveList, getLeaveStats, approveLeave, rejectLeave } from "../../api/leave";
import { useUserStore } from "../../stores/userStore";
import { ElMessage, ElMessageBox } from "element-plus";

const userStore = useUserStore();
/** 判断当前用户是否有审批权限（admin/kb_admin/teacher） */
const isAdmin = computed(() => ["admin", "kb_admin", "teacher"].includes(userStore.user?.role));

/** 请假列表和统计数据 */
const list = ref([]);          // 请假记录列表
const stats = ref({ total: 0, pending: 0, approved: 0, rejected: 0 }); // 统计概览
const loading = ref(false);    // 加载状态
const statusFilter = ref("");  // 状态筛选（空=全部，pending/approved/rejected）

/** 将状态码映射为 Tag 颜色类型 */
function statusType(s) {
  return { pending: "warning", approved: "success", rejected: "danger" }[s] || "info";
}

/** 将状态码映射为中文标签 */
function statusLabel(s) {
  return { pending: "待审批", approved: "已批准", rejected: "已驳回" }[s] || s;
}

/** 格式化时间为中文本地化格式 */
function formatDate(d) {
  if (!d) return "-";
  return new Date(d).toLocaleString("zh-CN");
}

/** 加载请假列表：支持状态筛选 */
async function loadList() {
  loading.value = true;
  try {
    list.value = await getLeaveList(statusFilter.value || undefined);
  } catch (e) {
    console.error("加载请假列表失败:", e);
    const msg = e.response?.data?.detail || e.message || "加载失败";
    ElMessage.error("加载失败: " + msg);
  }
  loading.value = false;
}

/** 加载统计数据：各状态的请假数量 */
async function loadStats() {
  try {
    stats.value = await getLeaveStats();
  } catch (e) {
    console.error("加载请假统计失败:", e);
  }
}

/** 批准请假：二次确认后调用 API，刷新列表和统计 */
async function handleApprove(id) {
  try {
    await ElMessageBox.confirm("确定批准此请假申请？", "审批确认", { type: "success" });
    await approveLeave(id);
    ElMessage.success("已批准");
    loadList();
    loadStats();
  } catch (e) {
    if (e !== "cancel") ElMessage.error("操作失败：" + (e.response?.data?.detail || e.message));
  }
}

/** 驳回请假：二次确认后调用 API，刷新列表和统计 */
async function handleReject(id) {
  try {
    await ElMessageBox.confirm("确定驳回此请假申请？", "审批确认", { type: "warning" });
    await rejectLeave(id);
    ElMessage.success("已驳回");
    loadList();
    loadStats();
  } catch (e) {
    if (e !== "cancel") ElMessage.error("操作失败：" + (e.response?.data?.detail || e.message));
  }
}

onMounted(() => {
  loadList();
  loadStats();
});
</script>

<style scoped>
.page-container { padding: 24px 32px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #f0ebe5; }
.filter-bar { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; }
.stat-mini { text-align: center; }
.stat-num { font-size: 28px; font-weight: 700; font-family: monospace; }
.stat-num.pending { color: #f59e0b; }
.stat-num.approved { color: #43e97b; }
.stat-num.rejected { color: #ef4444; }
.stat-num.total { color: #00f2fe; }
.stat-lbl { font-size: 12px; color: rgba(255,255,255,0.4); margin-top: 4px; }
.action-done { font-size: 12px; color: rgba(255,255,255,0.25); }

:deep(.el-table) { background: transparent !important; }
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
