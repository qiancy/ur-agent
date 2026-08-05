<script setup lang="ts">
withDefaults(defineProps<{
  title?: string
  items?: string[]
  variant?: 'insight' | 'warning'
}>(), {
  title: 'AI 经营摘要',
  items: () => [],
  variant: 'insight',
})
</script>

<template>
  <div class="ai-card" :class="`is-${variant}`">
    <div class="ai-head">
      <span class="ai-title">{{ title }}</span>
      <span class="ai-badge">只读</span>
    </div>
    <ul v-if="items.length" class="ai-list">
      <li v-for="(item, idx) in items" :key="idx" class="ai-item">
        {{ item }}
      </li>
    </ul>
    <p v-else class="ai-empty">暂无摘要</p>
  </div>
</template>

<style scoped>
.ai-card {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
  padding: 14px;
  background: var(--panel, #ffffff);
}
.ai-card.is-warning {
  border-left: 3px solid #f59e0b;
}
.ai-card.is-insight {
  border-left: 3px solid var(--teal, #0f766e);
}
.ai-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}
.ai-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--ink, #17202a);
}
.ai-badge {
  font-size: 11px;
  font-weight: 600;
  color: var(--muted, #637083);
  padding: 2px 8px;
  border-radius: 999px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
}
.ai-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ai-item {
  font-size: 13px;
  color: #334155;
  line-height: 1.5;
  padding-left: 14px;
  position: relative;
}
.ai-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--teal, #0f766e);
}
.ai-card.is-warning .ai-item::before {
  background: #f59e0b;
}
.ai-empty {
  margin: 0;
  font-size: 13px;
  color: var(--muted, #637083);
}
</style>
