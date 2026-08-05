<script setup lang="ts">
withDefaults(defineProps<{
  time: string
  label?: string
}>(), {
  label: '最近更新',
})
</script>

<template>
  <span class="snapshot-line">
    <span class="snapshot-label">{{ label }}</span>
    <span class="snapshot-time">{{ time }}</span>
  </span>
</template>

<style scoped>
.snapshot-line {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--muted, #637083);
  line-height: 1.4;
}
.snapshot-label {
  color: var(--muted, #637083);
}
.snapshot-time {
  font-weight: 600;
  color: #475569;
  font-variant-numeric: tabular-nums;
}
</style>
