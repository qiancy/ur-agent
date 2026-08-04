<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getToken, clearToken } from './api/client'
import { isAuthenticated, setAuthenticated } from './api/session'
import type { SellerLoginResult } from './api/seller'
import {
  myOrganizations,
  switchOrganization,
  type UserOrganization,
} from './api/auth'
import LoginView from './views/LoginView.vue'
import WorkbenchView from './views/WorkbenchView.vue'
import StockView from './views/StockView.vue'
import MovementsView from './views/MovementsView.vue'
import SummaryView from './views/SummaryView.vue'
import ChatView from './views/ChatView.vue'
import ProductsView from './views/ProductsView.vue'
import GenericSpaceView from './views/GenericSpaceView.vue'
import PlaceholderView from './views/PlaceholderView.vue'
import SidebarNav from './components/SidebarNav.vue'
import AppHeader from './components/AppHeader.vue'

const CTX_KEY = 'unires_ctx'

interface AppContext {
  personName: string
  puid: string
  organizationName: string
  ouid: string
  orgType: string
  role: string
}

interface Exchange {
  question: string
  answer: string
}

setAuthenticated(getToken() !== null)

const authenticated = isAuthenticated
const currentView = ref('workbench')
const organizations = ref<UserOrganization[]>([])
const headerExchange = ref<Exchange | null>(null)
const placeholderMessage = ref('功能即将开放')

function loadCtx(): AppContext {
  try {
    const raw = localStorage.getItem(CTX_KEY)
    if (raw) return JSON.parse(raw) as AppContext
  } catch {
    /* ignore corrupt ctx */
  }
  return {
    personName: '',
    puid: '',
    organizationName: '',
    ouid: '',
    orgType: '',
    role: '',
  }
}

const ctx = ref<AppContext>(loadCtx())

const isEcommerce = computed(() => ctx.value.orgType === 'ecommerce')

function defaultViewFor(orgType: string): string {
  return orgType === 'ecommerce' ? 'workbench' : 'overview'
}

async function refreshOrganizations() {
  try {
    organizations.value = await myOrganizations()
  } catch {
    organizations.value = []
  }
}

function applyContext(result: SellerLoginResult) {
  if (!result.organization || !result.membership) {
    return
  }
  const nextCtx: AppContext = {
    personName: result.person.name,
    puid: result.person.puid,
    organizationName: result.organization.name,
    ouid: result.organization.ouid,
    orgType: result.organization.type,
    role: result.membership.role,
  }
  ctx.value = nextCtx
  localStorage.setItem(CTX_KEY, JSON.stringify(nextCtx))
}

async function onAuthenticated(result: SellerLoginResult) {
  applyContext(result)
  if (!result.organization || !result.access_token) {
    setAuthenticated(false)
    return
  }
  currentView.value = defaultViewFor(result.organization.type)
  headerExchange.value = null
  setAuthenticated(true)
  await refreshOrganizations()
}

async function onSwitchOrganization(ouid: string) {
  if (ouid === ctx.value.ouid) return
  try {
    const result = await switchOrganization(ouid)
    applyContext(result)
    // Clamp to a legal view key for the new organization type.
    currentView.value = result.organization
      ? defaultViewFor(result.organization.type)
      : currentView.value
  } catch {
    // token/ctx unchanged; keep the old selection via the dropdown value
    await refreshOrganizations()
    return
  }
  headerExchange.value = null
  placeholderMessage.value = '功能即将开放'
  await refreshOrganizations()
}

function onLoggedOut() {
  clearToken()
  localStorage.removeItem(CTX_KEY)
  setAuthenticated(false)
  currentView.value = 'workbench'
}

function onNavigate(view: string) {
  currentView.value = view
}

function onSpaceMenuAction(_action: string) {
  placeholderMessage.value = '功能即将开放'
  currentView.value = 'placeholder'
}

const currentComponent = computed(() => {
  const view = currentView.value
  if (view === 'placeholder') return PlaceholderView
  if (isEcommerce.value) {
    switch (view) {
      case 'stock':
        return StockView
      case 'movements':
        return MovementsView
      case 'summary':
        return SummaryView
      case 'chat':
        return ChatView
      case 'products':
        return ProductsView
      default:
        return WorkbenchView
    }
  }
  return GenericSpaceView
})

onMounted(() => {
  if (getToken()) {
    refreshOrganizations()
  }
})
</script>

<template>
  <div v-if="authenticated" class="shell authed">
    <AppHeader
      :person-name="ctx.personName"
      :puid="ctx.puid"
      :organization-name="ctx.organizationName"
      :ouid="ctx.ouid"
      :org-type="ctx.orgType"
      :role="ctx.role"
      :organizations="organizations"
      @switch-organization="onSwitchOrganization"
      @logout="onLoggedOut"
      @navigate-space-menu="onSpaceMenuAction"
    />
    <div class="body-grid">
      <SidebarNav
        :current-view="currentView"
        :org-type="ctx.orgType"
        @navigate="onNavigate"
      />
      <div class="main-col">
        <main class="main">
          <div class="views">
            <PlaceholderView
              v-if="currentView === 'placeholder'"
              :message="placeholderMessage"
            />
            <component
              v-else-if="isEcommerce"
              :is="currentComponent"
              :header-exchange="currentView === 'chat' ? headerExchange : null"
              @logged-out="onLoggedOut"
            />
            <component
              v-else
              :is="currentComponent"
              :ouid="ctx.ouid"
              @logged-out="onLoggedOut"
            />
          </div>
        </main>
      </div>
    </div>
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
  display: flex;
  flex-direction: column;
}
.body-grid {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 236px 1fr;
}
.main-col {
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.main {
  padding: 22px;
  min-width: 0;
}
.views {
  min-width: 0;
}
@media (max-width: 980px) {
  .body-grid {
    grid-template-columns: 1fr;
  }
}
</style>
