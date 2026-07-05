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
        <el-table-column label="操作" width="260">
          <template #default="{ row }">
            <el-button size="small" @click="handlePreview(row.id)">预览</el-button>
            <el-button size="small" @click="handleVersions(row.id)">版本</el-button>
            <el-button size="small" @click="handleVectors(row.id)">向量</el-button>
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

    <el-dialog v-model="versionVisible" title="版本历史" width="500px">
      <div v-if="versionData">
        <p><strong>当前版本：</strong>第 {{ versionData.current_version }} 版</p>
        <el-divider />
        <div v-if="versionData.versions.length === 0" class="empty-versions">
          暂无历史版本
        </div>
        <div v-else class="version-list">
          <div v-for="v in versionData.versions" :key="v.version" class="version-item">
            <span class="version-num">版本 {{ v.version }}</span>
            <span class="version-time">{{ formatTime(v.time) }}</span>
            <el-button size="small" type="warning" @click="handleRollback(v.version)">回滚</el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="vectorVisible" title="向量预览" width="600px">
      <div v-if="vectorData">
        <p><strong>文件名：</strong>{{ vectorData.filename }}</p>
        <p><strong>向量数量：</strong>{{ vectorData.count }}</p>
        <p><strong>向量维度：</strong>{{ vectorData.dimension }}</p>
        <el-divider />
        <div v-if="vectorData.vectors.length === 0" class="empty-versions">
          暂无向量数据
        </div>
        <div v-else class="vector-list">
          <div v-for="v in vectorData.vectors" :key="v.id" class="vector-item">
            <div class="vector-id">{{ v.id }}</div>
            <div class="vector-doc">{{ v.document }}...</div>
            <div class="vector-meta">
              <span>维度: {{ v.dimension }}</span>
              <span>doc_id: {{ v.metadata.doc_id }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import { listKBs } from "../../api/kb";
import { listDocs, deleteDoc, previewDoc, getVersions, rollbackDoc, getVectors } from "../../api/doc";
import FileUploader from "../../components/upload/FileUploader.vue";
import { ElMessage, ElMessageBox } from "element-plus";

const kbs = ref([]);
const docs = ref([]);
const selectedKB = ref(null);
let pollTimer = null;
const previewVisible = ref(false);
const previewData = ref(null);
const versionVisible = ref(false);
const versionData = ref(null);
const vectorVisible = ref(false);
const vectorData = ref(null);

function statusType(s) {
  return { ready: "success", error: "danger", uploading: "warning", parsing: "warning", indexing: "info" }[s] || "info";
}

function statusLabel(s) {
  return { ready: "就绪", error: "失败", uploading: "上传中", parsing: "解析中", indexing: "索引中" }[s] || s;
}

function formatTime(timestamp) {
  return new Date(timestamp * 1000).toLocaleString();
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

async function handleVersions(docId) {
  try {
    versionData.value = await getVersions(docId);
    versionVisible.value = true;
  } catch (e) {
    ElMessage.error("获取版本失败：" + (e.response?.data?.detail || e.message));
  }
}

async function handleVectors(docId) {
  try {
    vectorData.value = await getVectors(docId);
    vectorVisible.value = true;
  } catch (e) {
    ElMessage.error("获取向量失败：" + (e.response?.data?.detail || e.message));
  }
}

async function handleRollback(version) {
  try {
    await ElMessageBox.confirm(`确定回滚到版本 ${version}？`, "确认回滚", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    await rollbackDoc(versionData.value.current_version > 1 ? versionData.value.current_version - 1 : 1, version);
    ElMessage.success("回滚成功，正在重新向量化");
    versionVisible.value = false;
    await loadDocs();
  } catch (e) {
    if (e !== "cancel") {
      ElMessage.error("回滚失败：" + (e.response?.data?.detail || e.message));
    }
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

.empty-versions {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
}

.version-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.version-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
}

.version-num {
  font-weight: 500;
  color: var(--text-primary);
}

.version-time {
  font-size: 12px;
  color: var(--text-muted);
}

.vector-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.vector-item {
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
}

.vector-id {
  font-family: monospace;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.vector-doc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.vector-meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: var(--text-muted);
}
</style>
