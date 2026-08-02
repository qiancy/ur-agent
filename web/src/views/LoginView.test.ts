import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import LoginView from './LoginView.vue'

const loginMock = vi.fn()

vi.mock('../api/seller', () => ({
  sellerLogin: (...args: unknown[]) => loginMock(...args),
}))

const RESULT = {
  access_token: 'token-1',
  token_type: 'bearer',
  person: { puid: 'shopkeeper', name: '店主' },
  organization: { ouid: 'shop_demo', name: '示例店铺', type: 'ecommerce' },
  membership: { role: 'owner' },
  system_role: 'user',
}

describe('LoginView', () => {
  beforeEach(() => {
    loginMock.mockReset()
  })

  it('renders a login form with login/password fields', () => {
    const wrapper = mount(LoginView)
    expect(wrapper.find('input[data-test="login"]').exists()).toBe(true)
    expect(wrapper.find('input[data-test="password"]').exists()).toBe(true)
    expect(wrapper.find('form').exists()).toBe(true)
  })

  it('calls sellerLogin with the entered credentials and emits authenticated on success', async () => {
    loginMock.mockResolvedValue(RESULT)
    const wrapper = mount(LoginView)

    await wrapper.find('input[data-test="login"]').setValue('shopkeeper@shop_demo')
    await wrapper.find('input[data-test="password"]').setValue('pass123')
    await wrapper.find('form').trigger('submit')

    expect(loginMock).toHaveBeenCalledWith('shopkeeper@shop_demo', 'pass123')
    expect(wrapper.emitted('authenticated')).toBeTruthy()
    expect(wrapper.emitted('authenticated')![0]).toEqual([RESULT])
  })

  it('shows an error message and does not emit on failed login', async () => {
    loginMock.mockRejectedValue(new Error('Invalid credentials'))
    const wrapper = mount(LoginView)

    await wrapper.find('input[data-test="login"]').setValue('shopkeeper@shop_demo')
    await wrapper.find('input[data-test="password"]').setValue('wrong')
    await wrapper.find('form').trigger('submit')

    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('authenticated')).toBeUndefined()
    expect(wrapper.text()).toContain('Invalid credentials')
  })
})
