<template>
  <el-upload
    drag
    :auto-upload="false"
    :on-change="handleChange"
    :file-list="fileList"
    accept=".pdf,.docx,.doc,.txt,.md"
  >
    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
    <div class="el-upload__text">拖拽文件到此处，或 <em>点击上传</em></div>
    <template #tip>
      <div class="el-upload__tip">支持 PDF、Word、TXT、Markdown 格式</div>
    </template>
  </el-upload>
  <el-button type="primary" @click="handleUpload" :loading="uploading" :disabled="!fileList.length" style="margin-top: 12px">
    开始上传
  </el-button>
</template>

<script setup>
/**
 * FileUploader - 文件上传组件
 * 职责：拖拽/点击上传文档到指定知识库
 * 支持格式：PDF、Word、TXT、Markdown
 * 流程：选择文件 → 点击上传按钮 → 调用 uploadDoc API → 通知父组件刷新
 * 注意：每次只上传单个文件（覆盖选择）
 */
import { ref } from "vue";
import { uploadDoc } from "../../api/doc";
import { ElMessage } from "element-plus";

const props = defineProps({ kbId: Number });    // 目标知识库 ID
const emit = defineEmits(["uploaded"]);         // 上传成功事件，通知父组件刷新

const fileList = ref([]);     // 已选择的文件列表（Element Upload 格式）
const uploading = ref(false); // 上传中状态

/** 文件选择回调：替换为最新选择的文件 */
function handleChange(file) {
  fileList.value = [file];
}

/** 执行上传：调用 API 上传文件到指定知识库，成功后清空列表并通知父组件 */
async function handleUpload() {
  if (!fileList.value.length) return;
  uploading.value = true;
  try {
    await uploadDoc(props.kbId, fileList.value[0].raw);
    ElMessage.success("上传成功");
    fileList.value = [];
    emit("uploaded");
  } catch (e) {
    ElMessage.error("上传失败：" + e.message);
  } finally {
    uploading.value = false;
  }
}
</script>
