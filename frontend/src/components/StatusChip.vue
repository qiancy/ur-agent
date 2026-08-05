<script setup lang="ts">
withDefaults(defineProps<{
  label: string
  variant?: 'default' | 'ok' | 'off' | 'warning' | 'danger'
}>(), {
  variant: 'default',
})
</script>

<template>
  <span class="status-chip" :class="`is-${variant}`">
    {{ label }}
  </span>
</template>

<style scoped>
.status-chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.4;
  white-space: nowrap;
  border: 1px solid transparent;
}
.status-chip.is-default {
  background: #f1f5f9;
  color: #475569;
  border-color: #e2e8f0;
}
.status-chip.is-ok {
  background: #ecfdf5;
  color: #047857;
  border-color: #a7f3d0;
}
.status-chip.is-off {
  background: #fef2f2;
  color: #b42318;
  border-color: #fecaca;
}
.status-chip.is-warning {
  background: #fffbeb;
  color: #b45309;
  border-color: #fde68a;
}
.status-chip.is-danger {
  background: #fef2f2;
  color: #b42318;
  border-color: #fecaca;
}
</style>
