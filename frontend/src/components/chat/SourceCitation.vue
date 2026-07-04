<template>
  <div class="sources" v-if="sources.length">
    <el-collapse>
      <el-collapse-item>
        <template #title>
          <div class="source-toggle">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <span>参考来源 ({{ sources.length }})</span>
          </div>
        </template>
        <div v-for="(s, i) in sources" :key="i" class="source-card">
          <div class="source-meta">
            <span class="source-score">{{ (s.score * 100).toFixed(0) }}%</span>
            <span class="source-label">相关度</span>
          </div>
          <div class="source-text">{{ s.content }}</div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
defineProps({ sources: { type: Array, default: () => [] } });
</script>

<style scoped>
.sources { margin-top: 10px; }
.sources :deep(.el-collapse-item__header) {
  background: transparent !important; border: none !important;
  color: rgba(255,255,255,0.35) !important; font-size: 12px;
  height: 30px; line-height: 30px; padding: 0 !important;
}
.sources :deep(.el-collapse-item__wrap) {
  background: transparent !important; border: none !important;
}
.source-toggle {
  display: flex; align-items: center; gap: 6px;
}
.source-toggle:hover { color: rgba(0,242,254,0.6); }
.source-card {
  padding: 10px 14px; margin: 5px 0;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px; font-size: 12px; backdrop-filter: blur(10px);
}
.source-meta { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.source-score { color: #00f2fe; font-weight: 600; font-size: 13px; }
.source-label { color: rgba(255,255,255,0.3); font-size: 11px; }
.source-text { color: rgba(255,255,255,0.5); line-height: 1.5; }
</style>
