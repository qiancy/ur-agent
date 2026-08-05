<script setup lang="ts">
withDefaults(defineProps<{
  title?: string
  padding?: string
  testId?: string
}>(), {
  title: '',
  padding: '16px',
  testId: '',
})
</script>

<template>
  <section
    class="section-card"
    :data-test="testId || undefined"
    :style="{ padding }"
  >
    <div v-if="title || $slots.filters" class="section-head">
      <h2 v-if="title" class="section-title">{{ title }}</h2>
      <div v-if="$slots.filters" class="section-filters">
        <slot name="filters" />
      </div>
    </div>
    <div class="section-body">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.section-card {
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--line, #d8dee8);
}
.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--ink, #17202a);
  line-height: 1.3;
}
.section-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.section-body {
  min-width: 0;
  padding: 16px;
}
</style>
