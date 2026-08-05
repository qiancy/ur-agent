<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  label: string
  value: string | number
  trend?: string
  accent?: 'default' | 'warning' | 'danger' | 'success'
  align?: 'left' | 'right'
}>(), {
  trend: '',
  accent: 'default',
  align: 'right',
})

const accentClass = computed(() => {
  if (props.accent === 'warning') return 'is-warning'
  if (props.accent === 'danger') return 'is-danger'
  if (props.accent === 'success') return 'is-success'
  return ''
})
</script>

<template>
  <div class="metric-tile" :class="accentClass">
    <span class="metric-label">{{ label }}</span>
    <span class="metric-value" :style="{ textAlign: align }">{{ value }}</span>
    <span v-if="trend" class="metric-trend" :class="accentClass">{{ trend }}</span>
  </div>
</template>

<style scoped>
.metric-tile {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px;
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
  background: var(--panel, #ffffff);
  min-width: 0;
}
.metric-label {
  font-size: 12px;
  color: var(--muted, #637083);
  line-height: 1.4;
}
.metric-value {
  font-size: 22px;
  font-weight: 750;
  color: var(--ink, #17202a);
  line-height: 1.2;
  letter-spacing: -0.01em;
}
.metric-trend {
  font-size: 12px;
  font-weight: 600;
  color: var(--muted, #637083);
}
.metric-trend.is-warning {
  color: #b45309;
}
.metric-trend.is-danger {
  color: #b42318;
}
.metric-trend.is-success {
  color: #047857;
}
.metric-tile.is-warning .metric-value {
  color: #b45309;
}
.metric-tile.is-danger .metric-value {
  color: #b42318;
}
.metric-tile.is-success .metric-value {
  color: #047857;
}
</style>
