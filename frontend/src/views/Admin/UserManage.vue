<template>
  <div class="page-container">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="refreshUsers" size="small">刷新</el-button>
    </div>

    <el-card>
    <el-table :data="users" stripe style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" min-width="150" />
      <el-table-column prop="role" label="角色" width="120">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : row.role === 'kb_admin' ? 'warning' : 'info'" size="small">
            {{ row.role === 'admin' ? '管理员' : row.role === 'kb_admin' ? '知识库管理员' : '普通用户' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" min-width="180">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" min-width="200">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editVisible" title="编辑用户" width="400px">
      <el-form :model="editForm" label-width="60px">
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="editForm.password" placeholder="留空则不修改" type="password" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role">
            <el-option label="管理员" value="admin" />
            <el-option label="知识库管理员" value="kb_admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEdit">保存</el-button>
      </template>
    </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
/**
 * UserManage - 用户管理页面
 * 职责：管理员查看、编辑、删除系统用户
 * 权限：仅 admin 可访问
 * 角色选项：admin（管理员）、kb_admin（知识库管理员）、user（普通用户）
 */
import { ref, onMounted } from "vue";
import { getUsers, updateUser, deleteUser } from "../../api/users";
import { ElMessage } from "element-plus";

const users = ref([]);         // 用户列表
const loading = ref(false);     // 加载状态
const editVisible = ref(false); // 编辑弹窗控制
const editForm = ref({ id: 0, username: "", password: "", role: "user" }); // 编辑表单（密码留空不修改）

/** 刷新用户列表 */
async function refreshUsers() {
  try {
    users.value = await getUsers();
  } catch (e) {
    ElMessage.error("获取用户列表失败");
  }
}

/** 格式化创建时间为中文本地化格式 */
function formatDate(d) {
  if (!d) return "-";
  return new Date(d).toLocaleString("zh-CN");
}

/** 打开编辑弹窗：预填用户名和角色，密码留空 */
function openEdit(row) {
  editForm.value = { id: row.id, username: row.username, password: "", role: row.role };
  editVisible.value = true;
}

/** 保存用户编辑：密码留空则不修改，否则更新密码 */
async function handleEdit() {
  try {
    const payload = { username: editForm.value.username, role: editForm.value.role };
    if (editForm.value.password) payload.password = editForm.value.password;
    await updateUser(editForm.value.id, payload);
    ElMessage.success("保存成功");
    editVisible.value = false;
    refreshUsers();
  } catch (e) {
    ElMessage.error("保存失败：" + (e.response?.data?.detail || e.message));
  }
}

/** 删除用户（使用 Popconfirm 二次确认） */
async function handleDelete(id) {
  try {
    await deleteUser(id);
    ElMessage.success("删除成功");
    refreshUsers();
  } catch (e) {
    ElMessage.error("删除失败：" + (e.response?.data?.detail || e.message));
  }
}

onMounted(refreshUsers);
</script>

<style scoped>
.page-container { padding: 16px 32px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #f0ebe5; }

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
