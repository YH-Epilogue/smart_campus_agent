<template>
  <div class="message" :class="message.role">
    <div class="msg-avatar" :class="message.role">
      <template v-if="message.role === 'user'">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
        </svg>
      </template>
      <template v-else>
        <span style="font-size:12px;font-weight:700;letter-spacing:-0.5px">AI</span>
      </template>
    </div>
    <div class="msg-content">
      <div class="msg-bubble" :class="message.role" v-html="rendered"></div>
      <SourceCitation v-if="message.sources?.length" :sources="message.sources" />
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import SourceCitation from "./SourceCitation.vue";

const props = defineProps({ message: Object });

const rendered = computed(() => {
  return props.message.content
    .replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br>");
});
</script>

<style scoped>
.message {
  display: flex; gap: 14px; max-width: 80%;
  animation: msgIn 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative; z-index: 2; margin-bottom: 20px;
}
.message.user { flex-direction: row-reverse; margin-left: auto; }
.message.assistant { margin-right: auto; }

@keyframes msgIn {
  from { opacity: 0; transform: translateY(16px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.msg-avatar {
  width: 34px; height: 34px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.3s;
}
.msg-avatar:hover { transform: scale(1.1); }
.msg-avatar.user {
  background: rgba(0,242,254,0.08); border: 1px solid rgba(0,242,254,0.2);
  color: #00f2fe;
}
.msg-avatar.assistant {
  background: rgba(67,233,123,0.08); border: 1px solid rgba(67,233,123,0.2);
  color: #43e97b;
}

.msg-content { max-width: 75%; }

.msg-bubble {
  padding: 14px 18px; border-radius: 18px; font-size: 14px; line-height: 1.7;
  transition: transform 0.2s;
}
.msg-bubble:hover { transform: translateY(-1px); }
.msg-bubble.user {
  background: rgba(0,242,254,0.06); border: 1px solid rgba(0,242,254,0.12);
  color: #ffffff;
  border-bottom-right-radius: 4px;
}
.msg-bubble.assistant {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.85); backdrop-filter: blur(12px);
  border-bottom-left-radius: 4px;
}

.msg-bubble :deep(pre) {
  background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 12px; padding: 12px; margin: 10px 0; overflow-x: auto;
  font-size: 13px;
}
.msg-bubble :deep(code) {
  background: rgba(0,242,254,0.08); padding: 2px 6px; border-radius: 4px;
  font-size: 13px; color: #00f2fe;
}
.msg-bubble :deep(strong) { color: #00f2fe; }
.msg-bubble :deep(ul), .msg-bubble :deep(ol) { padding-left: 20px; margin: 8px 0; }
.msg-bubble :deep(li) { margin-bottom: 4px; }
</style>
