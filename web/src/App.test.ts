import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'
import App from './App.vue'
import { setAuthenticated } from './api/session'

const sellerLoginMock = vi.fn()
const sellerChatMock = vi.fn()
const sellerSummaryMock = vi.fn()
const sellerStockMock = vi.fn()
const sellerMovementsMock = vi.fn()
const myOrganizationsMock = vi.fn()
const switchOrganizationMock = vi.fn()

vi.mock('./api/seller', () => ({
  sellerLogin: (...args: unknown[]) => sellerLoginMock(...args),
  sellerChat: (...args: unknown[]) => sellerChatMock(...args),
  sellerSummary: (...args: unknown[]) => sellerSummaryMock(...args),
  sellerStock: (...args: unknown[]) => sellerStockMock(...args),
  sellerInventoryMovements: (...args: unknown[]) => sellerMovementsMock(...args),
}))

vi.mock('./api/auth', () => ({
  loginAccount: (...args: unknown[]) => sellerLoginMock(...args),
  myOrganizations: (...args: unknown[]) => myOrganizationsMock(...args),
  switchOrganization: (...args: unknown[]) => switchOrganizationMock(...args),
}))

vi.mock('./views/WorkbenchView.vue', () => ({
  default: {
    name: 'WorkbenchView',
    template: '<div class="view-workbench">经营工作台</div>',
  },
}))
vi.mock('./views/StockView.vue', () => ({
  default: { name: 'StockView', template: '<div class="view-stock">库存</div>' },
}))
vi.mock('./views/MovementsView.vue', () => ({
  default: { name: 'MovementsView', template: '<div class="view-movements">库存流水</div>' },
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
  default: { name: 'ChatView', template: '<div class="view-chat">Seller AI</div>' },
}))
vi.mock('./views/ProductsView.vue', () => ({
  default: {
    name: 'ProductsView',
    emits: ['logged-out'],
    template: '<div class="view-products" data-test="products-view">商品管理</div>',
  },
}))
vi.mock('./views/GenericSpaceView.vue', () => ({
  default: {
    name: 'GenericSpaceView',
    props: ['ouid'],
    template:
      '<div class="view-generic" data-test="generic-space">空间观察({{ ouid }})</div>',
  },
}))
vi.mock('./views/SpaceManageView.vue', () => ({
  default: {
    name: 'SpaceManageView',
    template: '<div class="view-space-manage" data-test="space-manage">管理空间</div>',
  },
}))
vi.mock('./views/SpaceCreateView.vue', () => ({
  default: {
    name: 'SpaceCreateView',
    template: '<div class="view-space-create" data-test="space-create">创建空间</div>',
  },
}))
vi.mock('./views/JoinSpaceView.vue', () => ({
  default: {
    name: 'JoinSpaceView',
    template: '<div class="view-space-join" data-test="space-join">加入空间</div>',
  },
}))
vi.mock('./views/ReviewRequestsView.vue', () => ({
  default: {
    name: 'ReviewRequestsView',
    template: '<div class="view-space-review" data-test="space-review">审核申请</div>',
  },
}))
vi.mock('./views/LeaveSpaceView.vue', () => ({
  default: {
    name: 'LeaveSpaceView',
    template: '<div class="view-space-leave" data-test="space-leave">退出空间</div>',
  },
}))

const LOGIN_RESULT = {
  access_token: 'token-1',
  token_type: 'bearer',
  person: { puid: 'shopkeeper', name: '店主' },
  organization: { ouid: 'shop_demo', name: '示例店铺', type: 'ecommerce' },
  membership: { role: 'owner' },
  system_role: 'user',
  organizations: [
    { ouid: 'shop_demo', name: '示例店铺', type: 'ecommerce', role: 'owner' },
    { ouid: 'family', name: '我的家庭', type: 'family', role: 'member' },
  ],
  requires_organization: false,
}

const ORG_LIST = [
  { ouid: 'shop_demo', name: '示例店铺', type: 'ecommerce', role: 'owner' },
  { ouid: 'family', name: '我的家庭', type: 'family', role: 'member' },
]

const FAMILY_RESULT = {
  access_token: 'token-2',
  token_type: 'bearer',
  person: { puid: 'shopkeeper', name: '店主' },
  organization: { ouid: 'family', name: '我的家庭', type: 'family' },
  membership: { role: 'member' },
  system_role: 'user',
  organizations: ORG_LIST,
  requires_organization: false,
}

const ECOMMERCE_CTX = {
  personName: '店主',
  puid: 'shopkeeper',
  organizationName: '示例店铺',
  ouid: 'shop_demo',
  orgType: 'ecommerce',
  role: 'owner',
}

beforeEach(() => {
  localStorage.clear()
  setAuthenticated(false)
  sellerLoginMock.mockReset()
  sellerLoginMock.mockResolvedValue(LOGIN_RESULT)
  sellerChatMock.mockReset()
  myOrganizationsMock.mockReset()
  myOrganizationsMock.mockResolvedValue(ORG_LIST)
  switchOrganizationMock.mockReset()
  switchOrganizationMock.mockImplementation((ouid: string) =>
    ouid === 'family'
      ? Promise.resolve(FAMILY_RESULT)
      : Promise.resolve(LOGIN_RESULT),
  )
  sellerSummaryMock.mockReset()
  sellerStockMock.mockReset()
  sellerMovementsMock.mockReset()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

async function login(wrapper: ReturnType<typeof mount>) {
  await wrapper.find('input[data-test="login"]').setValue('shopkeeper')
  await wrapper.find('input[data-test="password"]').setValue('pass123')
  await wrapper.find('form').trigger('submit')
  await flushPromises()
}

function mountAuthed(localCtx: Record<string, string> = ECOMMERCE_CTX) {
  localStorage.setItem('unires_token', 'existing-token')
  localStorage.setItem('unires_ctx', JSON.stringify(localCtx))
  return mount(App)
}

describe('App shell', () => {
  it('shows the login view when there is no token', () => {
    const wrapper = mount(App)
    expect(wrapper.find('[data-test="login"]').exists()).toBe(true)
  })

  it('centers the login card full-width, outside the two-column shell', () => {
    const wrapper = mount(App)
    expect(wrapper.find('[data-test="auth-area"]').exists()).toBe(true)
    expect(wrapper.find('.shell.authed').exists()).toBe(false)
  })

  it('uses the two-column layout only after login', async () => {
    const wrapper = mount(App)
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

    const body = shell.find('.body-grid')
    expect(body.exists()).toBe(true)
    expect(body.find('.side').exists()).toBe(true)
    expect(body.find('.main').exists()).toBe(true)
    expect(body.element.previousElementSibling).toBe(header.element)
  })

  it('returns to the login view when the session is unauthenticated (401 path)', async () => {
    const wrapper = mount(App)
    await login(wrapper)
    expect(wrapper.find('.view-workbench').exists()).toBe(true)

    setAuthenticated(false)
    await nextTick()

    expect(wrapper.find('[data-test="login"]').exists()).toBe(true)
    expect(wrapper.find('.view-workbench').exists()).toBe(false)
  })

  it('returns to the login view when a view emits logged-out', async () => {
    const wrapper = mountAuthed()
    expect(wrapper.find('.view-workbench').exists()).toBe(true)

    await wrapper.find('[data-view="summary"]').trigger('click')
    expect(wrapper.find('[data-test="summary-view"]').exists()).toBe(true)

    await wrapper.find('[data-test="trigger-logout"]').trigger('click')
    await nextTick()

    expect(localStorage.getItem('unires_token')).toBeNull()
    expect(wrapper.find('[data-test="login"]').exists()).toBe(true)
  })

  it('shows the workbench by default after login', async () => {
    const wrapper = mount(App)
    await login(wrapper)
    expect(wrapper.find('.view-workbench').exists()).toBe(true)
    expect(wrapper.find('.view-stock').exists()).toBe(false)
  })

  it('navigates to the selected ecommerce view when a nav item is clicked', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    await wrapper.find('[data-view="movements"]').trigger('click')
    expect(wrapper.find('.view-movements').exists()).toBe(true)

    await wrapper.find('[data-view="chat"]').trigger('click')
    expect(wrapper.find('.view-chat').exists()).toBe(true)
  })

  it('opens the ProductsView for the products route key', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    await wrapper.find('[data-view="products"]').trigger('click')
    expect(wrapper.find('[data-test="products-view"]').exists()).toBe(true)
    expect(wrapper.find('.view-workbench').exists()).toBe(false)
  })

  it('returns to the workbench on refresh-like remount when a token exists', () => {
    const wrapper = mountAuthed()
    expect(wrapper.find('.view-workbench').exists()).toBe(true)
  })

  it('logs out and returns to login via the header', async () => {
    const wrapper = mountAuthed()
    await wrapper.find('[data-test="header-logout"]').trigger('click')
    expect(localStorage.getItem('unires_token')).toBeNull()
    expect(wrapper.find('[data-test="login"]').exists()).toBe(true)
  })
})

describe('organization switching', () => {
  it('renders the current user and organization in the header after login', async () => {
    const wrapper = mount(App)
    await login(wrapper)
    expect(wrapper.find('[data-test="app-header"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="app-header"]').text()).toContain('示例店铺')
    expect(wrapper.find('[data-test="app-header"]').text()).toContain('店主')
  })

  it('pulls the organization list after login and lists them in the dropdown', async () => {
    const wrapper = mount(App)
    await login(wrapper)
    expect(myOrganizationsMock).toHaveBeenCalled()
    const options = wrapper.findAll('select[data-test="org-switch"] option')
    expect(options).toHaveLength(2)
  })

  it('switches organization by posting only ouid and lands on the space overview', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    await wrapper.find('select[data-test="org-switch"]').setValue('family')
    await flushPromises()

    expect(switchOrganizationMock).toHaveBeenCalledWith('family')
    expect(wrapper.find('[data-test="app-header"]').text()).toContain('我的家庭')
    expect(JSON.parse(localStorage.getItem('unires_ctx')!).ouid).toBe('family')
    // family is non-ecommerce: the GenericSpaceView renders, no empty state
    expect(wrapper.find('[data-test="generic-space"]').exists()).toBe(true)
    expect(wrapper.find('.view-workbench').exists()).toBe(false)
  })

  it('renders GenericSpaceView for non-ecommerce orgs and never calls seller APIs', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    sellerSummaryMock.mockClear()
    sellerStockMock.mockClear()
    sellerMovementsMock.mockClear()

    await wrapper.find('select[data-test="org-switch"]').setValue('family')
    await flushPromises()

    expect(wrapper.find('[data-test="generic-space"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="non-ecommerce-empty"]').exists()).toBe(false)
    expect(sellerSummaryMock).not.toHaveBeenCalled()
    expect(sellerStockMock).not.toHaveBeenCalled()
    expect(sellerMovementsMock).not.toHaveBeenCalled()
  })

  it('clamps the current view to a legal key when switching back to ecommerce', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    await wrapper.find('select[data-test="org-switch"]').setValue('family')
    await flushPromises()
    expect(wrapper.find('[data-test="generic-space"]').exists()).toBe(true)

    await wrapper.find('select[data-test="org-switch"]').setValue('shop_demo')
    await flushPromises()
    expect(wrapper.find('.view-workbench').exists()).toBe(true)
  })

  it('shows space navigation for non-ecommerce orgs and navigates the overview', async () => {
    const wrapper = mount(App)
    await login(wrapper)
    await wrapper.find('select[data-test="org-switch"]').setValue('family')
    await flushPromises()

    expect(wrapper.find('[data-view="overview"]').exists()).toBe(true)
    expect(wrapper.find('[data-view="products"]').exists()).toBe(false)
    expect(wrapper.find('[data-view="chat"]').exists()).toBe(false)

    await wrapper.find('[data-view="resources"]').trigger('click')
    expect(wrapper.find('[data-test="generic-space"]').exists()).toBe(true)
  })
})

describe('space menu navigation', () => {
  it('routes 管理空间 to the real SpaceManageView (no placeholder)', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    await wrapper.find('[data-test="space-menu-toggle"]').trigger('click')
    await wrapper.find('[data-test="space-menu-item-manage"]').trigger('click')
    await nextTick()

    expect(wrapper.find('[data-test="placeholder-view"]').exists()).toBe(false)
    expect(wrapper.find('[data-test="space-manage"]').exists()).toBe(true)
  })

  it('routes 创建空间 to SpaceCreateView', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    await wrapper.find('[data-test="space-menu-toggle"]').trigger('click')
    await wrapper.find('[data-test="space-menu-item-create"]').trigger('click')
    await nextTick()

    expect(wrapper.find('[data-test="space-create"]').exists()).toBe(true)
  })

  it('routes 加入空间 to JoinSpaceView', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    await wrapper.find('[data-test="space-menu-toggle"]').trigger('click')
    await wrapper.find('[data-test="space-menu-item-join"]').trigger('click')
    await nextTick()

    expect(wrapper.find('[data-test="space-join"]').exists()).toBe(true)
  })

  it('routes 审核申请 to ReviewRequestsView', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    await wrapper.find('[data-test="space-menu-toggle"]').trigger('click')
    await wrapper.find('[data-test="space-menu-item-review"]').trigger('click')
    await nextTick()

    expect(wrapper.find('[data-test="space-review"]').exists()).toBe(true)
  })

  it('routes 退出空间 to LeaveSpaceView', async () => {
    const wrapper = mount(App)
    await login(wrapper)

    await wrapper.find('[data-test="space-menu-toggle"]').trigger('click')
    await wrapper.find('[data-test="space-menu-item-leave"]').trigger('click')
    await nextTick()

    expect(wrapper.find('[data-test="space-leave"]').exists()).toBe(true)
  })
})
