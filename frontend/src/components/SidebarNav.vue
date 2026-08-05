<script setup lang="ts">
import { computed } from 'vue'
import type { WorkspaceNavItem } from '../workspace/types'

const props = defineProps<{
  currentView: string
  navItems: WorkspaceNavItem[]
}>()

const emit = defineEmits<{
  (e: 'navigate', view: string): void
}>()

const grouped = computed(() => {
  const groups: Record<string, WorkspaceNavItem[]> = {}
  for (const item of props.navItems) {
    if (!groups[item.group]) groups[item.group] = []
    groups[item.group].push(item)
  }
  return groups
})

function onNavigate(view: string) {
  if (view !== props.currentView) {
    emit('navigate', view)
  }
}
</script>

<template>
  <aside class="side">
    <div class="brand">
      <div class="mark">UA</div>
      <div class="brand-text">Uni-Resource Agent</div>
    </div>
    <nav class="nav">
      <template v-for="(items, groupKey) in grouped" :key="groupKey">
        <div class="nav-group">
          <div class="nav-group-label">{{ groupKey === 'observe' ? '观察' : groupKey === 'operate' ? '经营' : groupKey === 'ai' ? 'AI' : '空间治理' }}</div>
          <button
            v-for="item in items"
            :key="item.key"
            type="button"
            :data-view="item.key"
            :class="['nav-item', { active: currentView === item.key }]"
            :title="item.label"
            @click="onNavigate(item.key)"
          >
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path :d="item.icon" />
            </svg>
            <span class="nav-label">{{ item.label }}</span>
          </button>
        </div>
      </template>
    </nav>
  </aside>
</template>

<style scoped>
.side {
  background: #1E293B;
  color: #e7edf5;
  padding: 18px 12px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 100vh;
  overflow-y: auto;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 6px;
}
.mark {
  width: 32px;
  height: 32px;
  border-radius: 7px;
  background: #0f766e;
  color: #ffffff;
  display: grid;
  place-items: center;
  font-weight: 800;
  font-size: 13px;
  flex-shrink: 0;
}
.brand-text {
  font-weight: 800;
  font-size: 14px;
  line-height: 1.2;
  color: #f1f5f9;
}
.nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.nav-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.nav-group + .nav-group {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #334155;
}
.nav-group-label {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  padding: 0 12px 4px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  border: 0;
  color: #cbd5e1;
  background: transparent;
  text-align: left;
  padding: 10px 12px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: background 120ms, color 120ms;
}
.nav-item:hover {
  background: #334155;
  color: #f1f5f9;
}
.nav-item.active {
  background: #0f766e;
  color: #ffffff;
  font-weight: 700;
}
.nav-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  opacity: 0.85;
}
.nav-item.active .nav-icon {
  opacity: 1;
}
.nav-label {
  line-height: 1.3;
}
</style>
