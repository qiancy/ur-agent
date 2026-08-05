<script setup lang="ts">
interface Props {
  title: string
  subtitle?: string
  status?: string
}

withDefaults(defineProps<Props>(), {
  subtitle: '',
  status: '',
})
</script>

<template>
  <div class="page-head">
    <div>
      <h1 class="page-title">{{ title }}</h1>
      <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="status" class="page-status">{{ status }}</div>
    <div v-if="$slots.default" class="page-actions">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 750;
  line-height: 1.3;
  color: var(--ink, #17202a);
}
.page-subtitle {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--muted, #637083);
  line-height: 1.5;
}
.page-status {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--muted, #637083);
  padding: 6px 10px;
  border: 1px solid var(--line, #d8dee8);
  border-radius: 6px;
  background: var(--panel, #ffffff);
  white-space: nowrap;
}
.page-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  margin-left: auto;
}
@media (max-width: 768px) {
  .page-head {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  .page-actions {
    margin-left: 0;
    width: 100%;
  }
}
</style>
