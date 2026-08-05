<script setup lang="ts">
withDefaults(defineProps<{
  type?: 'guided' | 'filtered' | 'readonly'
  title?: string
  description?: string
  actionLabel?: string
  onAction?: () => void
}>(), {
  type: 'readonly',
  title: '',
  description: '',
  actionLabel: '',
  onAction: undefined,
})
</script>

<template>
  <div class="empty-state" :class="`is-${type}`">
    <div class="empty-icon" aria-hidden="true">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    </div>
    <p class="empty-title">{{ title }}</p>
    <p class="empty-desc">{{ description }}</p>
    <button
      v-if="type === 'guided' && actionLabel && onAction"
      type="button"
      class="btn primary"
      @click="onAction"
    >
      {{ actionLabel }}
    </button>
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px 24px;
  text-align: center;
  border: 1px dashed var(--line, #d8dee8);
  border-radius: 8px;
  background: #fafbfc;
}
.empty-icon {
  color: var(--muted, #637083);
  opacity: 0.6;
}
.empty-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--ink, #17202a);
}
.empty-desc {
  margin: 0;
  font-size: 13px;
  color: var(--muted, #637083);
  max-width: 360px;
  line-height: 1.5;
}
.btn {
  margin-top: 8px;
  border: 1px solid var(--line, #d8dee8);
  background: var(--panel, #ffffff);
  color: var(--ink, #17202a);
  border-radius: 6px;
  padding: 8px 16px;
  font-weight: 650;
  font-size: 13px;
  cursor: pointer;
}
.btn.primary {
  background: var(--teal, #0f766e);
  color: #ffffff;
  border-color: var(--teal, #0f766e);
}
.btn.primary:hover {
  background: #115e59;
}
</style>
