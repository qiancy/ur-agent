<script setup lang="ts">
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
</script>

<template>
  <header class="app-header" data-test="app-header">
    <div class="brand">
      <div class="mark">UA</div>
      <div class="brand-text">
        <div class="brand-name">Uni-Resource Agent</div>
        <div class="brand-meta">{{ organizationName }}</div>
      </div>
    </div>

    <div class="org-ctx">
      <span class="chip">{{ orgType }}</span>
      <span class="ouid">{{ ouid }}</span>
      <select
        class="org-switch"
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

    <div class="quick">
      <SpaceMenu :role="role" :org-type="orgType" @select="(action) => emit('navigate-space-menu', action)" />
    </div>

    <div class="user">
      <div class="user-name">{{ personName }}</div>
      <div class="user-meta">
        {{ puid }} · {{ role }}
      </div>
    </div>

    <button
      type="button"
      class="logout"
      data-test="header-logout"
      @click="emit('logout')"
    >
      退出登录
    </button>
  </header>
</template>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 30;
  background: var(--panel, #ffffff);
  border-bottom: 1px solid var(--line, #d8dee8);
  padding: 12px 22px;
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
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
}
.brand-meta {
  color: var(--muted, #637083);
  font-size: 12px;
}
.org-ctx {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.chip {
  border: 1px solid var(--line, #d8dee8);
  border-radius: 999px;
  padding: 5px 10px;
  color: var(--muted, #637083);
  font-size: 12px;
  background: #fbfcfe;
}
.ouid {
  color: var(--muted, #637083);
  font-size: 12px;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.org-switch {
  border: 1px solid var(--line, #d8dee8);
  background: #ffffff;
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 13px;
  color: var(--ink, #17202a);
  max-width: 200px;
}
.quick {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}
.user {
  text-align: right;
  min-width: 0;
}
.user-name {
  font-size: 13px;
  font-weight: 700;
}
.user-meta {
  color: var(--muted, #637083);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 180px;
}
.logout {
  border: 1px solid var(--line, #d8dee8);
  background: #ffffff;
  color: var(--ink, #17202a);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 12px;
  cursor: pointer;
}
.logout:hover {
  background: #f4f6f8;
}
@media (max-width: 980px) {
  .app-header {
    align-items: stretch;
    flex-direction: column;
  }
  .quick {
    margin-left: 0;
  }
  .user {
    text-align: left;
  }
}
</style>
