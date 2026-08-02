import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import App from './App.vue'

const sellerLoginMock = vi.fn()

vi.mock('./api/seller', () => ({
  sellerLogin: (...args: unknown[]) => sellerLoginMock(...args),
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
  default: { name: 'SummaryView', template: '<div class="view-summary">经营摘要</div>' },
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

beforeEach(() => {
  localStorage.clear()
  sellerLoginMock.mockReset()
  sellerLoginMock.mockResolvedValue(LOGIN_RESULT)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('App shell', () => {
  it('shows the login view when there is no token', () => {
    const wrapper = mount(App)
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
    const wrapper = mount(App)
    expect(wrapper.find('.view-workbench').exists()).toBe(true)
  })

  it('logs out and returns to login', async () => {
    localStorage.setItem('unires_token', 'existing-token')
    const wrapper = mount(App)

    await wrapper.find('[data-test="logout"]').trigger('click')

    expect(localStorage.getItem('unires_token')).toBeNull()
    expect(wrapper.find('[data-test="login"]').exists()).toBe(true)
  })
})
