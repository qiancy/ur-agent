<script setup lang="ts">
import { computed, ref } from 'vue'
import { getToken, clearToken } from './api/client'
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

const authenticated = ref(getToken() !== null)
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
  authenticated.value = true
}

function onLoggedOut() {
  clearToken()
  localStorage.removeItem(CTX_KEY)
  authenticated.value = false
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
  <div class="shell">
    <template v-if="authenticated">
      <SidebarNav
        :current-view="currentView"
        :organization-name="ctx.organizationName"
        :ouid="ctx.ouid"
        :role="ctx.role"
        @navigate="currentView = $event"
        @logout="onLoggedOut"
      />
      <main class="main">
        <component :is="currentComponent" />
      </main>
    </template>
    <main v-else class="main">
      <LoginView @authenticated="onAuthenticated" />
    </main>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  background: var(--bg, #f4f6f8);
  color: var(--ink, #17202a);
  font-family: Inter, 'PingFang SC', 'Microsoft YaHei', Arial, sans-serif;
  display: grid;
  grid-template-columns: 236px 1fr;
}
.main {
  padding: 22px;
  min-width: 0;
}
@media (max-width: 980px) {
  .shell {
    grid-template-columns: 1fr;
  }
}
</style>
