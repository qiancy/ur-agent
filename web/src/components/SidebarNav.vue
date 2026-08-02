<script setup lang="ts">
const props = defineProps<{
  currentView: string
}>()

const emit = defineEmits<{
  (e: 'navigate', view: string): void
}>()

const navItems = [
  { key: 'workbench', label: '经营工作台' },
  { key: 'stock', label: '库存' },
  { key: 'movements', label: '库存流水' },
  { key: 'summary', label: '经营摘要' },
  { key: 'chat', label: 'Seller AI' },
]

function onNavigate(view: string) {
  if (view !== props.currentView) {
    emit('navigate', view)
  }
}
</script>

<template>
  <aside class="side">
    <div class="brand">
      Uni-Resource Agent
    </div>
    <nav class="nav">
      <button
        v-for="item in navItems"
        :key="item.key"
        type="button"
        :data-view="item.key"
        :class="['nav-item', { active: currentView === item.key }]"
        @click="onNavigate(item.key)"
      >
        {{ item.label }}
      </button>
    </nav>
  </aside>
</template>

<style scoped>
.side {
  background: #16202e;
  color: #e7edf5;
  padding: 22px 16px;
  display: flex;
  flex-direction: column;
  gap: 22px;
}
.brand {
  font-weight: 800;
  font-size: 18px;
  line-height: 1.2;
}
.brand span {
  display: block;
  color: #9fb3ca;
  font-size: 12px;
  font-weight: 500;
  margin-top: 6px;
}
.nav {
  display: grid;
  gap: 6px;
}
.nav-item {
  border: 0;
  color: #dbe5f0;
  background: transparent;
  text-align: left;
  padding: 11px 12px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}
.nav-item.active {
  background: #233247;
  color: #ffffff;
  border-left: 3px solid #45b8ac;
}
</style>
