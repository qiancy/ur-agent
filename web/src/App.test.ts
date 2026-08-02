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

const LOGIN_RESULT = {
  access_token: 'token-1',
  token_type: 'bearer',
  person: { puid: 'shopkeeper', name: '店主' },
  organization: { ouid: 'shop_demo', name: '示例店铺', type: 'ecommerce' },
  membership: { role: 'owner' },
  system_role: 'user',
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
  switchOrganizationMock.mockResolvedValue(FAMILY_RESULT)
  sellerSummaryMock.mockReset()
  sellerStockMock.mockReset()
  sellerMovementsMock.mockReset()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

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
    await wrapper.find('input[data-test="login"]').setValue('shopkeeper@shop_demo')
    await wrapper.find('input[data-test="password"]').setValue('pass123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.shell.authed').exists()).toBe(true)
    expect(wrapper.find('[data-test="auth-area"]').exists()).toBe(false)
  })

  it('returns to the login view when the session is unauthenticated (401 path)', async () => {
    const wrapper = mount(App)
    await wrapper.find('input[data-test="login"]').setValue('shopkeeper@shop_demo')
    await wrapper.find('input[data-test="password"]').setValue('pass123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('.view-workbench').exists()).toBe(true)

    setAuthenticated(false)
    await nextTick()

    expect(wrapper.find('[data-test="login"]').exists()).toBe(true)
    expect(wrapper.find('.view-workbench').exists()).toBe(false)
  })

  it('returns to the login view when a view emits logged-out', async () => {
    localStorage.setItem('unires_token', 'existing-token')
    localStorage.setItem(
      'unires_ctx',
      JSON.stringify({
        personName: '店主',
        puid: 'shopkeeper',
        organizationName: '示例店铺',
        ouid: 'shop_demo',
        orgType: 'ecommerce',
        role: 'owner',
      }),
    )
    const wrapper = mount(App)
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
    await wrapper.find('input[data-test="login"]').setValue('shopkeeper@shop_demo')
    await wrapper.find('input[data-test="password"]').setValue('pass123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('.view-workbench').exists()).toBe(true)
    expect(wrapper.find('.view-stock').exists()).toBe(false)
  })

  it('navigates to the selected view when a nav item is clicked', async () => {
    const wrapper = mount(App)
    await wrapper.find('input[data-test="login"]').setValue('shopkeeper@shop_demo')
    await wrapper.find('input[data-test="password"]').setValue('pass123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    await wrapper.find('[data-view="movements"]').trigger('click')
    expect(wrapper.find('.view-movements').exists()).toBe(true)

    await wrapper.find('[data-view="chat"]').trigger('click')
    expect(wrapper.find('.view-chat').exists()).toBe(true)
  })

  it('returns to the workbench on refresh-like remount when a token exists', () => {
    localStorage.setItem('unires_token', 'existing-token')
    localStorage.setItem(
      'unires_ctx',
      JSON.stringify({
        personName: '店主',
        puid: 'shopkeeper',
        organizationName: '示例店铺',
        ouid: 'shop_demo',
        orgType: 'ecommerce',
        role: 'owner',
      }),
    )
    const wrapper = mount(App)
    expect(wrapper.find('.view-workbench').exists()).toBe(true)
  })

  it('logs out and returns to login via the header', async () => {
    localStorage.setItem('unires_token', 'existing-token')
    const wrapper = mount(App)

    await wrapper.find('[data-test="header-logout"]').trigger('click')

    expect(localStorage.getItem('unires_token')).toBeNull()
    expect(wrapper.find('[data-test="login"]').exists()).toBe(true)
  })
})

describe('FE-08 organization switching', () => {
  it('renders the current user and organization in the header after login', async () => {
    const wrapper = mount(App)
    await wrapper.find('input[data-test="login"]').setValue('shopkeeper@shop_demo')
    await wrapper.find('input[data-test="password"]').setValue('pass123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.find('[data-test="app-header"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="app-header"]').text()).toContain('示例店铺')
    expect(wrapper.find('[data-test="app-header"]').text()).toContain('店主')
  })

  it('pulls the organization list after login and lists them in the dropdown', async () => {
    const wrapper = mount(App)
    await wrapper.find('input[data-test="login"]').setValue('shopkeeper@shop_demo')
    await wrapper.find('input[data-test="password"]').setValue('pass123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(myOrganizationsMock).toHaveBeenCalled()
    const options = wrapper.findAll('select[data-test="org-switch"] option')
    expect(options).toHaveLength(2)
  })

  it('switches organization by posting only ouid and updates token + context', async () => {
    const wrapper = mount(App)
    await wrapper.find('input[data-test="login"]').setValue('shopkeeper@shop_demo')
    await wrapper.find('input[data-test="password"]').setValue('pass123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    await wrapper.find('select[data-test="org-switch"]').setValue('family')
    await flushPromises()

    expect(switchOrganizationMock).toHaveBeenCalledWith('family')
    expect(wrapper.find('[data-test="app-header"]').text()).toContain('我的家庭')
    expect(JSON.parse(localStorage.getItem('unires_ctx')!).ouid).toBe('family')
    // family is non-ecommerce: the empty state shows instead of the workbench
    expect(wrapper.find('[data-test="non-ecommerce-empty"]').exists()).toBe(true)
  })

  it('shows an empty state for non-ecommerce orgs and never calls seller APIs', async () => {
    const wrapper = mount(App)
    await wrapper.find('input[data-test="login"]').setValue('shopkeeper@shop_demo')
    await wrapper.find('input[data-test="password"]').setValue('pass123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    sellerSummaryMock.mockClear()
    sellerStockMock.mockClear()
    sellerMovementsMock.mockClear()

    await wrapper.find('select[data-test="org-switch"]').setValue('family')
    await flushPromises()

    expect(wrapper.find('[data-test="non-ecommerce-empty"]').exists()).toBe(true)
    expect(wrapper.find('.view-workbench').exists()).toBe(false)
    expect(sellerSummaryMock).not.toHaveBeenCalled()
    expect(sellerStockMock).not.toHaveBeenCalled()
    expect(sellerMovementsMock).not.toHaveBeenCalled()
  })
})

describe('FE-08 header AI', () => {
  it('asks the seller chat only through /seller/chat and switches to the AI view', async () => {
    sellerChatMock.mockResolvedValue({
      response: '当前低库存 2 项',
      ouid: 'shop_demo',
    })
    const wrapper = mount(App)
    await wrapper.find('input[data-test="login"]').setValue('shopkeeper@shop_demo')
    await wrapper.find('input[data-test="password"]').setValue('pass123')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    await wrapper.find('input[data-test="header-ai"]').setValue('低库存有哪些')
    await wrapper.find('input[data-test="header-ai"]').trigger('keyup.enter')
    await flushPromises()

    expect(sellerChatMock).toHaveBeenCalledTimes(1)
    expect(sellerChatMock).toHaveBeenCalledWith('低库存有哪些')
    expect(wrapper.find('.view-chat').exists()).toBe(true)
  })
})
