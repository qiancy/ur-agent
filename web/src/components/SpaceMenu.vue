<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  role: string
  orgType: string
}>()

const emit = defineEmits<{
  (e: 'select', action: string): void
}>()

const open = ref(false)

const isOwnerOrAdmin = computed(
  () => props.role === 'owner' || props.role === 'admin',
)

const isPersonal = computed(() => props.orgType === 'personal')

interface MenuItem {
  key: string
  label: string
}

const items = computed<MenuItem[]>(() => {
  const list: MenuItem[] = [
    { key: 'manage', label: '管理空间' },
    { key: 'create', label: '创建空间' },
    { key: 'join', label: '加入空间' },
  ]
  if (isOwnerOrAdmin.value) {
    list.push({ key: 'review', label: '审核申请' })
  }
  if (!isPersonal.value) {
    list.push({ key: 'leave', label: '退出空间' })
  }
  return list
})

function onSelect(action: string) {
  open.value = false
  emit('select', action)
}
</script>

<template>
  <div class="space-menu" data-test="space-menu">
    <button
      type="button"
      class="btn"
      data-test="space-menu-toggle"
      aria-haspopup="menu"
      :aria-expanded="open"
      @click="open = !open"
    >
      空间
    </button>
    <div v-if="open" class="menu" role="menu" data-test="space-menu-panel">
      <button
        v-for="item in items"
        :key="item.key"
        type="button"
        class="menu-item"
        role="menuitem"
        :data-test="`space-menu-item-${item.key}`"
        @click="onSelect(item.key)"
      >
        {{ item.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.space-menu {
  position: relative;
}
.btn {
  border: 1px solid var(--line, #d8dee8);
  background: var(--panel, #ffffff);
  color: var(--ink, #17202a);
  border-radius: 6px;
  padding: 9px 14px;
  font-weight: 650;
  font-size: 13px;
  cursor: pointer;
}
.menu {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  min-width: 150px;
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
  box-shadow: 0 10px 28px rgba(22, 32, 46, 0.14);
  padding: 6px;
  display: grid;
  gap: 2px;
  z-index: 40;
}
.menu-item {
  border: 0;
  background: transparent;
  color: var(--ink, #17202a);
  text-align: left;
  padding: 9px 11px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}
.menu-item:hover {
  background: #f4f6f8;
}
</style>
