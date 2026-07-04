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
import { ref } from "vue";
import { uploadDoc } from "../../api/doc";
import { ElMessage } from "element-plus";

const props = defineProps({ kbId: Number });
const emit = defineEmits(["uploaded"]);

const fileList = ref([]);
const uploading = ref(false);

function handleChange(file) {
  fileList.value = [file];
}

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
