<script setup lang="ts">
withDefaults(defineProps<{
  title?: string
  actions?: Array<{ label: string; onClick: () => void; primary?: boolean }>
}>(), {
  title: '',
  actions: () => [],
})
</script>

<template>
  <div class="command-bar">
    <div class="command-left">
      <h3 v-if="title" class="command-title">{{ title }}</h3>
      <slot name="filters" />
    </div>
    <div v-if="actions.length" class="command-actions">
      <button
        v-for="(action, idx) in actions"
        :key="idx"
        type="button"
        :class="['btn', { primary: action.primary }]"
        @click="action.onClick"
      >
        {{ action.label }}
      </button>
      <slot name="actions" />
    </div>
  </div>
</template>

<style scoped>
.command-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.command-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}
.command-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--ink, #17202a);
  line-height: 1.3;
}
.command-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.btn {
  border: 1px solid var(--line, #d8dee8);
  background: var(--panel, #ffffff);
  color: var(--ink, #17202a);
  border-radius: 6px;
  padding: 8px 14px;
  font-weight: 650;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}
.btn.primary {
  background: var(--teal, #0f766e);
  color: #ffffff;
  border-color: var(--teal, #0f766e);
}
.btn.primary:hover {
  background: #115e59;
}
.btn:hover {
  background: #f4f6f8;
}
</style>
