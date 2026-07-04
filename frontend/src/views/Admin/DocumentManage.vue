<template>
  <div class="page-container">
    <div class="page-header">
      <h2>文档管理</h2>
    </div>
    <el-card>
      <div class="toolbar">
        <el-select v-model="selectedKB" placeholder="选择知识库" @change="loadDocs">
          <el-option v-for="kb in kbs" :key="kb.id" :label="kb.name" :value="kb.id" />
        </el-select>
        <el-button @click="loadDocs" :disabled="!selectedKB">刷新</el-button>
      </div>
      <FileUploader v-if="selectedKB" :kbId="selectedKB" @uploaded="loadDocs" />
      <el-table :data="docs" style="margin-top: 16px">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="filename" label="文件名" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="180">
          <template #default="{ row }">
            <el-progress
              v-if="row.status === 'parsing' || row.status === 'indexing' || row.status === 'uploading'"
              :percentage="row.progress"
              :status="row.status === 'error' ? 'exception' : ''"
            />
            <span v-else-if="row.status === 'ready'" class="status-ready">100%</span>
            <span v-else-if="row.status === 'error'" class="status-error">失败</span>
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="切片数" width="100" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" @click="handlePreview(row.id)">预览</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="previewVisible" title="文档预览" width="70%">
      <div v-if="previewData">
        <p><strong>文件名：</strong>{{ previewData.filename }}</p>
        <p><strong>总长度：</strong>{{ previewData.total_length }} 字符</p>
        <el-divider />
        <pre class="preview-content">{{ previewData.content }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { listKBs } from "../../api/kb";
import { listDocs, deleteDoc, previewDoc } from "../../api/doc";
import FileUploader from "../../components/upload/FileUploader.vue";
import { ElMessage, ElMessageBox } from "element-plus";

const kbs = ref([]);
const docs = ref([]);
const selectedKB = ref(null);
let pollTimer = null;
const previewVisible = ref(false);
const previewData = ref(null);

function statusType(s) {
  return { ready: "success", error: "danger", uploading: "warning", parsing: "warning", indexing: "info" }[s] || "info";
}

function statusLabel(s) {
  return { ready: "就绪", error: "失败", uploading: "上传中", parsing: "解析中", indexing: "索引中" }[s] || s;
}

async function loadDocs() {
  if (!selectedKB.value) return;
  docs.value = await listDocs(selectedKB.value);
}

async function handlePreview(docId) {
  try {
    previewData.value = await previewDoc(docId);
    previewVisible.value = true;
  } catch (e) {
    ElMessage.error("预览失败：" + (e.response?.data?.detail || e.message));
  }
}

async function handleDelete(docId) {
  try {
    await ElMessageBox.confirm("确定删除此文档？删除后向量数据也会被清除。", "确认删除", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    await deleteDoc(docId);
    ElMessage.success("删除成功");
    await loadDocs();
  } catch (e) {
    if (e !== "cancel") {
      ElMessage.error("删除失败：" + (e.response?.data?.detail || e.message));
    }
  }
}

function startPolling() {
  pollTimer = setInterval(() => {
    const hasProcessing = docs.value.some(
      (d) => d.status === "parsing" || d.status === "indexing" || d.status === "uploading"
    );
    if (hasProcessing) loadDocs();
  }, 2000);
}

onMounted(async () => {
  kbs.value = await listKBs();
  startPolling();
});

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
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

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.status-ready {
  color: #64b4ff;
  font-weight: 500;
}

.status-error {
  color: var(--danger);
  font-weight: 500;
}

.preview-content {
  background: rgba(5, 5, 15, 0.8);
  border: 1px solid rgba(100, 180, 255, 0.1);
  padding: 16px;
  border-radius: var(--radius);
  max-height: 400px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 13px;
  line-height: 1.6;
  color: rgba(200, 190, 175, 0.7);
}
</style>
