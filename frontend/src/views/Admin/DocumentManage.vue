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
        <el-button type="warning" size="small" :disabled="!selectedKB" @click="handleDedup">向量去重</el-button>
        <label class="batch-btn">
          <input type="file" multiple @change="handleBatchUpload" style="display:none" />
          <el-button size="small">批量上传</el-button>
        </label>
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
        <el-table-column label="操作" width="400">
          <template #default="{ row }">
            <div class="op-btns">
              <el-button size="small" @click="handlePreview(row.id)">预览</el-button>
              <el-button size="small" @click="handleVersions(row.id)">版本</el-button>
              <el-button size="small" @click="handleVectors(row.id)">向量</el-button>
              <el-button size="small" @click="handleSplitPreview(row.id)">拆分</el-button>
              <el-button size="small" type="warning" @click="openEdit(row)">编辑</el-button>
              <el-button type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
            </div>
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

    <el-dialog v-model="editVisible" title="编辑文档" width="70%">
      <p><strong>{{ editForm.filename }}</strong></p>
      <el-input v-model="editForm.content" type="textarea" :rows="20" placeholder="文档内容" />
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEditSave" :loading="editSaving">保存并重新向量化</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="splitVisible" title="拆分预览" width="600px">
      <div v-if="splitData">
        <p><strong>拆分片段数：</strong>{{ splitData.chunks?.length || 0 }}</p>
        <el-divider />
        <div v-for="(chunk, i) in splitData.chunks" :key="i" class="split-item">
          <span class="split-index">#{{ i + 1 }}</span>
          <span class="split-text">{{ chunk }}</span>
        </div>
        <div v-if="!splitData.chunks?.length" class="empty-versions">暂无数据</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * DocumentManage - 文档管理页面
 * 职责：管理选定知识库下的文档生命周期，包括上传、预览、编辑、删除、版本回滚、向量去重
 * 操作流程：先选择知识库 → 加载文档列表 → 对单个文档执行各种操作
 * 轮询机制：2 秒轮询检测处理中的文档状态（parsing/indexing/uploading）
 * 权限：teacher/admin 可管理所有知识库文档，普通用户仅管理自己的
 */
import { ref, onMounted, onUnmounted } from "vue";
import { listKBs } from "../../api/kb";
import { listDocs, deleteDoc, previewDoc, getVersions, rollbackDoc, getVectors, editDoc, batchUpload, dedupVectors, splitPreview } from "../../api/doc";
import FileUploader from "../../components/upload/FileUploader.vue";
import { ElMessage, ElMessageBox } from "element-plus";

/** 核心状态 */
const kbs = ref([]);              // 可用知识库列表
const docs = ref([]);             // 当前知识库的文档列表
const selectedKB = ref(null);     // 当前选中的知识库 ID
let pollTimer = null;             // 轮询定时器句柄

/** 弹窗控制状态 */
const previewVisible = ref(false);    // 预览弹窗
const previewData = ref(null);        // 预览数据
const versionVisible = ref(false);    // 版本历史弹窗
const versionData = ref(null);        // 版本历史数据
const currentDocId = ref(null);       // 当前操作的文档 ID（用于版本回滚）
const vectorVisible = ref(false);     // 向量预览弹窗
const vectorData = ref(null);         // 向量数据
const editVisible = ref(false);       // 编辑弹窗
const editSaving = ref(false);        // 编辑保存中状态
const editForm = ref({ id: 0, filename: "", content: "" }); // 编辑表单
const splitVisible = ref(false);      // 拆分预览弹窗
const splitData = ref(null);          // 拆分数据

/** 将文档状态映射为 Element Plus Tag 类型 */
function statusType(s) {
  return { ready: "success", error: "danger", uploading: "warning", parsing: "warning", indexing: "info" }[s] || "info";
}

/** 将文档状态映射为中文标签 */
function statusLabel(s) {
  return { ready: "就绪", error: "失败", uploading: "上传中", parsing: "解析中", indexing: "索引中" }[s] || s;
}

/** 版本时间戳格式化：秒级时间戳 → 本地化字符串 */
function formatTime(timestamp) {
  return new Date(timestamp * 1000).toLocaleString();
}

/** 加载当前选中知识库的文档列表 */
async function loadDocs() {
  if (!selectedKB.value) return;
  docs.value = await listDocs(selectedKB.value);
}

/** 预览文档：获取文档纯文本内容并显示在弹窗中 */
async function handlePreview(docId) {
  try {
    previewData.value = await previewDoc(docId);
    previewVisible.value = true;
  } catch (e) {
    ElMessage.error("预览失败：" + (e.response?.data?.detail || e.message));
  }
}

/** 查看版本历史：记录 currentDocId 供回滚操作使用 */
async function handleVersions(docId) {
  try {
    currentDocId.value = docId;
    versionData.value = await getVersions(docId);
    versionVisible.value = true;
  } catch (e) {
    ElMessage.error("获取版本失败：" + (e.response?.data?.detail || e.message));
  }
}

/** 查看向量详情：显示文档的向量切片信息 */
async function handleVectors(docId) {
  try {
    vectorData.value = await getVectors(docId);
    vectorVisible.value = true;
  } catch (e) {
    ElMessage.error("获取向量失败：" + (e.response?.data?.detail || e.message));
  }
}

/** 版本回滚：确认后将文档恢复到指定版本，并重新向量化 */
async function handleRollback(version) {
  try {
    await ElMessageBox.confirm(`确定回滚到版本 ${version}？`, "确认回滚", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    await rollbackDoc(currentDocId.value, version);
    ElMessage.success("回滚成功，正在重新向量化");
    versionVisible.value = false;
    await loadDocs();
  } catch (e) {
    if (e !== "cancel") {
      ElMessage.error("回滚失败：" + (e.response?.data?.detail || e.message));
    }
  }
}

/** 删除文档：二次确认后删除，同时清除关联的向量数据 */
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

/** 打开编辑弹窗：先加载文档内容，再显示编辑器 */
function openEdit(row) {
  editForm.value = { id: row.id, filename: row.filename, content: "" };
  previewDoc(row.id).then(data => {
    editForm.value.content = data.content || "";
    editVisible.value = true;
  }).catch(() => ElMessage.error("加载文档内容失败"));
}

/** 保存编辑：提交修改内容，后端会自动重新切片和向量化 */
async function handleEditSave() {
  editSaving.value = true;
  try {
    await editDoc(editForm.value.id, editForm.value.content);
    ElMessage.success("保存成功，正在重新向量化");
    editVisible.value = false;
    await loadDocs();
  } catch (e) {
    ElMessage.error("保存失败：" + (e.response?.data?.detail || e.message));
  }
  editSaving.value = false;
}

/** 批量上传：选择多个文件一次性上传到选定知识库 */
async function handleBatchUpload(event) {
  const files = event.target.files;
  if (!files.length || !selectedKB.value) return;
  try {
    await batchUpload(selectedKB.value, Array.from(files));
    ElMessage.success("批量上传成功");
    event.target.value = "";
    await loadDocs();
  } catch (e) {
    ElMessage.error("批量上传失败：" + (e.response?.data?.detail || e.message));
  }
}

/** 向量去重：清理重复的向量切片，释放存储空间 */
async function handleDedup() {
  if (!selectedKB.value) return;
  try {
    const result = await dedupVectors(selectedKB.value);
    ElMessage.success(`去重完成，删除了 ${result.removed || 0} 条重复向量`);
  } catch (e) {
    ElMessage.error("去重失败：" + (e.response?.data?.detail || e.message));
  }
}

/** 拆分预览：查看文档被切片后的各个片段内容 */
async function handleSplitPreview(docId) {
  try {
    splitData.value = await splitPreview(docId);
    splitVisible.value = true;
  } catch (e) {
    ElMessage.error("拆分预览失败：" + (e.response?.data?.detail || e.message));
  }
}

/**
 * 启动轮询：每 2 秒检查是否有文档正在处理
 * 仅在存在 parsing/indexing/uploading 状态的文档时才刷新列表
 * 避免不必要的请求
 */
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

.split-item {
  display: flex;
  gap: 10px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
  margin-bottom: 8px;
}

.split-index {
  color: #64b4ff;
  font-weight: 500;
  min-width: 30px;
}

.op-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.op-btns .el-button {
  margin-left: 0;
}

.split-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}
</style>
