<script setup lang="ts">
import { computed } from 'vue'
import type { UserOrganization } from '../api/auth'
import SpaceMenu from './SpaceMenu.vue'

const props = defineProps<{
  personName: string
  puid: string
  organizationName: string
  ouid: string
  orgType: string
  role: string
  organizations: UserOrganization[]
}>()

const emit = defineEmits<{
  (e: 'switch-organization', ouid: string): void
  (e: 'logout'): void
  (e: 'navigate-space-menu', action: string): void
}>()

function onSwitch(event: Event) {
  const target = event.target as HTMLSelectElement
  const ouid = target.value
  if (ouid && ouid !== props.ouid) {
    emit('switch-organization', ouid)
  }
}

const orgLabel = computed(() => props.organizationName || props.ouid)
</script>

<template>
  <header class="app-header" data-test="app-header">
    <div class="brand">
      <div class="mark">UA</div>
      <div class="brand-name">Uni-Resource Agent</div>
    </div>

    <div class="ctx-card">
      <span class="ctx-name" :title="orgLabel">{{ orgLabel }}</span>
      <span class="ctx-chip">{{ orgType }}</span>
      <span class="ctx-chip">{{ role }}</span>
      <span class="ctx-meta">{{ puid }}</span>
      <select
        class="ctx-switch"
        data-test="org-switch"
        :value="ouid"
        aria-label="切换组织"
        @change="onSwitch"
      >
        <option v-for="org in organizations" :key="org.ouid" :value="org.ouid">
          {{ org.name }} ({{ org.type }})
        </option>
      </select>
    </div>

    <div class="actions">
      <div class="user">
        <span class="user-name">{{ personName }}</span>
        <span class="user-meta">{{ role }} · {{ puid }}</span>
      </div>
      <SpaceMenu :role="role" :org-type="orgType" @select="(action) => emit('navigate-space-menu', action)" />
      <button
        type="button"
        class="btn logout"
        data-test="header-logout"
        @click="emit('logout')"
      >
        退出登录
      </button>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 30;
  background: var(--panel, #ffffff);
  border-bottom: 1px solid var(--line, #d8dee8);
  padding: 10px 22px;
  display: flex;
  align-items: center;
  gap: 18px;
  min-height: 56px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.mark {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: #243447;
  color: #ffffff;
  display: grid;
  place-items: center;
  font-weight: 800;
  font-size: 14px;
}
.brand-name {
  font-weight: 800;
  font-size: 15px;
  color: var(--ink, #17202a);
}
.ctx-card {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
  padding: 6px 12px;
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
  background: #f8fafc;
}
.ctx-name {
  font-weight: 700;
  font-size: 14px;
  color: var(--ink, #17202a);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ctx-chip {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  background: #eef2ff;
  color: #4338ca;
  border: 1px solid #c7d2fe;
  white-space: nowrap;
}
.ctx-meta {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--muted, #637083);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 120px;
}
.ctx-switch {
  flex-shrink: 0;
  border: 1px solid var(--line, #d8dee8);
  background: #ffffff;
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 13px;
  color: var(--ink, #17202a);
  max-width: 180px;
}
.actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-right: 10px;
  border-right: 1px solid var(--line, #d8dee8);
}
.user-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--ink, #17202a);
}
.user-meta {
  font-size: 12px;
  color: var(--muted, #637083);
  white-space: nowrap;
}
.logout {
  border: 1px solid var(--line, #d8dee8);
  background: #ffffff;
  color: var(--ink, #17202a);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 13px;
  cursor: pointer;
}
.logout:hover {
  background: #f4f6f8;
}

@media (max-width: 768px) {
  .app-header {
    flex-wrap: wrap;
    gap: 10px;
    padding: 10px 14px;
  }
  .ctx-card {
    order: 10;
    flex: 1 1 100%;
    padding: 8px 10px;
  }
  .ctx-meta {
    display: none;
  }
  .ctx-switch {
    max-width: 140px;
  }
  .actions {
    margin-left: auto;
  }
}
</style>
