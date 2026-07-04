<template>
  <div class="page-container">
    <div class="page-header">
      <h2>知识库管理</h2>
    </div>
    <el-card>
      <div class="create-bar">
        <el-input v-model="newName" placeholder="知识库名称" style="width: 200px" />
        <el-input v-model="newDesc" placeholder="描述（可选）" style="width: 300px" />
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

async function load() {
  try {
    error.value = "";
    kbs.value = await listKBs();
  } catch (e) {
    error.value = "加载失败：" + (e.response?.data?.detail || e.message);
  }
}

async function handleCreate() {
  if (!newName.value.trim()) return;
  try {
    await createKB(newName.value, newDesc.value);
    newName.value = "";
    newDesc.value = "";
    ElMessage.success("创建成功");
    await load();
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
    await load();
  } catch (e) {
    ElMessage.error("修改失败：" + (e.response?.data?.detail || e.message));
  }
}

async function handleClone(kbId) {
  try {
    await cloneKB(kbId);
    ElMessage.success("克隆成功");
    await load();
  } catch (e) {
    ElMessage.error("克隆失败：" + (e.response?.data?.detail || e.message));
  }
}

async function handleDelete(id) {
  try {
    await deleteKB(id);
    ElMessage.success("已删除");
    await load();
  } catch (e) {
    ElMessage.error("删除失败：" + (e.response?.data?.detail || e.message));
  }
}

onMounted(load);
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

.error-tip {
  color: var(--danger);
  font-size: 13px;
  margin-top: 12px;
}
</style>
