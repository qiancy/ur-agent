import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import App from './App.vue'
import { setAuthenticated } from './api/session'

const loginMock = vi.fn()
const myOrganizationsMock = vi.fn()
const switchOrganizationMock = vi.fn()

vi.mock('./api/auth', () => ({
  loginAccount: (...args: unknown[]) => loginMock(...args),
  myOrganizations: (...args: unknown[]) => myOrganizationsMock(...args),
  switchOrganization: (...args: unknown[]) => switchOrganizationMock(...args),
}))

vi.mock('./views/WorkbenchView.vue', () => ({
  default: { name: 'WorkbenchView', template: '<div class="view-workbench" data-test="workbench">经营工作台</div>' },
}))
vi.mock('./views/ProductsView.vue', () => ({
  default: { name: 'ProductsView', template: '<div class="view-products" data-test="products-view">商品</div>' },
}))
vi.mock('./views/StockView.vue', () => ({
  default: { name: 'StockView', template: '<div class="view-stock" data-test="stock-view">库存</div>' },
}))
vi.mock('./views/MovementsView.vue', () => ({
  default: { name: 'MovementsView', template: '<div class="view-movements" data-test="movements-view">库存流水</div>' },
}))
vi.mock('./views/SummaryView.vue', () => ({
  default: {
    name: 'SummaryView',
    emits: ['logged-out'],
    template:
      '<div class="view-summary" data-test="summary-view">经营摘要<button data-test="trigger-logout" @click="$emit(\'logged-out\')">触发登出</button></div>',
  },
}))
vi.mock('./views/ChatView.vue', () => ({
  default: { name: 'ChatView', template: '<div class="view-chat" data-test="chat-view">Seller AI</div>' },
}))
vi.mock('./views/GenericSpaceView.vue', () => ({
  default: {
    name: 'GenericSpaceView',
    props: ['ouid', 'activeSection'],
    emits: ['logged-out'],
    template:
      '<div class="view-generic" data-test="generic-space" :data-section="activeSection">空间观察 {{ ouid }} {{ activeSection }}</div>',
  },
}))
vi.mock('./views/SpaceManageView.vue', () => ({
  default: { name: 'SpaceManageView', template: '<div data-test="space-manage">管理空间</div>' },
}))
vi.mock('./views/SpaceCreateView.vue', () => ({
  default: { name: 'SpaceCreateView', template: '<div data-test="space-create">创建空间</div>' },
}))
vi.mock('./views/JoinSpaceView.vue', () => ({
  default: { name: 'JoinSpaceView', template: '<div data-test="space-join">加入空间</div>' },
}))
vi.mock('./views/ReviewRequestsView.vue', () => ({
  default: { name: 'ReviewRequestsView', template: '<div data-test="space-review">审核申请</div>' },
}))
vi.mock('./views/LeaveSpaceView.vue', () => ({
  default: { name: 'LeaveSpaceView', template: '<div data-test="space-leave">退出空间</div>' },
}))

const ORGANIZATIONS = [
  { ouid: 'shop_demo', name: '示例店铺', type: 'ecommerce', role: 'owner' },
  { ouid: 'family', name: '我的家庭', type: 'family', role: 'member' },
  { ouid: 'personal', name: '个人空间', type: 'personal', role: 'owner' },
]

const LOGIN_RESULT = {
  access_token: 'token-1',
  token_type: 'bearer',
  person: { puid: 'shopkeeper', name: '店主' },
  organization: { ouid: 'shop_demo', name: '示例店铺', type: 'ecommerce' },
  membership: { role: 'owner' },
  system_role: 'user',
  organizations: ORGANIZATIONS,
  requires_organization: false,
}

const FAMILY_RESULT = {
  access_token: 'token-2',
  token_type: 'bearer',
  person: { puid: 'shopkeeper', name: '店主' },
  organization: { ouid: 'family', name: '我的家庭', type: 'family' },
  membership: { role: 'member' },
  system_role: 'user',
  organizations: ORGANIZATIONS,
  requires_organization: false,
}

const PERSONAL_RESULT = {
  access_token: 'token-3',
  token_type: 'bearer',
  person: { puid: 'shopkeeper', name: '店主' },
  organization: { ouid: 'personal', name: '个人空间', type: 'personal' },
  membership: { role: 'owner' },
  system_role: 'user',
  organizations: ORGANIZATIONS,
  requires_organization: false,
}

beforeEach(() => {
  localStorage.clear()
  window.history.replaceState(null, '', '/')
  setAuthenticated(false)
  loginMock.mockReset()
  loginMock.mockResolvedValue(LOGIN_RESULT)
  myOrganizationsMock.mockReset()
  myOrganizationsMock.mockResolvedValue(ORGANIZATIONS)
  switchOrganizationMock.mockReset()
  switchOrganizationMock.mockImplementation((ouid: string) => {
    if (ouid === 'family') return Promise.resolve(FAMILY_RESULT)
    if (ouid === 'personal') return Promise.resolve(PERSONAL_RESULT)
    return Promise.resolve(LOGIN_RESULT)
  })
})

afterEach(() => {
  vi.unstubAllGlobals()
  window.history.replaceState(null, '', '/')
})

async function login(wrapper: ReturnType<typeof mount>) {
  await wrapper.find('input[data-test="login"]').setValue('shopkeeper')
  await wrapper.find('input[data-test="password"]').setValue('pass123')
  await wrapper.find('form').trigger('submit')
  await flushPromises()
}

function mountAuthed(ctx = {
  personName: '店主',
  puid: 'shopkeeper',
  organizationName: '示例店铺',
  ouid: 'shop_demo',
  orgType: 'ecommerce',
  role: 'owner',
}) {
  localStorage.setItem('unires_token', 'existing-token')
  localStorage.setItem('unires_ctx', JSON.stringify(ctx))
  setAuthenticated(true)
  return mount(App)
}

describe('App shell', () => {
  it('shows the login view when there is no token', () => {
    const wrapper = mount(App)
    expect(wrapper.find('[data-test="login"]').exists()).toBe(true)
  })

  it('uses the two-column layout only after login', async () => {
    const wrapper = mount(App)
    expect(wrapper.find('[data-test="auth-area"]').exists()).toBe(true)

    await login(wrapper)

    expect(wrapper.find('.shell.authed').exists()).toBe(true)
    expect(wrapper.find('[data-test="auth-area"]').exists()).toBe(false)
  })

  it('places the header full-width on top, above the sidebar+main body grid', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    const shell = wrapper.find('.shell.authed')
    const header = shell.find('[data-test="app-header"]')
    expect(header.exists()).toBe(true)
    expect(shell.element.firstElementChild).toBe(header.element)
    expect(shell.find('.body-grid').element.previousElementSibling).toBe(header.element)
  })

  it('returns to the login view when the session is unauthenticated', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    setAuthenticated(false)
    await nextTick()

    expect(wrapper.find('[data-test="login"]').exists()).toBe(true)
    expect(wrapper.find('.shell.authed').exists()).toBe(false)
  })

  it('shows the Seller workbench by default after ecommerce login and writes the URL', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    expect(wrapper.find('[data-test="workbench"]').exists()).toBe(true)
    expect(window.location.search).toBe('?view=workbench')
  })

  it('navigates through Sidebar by URL-backed view keys', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    await wrapper.find('[data-view="stock"]').trigger('click')
    await nextTick()

    expect(wrapper.find('[data-test="stock-view"]').exists()).toBe(true)
    expect(window.location.search).toBe('?view=stock')
  })

  it('restores the current view from the URL on refresh-like mount', async () => {
    window.history.replaceState(null, '', '/workbench?view=stock')
    const wrapper = mountAuthed()
    await flushPromises()

    expect(wrapper.find('[data-test="stock-view"]').exists()).toBe(true)
    expect(wrapper.find('[data-view="stock"]').classes()).toContain('active')
  })

  it('returns to login when a rendered view emits logged-out', async () => {
    const wrapper = mountAuthed()
    await flushPromises()

    await wrapper.find('[data-view="summary"]').trigger('click')
    await nextTick()
    await wrapper.find('[data-test="trigger-logout"]').trigger('click')
    await nextTick()

    expect(localStorage.getItem('unires_token')).toBeNull()
    expect(wrapper.find('[data-test="login"]').exists()).toBe(true)
  })
})

describe('organization switching', () => {
  it('renders the current user and organization in the header after login', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    expect(wrapper.find('[data-test="app-header"]').text()).toContain('示例店铺')
    expect(wrapper.find('[data-test="app-header"]').text()).toContain('店主')
  })

  it('pulls the organization list after login and lists them in the dropdown', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    expect(myOrganizationsMock).toHaveBeenCalled()
    expect(wrapper.findAll('select[data-test="org-switch"] option')).toHaveLength(3)
  })

  it('switches organization by posting only ouid and clamps illegal views', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    await wrapper.find('[data-view="stock"]').trigger('click')
    await nextTick()
    expect(window.location.search).toBe('?view=stock')

    await wrapper.find('select[data-test="org-switch"]').setValue('family')
    await flushPromises()

    expect(switchOrganizationMock).toHaveBeenCalledWith('family')
    expect(wrapper.find('[data-test="app-header"]').text()).toContain('我的家庭')
    expect(JSON.parse(localStorage.getItem('unires_ctx')!).ouid).toBe('family')
    expect(wrapper.find('[data-test="generic-space"]').attributes('data-section')).toBe('overview')
    expect(window.location.search).toBe('?view=overview')
  })

  it('shows generic space navigation for non-ecommerce orgs without Seller keys', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    await wrapper.find('select[data-test="org-switch"]').setValue('family')
    await flushPromises()

    expect(wrapper.find('[data-view="overview"]').exists()).toBe(true)
    expect(wrapper.find('[data-view="resources"]').exists()).toBe(true)
    expect(wrapper.find('[data-view="seller-ai"]').exists()).toBe(false)
    expect(wrapper.find('[data-view="stock"]').exists()).toBe(false)

    await wrapper.find('[data-view="resources"]').trigger('click')
    await nextTick()
    expect(wrapper.find('[data-test="generic-space"]').attributes('data-section')).toBe('resources')
    expect(window.location.search).toBe('?view=resources')
  })

  it('does not expose space leave for personal workspaces', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    await wrapper.find('select[data-test="org-switch"]').setValue('personal')
    await flushPromises()

    expect(wrapper.find('[data-view="space-leave"]').exists()).toBe(false)
    expect(wrapper.find('[data-view="seller-ai"]').exists()).toBe(false)
  })
})
