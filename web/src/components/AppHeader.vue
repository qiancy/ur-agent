<script setup lang="ts">
import { computed } from 'vue'
import type { UserOrganization } from '../api/auth'

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
  (e: 'ask', message: string): void
}>()

const aiEnabled = computed(() => props.orgType === 'ecommerce')

function onSwitch(event: Event) {
  const target = event.target as HTMLSelectElement
  const ouid = target.value
  if (ouid && ouid !== props.ouid) {
    emit('switch-organization', ouid)
  }
}

function onAsk(event: Event) {
  if (!aiEnabled) return
  const input = event.target as HTMLInputElement
  const message = input.value.trim()
  if (!message) return
  emit('ask', message)
  input.value = ''
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

    <div class="ai">
      <input
        data-test="header-ai"
        type="text"
        :disabled="!aiEnabled"
        :placeholder="
          aiEnabled
            ? '查询当前空间的库存、低库存、销售收入、采购支出'
            : 'AI 查询仅 ecommerce 空间可用'
        "
        @keyup.enter="onAsk"
      />
      <button
        type="button"
        class="btn primary"
        data-test="header-ai-send"
        :disabled="!aiEnabled"
        @click="onAsk"
      >
        问 AI
      </button>
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
.ai {
  flex: 1;
  min-width: 220px;
  max-width: 420px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
}
.ai input {
  border: 1px solid var(--line, #d8dee8);
  background: #ffffff;
  border-radius: 6px;
  padding: 9px 11px;
  font-size: 13px;
}
.ai input:disabled {
  background: #f4f6f8;
  color: var(--muted, #637083);
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
.btn.primary {
  background: var(--teal, #0f766e);
  color: #ffffff;
  border-color: var(--teal, #0f766e);
}
.btn:disabled {
  opacity: 0.6;
  cursor: default;
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
  .ai {
    max-width: none;
    width: 100%;
  }
  .user {
    text-align: left;
  }
}
</style>
