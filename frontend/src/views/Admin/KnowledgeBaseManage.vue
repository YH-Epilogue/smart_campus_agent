<template>
  <div class="page-container">
    <div class="page-header">
      <h2>知识库管理</h2>
    </div>
    <el-card>
      <div class="filter-bar">
        <el-input v-model="filterName" placeholder="按名称搜索" style="width: 180px" clearable @clear="loadKBs" @keyup.enter="loadKBs" />
        <el-input v-model="filterDept" placeholder="按部门筛选" style="width: 150px" clearable @clear="loadKBs" @keyup.enter="loadKBs" />
        <el-date-picker v-model="filterDate" type="daterange" range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期" style="width: 260px" @change="loadKBs" />
        <el-button @click="loadKBs">搜索</el-button>
      </div>
      <div class="create-bar">
        <el-input v-model="newName" placeholder="知识库名称" style="width: 180px" />
        <el-input v-model="newDesc" placeholder="描述（可选）" style="width: 180px" />
        <el-input v-model="newDept" placeholder="所属部门" style="width: 140px" />
        <el-button type="primary" @click="handleCreate">创建</el-button>
      </div>
      <el-table :data="kbs">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="document_count" label="文档数" width="100" />
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" @click="handleClone(row.id)">克隆</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="error" class="error-tip">{{ error }}</div>
    </el-card>

    <el-dialog v-model="editVisible" title="编辑知识库" width="400px">
      <el-form :model="editForm">
        <el-form-item label="名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { listKBs, createKB, deleteKB, updateKB, cloneKB } from "../../api/kb";
import { ElMessage } from "element-plus";

const kbs = ref([]);
const newName = ref("");
const newDesc = ref("");
const error = ref("");
const editVisible = ref(false);
const editForm = reactive({ id: 0, name: "", description: "" });
const filterName = ref("");
const filterDept = ref("");
const filterDate = ref(null);

async function loadKBs() {
  try {
    error.value = "";
    const params = {};
    if (filterName.value) params.name = filterName.value;
    if (filterDept.value) params.department = filterDept.value;
    if (filterDate.value && filterDate.value.length === 2) {
      params.start_date = filterDate.value[0].toISOString().split("T")[0];
      params.end_date = filterDate.value[1].toISOString().split("T")[0];
    }
    kbs.value = await listKBs(params);
  } catch (e) {
    error.value = "加载失败：" + (e.response?.data?.detail || e.message);
  }
}

async function handleCreate() {
  if (!newName.value.trim()) return;
  try {
    await createKB(newName.value, newDesc.value, newDept.value);
    newName.value = "";
    newDesc.value = "";
    newDept.value = "";
    ElMessage.success("创建成功");
    await loadKBs();
  } catch (e) {
    ElMessage.error("创建失败：" + (e.response?.data?.detail || e.message));
  }
}

function openEdit(kb) {
  editForm.id = kb.id;
  editForm.name = kb.name;
  editForm.description = kb.description;
  editVisible.value = true;
}

async function handleEdit() {
  try {
    await updateKB(editForm.id, editForm.name, editForm.description);
    editVisible.value = false;
    ElMessage.success("修改成功");
    await loadKBs();
  } catch (e) {
    ElMessage.error("修改失败：" + (e.response?.data?.detail || e.message));
  }
}

async function handleClone(kbId) {
  try {
    await cloneKB(kbId);
    ElMessage.success("克隆成功");
    await loadKBs();
  } catch (e) {
    ElMessage.error("克隆失败：" + (e.response?.data?.detail || e.message));
  }
}

async function handleDelete(id) {
  try {
    await deleteKB(id);
    ElMessage.success("已删除");
    await loadKBs();
  } catch (e) {
    ElMessage.error("删除失败：" + (e.response?.data?.detail || e.message));
  }
}

onMounted(loadKBs);
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

.create-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.error-tip {
  color: var(--danger);
  font-size: 13px;
  margin-top: 12px;
}
</style>
