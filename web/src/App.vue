<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getToken, clearToken } from './api/client'
import { isAuthenticated, setAuthenticated } from './api/session'
import { sellerChat, type SellerLoginResult } from './api/seller'
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

async function refreshOrganizations() {
  try {
    organizations.value = await myOrganizations()
  } catch {
    organizations.value = []
  }
}

function applyContext(result: SellerLoginResult) {
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
  currentView.value = 'workbench'
  headerExchange.value = null
  setAuthenticated(true)
  await refreshOrganizations()
}

async function onSwitchOrganization(ouid: string) {
  if (ouid === ctx.value.ouid) return
  try {
    const result = await switchOrganization(ouid)
    applyContext(result)
  } catch {
    // token/ctx unchanged; keep the old selection via the dropdown value
    await refreshOrganizations()
    return
  }
  currentView.value = 'workbench'
  headerExchange.value = null
  await refreshOrganizations()
}

async function onHeaderAsk(message: string) {
  if (!isEcommerce.value) return
  try {
    const result = await sellerChat(message)
    headerExchange.value = { question: message, answer: result.response }
  } catch (e) {
    headerExchange.value = {
      question: message,
      answer: e instanceof Error ? e.message : 'AI 处理失败，请稍后重试',
    }
  }
  currentView.value = 'chat'
}

function onLoggedOut() {
  clearToken()
  localStorage.removeItem(CTX_KEY)
  setAuthenticated(false)
  currentView.value = 'workbench'
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

onMounted(() => {
  if (getToken()) {
    refreshOrganizations()
  }
})
</script>

<template>
  <div v-if="authenticated" class="shell authed">
    <SidebarNav :current-view="currentView" @navigate="currentView = $event" />
    <div class="main-col">
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
        @ask="onHeaderAsk"
      />
      <main class="main">
        <div v-if="isEcommerce" class="views">
          <component
            :is="currentComponent"
            :header-exchange="currentView === 'chat' ? headerExchange : null"
            @logged-out="onLoggedOut"
          />
        </div>
        <div v-else class="empty" data-test="non-ecommerce-empty">
          <p class="empty-title">该业务形态暂未接入经营工作台</p>
          <p class="empty-sub">
            当前空间为 {{ ctx.orgType }} · {{ ctx.organizationName }}，Seller
            经营工作台仅面向 ecommerce 空间。
          </p>
        </div>
      </main>
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
  display: grid;
  grid-template-columns: 1fr;
}
.shell.authed {
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
.empty {
  background: var(--panel, #ffffff);
  border: 1px solid var(--line, #d8dee8);
  border-radius: 8px;
  padding: 48px 24px;
  text-align: center;
}
.empty-title {
  margin: 0;
  font-size: 18px;
  font-weight: 750;
}
.empty-sub {
  margin: 8px 0 0;
  color: var(--muted, #637083);
  font-size: 13px;
}
@media (max-width: 980px) {
  .shell.authed {
    grid-template-columns: 1fr;
  }
}
</style>
