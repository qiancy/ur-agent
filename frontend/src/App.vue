<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, shallowRef } from 'vue'
import { getToken, clearToken } from './api/client'
import { isAuthenticated, setAuthenticated } from './api/session'
import type { SellerLoginResult } from './api/seller'
import {
  myOrganizations,
  switchOrganization,
  type UserOrganization,
} from './api/auth'
import LoginView from './views/LoginView.vue'
import PlaceholderView from './views/PlaceholderView.vue'
import SidebarNav from './components/SidebarNav.vue'
import AppHeader from './components/AppHeader.vue'
import {
  getWorkspaceDefinition,
  filterNavItems,
  clampToAllowedView,
  type WorkspaceDefinition,
  type WorkspaceCapability,
} from './workspace/registry'

const CTX_KEY = 'unires_ctx'
const VIEW_QUERY = 'view'

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
const organizations = ref<UserOrganization[]>([])
const headerExchange = ref<Exchange | null>(null)
const placeholderMessage = ref('功能即将开放')

// URL state
const currentView = ref<WorkspaceCapability>('overview')
const workspaceDefinition = shallowRef<WorkspaceDefinition | null>(null)
const navItems = computed(() => {
  if (!workspaceDefinition.value) return []
  return filterNavItems(workspaceDefinition.value.navItems, ctx.value.role)
})
const currentNavItem = computed(() =>
  navItems.value.find((item) => item.key === currentView.value) ?? navItems.value[0],
)
const currentComponent = computed(() => currentNavItem.value?.component ?? PlaceholderView)
const currentSection = computed(() => currentNavItem.value?.section)
const isGovernanceView = computed(() =>
  ['space-manage', 'space-create', 'space-join', 'space-review', 'space-leave'].includes(currentView.value),
)

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

function readViewFromUrl(): string | undefined {
  try {
    const params = new URLSearchParams(window.location.search)
    return params.get(VIEW_QUERY) ?? undefined
  } catch {
    // ignore
  }
  return undefined
}

function writeViewToUrl(view: WorkspaceCapability, replace = false) {
  try {
    const url = new URL(window.location.href)
    url.searchParams.set(VIEW_QUERY, view)
    const href = url.toString()
    if (replace) {
      window.history.replaceState(null, '', href)
    } else {
      window.history.pushState(null, '', href)
    }
  } catch {
    // jsdom may not support pushState with about:blank; ignore
  }
}

function applyView(view: WorkspaceCapability, replace = false) {
  currentView.value = view
  writeViewToUrl(view, replace)
}

function applyWorkspaceDefinition(orgType: string, role: string) {
  const def = getWorkspaceDefinition(orgType)
  workspaceDefinition.value = def
  try {
    const params = new URLSearchParams(window.location.search)
    const hasUrlView = params.has(VIEW_QUERY)
    if (hasUrlView) {
      const requested = readViewFromUrl()
      const clamped = clampToAllowedView(requested, def, role)
      applyView(clamped, true)
    } else {
      applyView(def.defaultView, true)
    }
  } catch {
    applyView(def.defaultView, true)
  }
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
  if (!result.organization || !result.access_token || !result.membership) {
    setAuthenticated(false)
    return
  }
  applyWorkspaceDefinition(result.organization.type, result.membership.role)
  headerExchange.value = null
  setAuthenticated(true)
  await refreshOrganizations()
}

async function onSwitchOrganization(ouid: string) {
  if (ouid === ctx.value.ouid) return
  try {
    const result = await switchOrganization(ouid)
    applyContext(result)
    if (!result.organization || !result.membership) return
    applyWorkspaceDefinition(result.organization.type, result.membership.role)
  } catch {
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
  currentView.value = 'overview'
  workspaceDefinition.value = null
}

function onNavigate(view: string) {
  if (navItems.value.some((item) => item.key === view)) {
    applyView(view as WorkspaceCapability)
  }
}

function onSpaceMenuAction(action: string) {
  const viewMap: Record<string, string> = {
    manage: 'space-manage',
    create: 'space-create',
    join: 'space-join',
    review: 'space-review',
    leave: 'space-leave',
  }
  const target = viewMap[action]
  if (target && navItems.value.some((item) => item.key === target)) {
    applyView(target as WorkspaceCapability)
  }
}

function onContextUpdated(result: SellerLoginResult) {
  if (!result.organization || !result.access_token || !result.membership) return
  applyContext(result)
  applyWorkspaceDefinition(result.organization.type, result.membership.role)
  headerExchange.value = null
  placeholderMessage.value = '功能即将开放'
  setAuthenticated(true)
  refreshOrganizations()
}

async function onLeaveConfirmed() {
  await refreshOrganizations()
  const personal = organizations.value.find((o) => o.type === 'personal')
  if (!personal) {
    onLoggedOut()
    return
  }
  try {
    const result = await switchOrganization(personal.ouid)
    onContextUpdated(result)
  } catch {
    onLoggedOut()
  }
}

function onNavigateSpace(action: string) {
  onSpaceMenuAction(action)
}

// Handle browser back/forward
function onPopState() {
  if (!workspaceDefinition.value) return
  try {
    const requested = readViewFromUrl()
    const clamped = clampToAllowedView(requested, workspaceDefinition.value, ctx.value.role)
    if (requested !== clamped) {
      applyView(clamped, true)
    } else {
      currentView.value = clamped
    }
  } catch {
    // ignore URL parsing errors
  }
}

onMounted(() => {
  window.addEventListener('popstate', onPopState)
  if (getToken() && ctx.value.ouid) {
    applyWorkspaceDefinition(ctx.value.orgType, ctx.value.role)
    refreshOrganizations()
  }
})

onUnmounted(() => {
  window.removeEventListener('popstate', onPopState)
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
        :nav-items="navItems"
        @navigate="onNavigate"
      />
      <div class="main-col">
        <main class="main">
          <div class="views">
            <component
              v-if="isGovernanceView"
              :is="currentComponent"
              :ouid="ctx.ouid"
              :org-type="ctx.orgType"
              :role="ctx.role"
              :puid="ctx.puid"
              :person-name="ctx.personName"
              :organization-name="ctx.organizationName"
              @navigate-space="onNavigateSpace"
              @context-updated="onContextUpdated"
              @leave-confirmed="onLeaveConfirmed"
              @logged-out="onLoggedOut"
            />
            <component
              v-else-if="currentSection"
              :is="currentComponent"
              :ouid="ctx.ouid"
              :active-section="currentSection"
              @logged-out="onLoggedOut"
            />
            <component
              v-else
              :is="currentComponent"
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
  background: var(--bg, #f8fafc);
  color: var(--ink, #17202a);
}
.shell {
  min-height: 100vh;
  background: var(--bg, #f8fafc);
  color: var(--ink, #17202a);
  display: flex;
  flex-direction: column;
}
.body-grid {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 220px 1fr;
}
.main-col {
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.main {
  padding: 22px;
  min-width: 0;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
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
