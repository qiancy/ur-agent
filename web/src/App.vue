<script setup lang="ts">
import { computed, ref } from 'vue'
import { getToken, clearToken } from './api/client'
import { isAuthenticated, setAuthenticated } from './api/session'
import type { SellerLoginResult } from './api/seller'
import LoginView from './views/LoginView.vue'
import WorkbenchView from './views/WorkbenchView.vue'
import StockView from './views/StockView.vue'
import MovementsView from './views/MovementsView.vue'
import SummaryView from './views/SummaryView.vue'
import ChatView from './views/ChatView.vue'
import SidebarNav from './components/SidebarNav.vue'

const CTX_KEY = 'unires_ctx'

interface AppContext {
  organizationName: string
  ouid: string
  role: string
}

setAuthenticated(getToken() !== null)

const authenticated = isAuthenticated
const currentView = ref('workbench')

function loadCtx(): AppContext {
  try {
    const raw = localStorage.getItem(CTX_KEY)
    if (raw) return JSON.parse(raw) as AppContext
  } catch {
    /* ignore corrupt ctx */
  }
  return { organizationName: '', ouid: '', role: '' }
}

const ctx = ref<AppContext>(loadCtx())

function onAuthenticated(result: SellerLoginResult) {
  const nextCtx = {
    organizationName: result.organization.name,
    ouid: result.organization.ouid,
    role: result.membership.role,
  }
  ctx.value = nextCtx
  localStorage.setItem(CTX_KEY, JSON.stringify(nextCtx))
  currentView.value = 'workbench'
  setAuthenticated(true)
}

function onLoggedOut() {
  clearToken()
  localStorage.removeItem(CTX_KEY)
  setAuthenticated(false)
}

const currentComponent = computed(() => {
  switch (currentView.value) {
    case 'stock':
      return StockView
    case 'movements':
      return MovementsView
    case 'summary':
      return SummaryView
    case 'chat':
      return ChatView
    default:
      return WorkbenchView
  }
})
</script>

<template>
  <div v-if="authenticated" class="shell authed">
    <SidebarNav
      :current-view="currentView"
      :organization-name="ctx.organizationName"
      :ouid="ctx.ouid"
      :role="ctx.role"
      @navigate="currentView = $event"
      @logout="onLoggedOut"
    />
    <main class="main">
      <component :is="currentComponent" @logged-out="onLoggedOut" />
    </main>
  </div>
  <div v-else class="auth-area" data-test="auth-area">
    <LoginView @authenticated="onAuthenticated" />
  </div>
</template>

<style scoped>
.auth-area {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--bg, #f4f6f8);
  color: var(--ink, #17202a);
  font-family: Inter, 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
}
.shell {
  min-height: 100vh;
  background: var(--bg, #f4f6f8);
  color: var(--ink, #17202a);
  font-family: Inter, 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
  display: grid;
  grid-template-columns: 1fr;
}
.shell.authed {
  grid-template-columns: 236px 1fr;
}
.main {
  padding: 22px;
  min-width: 0;
}
@media (max-width: 980px) {
  .shell.authed {
    grid-template-columns: 1fr;
  }
}
</style>
