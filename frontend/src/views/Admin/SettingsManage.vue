<template>
  <div class="page-container">
    <div class="page-header">
      <h2>系统配置</h2>
      <el-button type="primary" @click="handleSave" :loading="saving">保存配置</el-button>
    </div>

    <el-card v-loading="loading">
      <el-form :model="form" label-width="140px" style="max-width: 600px;">
        <el-divider content-position="left">检索参数</el-divider>
        <el-form-item label="chunk_size">
          <el-input-number v-model="form.chunk_size" :min="100" :max="2000" :step="50" />
          <span class="form-hint">文本切片大小（字符）</span>
        </el-form-item>
        <el-form-item label="chunk_overlap">
          <el-input-number v-model="form.chunk_overlap" :min="0" :max="200" :step="10" />
          <span class="form-hint">切片重叠长度</span>
        </el-form-item>
        <el-form-item label="top_k">
          <el-input-number v-model="form.top_k" :min="1" :max="20" />
          <span class="form-hint">检索返回结果数</span>
        </el-form-item>
        <el-form-item label="min_score">
          <el-input-number v-model="form.min_score" :min="0" :max="1" :step="0.05" :precision="2" />
          <span class="form-hint">相似度阈值</span>
        </el-form-item>

        <el-divider content-position="left">LLM 配置</el-divider>
        <el-form-item label="llm_model">
          <el-input v-model="form.llm_model" />
          <span class="form-hint">大语言模型名称</span>
        </el-form-item>

        <el-divider content-position="left">对话参数</el-divider>
        <el-form-item label="max_context_turns">
          <el-input-number v-model="form.max_context_turns" :min="1" :max="20" />
          <span class="form-hint">多轮对话上下文轮数</span>
        </el-form-item>
        <el-form-item label="max_answer_length">
          <el-input-number v-model="form.max_answer_length" :min="100" :max="5000" :step="100" />
          <span class="form-hint">回答最大字数</span>
        </el-form-item>

        <el-divider content-position="left">快捷提问</el-divider>
        <el-form-item label="quick_questions">
          <div style="width: 100%;">
            <div v-for="(q, i) in form.quick_questions" :key="i" style="display: flex; gap: 8px; margin-bottom: 8px;">
              <el-input v-model="form.quick_questions[i]" placeholder="输入快捷问题" />
              <el-button type="danger" size="small" @click="form.quick_questions.splice(i, 1)">删除</el-button>
            </div>
            <el-button size="small" @click="form.quick_questions.push('')">+ 添加问题</el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
/**
 * SettingsManage - 系统配置管理页面
 * 职责：配置 RAG 检索参数、LLM 模型、对话参数、快捷提问
 * 权限：仅 admin 可访问
 * 参数分组：检索参数 / LLM 配置 / 对话参数 / 快捷提问
 * 注意：当前 GET/PUT 无角色限制（已知安全问题，待修复）
 */
import { ref, onMounted } from "vue";
import { getSettings, updateSettings } from "../../api/settings";
import { ElMessage } from "element-plus";

const loading = ref(false);  // 加载配置中
const saving = ref(false);   // 保存配置中

/** 配置表单：包含所有可配置项及其默认值 */
const form = ref({
  chunk_size: 500,           // 文本切片大小（字符）
  chunk_overlap: 50,         // 切片重叠长度
  top_k: 5,                  // 检索返回结果数
  min_score: 0.3,            // 相似度阈值
  llm_model: "deepseek-chat", // 大语言模型名称
  max_context_turns: 10,     // 多轮对话上下文轮数
  max_answer_length: 2000,   // 回答最大字数
  quick_questions: [],       // 快捷提问列表
});

/** 从后端加载当前配置，覆盖默认值 */
async function loadSettings() {
  loading.value = true;
  try {
    const data = await getSettings();
    Object.keys(form.value).forEach(k => {
      if (data[k] !== undefined) form.value[k] = data[k];
    });
  } catch (e) {
    ElMessage.error("加载配置失败");
  }
  loading.value = false;
}

/** 保存配置到后端 */
async function handleSave() {
  saving.value = true;
  try {
    await updateSettings(form.value);
    ElMessage.success("配置已保存");
  } catch (e) {
    ElMessage.error("保存失败：" + (e.response?.data?.detail || e.message));
  }
  saving.value = false;
}

onMounted(loadSettings);
</script>

<style scoped>
.page-container { padding: 24px 32px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { font-size: 18px; font-weight: 600; color: #f0ebe5; }
.form-hint { margin-left: 12px; font-size: 12px; color: rgba(255,255,255,0.3); }
</style>
