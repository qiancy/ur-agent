<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  currentView: string
  orgType: string
}>()

const emit = defineEmits<{
  (e: 'navigate', view: string): void
}>()

interface NavItem {
  key: string
  label: string
  icon: string
}

const sellerItems: NavItem[] = [
  { key: 'workbench', label: '工作台', icon: 'M3 12l2-2m7-7l7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { key: 'products', label: '商品', icon: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4' },
  { key: 'stock', label: '库存', icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' },
  { key: 'movements', label: '库存流水', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
  { key: 'summary', label: '经营摘要', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
  { key: 'chat', label: 'Seller AI', icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-4.272C3.512 14.461 3 13.762 3 13c0-4.418 4.03-8 9-8s9 3.582 9 8z' },
]

const genericItems: NavItem[] = [
  { key: 'overview', label: '空间总览', icon: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' },
  { key: 'resources', label: '资源', icon: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4' },
  { key: 'persons', label: '人员', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z' },
  { key: 'timeline', label: '时间线', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
  { key: 'flows', label: '多维观察', icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
]

const navItems = computed<NavItem[]>(() =>
  props.orgType === 'ecommerce' ? sellerItems : genericItems,
)

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
      <button
        v-for="item in navItems"
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
  display: grid;
  gap: 4px;
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
